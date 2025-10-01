🌍 GeoAlertAR Demo – NASA Space Apps Challenge










🚀 Descripción

GeoAlertAR Demo es un prototipo presentado en el NASA Space Apps Challenge 2025.
El sistema combina datos satelitales (MODIS, CHIRPS, SRTM) y climáticos en tiempo real (Open-Meteo) para generar un índice de riesgo de incendios forestales en Córdoba, Argentina.

El objetivo es demostrar cómo la integración de ciencia de datos, observación de la Tierra y lógica física aplicada puede brindar un sistema de alerta temprana, validado científicamente y escalable a nivel nacional.

📂 Estructura del Proyecto
geoalertar_demo/
├── datos_geo/                  # Datos geográficos de referencia
│   └── puntos_cordoba.geojson
│
├── webapp/                     # Interfaz web (mapa interactivo)
│   ├── layers/                 # Capas de contexto (áreas protegidas, bomberos, etc.)
│   │   ├── Areas_Protegidas_Poligono.geojson
│   │   └── Cuartel_Bomberos_Punto.geojson
│   ├── index.html              # Frontend con Leaflet + Tailwind
│   └── riesgo_cordoba.csv      # Resultados del análisis (generados por el script)
│
├── analizador_demo.py          # Script principal de análisis (GEE + Open-Meteo)
└── estructura_proyecto.txt     # Resumen técnico

⚙️ Tecnologías Utilizadas

Google Earth Engine (GEE) – Procesamiento satelital masivo.

MODIS (NASA) – NDVI, NBR y temperatura superficial (LST).

CHIRPS – Precipitación acumulada (60 días).

Open-Meteo API – Pronóstico de viento y humedad relativa.

Python 3.x – Motor de análisis (Pandas, Requests, GeoJSON).

Leaflet + TailwindCSS – Visualización web interactiva.

📊 Variables Analizadas

🌱 NDVI (Normalized Difference Vegetation Index): Estado de la vegetación.

🔥 NBR (Normalized Burn Ratio): Estrés hídrico y detección de áreas quemadas.

🌡 LST (Land Surface Temperature): Temperatura superficial terrestre.

☔ Precipitación acumulada (60 días): Nivel de sequía.

💨 Humedad relativa mínima: Influencia en la inflamabilidad del combustible.

🌬 Viento máximo (10m): Factor clave de propagación del fuego.

🧮 Lógica de Análisis

El riesgo final se calcula como combinación ponderada de índices satelitales y meteorológicos.
Esta lógica está inspirada en modelos internacionales (FWI, EFFIS, NFDRS), adaptada a la realidad argentina y a los datos disponibles.

1. Factores satelitales

Riesgo NDVI

𝑅
𝑁
𝐷
𝑉
𝐼
=
1
−
𝑁
𝐷
𝑉
𝐼
−
0.1
0.5
R
NDVI
	​

=1−
0.5
NDVI−0.1
	​


Riesgo NBR

𝑅
𝑁
𝐵
𝑅
=
1
−
𝑁
𝐵
𝑅
−
0.0
0.5
R
NBR
	​

=1−
0.5
NBR−0.0
	​


Riesgo Temperatura (LST)

𝑅
𝐿
𝑆
𝑇
=
𝐿
𝑆
𝑇
−
15
30
R
LST
	​

=
30
LST−15
	​


Riesgo Precipitación (60d)

𝑅
𝑃
𝑟
𝑒
𝑐
=
1
−
𝑃
𝑟
𝑒
𝑐
60
𝑑
−
10
140
R
Prec
	​

=1−
140
Prec
60d
	​

−10
	​

2. Factores meteorológicos

Riesgo Humedad relativa mínima

𝑅
𝐻
𝑢
𝑚
=
1
−
𝐻
𝑅
𝑚
𝑖
𝑛
−
15
65
R
Hum
	​

=1−
65
HR
min
	​

−15
	​


Riesgo Viento máximo

𝑅
𝑉
𝑖
𝑒
𝑛
𝑡
𝑜
=
𝑉
𝑚
𝑎
𝑥
−
10
50
R
Viento
	​

=
50
V
max
	​

−10
	​

3. Combinación ponderada

El riesgo final (0–100) es:

𝑅
𝑖
𝑒
𝑠
𝑔
𝑜
=
(
𝑅
𝑁
𝐵
𝑅
⋅
0.25
)
+
(
𝑅
𝑃
𝑟
𝑒
𝑐
⋅
0.10
)
+
(
𝑅
𝐻
𝑢
𝑚
⋅
0.30
)
+
(
𝑅
𝑉
𝑖
𝑒
𝑛
𝑡
𝑜
⋅
0.25
)
+
(
𝑅
𝐿
𝑆
𝑇
⋅
0.05
)
+
(
𝑅
𝑁
𝐷
𝑉
𝐼
⋅
0.05
)
Riesgo=(R
NBR
	​

⋅0.25)+(R
Prec
	​

⋅0.10)+(R
Hum
	​

⋅0.30)+(R
Viento
	​

⋅0.25)+(R
LST
	​

⋅0.05)+(R
NDVI
	​

⋅0.05)
🔥 Clasificación de Riesgo

🟢 BAJO: <25

🟡 MODERADO: 25–49

🟠 ALTO: 50–74

🔴 CRÍTICO: ≥75

🗺️ Interfaz Web

Visualización en mapa interactivo Leaflet.

Filtros dinámicos por nivel de riesgo.

Capas contextuales: Áreas Protegidas + Cuarteles de Bomberos.

Reportes emergentes con factores detallados: temperatura, viento, humedad, NBR y precipitación.

📌 Aplicaciones

Prevención y alerta temprana de incendios forestales.

Apoyo directo a bomberos, brigadistas y protección civil.

Protección de áreas naturales y comunidades vulnerables.

Escalabilidad a otras provincias y países de Latinoamérica.

📚 Referencias Científicas

Van Wagner, C.E. (1987). Development and structure of the Canadian Forest Fire Weather Index System. Forestry Technical Report 35.

San-Miguel-Ayanz, J. et al. (2012). Comprehensive Monitoring of Wildfires in Europe: The European Forest Fire Information System (EFFIS).

Andrews, P.L. et al. (2007). The US Fire Danger Rating System. USDA Forest Service.

Dowdy, A.J. (2018). Climatological variability of fire weather in Australia. International Journal of Climatology.

NASA ARSET Training (2023). Introduction to Remote Sensing for Wildfire Applications.

CHIRPS: Climate Hazards Group InfraRed Precipitation with Station Data (UC Santa Barbara).

Open-Meteo API: Open weather forecast data for research and applications.

👨‍💻 Autor

Federico Nicolás Sinato – Argentina, 2025
Proyecto GeoAlertAR 🌍🔥
