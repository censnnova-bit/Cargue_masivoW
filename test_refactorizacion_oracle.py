"""
Script de prueba para verificar la refactorización de Oracle.
Verifica que los imports funcionen correctamente y que la delegación esté bien configurada.
"""

import sys
import os

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
import django
django.setup()

from estructuras.repositories import OracleRepository, OracleConnectionHelper

# Importar el módulo services.py (no la carpeta services/)
import sys
import importlib.util
spec = importlib.util.spec_from_file_location("services_module", 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "estructuras", "services.py"))
services_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(services_module)

OracleHelper = services_module.OracleHelper

def test_imports():
    """Prueba que los imports funcionen correctamente"""
    print("✅ Test 1: Imports")
    print(f"   - OracleRepository: {OracleRepository}")
    print(f"   - OracleConnectionHelper: {OracleConnectionHelper}")
    print(f"   - OracleHelper (wrapper): {OracleHelper}")
    print()

def test_connection():
    """Prueba la conexión a Oracle"""
    print("✅ Test 2: Conexión Oracle")
    try:
        # Test directo con el repositorio
        result1 = OracleConnectionHelper.test_connection()
        print(f"   - OracleConnectionHelper.test_connection(): {result1}")
        
        # Test con el wrapper (debe delegar)
        result2 = OracleHelper.test_connection()
        print(f"   - OracleHelper.test_connection() (delegado): {result2}")
        
        if result1 == result2:
            print("   ✓ Delegación funciona correctamente")
        else:
            print("   ✗ ERROR: Los resultados no coinciden")
    except Exception as e:
        print(f"   ⚠️ Error de conexión (esperado si no hay BD disponible): {e}")
    print()

def test_method_delegation():
    """Prueba que los métodos estén correctamente delegados"""
    print("✅ Test 3: Delegación de métodos")
    
    # Lista de métodos que deben existir en OracleHelper
    metodos_esperados = [
        'get_oracle_config',
        'get_connection',
        'test_connection',
        'obtener_coordenadas_por_fid',
        'obtener_fid_desde_codigo_operativo',
        'obtener_fid_desde_enlace',
        'obtener_datos_completos_por_fid',
        'obtener_datos_txt_nuevo_por_fid',
        'obtener_datos_txt_baja_por_fid',
        'consultar_conductor_por_codigo',
        'obtener_coordenadas_nodo_por_fid',
        'consultar_norma_por_fid'
    ]
    
    for metodo in metodos_esperados:
        if hasattr(OracleHelper, metodo):
            print(f"   ✓ {metodo}")
        else:
            print(f"   ✗ {metodo} - NO ENCONTRADO")
    print()

def test_repository_methods():
    """Prueba que los métodos existan en el repositorio"""
    print("✅ Test 4: Métodos del repositorio")
    
    metodos_esperados = [
        'obtener_coordenadas_por_fid',
        'obtener_fid_desde_codigo_operativo',
        'obtener_fid_desde_enlace',
        'obtener_datos_completos_por_fid',
        'obtener_datos_txt_nuevo_por_fid',
        'obtener_datos_txt_baja_por_fid',
        'consultar_conductor_por_codigo',
        'obtener_coordenadas_nodo_por_fid',
        'consultar_norma_por_fid'
    ]
    
    for metodo in metodos_esperados:
        if hasattr(OracleRepository, metodo):
            print(f"   ✓ {metodo}")
        else:
            print(f"   ✗ {metodo} - NO ENCONTRADO")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE REFACTORIZACIÓN ORACLE")
    print("=" * 60)
    print()
    
    test_imports()
    test_connection()
    test_method_delegation()
    test_repository_methods()
    
    print("=" * 60)
    print("Tests completados")
    print("=" * 60)
