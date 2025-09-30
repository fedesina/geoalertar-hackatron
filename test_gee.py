#!/usr/bin/env python3
"""
test_gee_mod.py

Script de diagnóstico robusto para Google Earth Engine (GEE).
Propósito:
 - Hacer una única petición "de prueba" (batch) contra GEE usando 3 puntos del GeoJSON
 - Pedir NDVI, NBR, LST (°C) y precipitación acumulada (mm) en un rango seguro (mes anterior)
 - Imprimir la respuesta cruda (JSON) y un resumen legible

Instrucciones:
 - Colocar en la raíz de geoalertar_demo (junto a datos_geo/puntos_cordoba.geojson)
 - Ejecutar con el venv activo: python test_gee_mod.py
"""

import ee
import geojson
import json
import sys
from datetime import datetime, date, timedelta

# --------------------------
# CONFIGURACIÓN (ajustable)
# --------------------------
# GeoJSON con puntos (toma los primeros 3)
PUNTOS_GEOJSON = 'datos_geo/puntos_cordoba.geojson'

# Por defecto usaremos el mes anterior completo (más seguro por latencia MODIS/CHIRPS).
# Si preferís otro rango, pon aquí FECHA_INICIO y FECHA_FIN en formato YYYY-MM-DD.
USE_PREVIOUS_MONTH = True
FECHA_INICIO = None  # ejemplo: '2025-08-01'  (None -> calculado automáticamente)
FECHA_FIN = None     # ejemplo: '2025-08-31'  (None -> calculado automáticamente)

# Escalas (metros)
SCALE_MODIS = 1000
SCALE_CHIRPS = 5000

# --------------------------
# UTILIDADES de FECHAS
# --------------------------
def previous_month_dates(ref_date=None):
    """Devuelve (inicio_str, fin_str) para el mes anterior a ref_date."""
    if ref_date is None:
        ref_date = date.today()
    first_of_this_month = ref_date.replace(day=1)
    last_of_prev = first_of_this_month - timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev.strftime('%Y-%m-%d'), last_of_prev.strftime('%Y-%m-%d')

# --------------------------
# Inicializar GEE (autenticando si hace falta)
# --------------------------
def init_gee(project_id="portafolio-aegis"):
    try:
        if project_id:
            ee.Initialize(project=project_id)
        else:
            ee.Initialize()
        print("✔️  GEE inicializado.")
    except Exception as e:
        print("⚠️  No inicializado. Intentando autenticar... (se abrirá navegador)")
        try:
            ee.Authenticate()
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            print("✔️  Autenticado e inicializado.")
        except Exception as e2:
            print("❌ Error inicializando/ autenticando GEE:", e2)
            sys.exit(1)

# --------------------------
# Función helper segura para reducir regiones en GEE
# --------------------------
def reducir_region_o_cero(imagen, banda, geom, scale):
    """
    Reduce 'imagen' sobre 'geom' y devuelve un ee.Number.
    Si el valor es null, devuelve 0 usando ee.Algorithms.If (robusto).
    """
    valor = imagen.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=scale,
        bestEffort=True,
        maxPixels=1e13
    ).get(banda)
    # Si 'valor' es null -> devuelvo 0; si no -> valor.
    return ee.Number(ee.Algorithms.If(valor, valor, 0))

# --------------------------
# Función que se ejecuta en GEE para cada punto (versión de prueba)
# --------------------------
def analizar_punto_simple(punto, fecha_inicio_str, fecha_fin_str):
    """
    Recibe un ee.Feature (punto) y devuelve properties añadidas:
     - ndvi
     - nbr
     - lst_celsius
     - precip_60d_mm
    Rango de fechas en formato 'YYYY-MM-DD' (strings).
    """
    fecha_inicio = ee.Date(fecha_inicio_str)
    fecha_fin = ee.Date(fecha_fin_str)

    # Colecciones
    modis_ref = ee.ImageCollection('MODIS/061/MOD09GA').filterDate(fecha_inicio, fecha_fin)
    modis_lst = ee.ImageCollection('MODIS/061/MOD11A1').filterDate(fecha_inicio, fecha_fin)
    chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').filterDate(fecha_inicio, fecha_fin)

    # NDVI & NBR (primera imagen del rango)
    img_ref = modis_ref.sort('system:time_start', False).first()

    def calc_indices(img):
        ndvi_img = img.normalizedDifference(['sur_refl_b02', 'sur_refl_b01']).rename('ndvi')
        nbr_img = img.normalizedDifference(['sur_refl_b02', 'sur_refl_b07']).rename('nbr')
        ndvi_val = reducir_region_o_cero(ndvi_img, 'ndvi', punto.geometry(), SCALE_MODIS)
        nbr_val = reducir_region_o_cero(nbr_img, 'nbr', punto.geometry(), SCALE_MODIS)
        return ee.Dictionary({'ndvi': ndvi_val, 'nbr': nbr_val})

    indices = ee.Dictionary(ee.Algorithms.If(img_ref, calc_indices(img_ref), ee.Dictionary({'ndvi': 0, 'nbr': 0})))

    # LST (MOD11A1) - primera imagen del rango
    img_lst = modis_lst.select('LST_Day_1km').sort('system:time_start', False).first()
    def calc_lst(im):
        lst_k = reducir_region_o_cero(im, 'LST_Day_1km', punto.geometry(), SCALE_MODIS).multiply(0.02)
        return lst_k.subtract(273.15)
    lst_c = ee.Number(ee.Algorithms.If(img_lst, calc_lst(img_lst), 0))

    # Precipitación acumulada (sum of pentads)
    precip_img = ee.Image(chirps.sum()).rename('precip')
    precip_mm = reducir_region_o_cero(precip_img, 'precip', punto.geometry(), SCALE_CHIRPS)

    # Anexar propiedades y devolver feature
    return punto.set({
        'ndvi_test': indices.get('ndvi'),
        'nbr_test': indices.get('nbr'),
        'lst_test_c': lst_c,
        'precip_test_mm': precip_mm
    })

# --------------------------
# Main de prueba
# --------------------------
def main():
    # 1) Calcular rango de fechas
    if USE_PREVIOUS_MONTH:
        inicio, fin = previous_month_dates()
    else:
        inicio = FECHA_INICIO if FECHA_INICIO else previous_month_dates()[0]
        fin = FECHA_FIN if FECHA_FIN else previous_month_dates()[1]

    print(f"Usando rango de fechas para test: {inicio} -> {fin}")

    # 2) Inicializar GEE
    init_gee()  # si usás proyecto específico, pasar project_id='tu-proyecto'

    # 3) Leer GeoJSON y tomar primeros 3 puntos
    try:
        with open(PUNTOS_GEOJSON, 'r', encoding='utf-8') as f:
            gj = geojson.load(f)
        features = gj.get('features', [])[:3]
        if len(features) == 0:
            print("❌ El GeoJSON no tiene features. Revisa datos_geo/puntos_cordoba.geojson")
            sys.exit(1)
        print(f"✔️  Cargados {len(features)} puntos del GeoJSON para el test.")
    except Exception as e:
        print("❌ Error leyendo el GeoJSON:", e)
        sys.exit(1)

    # 4) Crear FeatureCollection y aplicar la función simple (UN SOLO map)
    puntos_fc = ee.FeatureCollection(features)
    # Creamos una función inline que llama a 'analizar_punto_simple' con las fechas
    def map_func(feature):
        return analizar_punto_simple(feature, inicio, fin)
    # Promover la función a GEE
    puntos_result = puntos_fc.map(map_func)

    # 5) Obtener resultados (getInfo) y mostrar
    print("⚙️  Enviando petición de test a GEE...")
    try:
        res = puntos_result.getInfo()
    except Exception as e:
        print("❌ Error en getInfo() de GEE:", e)
        print("Sugerencia: prueba con menos puntos o ajusta las fechas/rango.")
        sys.exit(1)

    # 6) Imprimir JSON crudo y resumen legible
    print("✅ Respuesta cruda de GEE (JSON):\n")
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("\n🔎 Resumen amigable:")
    for f in res.get('features', []):
        props = f.get('properties', {})
        nombre = props.get('nombre', 'sin_nombre')
        ndvi = props.get('ndvi_test', 0)
        nbr = props.get('nbr_test', 0)
        lst = props.get('lst_test_c', 0)
        precip = props.get('precip_test_mm', 0)
        print(f" - {nombre}: NDVI={ndvi}, NBR={nbr}, LST(°C)={lst}, PRECIP(60d mm)={precip}")

if __name__ == '__main__':
    main()
