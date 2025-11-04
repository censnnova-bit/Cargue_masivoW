#!/usr/bin/env python3
"""
Script para probar las consultas Oracle reales que usa TXT LINEA.
Basado en la estructura real de la tabla econ_pri_at.
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.repositories import OracleConnectionHelper

def test_consultas_txt_linea():
    """
    Prueba las consultas Oracle que usa TXT LINEA con la estructura real.
    """
    print("=" * 80)
    print("🔍 DATOS QUE TRAE TXT LINEA DESDE ORACLE")
    print("=" * 80)
    
    if not OracleConnectionHelper.test_connection():
        print("❌ No hay conexión a Oracle")
        return
    
    try:
        with OracleConnectionHelper.get_connection() as conn:
            with conn.cursor() as cursor:
                
                # 1. Probar con códigos reales de la muestra
                print("\n1️⃣ Probando con código real encontrado: L140504")
                codigo_real = 'L140504'
                
                # Query simplificada basada en la estructura real
                query_basica = """
                    SELECT 
                        e.G3E_FID,
                        e.CODIGO,
                        e.CALIBRE,
                        e.TIPO_CONDUCTOR,
                        e.MATERIAL,
                        e.AISLAMIENTO,
                        e.PROPIETARIO,
                        e.USO,
                        c.coor_gps_lon,
                        c.coor_gps_lat,
                        c.estado,
                        c.ubicacion
                    FROM econ_pri_at e
                    LEFT JOIN ccomun c ON e.g3e_fid = c.g3e_fid
                    WHERE e.CODIGO = :codigo
                """
                
                cursor.execute(query_basica, {'codigo': codigo_real})
                result = cursor.fetchone()
                
                if result:
                    columns = [col[0] for col in cursor.description]
                    print(f"   ✅ Datos encontrados para '{codigo_real}':")
                    for col, val in zip(columns, result):
                        valor_str = str(val) if val is not None else 'NULL'
                        print(f"      {col}: {valor_str}")
                else:
                    print(f"   ⚠️ No se encontraron datos para '{codigo_real}'")
                
                # 2. Verificar qué datos están disponibles en JOIN
                print(f"\n2️⃣ Verificando JOIN econ_pri_at + ccomun...")
                
                query_join = """
                    SELECT 
                        e.CODIGO,
                        e.G3E_FID,
                        e.CALIBRE,
                        e.TIPO_CONDUCTOR,
                        e.MATERIAL,
                        e.PROPIETARIO,
                        c.coor_gps_lon,
                        c.coor_gps_lat,
                        c.estado,
                        c.ubicacion,
                        c.codigo_material,
                        c.fecha_instalacion
                    FROM econ_pri_at e
                    LEFT JOIN ccomun c ON e.g3e_fid = c.g3e_fid
                    WHERE e.CODIGO IS NOT NULL 
                    AND ROWNUM <= 5
                """
                
                cursor.execute(query_join)
                results = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                
                print(f"   📋 Muestra de datos disponibles ({len(results)} registros):")
                for i, row in enumerate(results, 1):
                    print(f"\n      Registro {i}:")
                    for col, val in zip(columns, row):
                        valor_str = str(val) if val is not None else 'NULL'
                        print(f"         {col}: {valor_str}")
                
                # 3. Verificar si existe tabla cpropietario
                print(f"\n3️⃣ Verificando tabla cpropietario...")
                try:
                    cursor.execute("SELECT COUNT(*) FROM cpropietario")
                    count = cursor.fetchone()[0]
                    print(f"   ✅ Tabla cpropietario existe con {count} registros")
                    
                    # Probar JOIN completo
                    query_completo = """
                        SELECT 
                            e.CODIGO,
                            e.CALIBRE,
                            e.TIPO_CONDUCTOR,
                            e.MATERIAL,
                            e.PROPIETARIO as prop_econ,
                            c.coor_gps_lon,
                            c.coor_gps_lat,
                            c.estado,
                            c.ubicacion,
                            cp.propietario_1,
                            cp.porcentaje_prop_1
                        FROM econ_pri_at e
                        LEFT JOIN ccomun c ON e.g3e_fid = c.g3e_fid
                        LEFT JOIN cpropietario cp ON e.g3e_fid = cp.g3e_fid
                        WHERE e.CODIGO = :codigo
                    """
                    
                    cursor.execute(query_completo, {'codigo': codigo_real})
                    result = cursor.fetchone()
                    
                    if result:
                        columns = [col[0] for col in cursor.description]
                        print(f"\n   ✅ JOIN completo exitoso para '{codigo_real}':")
                        for col, val in zip(columns, result):
                            valor_str = str(val) if val is not None else 'NULL'
                            print(f"      {col}: {valor_str}")
                    
                except Exception as e:
                    print(f"   ❌ Error con cpropietario: {str(e)}")
                
                # 4. Listar códigos disponibles para pruebas
                print(f"\n4️⃣ Códigos de conductores disponibles para pruebas:")
                
                cursor.execute("""
                    SELECT CODIGO, G3E_FID, CALIBRE, MATERIAL, PROPIETARIO
                    FROM econ_pri_at 
                    WHERE CODIGO IS NOT NULL 
                    AND ROWNUM <= 10
                    ORDER BY CODIGO
                """)
                
                codigos = cursor.fetchall()
                print(f"   📋 Muestra de códigos ({len(codigos)} encontrados):")
                for codigo, fid, calibre, material, propietario in codigos:
                    print(f"      - {codigo} (FID: {fid}, {calibre} {material}, {propietario})")
                
                # 5. Resumen de campos Oracle disponibles para TXT LINEA
                print(f"\n5️⃣ RESUMEN: Campos Oracle disponibles para TXT LINEA")
                print(f"   🔍 Tabla principal: econ_pri_at")
                print(f"   📋 Campos de conductor (econ_pri_at):")
                print(f"      - G3E_FID: Identificador único")
                print(f"      - CODIGO: Código del conductor (ej: L140504)")  
                print(f"      - CALIBRE: Calibre del cable")
                print(f"      - TIPO_CONDUCTOR: Tipo (ej: MONOPOLAR)")
                print(f"      - MATERIAL: Material (ej: AL, ACSR)")
                print(f"      - AISLAMIENTO: Tipo aislamiento")
                print(f"      - PROPIETARIO: Propietario (ej: EPM, EDEQ)")
                print(f"      - USO: Uso del conductor")
                
                print(f"\n   📋 Campos de ubicación (ccomun via JOIN):")
                print(f"      - coor_gps_lon: Longitud GPS")
                print(f"      - coor_gps_lat: Latitud GPS")  
                print(f"      - estado: Estado operativo")
                print(f"      - ubicacion: Ubicación")
                print(f"      - codigo_material: Código material")
                print(f"      - fecha_instalacion: Fecha instalación")
                
                print(f"\n   📋 Campos de propiedad (cpropietario via JOIN):")
                print(f"      - propietario_1: Propietario principal")
                print(f"      - porcentaje_prop_1: Porcentaje propiedad")
    
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Verificación TXT LINEA Oracle completada")
    print("=" * 80)

if __name__ == '__main__':
    test_consultas_txt_linea()