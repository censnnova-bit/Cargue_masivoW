#!/usr/bin/env python3
"""
Test específico para verificar que la validación de año corregida funciona correctamente
"""

import os
import sys
import uuid
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
sys.path.append(str(Path(__file__).parent))

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from estructuras.models import ProcesoEstructura
from estructuras.services import ExcelProcessor, FileGenerator


def test_año_1996_valido():
    """Test que verifica que 1996 es un año válido y no genera error falso"""
    print("🧪 Testeando validación de año corregida con input5.xlsx")
    
    archivo_path = "media/uploads/excel/input5.xlsx"
    if not os.path.exists(archivo_path):
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return False
    
    try:
        with open(archivo_path, 'rb') as f:
            content = f.read()
        
        archivo_django = SimpleUploadedFile(
            name="input5.xlsx",
            content=content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        proceso = ProcesoEstructura.objects.create(
            id=uuid.uuid4(),
            archivo_excel=archivo_django,
            estado='PROCESANDO',
            circuito='TEST_CORRECCION'
        )
        
        processor = ExcelProcessor(proceso)
        datos, campos_faltantes = processor.procesar_archivo()
        
        if campos_faltantes:
            print(f"⚠️ Campos faltantes: {campos_faltantes}")
            return False
        
        proceso.datos_excel = datos
        proceso.save()
        
        generator = FileGenerator(proceso)
        
        try:
            resultado = generator.generar_txt()
            print(f"✅ Archivo TXT generado exitosamente: {resultado}")
            print("✅ La validación de año corregida funciona - no hay errores falsos")
            return True
            
        except Exception as e:
            if "VALIDATION_ERRORS" in str(e):
                errores = getattr(proceso, 'errores', [])
                
                # Buscar errores específicos de año con "1996"
                errores_año_1996 = [
                    err for err in errores 
                    if 'año' in err.get('descripcion', '').lower() and '1996' in str(err.get('descripcion', ''))
                ]
                
                if errores_año_1996:
                    print(f"❌ ERROR FALSO DETECTADO: Se encontraron {len(errores_año_1996)} errores con 1996:")
                    for err in errores_año_1996:
                        print(f"   - {err.get('descripcion', '')}")
                    return False
                else:
                    print(f"✅ No hay errores falsos de año 1996 (total errores: {len(errores)})")
                    # Mostrar otros tipos de errores si existen
                    if errores:
                        print("   Otros errores encontrados (no relacionados con año 1996):")
                        for err in errores[:3]:
                            desc = err.get('descripcion', '')
                            if 'año' not in desc.lower() or '1996' not in desc:
                                print(f"   - {desc}")
                    return True
            else:
                print(f"❌ Error inesperado: {e}")
                return False
    
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False
    
    finally:
        try:
            if 'proceso' in locals():
                proceso.delete()
        except Exception:
            pass


if __name__ == "__main__":
    print("🚀 VERIFICANDO CORRECCIÓN DE VALIDACIÓN DE AÑO")
    print("=" * 50)
    
    exito = test_año_1996_valido()
    
    if exito:
        print("\n🎉 ¡CORRECCIÓN EXITOSA!")
        print("✅ La validación de año ya no genera errores falsos")
        print("✅ El año 1996 se reconoce correctamente como válido")
    else:
        print("\n❌ La corrección necesita revisión")
        sys.exit(1)