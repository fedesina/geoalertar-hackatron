#!/usr/bin/env python3
"""
Test API CONAE - Focos de Calor
Ejecutá esto desde tu máquina para ver si te deja acceder
"""
import requests
import json

print("="*70)
print("🔥 TEST API CONAE - FOCOS DE CALOR")
print("="*70)

# URL base del geoservicio de CONAE
url = "https://geoservicios.conae.gov.ar/geoserver/ows"

# Parámetros del request WFS
params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "FocosDeCalor:FocoCalor",
    "outputFormat": "application/json"
}

print("\n📡 INTENTANDO CONECTAR...")
print(f"URL: {url}")
print(f"Parámetros: {json.dumps(params, indent=2)}")
print("\nEsperando respuesta...\n")

try:
    # Hacemos el request con timeout de 30 segundos
    response = requests.get(url, params=params, timeout=30)
    
    print(f"📊 Status Code: {response.status_code}")
    print(f"📋 Headers de respuesta:")
    for key, value in response.headers.items():
        print(f"   {key}: {value}")
    
    # Verificar si fue exitoso
    if response.status_code == 200:
        print("\n✅ CONEXIÓN EXITOSA!")
        
        try:
            data = response.json()
            
            print(f"\n🔍 Tipo de dato: {data.get('type', 'Unknown')}")
            
            if 'features' in data:
                total = len(data['features'])
                print(f"🔥 Total de focos: {total}")
                
                if total > 0:
                    print("\n📍 PRIMER FOCO (EJEMPLO):")
                    print(json.dumps(data['features'][0], indent=2, ensure_ascii=False))
                    
                    print("\n🗺️ FOCOS EN CÓRDOBA:")
                    focos_cba = []
                    for f in data['features']:
                        coords = f['geometry']['coordinates']
                        # Bbox aproximado de Córdoba
                        if -65.0 <= coords[0] <= -62.0 and -33.5 <= coords[1] <= -29.5:
                            focos_cba.append(f)
                    
                    print(f"   Encontrados en Córdoba: {len(focos_cba)}")
                    
                    if focos_cba:
                        print("\n   Primeros 5 focos:")
                        for i, foco in enumerate(focos_cba[:5], 1):
                            coords = foco['geometry']['coordinates']
                            props = foco['properties']
                            fecha = props.get('fecha', props.get('fecha_hora', 'N/A'))
                            print(f"   {i}. [{coords[1]:.4f}, {coords[0]:.4f}] - {fecha}")
                else:
                    print("⚠️ No hay focos actualmente")
            else:
                print(f"\n⚠️ Respuesta sin 'features'. Keys: {list(data.keys())}")
                
        except json.JSONDecodeError:
            print("\n❌ La respuesta no es JSON válido")
            print(f"Contenido: {response.text[:500]}")
    
    elif response.status_code == 403:
        print("\n❌ ACCESO DENEGADO (403 Forbidden)")
        print("\nPosibles causas:")
        print("  1. Requiere autenticación (usuario/password)")
        print("  2. Bloqueado por CORS (desde navegador)")
        print("  3. IP restringida (solo IPs argentinas?)")
        print("  4. Endpoint cambió o está mal")
        print("\n💡 Contactá al CONAE para pedir acceso")
        
    else:
        print(f"\n❌ ERROR HTTP {response.status_code}")
        print(f"Respuesta: {response.text[:500]}")

except requests.exceptions.Timeout:
    print("\n❌ TIMEOUT - La API no respondió en 30 segundos")
    
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR DE CONEXIÓN - No se pudo conectar al servidor")
    
except Exception as e:
    print(f"\n❌ ERROR INESPERADO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("FIN DEL TEST")
print("="*70)
print("\n💬 Pasale el resultado completo a Claude para ver qué sigue")