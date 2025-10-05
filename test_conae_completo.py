#!/usr/bin/env python3
"""
Test completo de servicios CONAE WFS
"""
import requests
import json

print("="*70)
print("🛰️ TEST COMPLETO - SERVICIOS CONAE")
print("="*70)

# Base URL
base_url = "https://geoservicios.conae.gov.ar/geoserver/ows"

# Servicios a probar
servicios = [
    # Suelo
    ("FocosDeCalor:FocoCalor", "Focos de Calor"),
    ("HumedadSuelo:SAOCOM", "Humedad SAOCOM"),
    ("HumedadSuelo:SMAP_SMOS", "Humedad SMAP-SMOS"),
    
    # Vegetación (probamos posibles nombres)
    ("Vegetacion:NDVI", "NDVI"),
    ("Vegetacion:Vegetation", "Vegetación"),
    
    # Agua
    ("Agua:EstatusHidrico", "Estatus Hídrico"),
    ("Agua:Precipitaciones", "Precipitaciones"),
    ("Agua:Inundaciones", "Inundaciones"),
]

resultados = []

for servicio, nombre in servicios:
    print(f"\n{'='*70}")
    print(f"🔍 Probando: {nombre}")
    print(f"   TypeName: {servicio}")
    print("-"*70)
    
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": servicio,
        "outputFormat": "application/json",
        "maxFeatures": 5  # Solo primeros 5 para no saturar
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                total = len(data.get('features', []))
                
                print(f"✅ FUNCIONA - {total} features")
                
                if total > 0:
                    primer_feature = data['features'][0]
                    props = primer_feature.get('properties', {})
                    
                    print(f"\n📊 Propiedades disponibles:")
                    for key in props.keys():
                        print(f"   - {key}")
                    
                    print(f"\n📍 Primer registro:")
                    print(json.dumps(primer_feature, indent=2, ensure_ascii=False)[:500])
                    
                    resultados.append({
                        'servicio': servicio,
                        'nombre': nombre,
                        'funciona': True,
                        'total': total,
                        'propiedades': list(props.keys())
                    })
                else:
                    print("⚠️ Respuesta vacía (sin features)")
                    resultados.append({
                        'servicio': servicio,
                        'nombre': nombre,
                        'funciona': True,
                        'total': 0,
                        'propiedades': []
                    })
                    
            except json.JSONDecodeError:
                print(f"❌ Respuesta no es JSON")
                print(f"   Contenido: {response.text[:200]}")
                resultados.append({
                    'servicio': servicio,
                    'nombre': nombre,
                    'funciona': False,
                    'error': 'JSON inválido'
                })
        else:
            print(f"❌ Error HTTP {response.status_code}")
            if response.status_code == 404:
                print("   (Servicio no existe con ese nombre)")
            resultados.append({
                'servicio': servicio,
                'nombre': nombre,
                'funciona': False,
                'error': f'HTTP {response.status_code}'
            })
            
    except Exception as e:
        print(f"❌ Error: {e}")
        resultados.append({
            'servicio': servicio,
            'nombre': nombre,
            'funciona': False,
            'error': str(e)
        })

# Resumen final
print("\n" + "="*70)
print("📊 RESUMEN FINAL")
print("="*70)

print("\n✅ SERVICIOS FUNCIONALES:")
for r in resultados:
    if r['funciona'] and r.get('total', 0) > 0:
        print(f"   • {r['nombre']}: {r['total']} registros")
        if r.get('propiedades'):
            print(f"     Propiedades: {', '.join(r['propiedades'][:5])}")

print("\n⚠️ SERVICIOS VACÍOS:")
for r in resultados:
    if r['funciona'] and r.get('total', 0) == 0:
        print(f"   • {r['nombre']}")

print("\n❌ SERVICIOS NO DISPONIBLES:")
for r in resultados:
    if not r['funciona']:
        print(f"   • {r['nombre']}: {r.get('error', 'Error desconocido')}")

print("\n" + "="*70)
print("💡 Ahora sabemos qué datos podemos integrar del CONAE")
print("="*70)