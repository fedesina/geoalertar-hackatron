# 🌍 GeoAlertAR Demo — NASA Space Apps Hackatron 2025

## 📖 Descripción

**GeoAlertAR Demo v6.0** integra observación de la Tierra (MODIS, CHIRPS), pronósticos climáticos (Open-Meteo), datos de humedad del suelo (SAOCOM/CONAE) y **detección de focos reales (NASA FIRMS)** para estimar un índice de riesgo de incendios en Córdoba, Argentina, y visualizarlo en un mapa interactivo con hexágonos.

El objetivo es demostrar un pipeline reproducible, científicamente sólido y escalable a otras provincias.

---

## 🚀 Novedades v6.0

### ✨ **Integración NASA FIRMS**
- 🔥 **Focos de incendio reales** detectados por satélite MODIS (últimos 7 días)
- 🟣 **Visualización con círculos violetas** animados en el mapa
- 📊 **Información detallada** por foco: brillo, confianza, fecha/hora
- 🎯 **Comparación directa** entre predicciones de riesgo y focos reales

### 🐛 **Correcciones Críticas**
- ✅ Manejo robusto de valores `null` en NDVI/NBR en el modal
- ✅ Conversión correcta de `NaN` a `None` en GeoJSON de salida
- ✅ Validación completa de datos antes de export

### 📅 **Mejoras de UX**
- ⏰ **Timestamp visible** de última actualización en el mapa
- 📊 **Contador de focos FIRMS** en el panel lateral
- 🎨 **Animación pulsante** en focos reales para mejor visibilidad

---

## 📦 Estructura del Repositorio

```
geoalertar-hackatron/
├── datos_geo/
│   └── grilla_hexagonos_cordoba.geojson    # Grilla hexagonal de Córdoba
├── datos_saocom/
│   └── humedad_suelo_demo.csv              # Datos de humedad (CONAE)
├── layers/
│   ├── Areas_Protegidas_Poligono.geojson   # Áreas protegidas
│   ├── Cuartel_Bomberos_Punto.geojson      # Cuarteles de bomberos
│   └── Comunidades_Indigenas_CBA.geojson   # Comunidades indígenas
├── docs/
│   ├── index.html                          # Mapa interactivo (v6.0)
│   ├── riesgo_hexagonos.geojson            # Output: Riesgo por hexágono
│   └── firms_focos.geojson                 # Output: Focos NASA FIRMS
├── analizador_demo.py                      # Motor de análisis (v6.0)
├── test_rapido.py                          # Script de validación
├── README.md
└── LICENSE
```

---

## ⚡️ Quickstart

### 1️⃣ **Dependencias**

```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv .venv

# Activar
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install earthengine-api pandas geojson requests numpy
```

### 2️⃣ **Autenticación Google Earth Engine**

```bash
earthengine authenticate
```

### 3️⃣ **Configurar NASA FIRMS (Opcional pero Recomendado)**

1. Creá una cuenta en: https://firms.modaps.eosdis.nasa.gov/
2. Obtené tu MAP_KEY (token) en: https://firms.modaps.eosdis.nasa.gov/api/data_availability/
3. Editá `analizador_demo.py` línea 21:
   ```python
   FIRMS_MAP_KEY = 'TU_TOKEN_AQUI'  # Reemplazá con tu token
   ```

**Nota:** Si no configurás el token, el sistema usará datos de prueba simulados.

### 4️⃣ **Ejecutar Análisis**

```bash
python analizador_demo.py
```

**Salida esperada:**
- `docs/riesgo_hexagonos.geojson` → Hexágonos con riesgo calculado
- `docs/firms_focos.geojson` → Focos reales detectados

**Tiempo de ejecución:** ~15 minutos para 195 hexágonos

### 5️⃣ **Visualizar Mapa**

```bash
# Abrir servidor local
python -m http.server 8000

# Abrir en navegador:
# http://localhost:8000/docs/index.html
```

### 6️⃣ **Testing Pre-Entrega**

```bash
python test_rapido.py
```

---

## 🧠 Pipeline de Análisis

### 📡 **ENTRADA: Datos Satelitales**

1. **Grilla Hexagonal**: División espacial de Córdoba (195 hexágonos)

2. **Google Earth Engine** (últimos 30-90 días):
   - **MODIS MOD09GA** → NDVI (vegetación), NBR (quemado)
   - **MODIS MOD11A1** → LST (temperatura superficial)
   - **CHIRPS** → Precipitación acumulada (60 días)
   - **Máscara de agua** → Excluye lagos/ríos del cálculo

3. **Open-Meteo API** (tiempo real):
   - Humedad relativa mínima (%)
   - Viento máximo (km/h)

4. **SAOCOM (CONAE)** (opcional):
   - Humedad del suelo (%) por zona

5. **NASA FIRMS** (últimos 7 días):
   - Focos de incendio detectados por MODIS
   - Brillo (Kelvin), confianza (%)

### 🧮 **PROCESO: Modelo de Riesgo**

```python
# Riesgo Base (sequedad de vegetación)
riesgo_base = (NBR_norm × 0.7) + ((1 - NDVI_norm) × 0.3)

# Multiplicadores climáticos
mult_temp     = 1 → 1.8×   # Temperatura extrema
mult_humedad  = 1 → 2.5×   # Humedad atmosférica baja
mult_viento   = 1 → 3.0×   # Viento fuerte
mult_precip   = 1 → 1.5×   # Sequía prolongada
mult_suelo    = 1 → 1.8×   # Suelo seco (SAOCOM)

# Riesgo Final (0-100%)
riesgo = riesgo_base × mult_temp × mult_humedad × mult_viento × mult_precip × mult_suelo × 100
```

**Clasificación:**
- **🔴 CRÍTICO**: > 80%
- **🟠 ALTO**: 60-80%
- **🟡 MODERADO**: 40-60%
- **🟢 BAJO**: < 40%

### 📤 **SALIDA: Visualización Web**

- Mapa interactivo Leaflet + Tailwind
- Filtros por nivel de riesgo
- Capas de contexto (áreas protegidas, bomberos, comunidades)
- **🔥 Focos reales NASA FIRMS** (círculos violetas)
- Pop-ups con reportes detallados

---

## 🗺️ Interfaz Web - Features

### 🎛️ **Controles Interactivos**

1. **Niveles de Riesgo**: Filtrar hexágonos por categoría
2. **Capas de Contexto**:
   - Áreas Protegidas
   - Cuarteles de Bomberos
   - Comunidades Indígenas
3. **🔥 Focos NASA FIRMS**: Toggle para mostrar/ocultar focos reales

### 🗺️ **Basemaps Disponibles**

- 🛰️ ESRI Satélite
- 🌍 NASA GIBS (MODIS True Color)
- 🌑 Mapa Oscuro (CartoDB)
- 🗺️ Calles (OpenStreetMap)

### 📊 **Reportes por Hexágono**

Click en cualquier hexágono para ver:
- Nivel de riesgo (%) y clasificación
- Pronóstico del día (viento, humedad)
- Humedad del suelo (SAOCOM)
- Estado de combustible (NDVI, NBR)
- Temperatura superficial (LST)
- Precipitación acumulada (60d)

---

## 🗃️ Fuentes de Datos

| Dataset | Fuente | Resolución | Actualización | Uso |
|---------|--------|------------|---------------|-----|
| **MODIS MOD09GA** | NASA Terra | 500m | Diaria | NDVI, NBR |
| **MODIS MOD11A1** | NASA Terra | 1km | Diaria | Temperatura LST |
| **CHIRPS** | UCSB/NASA | 5km | Pentad (5 días) | Precipitación |
| **SAOCOM** | CONAE | Variable | Ad-hoc | Humedad suelo |
| **Open-Meteo** | Open-Meteo | Variable | Tiempo real | Clima actual |
| **FIRMS** | NASA | 1km (MODIS) | 3 horas | Focos reales |

---

## 📅 Ventanas Temporales

| Variable | Ventana | Agregación |
|----------|---------|------------|
| NDVI/NBR | 90 días | Mediana |
| LST | 15 días | Máxima |
| Precipitación | 60 días | Suma |
| Clima (Open-Meteo) | Actual | Instantánea |
| SAOCOM | Fecha más cercana | - |
| FIRMS | 7 días | Puntos individuales |

---

## 🧪 Validación Científica

### ✅ **Fundamentos**

El modelo se basa en sistemas internacionales de referencia:
- 🇨🇦 **Canadian FWI** (Fire Weather Index)
- 🇪🇺 **EFFIS** (European Forest Fire Information System)
- 🇺🇸 **NFDRS** (National Fire Danger Rating System)
- 🇦🇺 **AFDRS** (Australian Fire Danger Rating System)

### 📊 **Validación con FIRMS**

La integración de NASA FIRMS permite:
1. **Comparación directa**: Predicciones vs focos reales
2. **Métricas de accuracy**: Precisión, recall, F1-score
3. **Análisis de falsos positivos/negativos**
4. **Calibración continua** del modelo

---

## 🎯 Ventajas Competitivas

### 1️⃣ **Integración SAOCOM (CONAE Argentina)**
- Único sistema que incorpora datos de humedad del suelo argentinos
- Ventaja sobre sistemas internacionales que no tienen esta data

### 2️⃣ **Análisis Espacial con Hexágonos**
- Superior a grillas cuadradas o puntos aislados
- Mejor representación de fenómenos naturales

### 3️⃣ **Validación en Tiempo Real con FIRMS**
- Comparación directa con focos satelitales reales
- Feedback loop para mejora continua

### 4️⃣ **Modelo Multivariable Avanzado**
- No solo índices de vegetación
- Considera clima, precipitación, humedad del suelo
- Multiplicadores dinámicos basados en física del fuego

### 5️⃣ **100% Open Source y Reproducible**
- Código abierto
- Datos públicos (excepto SAOCOM que es opcional)
- Pipeline documentado

---

## 📚 Referencias

1. Van Wagner, C.E. (1987). *Canadian Forest Fire Weather Index System*. Canadian Forestry Service.
2. San-Miguel-Ayanz, J. et al. (2012). *European Forest Fire Information System (EFFIS)*. JRC Technical Reports.
3. Andrews, P.L. et al. (2007). *National Fire Danger Rating System (NFDRS)*. USDA Forest Service.
4. Dowdy, A.J. (2018). *Fire weather in Australia*. Climate Dynamics.
5. NASA ARSET (2023). *Wildfire Applications of Remote Sensing*.
6. CHIRPS – Climate Hazards Group, UCSB.
7. NASA FIRMS (2024). *Fire Information for Resource Management System*.

---

## 👨‍💻 Desarrollo

### 📋 **TO-DO para Producción**

- [ ] Configurar FIRMS_MAP_KEY real (no usar datos simulados)
- [ ] Automatizar ejecución cada 12-24 horas
- [ ] Integrar sistema de alertas (email/SMS)
- [ ] Agregar más provincias (Buenos Aires, Mendoza, etc.)
- [ ] Implementar API REST para consultas
- [ ] Dashboard de métricas históricas
- [ ] Exportar reportes PDF automáticos

### 🐛 **Reportar Bugs**

Si encontrás algún problema, abrí un issue en GitHub con:
1. Descripción del error
2. Logs del script
3. Archivos GeoJSON generados (si aplica)
4. Sistema operativo y versión de Python

---

## 📄 Licencia

MIT License - Ver archivo `LICENSE`

---

## 👤 Autor

**Federico Nicolás Sinato**  
📧 Email: [tu-email@ejemplo.com]  
🔗 GitHub: [github.com/fedesina/geoalertar-hackatron](https://github.com/fedesina/geoalertar-hackatron)  
🇦🇷 Argentina, 2025

---

## 🏆 Hackatron 2025 - NASA Space Apps Challenge

**Proyecto GeoAlertAR** - Sistema de Predicción de Incendios con Validación Satelital en Tiempo Real

*Combinando lo mejor de la tecnología espacial argentina (SAOCOM/CONAE) con datos globales de NASA para proteger nuestros bosques.* 🌲🔥🛰️

---

## 🙏 Agradecimientos

- **NASA** por MODIS, CHIRPS y FIRMS
- **CONAE** por datos SAOCOM
- **Google Earth Engine** por infraestructura de procesamiento
- **Open-Meteo** por datos climáticos abiertos
- **OpenStreetMap** y contribuidores por mapas base

---

**¡Protejamos nuestros bosques con ciencia y tecnología!** 🌲🇦🇷