#!/usr/bin/env python3
"""
GeoAlertAR Demo - v5.3 - MÁSCARA DE AGUA
- Se añade una máscara de agua en GEE para excluir lagos y ríos del análisis.
"""
import ee
import pandas as pd
import geojson
import os
from datetime import datetime, timedelta
import sys
import requests
import numpy as np
import json

# --- CONFIGURACIÓN ---
GRILLA_GEOJSON = 'datos_geo/grilla_hexagonos_cordoba.geojson'
SAOCOM_CSV = 'datos_saocom/humedad_suelo_demo.csv'
CARPETA_SALIDA = 'docs'
ARCHIVO_SALIDA_GEOJSON = os.path.join(CARPETA_SALIDA, 'riesgo_hexagonos.geojson')
GEE_PROJECT_ID = 'portafolio-aegis'

def analizar_hexagono_en_gee(feature):
    geom = feature.geometry()
    fecha_fin = ee.Date(datetime.now()).advance(-2, 'day')
    
    # Máscara de agua global para excluirla de los cálculos
    waterMask = ee.Image("MODIS/051/MCD12Q1/2001_01_01").select('Land_Cover_Type_1').neq(0)

    # Rango para imágenes instantáneas (NDVI, NBR, LST)
    fecha_inicio_img = fecha_fin.advance(-30, 'day')
    rango_fechas_img = ee.DateRange(fecha_inicio_img, fecha_fin)

    def obtener_valor_reciente(coleccion, banda, factor=1):
        imagen = coleccion.filterDate(rango_fechas_img).first()
        def calcular(img):
            # Aplicar la máscara de agua antes de reducir
            valor = img.updateMask(waterMask).select(banda).reduceRegion(ee.Reducer.mean(), geom, 500).get(banda)
            return ee.Algorithms.If(valor, ee.Number(valor).multiply(factor), -999)
        return ee.Algorithms.If(imagen, calcular(imagen), -999)

    lst_kelvin = obtener_valor_reciente(ee.ImageCollection('MODIS/061/MOD11A1'), 'LST_Day_1km', 0.02)
    lst_celsius = ee.Algorithms.If(ee.Number(lst_kelvin).gt(0), ee.Number(lst_kelvin).subtract(273.15), -999)
    
    imagen_reflectancia = ee.ImageCollection('MODIS/061/MOD09GA').filterDate(rango_fechas_img).first()
    def calcular_indices(img):
        img_masked = img.updateMask(waterMask)
        ndvi = img_masked.normalizedDifference(['sur_refl_b02', 'sur_refl_b01']).rename('ndvi')
        nbr = img_masked.normalizedDifference(['sur_refl_b02', 'sur_refl_b07']).rename('nbr')
        valores = ndvi.addBands(nbr).reduceRegion(ee.Reducer.mean(), geom, 500)
        return ee.Dictionary({
            'ndvi': ee.Algorithms.If(valores.get('ndvi'), valores.get('ndvi'), -999),
            'nbr': ee.Algorithms.If(valores.get('nbr'), valores.get('nbr'), -999)
        })
    indices = ee.Dictionary(ee.Algorithms.If(imagen_reflectancia, calcular_indices(imagen_reflectancia), {'ndvi': -999, 'nbr': -999}))

    fecha_inicio_precip = fecha_fin.advance(-60, 'day')
    rango_fechas_precip = ee.DateRange(fecha_inicio_precip, fecha_fin)
    precip_total_img = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').filterDate(rango_fechas_precip).sum()
    valor_precip = precip_total_img.updateMask(waterMask).reduceRegion(ee.Reducer.mean(), geom, 5000).get('precipitation')
    precip_mm = ee.Algorithms.If(valor_precip, valor_precip, 0)

    return feature.set({ 'ndvi': indices.get('ndvi'), 'nbr': indices.get('nbr'), 'lst_celsius': lst_celsius, 'precip_60d_mm': precip_mm })


class AnalizadorHackathon:
    # El resto de la clase es idéntico a la v5.2
    def __init__(self):
        self._inicializar_gee()
        self.df_saocom = self._cargar_saocom()

    def _inicializar_gee(self):
        try:
            ee.Initialize(project=GEE_PROJECT_ID)
            print("✔️  Google Earth Engine inicializado.")
        except Exception as e:
            print(f"❌ ERROR GEE: {e}"); sys.exit(1)

    def _cargar_saocom(self):
        if os.path.exists(SAOCOM_CSV):
            print(f"✔️  Datos de Humedad de Suelo (SAOCOM) encontrados en '{SAOCOM_CSV}'.")
            return pd.read_csv(SAOCOM_CSV).set_index('id_hexagono')
        print("⚠️  No se encontró archivo de SAOCOM. El análisis continuará sin datos de humedad de suelo.")
        return None

    def obtener_datos_climaticos(self, lat, lon):
        try:
            params = { "latitude": lat, "longitude": lon, "daily": "relative_humidity_2m_min,wind_speed_10m_max", "wind_speed_unit": "kmh", "timezone": "auto", "forecast_days": 1 }
            response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()['daily']
            return { 'humedad_min': data['relative_humidity_2m_min'][0], 'viento_max_kmh': data['wind_speed_10m_max'][0] }
        except Exception:
            return {'humedad_min': None, 'viento_max_kmh': None}

    def calcular_riesgo_avanzado(self, props):
        C = { 'PESO_NBR': 0.7, 'PESO_NDVI': 0.3, 'TEMP_NORMAL': 15, 'TEMP_EXTREMA': 35, 'MULT_MAX_TEMP': 1.8, 'HUM_BAJA': 20, 'HUM_NORMAL': 60, 'MULT_MAX_HUM': 2.5, 'VIENTO_NORMAL': 15, 'VIENTO_EXTREMO': 60, 'MULT_MAX_VIENTO': 3.0, 'PRECIP_MIN_SECO': 10, 'PRECIP_MAX_SECO': 150, 'MULT_MAX_PRECIP': 1.5, 'SUELO_MIN_SECO_PCT': 10, 'SUELO_MAX_SECO_PCT': 30, 'MULT_MAX_SUELO_SECO': 1.8, 'ESCALA_FINAL': 100 }
        def _normalize(v, min_v, max_v): return np.clip((v - min_v) / (max_v - min_v), 0, 1)
        riesgo_base = (_normalize(props.get('nbr', 0), 0.5, -0.2) * C['PESO_NBR']) + ((1 - _normalize(props.get('ndvi', 0), 0.2, 0.8)) * C['PESO_NDVI'])
        mult_temp = 1 + (_normalize(props.get('lst_celsius', 15), C['TEMP_NORMAL'], C['TEMP_EXTREMA']) * (C['MULT_MAX_TEMP'] - 1))
        mult_hum = 1 + ((1 - _normalize(props.get('humedad_min', 100), C['HUM_BAJA'], C['HUM_NORMAL'])) * (C['MULT_MAX_HUM'] - 1))
        mult_viento = 1 + (_normalize(props.get('viento_max_kmh', 0), C['VIENTO_NORMAL'], C['VIENTO_EXTREMO']) * (C['MULT_MAX_VIENTO'] - 1))
        mult_precip = 1 + ((1 - _normalize(props.get('precip_60d_mm', 150), C['PRECIP_MIN_SECO'], C['PRECIP_MAX_SECO'])) * (C['MULT_MAX_PRECIP'] - 1))
        mult_humedad_suelo = 1.0
        if props.get('humedad_saocom_pct') is not None and not np.isnan(props.get('humedad_saocom_pct')):
            mult_humedad_suelo = 1 + ((1 - _normalize(props.get('humedad_saocom_pct'), C['SUELO_MIN_SECO_PCT'], C['SUELO_MAX_SECO_PCT'])) * (C['MULT_MAX_SUELO_SECO'] - 1))
        riesgo_bruto = riesgo_base * mult_temp * mult_hum * mult_viento * mult_precip * mult_humedad_suelo
        return np.clip(riesgo_bruto * C['ESCALA_FINAL'], 0, 100)

    def clasificar_nivel(self, riesgo):
        if riesgo > 80: return "CRÍTICO"
        if riesgo > 60: return "ALTO"
        if riesgo > 40: return "MODERADO"
        return "BAJO"

    def ejecutar(self):
        print("\n🛰️  Iniciando análisis v5.3 (Máscara de Agua)...")
        with open(GRILLA_GEOJSON, 'r', encoding='utf-8') as f: grilla = geojson.load(f)
        
        print(f"✔️  Grilla de {len(grilla['features'])} hexágonos cargada.")
        resultados_gee = ee.FeatureCollection(grilla).map(analizar_hexagono_en_gee).getInfo()
        
        print("🌦️  Obteniendo clima y calculando riesgo final...")
        lista_final = []
        total = len(resultados_gee['features'])
        for i, feature in enumerate(resultados_gee['features']):
            progreso = i + 1; porcentaje = (progreso / total) * 100; barra = '█' * int(50 * progreso // total) + '-' * (50 - int(50 * progreso // total))
            print(f'\r  Progreso: |{barra}| {progreso}/{total} ({porcentaje:.0f}%)', end="")
            
            props = feature['properties']
            centroid = ee.Geometry.Polygon(feature['geometry']['coordinates']).centroid().getInfo()['coordinates']
            datos_clima = self.obtener_datos_climaticos(centroid[1], centroid[0])
            humedad_saocom = np.nan
            if self.df_saocom is not None and props.get('id') in self.df_saocom.index:
                humedad_saocom = self.df_saocom.loc[props['id']]['humedad_pct']
            
            props_completas = {**props, **datos_clima, 'humedad_saocom_pct': humedad_saocom}
            
            if any(v == -999 for k, v in props_completas.items() if k in ['ndvi', 'nbr', 'lst_celsius']):
                riesgo, nivel = -1, "DATOS INSUFICENTES"
            else:
                riesgo = self.calcular_riesgo_avanzado(props_completas)
                nivel = self.clasificar_nivel(riesgo)

            lista_final.append({ 'id': props.get('id'), **props_completas, 'riesgo_final': round(riesgo, 1), 'nivel': nivel })

        print("\n\n✅ Análisis completo.")
        df = pd.DataFrame(lista_final)
        
        gdf = pd.DataFrame([f['properties'] for f in grilla['features']])
        gdf = gdf.merge(df, on='id', how='left')
        
        final_features = []
        for _, row in gdf.iterrows():
            feature = next((f for f in grilla['features'] if f['properties']['id'] == row['id']), None)
            if feature:
                # Convertir NaN de numpy a None para JSON
                feature['properties'] = {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in row.to_dict().items()}
                final_features.append(feature)
        
        final_geojson = {"type": "FeatureCollection", "features": final_features}
        
        with open(ARCHIVO_SALIDA_GEOJSON, 'w') as f:
            json.dump(final_geojson, f)
        
        print(f"✔️  Resultados guardados en '{ARCHIVO_SALIDA_GEOJSON}'.")
        print("\n📈 Resumen de Riesgos:")
        print(df['nivel'].value_counts())

if __name__ == "__main__":
    AnalizadorHackathon().ejecutar()

