#!/usr/bin/env python3
"""
Script de prueba para verificar qué datos trae TXT LINEA desde Oracle.

Simula las consultas Oracle que hace TXT LINEA para conductores.
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.repositories import OracleRepository, OracleConnectionHelper

def test_txt_linea_oracle():
    """
    Prueba las consultas Oracle específicas para TXT LINEA.
    
    TXT LINEA usa la tabla econ_pri_at + ccomun + cpropietario
    y busca por cp.codigo (código operativo de conductor).
    """
    print("=" * 80)
    print("🔍 VERIFICACIÓN: Datos que trae TXT LINEA desde Oracle")
    print("=" * 80)
    
    # 1. Verificar conexión
    print("\n1️⃣ Verificando conexión a Oracle...")
    if not OracleConnectionHelper.test_connection():
        print("❌ No hay conexión a Oracle")
        return
    print("✅ Conexión Oracle exitosa")
    
    # 2. Códigos de conductor para probar
    # Estos deberían ser códigos de la tabla econ_pri_at
    codigos_conductor = [
        'L129251',      # Código típico de conductor
        'AMVLS75784',   # Código con prefijo
        'GLVL38505',    # Otro código
        'Z12345',       # Código operativo con Z
    ]
    
    print(f"\n2️⃣ Probando consultas de conductores...")
    print(f"   Tabla: econ_pri_at + ccomun + cpropietario")
    print(f"   Campo búsqueda: cp.codigo")
    
    for codigo in codigos_conductor:
        print(f"\n🔍 Consultando conductor: '{codigo}'")
        
        # Usar la función específica para conductores
        datos = OracleRepository.consultar_conductor_por_codigo(codigo)
        
        if datos:
            print(f"   ✅ Datos encontrados:")
            for campo, valor in datos.items():
                print(f"      {campo}: {valor}")
        else:
            print(f"   ⚠️ No se encontraron datos para '{codigo}'")
    
    # 3. Probar consulta completa como la hace TXT LINEA
    print(f"\n3️⃣ Probando consulta completa TXT LINEA...")
    
    # Esta es la consulta que hace _consultar_conductor_oracle en services.py
    try:
        with OracleConnectionHelper.get_connection() as conn:
            with conn.cursor() as cursor:
                # Query original de TXT LINEA
                query = """
                    SELECT 
                        c.coor_gps_lon,
                        c.coor_gps_lat,
                        c.estado,
                        c.ubicacion,
                        c.codigo_material,
                        c.fecha_instalacion,
                        c.fecha_operacion,
                        c.proyecto,
                        c.empresa_origen,
                        c.observaciones,
                        c.tipo_proyecto,
                        c.id_mercado,
                        c.clasificacion_mercado,
                        c.uc,
                        c.estado_salud,
                        c.ot_maximo,
                        c.codigo_marcacion,
                        c.salinidad,
                        cp.uso,
                        pr.propietario_1,
                        pr.porcentaje_prop_1,
                        cp.g3e_fid,
                        cp.codigo
                    FROM econ_pri_at cp
                    JOIN ccomun c USING (g3e_fid)
                    LEFT JOIN cpropietario pr USING (g3e_fid)
                    WHERE cp.codigo = :codigo
                    AND ROWNUM = 1
                """
                
                # Probar con el primer código
                codigo_prueba = 'L129251'
                print(f"   Ejecutando query para: {codigo_prueba}")
                
                cursor.execute(query, {'codigo': codigo_prueba})
                row = cursor.fetchone()
                
                if row:
                    columns = [col[0] for col in cursor.description]
                    print(f"   ✅ Query exitosa - {len(columns)} campos encontrados:")
                    
                    for i, (col, val) in enumerate(zip(columns, row)):
                        valor_str = str(val) if val is not None else 'NULL'
                        print(f"      {i+1:2d}. {col}: {valor_str}")
                        
                else:
                    print(f"   ⚠️ No hay datos para '{codigo_prueba}'")
                    
                # Probar obtener algunos registros para ver qué códigos existen
                print(f"\n   📋 Obteniendo muestra de códigos existentes...")
                cursor.execute("""
                    SELECT codigo, g3e_fid 
                    FROM econ_pri_at 
                    WHERE ROWNUM <= 10
                """)
                
                registros = cursor.fetchall()
                if registros:
                    print(f"   Códigos disponibles en econ_pri_at:")
                    for codigo, fid in registros:
                        print(f"      - {codigo} (FID: {fid})")
                else:
                    print(f"   ⚠️ No se encontraron registros en econ_pri_at")
    
    except Exception as e:
        print(f"   ❌ Error en consulta: {str(e)}")
    
    # 4. Verificar tabla econ_pri_at
    print(f"\n4️⃣ Verificando estructura de tabla econ_pri_at...")
    try:
        with OracleConnectionHelper.get_connection() as conn:
            with conn.cursor() as cursor:
                # Contar registros
                cursor.execute("SELECT COUNT(*) FROM econ_pri_at")
                count = cursor.fetchone()[0]
                print(f"   📊 Registros en econ_pri_at: {count}")
                
                # Ver estructura (primeras 3 columnas)
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM user_tab_columns 
                    WHERE table_name = 'ECON_PRI_AT' 
                    AND ROWNUM <= 10
                    ORDER BY column_id
                """)
                
                columnas = cursor.fetchall()
                if columnas:
                    print(f"   📋 Primeras columnas de econ_pri_at:")
                    for col_name, data_type in columnas:
                        print(f"      - {col_name} ({data_type})")
                
    except Exception as e:
        print(f"   ❌ Error verificando tabla: {str(e)}")
    
    print(f"\n" + "=" * 80)
    print("✅ Verificación TXT LINEA Oracle completada")
    print("=" * 80)

if __name__ == '__main__':
    test_txt_linea_oracle()