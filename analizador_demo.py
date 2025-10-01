#!/usr/bin/env python3
"""
GeoAlertAR Demo - v4.1 - CORRECCIÓN DE RUTA
- Se corrige la ruta al archivo `puntos_cordoba.geojson`.
- Integra datos de Viento y Humedad Relativa desde Open-Meteo.
- La fórmula de riesgo ahora es mucho más precisa y realista.
"""
import ee
import pandas as pd
import geojson
import os
from datetime import datetime, timedelta
import sys
import requests

# --- CONFIGURACIÓN CON RUTA CORREGIDA ---
PUNTOS_GEOJSON = 'datos_geo/puntos_cordoba.geojson' # <-- ¡LÍNEA CORREGIDA!
CARPETA_SALIDA = 'docs'
ARCHIVO_SALIDA_CSV = os.path.join(CARPETA_SALIDA, 'riesgo_cordoba.csv')
GEE_PROJECT_ID = 'portafolio-aegis'

def analizar_punto_en_servidor_gee(punto):
    fecha_fin = ee.Date(datetime.now()).advance(-2, 'day')
    fecha_inicio = fecha_fin.advance(-30, 'day')
    rango_fechas = ee.DateRange(fecha_inicio, fecha_fin)

    def obtener_valor_seguro(coleccion, banda, factor_escala=1):
        imagen = coleccion.filterBounds(punto.geometry()).filterDate(rango_fechas).sort('system:time_start', False).first()
        def calcular_valor(img):
            valor_raw = img.select(banda).reduceRegion(ee.Reducer.mean(), punto.geometry(), 1000).get(banda)
            return ee.Algorithms.If(valor_raw, ee.Number(valor_raw).multiply(factor_escala), 0)
        return ee.Algorithms.If(imagen, calcular_valor(imagen), 0)

    coleccion_lst = ee.ImageCollection('MODIS/061/MOD11A1')
    lst_kelvin = obtener_valor_seguro(coleccion_lst, 'LST_Day_1km', 0.02)
    lst_celsius = ee.Algorithms.If(ee.Number(lst_kelvin).gt(0), ee.Number(lst_kelvin).subtract(273.15), 0)
    
    coleccion_reflectancia = ee.ImageCollection('MODIS/061/MOD09GA')
    imagen_reflectancia = coleccion_reflectancia.filterBounds(punto.geometry()).filterDate(rango_fechas).sort('system:time_start', False).first()
    def calcular_indices(img):
        ndvi = img.normalizedDifference(['sur_refl_b02', 'sur_refl_b01']).rename('ndvi')
        nbr = img.normalizedDifference(['sur_refl_b02', 'sur_refl_b07']).rename('nbr')
        valor_ndvi = ndvi.reduceRegion(ee.Reducer.mean(), punto.geometry(), 1000).get('ndvi')
        valor_nbr = nbr.reduceRegion(ee.Reducer.mean(), punto.geometry(), 1000).get('nbr')
        return ee.Dictionary({'ndvi': ee.Algorithms.If(valor_ndvi, valor_ndvi, 0), 'nbr': ee.Algorithms.If(valor_nbr, valor_nbr, 0)})
    indices = ee.Dictionary(ee.Algorithms.If(imagen_reflectancia, calcular_indices(imagen_reflectancia), {'ndvi': 0, 'nbr': 0}))

    coleccion_precip = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')
    fecha_inicio_precip = fecha_fin.advance(-60, 'day')
    imagen_precip_total = coleccion_precip.filterDate(fecha_inicio_precip, fecha_fin).sum().rename('precip')
    precip_mm = obtener_valor_seguro(ee.ImageCollection(imagen_precip_total), 'precip')

    return punto.set({'ndvi': indices.get('ndvi'), 'nbr': indices.get('nbr'), 'lst_celsius': lst_celsius, 'precip_60d_mm': precip_mm})


class AnalizadorHackathon:
    def __init__(self):
        self._inicializar_gee()

    def _inicializar_gee(self):
        try:
            ee.Initialize(project=GEE_PROJECT_ID)
            print(f"✔️  Google Earth Engine inicializado.")
        except Exception as e:
            print(f"❌ ERROR CRÍTICO GEE: {e}")
            sys.exit(1)

    def obtener_datos_climaticos(self, lat, lon):
        try:
            URL = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat, "longitude": lon,
                "daily": "relative_humidity_2m_min,wind_speed_10m_max",
                "wind_speed_unit": "kmh", "timezone": "auto", "forecast_days": 1
            }
            response = requests.get(URL, params=params)
            response.raise_for_status()
            data = response.json()['daily']
            return {
                'humedad_min': data['relative_humidity_2m_min'][0],
                'viento_max_kmh': data['wind_speed_10m_max'][0]
            }
        except Exception as e:
            print(f"  -> Error de clima: {e}")
            return {'humedad_min': None, 'viento_max_kmh': None}

    def calcular_riesgo_local(self, props):
        ndvi = props.get('ndvi', 0)
        nbr = props.get('nbr', 0)
        lst = props.get('lst_celsius', 0)
        precip = props.get('precip_60d_mm', 0)
        humedad = props.get('humedad_min', 100)
        viento = props.get('viento_max_kmh', 0)

        riesgo_ndvi = 1 - max(0, min(1, (ndvi - 0.1) / 0.5))
        riesgo_nbr = 1 - max(0, min(1, (nbr - 0.0) / 0.5))
        riesgo_lst = max(0, min(1, (lst - 15) / 30))
        riesgo_precip = 1 - max(0, min(1, (precip - 10) / 140))
        riesgo_humedad = 1 - max(0, min(1, (humedad - 15) / 65))
        riesgo_viento = max(0, min(1, (viento - 10) / 50))
        
        riesgo_final = (riesgo_nbr * 0.25 + 
                        riesgo_precip * 0.10 + 
                        riesgo_humedad * 0.30 +
                        riesgo_viento * 0.25 +
                        riesgo_lst * 0.05 +
                        riesgo_ndvi * 0.05) * 100
        
        return round(riesgo_final, 1)

    def clasificar_nivel(self, riesgo):
        if riesgo > 75: return "CRÍTICO"
        if riesgo > 50: return "ALTO"
        if riesgo > 25: return "MODERADO"
        return "BAJO"

    def ejecutar(self):
        print("\n🛰️  Iniciando análisis v4.1 (Ruta Corregida)...")
        
        try:
            with open(PUNTOS_GEOJSON, 'r', encoding='utf-8') as f:
                puntos_locales = geojson.load(f)
            print(f"✔️  {len(puntos_locales['features'])} puntos de análisis cargados.")
        except FileNotFoundError:
            print(f"❌ ERROR CRÍTICO: No se encontró '{PUNTOS_GEOJSON}'. Verifica la ruta.")
            sys.exit(1)

        puntos_gee = ee.FeatureCollection(puntos_locales)
        print("⚙️  Enviando trabajo a Google Earth Engine...")
        resultados_gee = puntos_gee.map(analizar_punto_en_servidor_gee)
        print("📥 Descargando resultados de GEE...")
        resultados_procesados = resultados_gee.getInfo()
        
        print("🌦️  Obteniendo datos de clima y calculando riesgo final...")
        lista_final = []
        for i, punto in enumerate(resultados_procesados['features']):
            nombre = punto['properties']['nombre']
            print(f"  [{i+1}/{len(resultados_procesados['features'])}] Procesando clima para {nombre}...", end="\r")
            
            props = punto['properties']
            coords = punto['geometry']['coordinates']
            
            datos_clima = self.obtener_datos_climaticos(coords[1], coords[0])
            
            props_completas = {**props, **datos_clima}
            
            riesgo = self.calcular_riesgo_local(props_completas)
            nivel = self.clasificar_nivel(riesgo)
            
            lista_final.append({
                'nombre': props.get('nombre'),
                'lat': coords[1], 'lon': coords[0],
                'ndvi': round(props.get('ndvi', 0), 3),
                'nbr': round(props.get('nbr', 0), 3),
                'lst_celsius': round(props.get('lst_celsius', 0), 1),
                'precip_60d_mm': round(props.get('precip_60d_mm', 0), 1),
                'humedad_min': datos_clima.get('humedad_min'),
                'viento_max_kmh': datos_clima.get('viento_max_kmh'),
                'riesgo_final': riesgo, 'nivel': nivel
            })
        print("\n")
        if not os.path.exists(CARPETA_SALIDA):
            os.makedirs(CARPETA_SALIDA)
        
        df = pd.DataFrame(lista_final)
        df.to_csv(ARCHIVO_SALIDA_CSV, index=False)
        print(f"✅ Análisis completo. Resultados guardados en '{ARCHIVO_SALIDA_CSV}'.")
        print("\n📈 Resumen de Riesgos:")
        print(df['nivel'].value_counts())

if __name__ == "__main__":
    analizador = AnalizadorHackathon()
    analizador.ejecutar()
