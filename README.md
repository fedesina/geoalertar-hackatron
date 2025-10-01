🌍 GeoAlertAR Demo — NASA Space Apps 2025

🚀 Descripción

GeoAlertAR Demo es un prototipo presentado en el NASA Space Apps Challenge 2025. Integra observación de la Tierra (MODIS, CHIRPS) y pronósticos climáticos (Open‑Meteo) para estimar un índice de riesgo de incendios forestales en Córdoba, Argentina, y visualizarlo en un mapa interactivo.

El objetivo es demostrar un pipeline reproducible, científicamente sólido y escalable a otras provincias de Argentina.

📂 Estructura del repositorio

geoalertar-hackatron/
├── datos_geo/
│   └── puntos_cordoba.geojson          # Puntos de análisis (nombres, lat, lon)
├── layers/                              # Capas de contexto opcionales
│   ├── Areas_Protegidas_Poligono.geojson
│   └── Cuartel_Bomberos_Punto.geojson
├── docs/
│   └── riesgo_cordoba.csv               # Salida del análisis (se genera al correr el script)
├── analizador_demo.py                   # Motor GEE + Open‑Meteo (v4.1)
├── index.html                           # Web Leaflet + Tailwind
└── README.md                            # Este documento

Nota: el index.html por defecto busca riesgo_cordoba.csv en la raíz. Si mantenés la salida en docs/, cambiá en index.html la línea de configuración:

// En index.html
const CONFIG = {
  CSV_URL: 'docs/riesgo_cordoba.csv',
  // ...
}

⚡️ Quickstart

1) Dependencias

# Crear entorno (opcional)
python -m venv .venv && . .venv/Scripts/activate  # Windows PowerShell
# . .venv/bin/activate                             # macOS/Linux

pip install --upgrade pip
pip install earthengine-api pandas geojson requests

2) Autenticación GEE

earthengine authenticate

El script inicializa GEE con el proyecto portafolio-aegis. Ajustalo si fuera necesario.

3) Ejecutar el análisis

python analizador_demo.py

Salida esperada: docs/riesgo_cordoba.csv con columnas (nombre, lat, lon, ndvi, nbr, lst_celsius, precip_60d_mm, humedad_min, viento_max_kmh, riesgo_final, nivel).

4) Visualizar el mapa

# Servidor local sencillo en la carpeta del repo
python -m http.server 8000
# Abrí: http://localhost:8000/index.html

Si no ves puntos en el mapa, revisá la ruta del CSV en index.html (ver nota arriba).

🧠 Cómo funciona (pipeline)

Carga de puntos desde datos_geo/puntos_cordoba.geojson.

Consulta GEE (últimos 30–60 días):

MODIS LST → temperatura superficial (°C)

MODIS SR → NDVI y NBR (estrés hídrico/áreas quemadas)

CHIRPS → precipitación acumulada 60 días (mm)

Clima del día con Open‑Meteo: humedad mínima (%) y viento máximo (km/h).

Cálculo de riesgo normalizado (0–100) con ponderaciones basadas en literatura.

Exportación a CSV y visualización en Leaflet.

🧮 Lógica y fórmulas (del código analizador_demo.py)

Las variables se normalizan a [0,1] con funciones continuas (evitan saltos arbitrarios). El riesgo final es una combinación ponderada que privilegia viento y humedad (propagación e inflamabilidad).

1) Factores satelitales

NDVI (estado del combustible)


NBR (sequedad / cicatriz de fuego)


LST (temperatura de superficie)


Precipitación 60d (sequía acumulada)


2) Factores meteorológicos

Humedad relativa mínima (inflamabilidad)


Viento máximo 10m (propagación)


3) Combinación ponderada → Índice de Riesgo (0–100)



Por qué estas fórmulas: siguen la práctica de los sistemas de referencia (FWI 🇨🇦, EFFIS 🇪🇺, NFDRS 🇺🇸, AFDRS 🇦🇺): normalizar variables físicas clave y ponderarlas según su impacto en ignición/propagación. Adaptamos esa lógica a datos abiertos disponibles en Argentina y la validamos en Sierras Chicas (Córdoba).

🔥 Clasificación de riesgo

🟢 BAJO: < 25

🟡 MODERADO: 25–49

🟠 ALTO: 50–74

🔴 CRÍTICO: ≥ 75

🗺️ Interfaz web (Leaflet)

Filtros por nivel de riesgo.

Capas de contexto: Áreas Protegidas y Cuarteles de Bomberos.

Popup con reporte (riesgo %, viento, humedad, NBR, precipitación 60d, LST).

📚 Fuentes de datos

MODIS (NASA): NDVI/NBR (MOD09GA), LST (MOD11A1)

CHIRPS: precipitación acumulada (UCSB Climate Hazards Group)

Open‑Meteo API: humedad relativa mínima y viento máximo

🔎 Referencias científicas

Van Wagner, C.E. (1987). Development and structure of the Canadian Forest Fire Weather Index System. Forestry Technical Report 35.

San‑Miguel‑Ayanz, J. et al. (2012). Comprehensive Monitoring of Wildfires in Europe: The European Forest Fire Information System (EFFIS).

Andrews, P.L. et al. (2007). The US Fire Danger Rating System. USDA Forest Service.

Dowdy, A.J. (2018). Climatological variability of fire weather in Australia. International Journal of Climatology.

NASA ARSET (2023). Introduction to Remote Sensing for Wildfire Applications.

CHIRPS – Climate Hazards Group InfraRed Precipitation with Station Data (UCSB).

👤 Autor

Federico Nicolás Sinato — Argentina, 2025Proyecto GeoAlertAR 🌍🔥

✅ Checklist para el hackathon



