#!/usr/bin/env python3
"""
Script para crear archivos Excel de prueba para validar las nuevas reglas de validación.
Basado en input5.xlsx
"""

import pandas as pd
import shutil
import os
from datetime import datetime

def crear_excel_coordenadas_invalidas():
    """Crear Excel con coordenadas inválidas"""
    print("Creando test_coordenadas_invalidas.xlsx...")
    
    # Copiar el archivo original
    origen = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/media/uploads/excel/input5.xlsx"
    destino = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/test_coordenadas_invalidas.xlsx"
    
    shutil.copy2(origen, destino)
    
    # Leer y modificar
    df = pd.read_excel(destino, sheet_name='Estructuras_N1-N2-N3', header=1)
    
    # Modificar coordenadas para crear errores
    # Fila 0: X positiva (debe ser negativa)
    df.loc[0, 'Coordenada_X1\nLONGITUD'] = 73.24081  # Positiva (ERROR)
    
    # Fila 1: Y negativa (debe ser positiva) 
    df.loc[1, 'Coordenada_Y1\nLATITUD'] = -8.257043  # Negativa (ERROR)
    
    # Fila 2: Ambas inválidas
    df.loc[2, 'Coordenada_X1\nLONGITUD'] = 74.12345  # Positiva (ERROR)
    df.loc[2, 'Coordenada_Y1\nLATITUD'] = -9.67890   # Negativa (ERROR)
    
    # Guardar
    with pd.ExcelWriter(destino, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=1)
        
        # Crear hoja con headers originales
        headers_df = pd.DataFrame([df.columns.tolist()])
        headers_df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=0)
    
    print(f"✓ Creado: {destino}")
    return destino

def crear_excel_año_invalido():
    """Crear Excel con años inválidos en entrada operación"""
    print("Creando test_año_invalido.xlsx...")
    
    origen = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/media/uploads/excel/input5.xlsx"
    destino = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/test_año_invalido.xlsx"
    
    shutil.copy2(origen, destino)
    df = pd.read_excel(destino, sheet_name='Estructuras_N1-N2-N3', header=1)
    
    # Agregar algunos códigos FID_rep para hacer que sean registros de desmantelado/reposición
    df.loc[0, 'Código FID_rep'] = 'Z123456'  # Registro con FID_rep
    df.loc[1, 'Código FID_rep'] = 'Z789012'  # Registro con FID_rep
    df.loc[2, 'Código FID_rep'] = 'Z345678'  # Registro con FID_rep
    
    # Modificar años para crear errores
    df.loc[0, 'Año entrada operación_rep'] = ''        # Vacío (ERROR)
    df.loc[1, 'Año entrada operación_rep'] = 2030      # Futuro (ERROR)  
    df.loc[2, 'Año entrada operación_rep'] = 'abc'     # No numérico (ERROR)
    
    # Guardar
    with pd.ExcelWriter(destino, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=1)
        headers_df = pd.DataFrame([df.columns.tolist()])
        headers_df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=0)
    
    print(f"✓ Creado: {destino}")
    return destino

def crear_excel_ubicacion_vacia():
    """Crear Excel con ubicación vacía"""
    print("Creando test_ubicacion_vacia.xlsx...")
    
    origen = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/media/uploads/excel/input5.xlsx"
    destino = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/test_ubicacion_vacia.xlsx"
    
    shutil.copy2(origen, destino)
    df = pd.read_excel(destino, sheet_name='Estructuras_N1-N2-N3', header=1)
    
    # Vaciar ubicación en algunas filas
    df.loc[0, 'Ubicación'] = ''          # Vacío (ERROR)
    df.loc[1, 'Ubicación'] = None        # Nulo (ERROR)
    df.loc[2, 'Ubicación'] = 'nan'       # NaN string (ERROR)
    
    # Guardar
    with pd.ExcelWriter(destino, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=1)
        headers_df = pd.DataFrame([df.columns.tolist()])
        headers_df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=0)
    
    print(f"✓ Creado: {destino}")
    return destino

def crear_excel_nombre_vacio():
    """Crear Excel con nombre vacío"""
    print("Creando test_nombre_vacio.xlsx...")
    
    origen = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/media/uploads/excel/input5.xlsx"
    destino = "c:/Users/wvelasco/OneDrive - Grupo EPM/Escritorio/Cargue-Masivo/Cargue_Masivo/test_nombre_vacio.xlsx"
    
    shutil.copy2(origen, destino)
    df = pd.read_excel(destino, sheet_name='Estructuras_N1-N2-N3', header=1)
    
    # Vaciar nombre en algunas filas  
    df.loc[0, 'Nombre'] = ''             # Vacío (ERROR)
    df.loc[1, 'Nombre'] = None           # Nulo (ERROR) 
    df.loc[2, 'Nombre'] = 'none'         # None string (ERROR)
    
    # Guardar
    with pd.ExcelWriter(destino, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=1)
        headers_df = pd.DataFrame([df.columns.tolist()])
        headers_df.to_excel(writer, sheet_name='Estructuras_N1-N2-N3', index=False, header=False, startrow=0)
    
    print(f"✓ Creado: {destino}")
    return destino

if __name__ == "__main__":
    print("=== Creando archivos Excel de prueba ===")
    
    try:
        archivos_creados = []
        archivos_creados.append(crear_excel_coordenadas_invalidas())
        archivos_creados.append(crear_excel_año_invalido()) 
        archivos_creados.append(crear_excel_ubicacion_vacia())
        archivos_creados.append(crear_excel_nombre_vacio())
        
        print(f"\n✅ COMPLETADO: {len(archivos_creados)} archivos de prueba creados:")
        for archivo in archivos_creados:
            print(f"  - {os.path.basename(archivo)}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise