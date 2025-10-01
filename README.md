🌍 GeoAlertAR Demo — NASA Space Apps 2025

📖 Descripción

GeoAlertAR Demo integra observación de la Tierra (MODIS, CHIRPS) y pronósticos climáticos (Open-Meteo) para estimar un índice de riesgo de incendios en Córdoba, Argentina, y visualizarlo en un mapa interactivo.
El objetivo es demostrar un pipeline reproducible, científicamente sólido y escalable a otras provincias.

📦 Estructura del repositorio
geoalertar-hackatron/
├─ datos_geo/
│  └─ puntos_cordoba.geojson
├─ layers/
│  ├─ Areas_Protegidas_Poligono.geojson
│  └─ Cuartel_Bomberos_Punto.geojson
├─ docs/
│  ├─ index.html
│  └─ riesgo_cordoba.csv
├─ analizador_demo.py
├─ README.md
└─ LICENSE


Nota: si index.html vive dentro de docs/, configurá la ruta del CSV así:

// index.html
const CONFIG = {
  CSV_URL: 'docs/riesgo_cordoba.csv',
  // ...
}

⚡️ Quickstart
1) Dependencias
# (opcional) entorno
python -m venv .venv && . .venv/Scripts/activate   # Windows
# source .venv/bin/activate                        # macOS/Linux

pip install --upgrade pip
pip install earthengine-api pandas geojson requests

2) Autenticación GEE
earthengine authenticate

3) Ejecutar análisis
python analizador_demo.py
# genera: docs/riesgo_cordoba.csv

4) Visualizar mapa local
python -m http.server 8000
# Abrir: http://localhost:8000/docs/index.html

🧠 Pipeline (cómo funciona)

Carga de puntos (datos_geo/puntos_cordoba.geojson).

Consulta GEE (últimos 30–60 días):

MODIS LST → temperatura superficial (°C)

MODIS SR → NDVI y NBR

CHIRPS → precipitación 60d (mm)

Clima del día (Open-Meteo): humedad mínima (%) y viento máx (km/h).

Índice de riesgo continuo 0–100 (pondera viento y humedad).

CSV → docs/riesgo_cordoba.csv y mapa en Leaflet.

🧮 Lógica (implementada en analizador_demo.py)

Normalizaciones (0–1):

NDVI
R_NDVI = 1 - (NDVI - 0.1) / 0.5

NBR
R_NBR = 1 - (NBR - 0.0) / 0.5

LST (°C)
R_LST = (LST - 15) / 30

Precip 60d (mm)
R_Prec = 1 - (Prec60d - 10) / 140

Humedad mínima (%)
R_Hum = 1 - (HRmin - 15) / 65

Viento máx (km/h)
R_Viento = (Vmax - 10) / 50

Índice compuesto (0–100):

Riesgo = 100 * (
  0.25*R_NBR   +
  0.10*R_Prec  +
  0.30*R_Hum   +
  0.25*R_Viento+
  0.05*R_LST   +
  0.05*R_NDVI
)


Rangos:

Nivel	Umbral
BAJO	< 25
MODERADO	25–49
ALTO	50–74
CRÍTICO	≥ 75

Fundamento: práctica de sistemas de referencia (FWI 🇨🇦, EFFIS 🇪🇺, NFDRS 🇺🇸, AFDRS 🇦🇺): normalizar variables físicas clave y ponderarlas según impacto en ignición/propagación. Adaptado a datos abiertos en Argentina y validado en Sierras Chicas (Córdoba).

🗺️ Interfaz web

Leaflet + Tailwind.

Filtros por nivel de riesgo.

Capas de contexto (Áreas Protegidas, Cuarteles de Bomberos).

Pop-ups con reporte: riesgo %, viento, humedad, NBR, precip 60d, LST.

🗃️ Fuentes de datos

MODIS (NASA): NDVI/NBR (MOD09GA), LST (MOD11A1)

CHIRPS (UCSB): precipitación acumulada

Open-Meteo API: humedad mínima y viento máximo

📚 Referencias

Van Wagner, C.E. (1987). Canadian Forest Fire Weather Index System.

San-Miguel-Ayanz, J. et al. (2012). EFFIS.

Andrews, P.L. et al. (2007). US NFDRS.

Dowdy, A.J. (2018). Fire weather in Australia.

NASA ARSET (2023). Wildfire Applications.

CHIRPS – Climate Hazards Group, UCSB.

👤 Autor

Federico Nicolás Sinato — Argentina, 2025
Proyecto GeoAlertAR 🌍🔥