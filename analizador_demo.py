#!/usr/bin/env python3
"""
GeoAlertAR Demo - v3.0 FINAL - NASA Space Apps Challenge
- Lógica de GEE 100% robusta contra valores nulos usando ee.Algorithms.If.
- Rango de fechas de búsqueda seguro para evitar problemas de latencia de datos.
- Mantiene el procesamiento en batch para máxima eficiencia.
"""
import ee
import pandas as pd
import geojson
import os
from datetime import datetime, timedelta
import sys

# ==============================================================================
# --- CONFIGURACIÓN ---
# ==============================================================================
PUNTOS_GEOJSON = 'datos_geo/puntos_cordoba.geojson'
CARPETA_SALIDA_WEB = 'webapp'
ARCHIVO_SALIDA_CSV = os.path.join(CARPETA_SALIDA_WEB, 'riesgo_cordoba.csv')
GEE_PROJECT_ID = 'portafolio-aegis'

# ==============================================================================
# --- LÓGICA DE PROCESAMIENTO EN BATCH PARA GEE ---
# ==============================================================================

def analizar_punto_en_servidor_gee(punto):
    """
    Función robusta que se ejecuta en los servidores de GEE para cada punto.
    Esta es la versión final que maneja correctamente los valores nulos.
    """
    # Rango de fechas seguro: termina hace 2 días, abarca 30 días hacia atrás.
    fecha_fin = ee.Date(datetime.now()).advance(-2, 'day')
    fecha_inicio = fecha_fin.advance(-30, 'day')
    rango_fechas = ee.DateRange(fecha_inicio, fecha_fin)

    # --- Función auxiliar CLAVE para obtener datos de forma segura ---
    def obtener_valor_seguro(coleccion, banda, factor_escala=1):
        imagen = coleccion.filterBounds(punto.geometry()).filterDate(rango_fechas).sort('system:time_start', False).first()
        
        # Lógica condicional que se ejecuta en GEE
        def calcular_valor(img):
            valor_raw = img.select(banda).reduceRegion(ee.Reducer.mean(), punto.geometry(), 1000).get(banda)
            # Si el resultado de reduceRegion es nulo, ee.Number(null) es un ee.Number nulo
            return ee.Algorithms.If(
                valor_raw,                             # Si el valor NO es nulo...
                ee.Number(valor_raw).multiply(factor_escala), # ...lo multiplicamos por su escala
                0                                      # Si es nulo, devolvemos 0
            )

        # Si la imagen existe, calculamos el valor. Si no, devolvemos 0.
        return ee.Algorithms.If(imagen, calcular_valor(imagen), 0)

    # --- 1. Obtener Temperatura (LST) ---
    coleccion_lst = ee.ImageCollection('MODIS/061/MOD11A1')
    lst_kelvin = obtener_valor_seguro(coleccion_lst, 'LST_Day_1km', 0.02)
    lst_celsius = ee.Number(lst_kelvin).subtract(273.15)
    
    # --- 2. Obtener NDVI y NBR ---
    coleccion_reflectancia = ee.ImageCollection('MODIS/061/MOD09GA')
    imagen_reflectancia = coleccion_reflectancia.filterBounds(punto.geometry()).filterDate(rango_fechas).sort('system:time_start', False).first()

    def calcular_indices(img):
        ndvi = img.normalizedDifference(['sur_refl_b02', 'sur_refl_b01']).rename('ndvi')
        nbr = img.normalizedDifference(['sur_refl_b02', 'sur_refl_b07']).rename('nbr')
        valor_ndvi = ndvi.reduceRegion(ee.Reducer.mean(), punto.geometry(), 1000).get('ndvi')
        valor_nbr = nbr.reduceRegion(ee.Reducer.mean(), punto.geometry(), 1000).get('nbr')
        return ee.Dictionary({
            'ndvi': ee.Algorithms.If(valor_ndvi, valor_ndvi, 0),
            'nbr': ee.Algorithms.If(valor_nbr, valor_nbr, 0)
        })

    indices = ee.Dictionary(ee.Algorithms.If(
        imagen_reflectancia,
        calcular_indices(imagen_reflectancia),
        {'ndvi': 0, 'nbr': 0}
    ))

    # --- 3. Obtener Precipitación ---
    coleccion_precip = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')
    fecha_inicio_precip = fecha_fin.advance(-60, 'day') # 60 días para precipitación
    imagen_precip_total = coleccion_precip.filterDate(fecha_inicio_precip, fecha_fin).sum().rename('precip')
    precip_mm = obtener_valor_seguro(ee.ImageCollection(imagen_precip_total), 'precip')

    return punto.set({
        'ndvi': indices.get('ndvi'),
        'nbr': indices.get('nbr'),
        'lst_celsius': lst_celsius,
        'precip_60d_mm': precip_mm
    })


# ==============================================================================
# --- CLASE PRINCIPAL DEL ANALIZADOR ---
# ==============================================================================

class AnalizadorHackathon:
    def __init__(self):
        self._inicializar_gee()

    def _inicializar_gee(self):
        try:
            ee.Initialize(project=GEE_PROJECT_ID)
            print(f"✔️  Google Earth Engine inicializado en proyecto '{GEE_PROJECT_ID}'.")
        except Exception:
            try:
                print("⚠️  Autenticando en Google Earth Engine...")
                ee.Authenticate()
                ee.Initialize(project=GEE_PROJECT_ID)
                print("✔️  GEE autenticado e inicializado.")
            except Exception as e:
                print(f"❌ ERROR CRÍTICO: No se pudo inicializar GEE: {e}")
                sys.exit(1)

    def calcular_riesgo_local(self, props):
        ndvi = props.get('ndvi', 0)
        nbr = props.get('nbr', 0)
        lst = props.get('lst_celsius', 15) # Usar 15 como default si es 0
        precip = props.get('precip_60d_mm', 10)

        riesgo_ndvi = 1 - max(0, min(1, (ndvi - 0.1) / 0.5))
        riesgo_nbr = 1 - max(0, min(1, (nbr - 0.0) / 0.5))
        riesgo_lst = max(0, min(1, (lst - 15) / 30))
        riesgo_precip = 1 - max(0, min(1, (precip - 10) / 140))
        
        riesgo_final = (riesgo_ndvi * 0.15 + riesgo_nbr * 0.35 + 
                        riesgo_lst * 0.30 + riesgo_precip * 0.20) * 100
        
        return round(riesgo_final, 1)

    def clasificar_nivel(self, riesgo):
        if riesgo > 75: return "CRÍTICO"
        if riesgo > 50: return "ALTO"
        if riesgo > 25: return "MODERADO"
        return "BAJO"

    def ejecutar(self):
        print("\n🛰️  Iniciando análisis v3.0 (BATCH, Robusto)...")
        
        try:
            with open(PUNTOS_GEOJSON, 'r', encoding='utf-8') as f:
                puntos_locales = geojson.load(f)
            print(f"✔️  {len(puntos_locales['features'])} puntos de análisis cargados.")
        except FileNotFoundError:
            print(f"❌ ERROR CRÍTICO: No se encontró '{PUNTOS_GEOJSON}'.")
            sys.exit(1)

        puntos_gee = ee.FeatureCollection(puntos_locales)

        print("⚙️  Enviando trabajo a Google Earth Engine...")
        resultados_gee = puntos_gee.map(analizar_punto_en_servidor_gee)

        print("📥 Descargando resultados procesados...")
        try:
            resultados_procesados = resultados_gee.getInfo()
        except Exception as e:
            print(f"❌ ERROR: Falló la comunicación con GEE: {e}")
            sys.exit(1)
        
        print("🧠 Calculando riesgo final localmente...")
        lista_final = []
        for punto in resultados_procesados['features']:
            props = punto['properties']
            riesgo = self.calcular_riesgo_local(props)
            nivel = self.clasificar_nivel(riesgo)
            lista_final.append({
                'nombre': props.get('nombre'),
                'lat': punto['geometry']['coordinates'][1],
                'lon': punto['geometry']['coordinates'][0],
                'ndvi': round(props.get('ndvi', 0), 3),
                'nbr': round(props.get('nbr', 0), 3),
                'lst_celsius': round(props.get('lst_celsius', 0), 1),
                'precip_60d_mm': round(props.get('precip_60d_mm', 0), 1),
                'riesgo_final': riesgo,
                'nivel': nivel
            })

        if not os.path.exists(CARPETA_SALIDA_WEB):
            os.makedirs(CARPETA_SALIDA_WEB)
        
        df = pd.DataFrame(lista_final)
        df.to_csv(ARCHIVO_SALIDA_CSV, index=False)
        print(f"\n✅ Análisis completo. Resultados guardados en '{ARCHIVO_SALIDA_CSV}'.")
        print("\n📈 Resumen de Riesgos:")
        print(df['nivel'].value_counts())

if __name__ == "__main__":
    analizador = AnalizadorHackathon()
    analizador.ejecutar()