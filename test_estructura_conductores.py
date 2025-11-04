#!/usr/bin/env python3
"""
Script para verificar la estructura real de las tablas de conductores en Oracle.
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
django.setup()

from estructuras.repositories import OracleConnectionHelper

def verificar_estructura_conductores():
    """
    Verifica la estructura real de las tablas relacionadas con conductores.
    """
    print("=" * 80)
    print("🔍 VERIFICACIÓN: Estructura de tablas de conductores en Oracle")
    print("=" * 80)
    
    if not OracleConnectionHelper.test_connection():
        print("❌ No hay conexión a Oracle")
        return
    
    try:
        with OracleConnectionHelper.get_connection() as conn:
            with conn.cursor() as cursor:
                
                # 1. Verificar si existe tabla econ_pri_at
                print("\n1️⃣ Verificando existencia de tabla econ_pri_at...")
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_tables 
                        WHERE table_name = 'ECON_PRI_AT'
                    """)
                    exists = cursor.fetchone()[0]
                    if exists:
                        print("✅ Tabla econ_pri_at existe")
                        
                        # Ver columnas de econ_pri_at
                        cursor.execute("""
                            SELECT column_name, data_type, data_length 
                            FROM user_tab_columns 
                            WHERE table_name = 'ECON_PRI_AT' 
                            ORDER BY column_id
                        """)
                        columnas = cursor.fetchall()
                        print(f"   📋 Columnas en econ_pri_at ({len(columnas)} total):")
                        for col_name, data_type, length in columnas:
                            print(f"      - {col_name} ({data_type}({length if length else 'N/A'}))")
                    else:
                        print("❌ Tabla econ_pri_at NO existe")
                except Exception as e:
                    print(f"❌ Error verificando econ_pri_at: {str(e)}")
                
                # 2. Buscar tablas relacionadas con conductores
                print("\n2️⃣ Buscando tablas relacionadas con conductores...")
                try:
                    cursor.execute("""
                        SELECT table_name 
                        FROM user_tables 
                        WHERE table_name LIKE '%CONDUC%' 
                           OR table_name LIKE '%ECON%'
                           OR table_name LIKE '%LINEA%'
                           OR table_name LIKE '%CONDUCTOR%'
                        ORDER BY table_name
                    """)
                    tablas = cursor.fetchall()
                    if tablas:
                        print("   📋 Tablas relacionadas con conductores:")
                        for (tabla,) in tablas:
                            # Contar registros en cada tabla
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                                count = cursor.fetchone()[0]
                                print(f"      - {tabla} ({count} registros)")
                            except:
                                print(f"      - {tabla} (sin acceso)")
                    else:
                        print("   ⚠️ No se encontraron tablas relacionadas con conductores")
                except Exception as e:
                    print(f"❌ Error buscando tablas: {str(e)}")
                
                # 3. Si econ_pri_at existe, ver muestra de datos
                print("\n3️⃣ Muestra de datos en econ_pri_at...")
                try:
                    cursor.execute("""
                        SELECT * FROM (
                            SELECT * FROM econ_pri_at WHERE ROWNUM <= 3
                        )
                    """)
                    
                    # Obtener descripción de columnas
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    
                    print(f"   📊 Columnas disponibles ({len(columns)} total):")
                    for i, col in enumerate(columns, 1):
                        print(f"      {i:2d}. {col}")
                    
                    if rows:
                        print(f"\n   📋 Muestra de datos ({len(rows)} registros):")
                        for i, row in enumerate(rows, 1):
                            print(f"      Registro {i}:")
                            for col, val in zip(columns, row):
                                valor_str = str(val) if val is not None else 'NULL'
                                # Truncar valores largos
                                if len(valor_str) > 50:
                                    valor_str = valor_str[:47] + '...'
                                print(f"         {col}: {valor_str}")
                            print()
                            
                except Exception as e:
                    print(f"❌ Error obteniendo datos: {str(e)}")
                
                # 4. Verificar si la query real de TXT LINEA funciona
                print("\n4️⃣ Verificando query específica de TXT LINEA...")
                
                # Buscar la columna correcta que podría ser el código
                try:
                    cursor.execute("""
                        SELECT column_name 
                        FROM user_tab_columns 
                        WHERE table_name = 'ECON_PRI_AT' 
                        AND (column_name LIKE '%CODIGO%' 
                             OR column_name LIKE '%CODE%'
                             OR column_name LIKE '%ID%')
                        ORDER BY column_name
                    """)
                    cols_codigo = cursor.fetchall()
                    if cols_codigo:
                        print("   📋 Posibles columnas de código:")
                        for (col,) in cols_codigo:
                            print(f"      - {col}")
                except Exception as e:
                    print(f"❌ Error buscando columnas de código: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ Verificación de estructura completada")
    print("=" * 80)

if __name__ == '__main__':
    verificar_estructura_conductores()