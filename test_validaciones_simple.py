#!/usr/bin/env python3
"""
Test simplificado para validar las nuevas reglas de validación
"""

import os
import sys
import uuid
from pathlib import Path

# Configuración Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')
sys.path.append(str(Path(__file__).parent))

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from estructuras.models import ProcesoEstructura
from estructuras.services import ExcelProcessor, FileGenerator


def test_archivo_excel(archivo_path, esperado_error_tipo):
    """Test individual para un archivo Excel"""
    print(f"\n🧪 Testeando: {archivo_path}")
    print(f"   Esperando errores de: {esperado_error_tipo}")
    
    if not os.path.exists(archivo_path):
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return False
    
    try:
        # Crear proceso temporal
        with open(archivo_path, 'rb') as f:
            content = f.read()
        
        archivo_django = SimpleUploadedFile(
            name=os.path.basename(archivo_path),
            content=content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        proceso = ProcesoEstructura.objects.create(
            id=uuid.uuid4(),
            archivo_excel=archivo_django,
            estado='PROCESANDO'
        )
        
        # Procesar Excel
        processor = ExcelProcessor(proceso)
        datos, campos_faltantes = processor.procesar_archivo()
        
        if campos_faltantes:
            print(f"⚠️  Campos faltantes: {campos_faltantes}")
            return False
        
        proceso.datos_excel = datos
        proceso.save()
        
        # Intentar generar TXT
        generator = FileGenerator(proceso)
        
        try:
            generator.generar_txt()
            print("❌ No se detectaron errores (debería haber errores)")
            return False
            
        except Exception as e:
            if "VALIDATION_ERRORS" in str(e):
                # Verificar errores en el proceso
                errores = getattr(proceso, 'errores', [])
                
                if errores:
                    print(f"✅ Se detectaron {len(errores)} errores de validación:")
                    for i, error in enumerate(errores[:3]):  # Mostrar máximo 3
                        desc = error.get('descripcion', 'Sin descripción')
                        print(f"   {i+1}. {desc}")
                    return True
                else:
                    print("❌ Excepción de validación pero sin errores registrados")
                    return False
            else:
                print(f"❌ Error inesperado: {str(e)[:100]}...")
                return False
    
    except Exception as e:
        print(f"❌ Error general: {str(e)[:100]}...")
        return False
    
    finally:
        # Limpiar proceso
        try:
            if 'proceso' in locals():
                proceso.delete()
        except Exception:
            pass


def test_archivo_valido():
    """Test con archivo válido (input5.xlsx original)"""
    print(f"\n🧪 Testeando archivo VÁLIDO")
    
    archivo_path = "media/uploads/excel/input5.xlsx"
    if not os.path.exists(archivo_path):
        print(f"❌ Archivo original no encontrado: {archivo_path}")
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
            circuito='TEST_CIRCUITO'
        )
        
        processor = ExcelProcessor(proceso)
        datos, campos_faltantes = processor.procesar_archivo()
        
        if campos_faltantes:
            print(f"⚠️  Campos faltantes: {campos_faltantes}")
            return False
        
        proceso.datos_excel = datos
        proceso.save()
        
        generator = FileGenerator(proceso)
        
        try:
            resultado = generator.generar_txt()
            print(f"✅ Archivo TXT generado exitosamente: {resultado}")
            
            # Verificar que se aplicó transformación de mayúsculas
            archivo_txt = os.path.join(generator.base_path, resultado)
            if os.path.exists(archivo_txt):
                with open(archivo_txt, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                
                # Verificar que hay contenido en mayúsculas
                lineas = content.split('\n')
                if len(lineas) > 1:
                    tiene_mayusculas = any(campo.isupper() and len(campo) > 1 
                                         for linea in lineas[1:3] 
                                         for campo in linea.split('|') 
                                         if campo.strip())
                    
                    if tiene_mayusculas:
                        print("✅ Transformación a mayúsculas aplicada correctamente")
                    else:
                        print("⚠️  No se detectó transformación a mayúsculas")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al generar TXT: {str(e)[:100]}...")
            return False
    
    except Exception as e:
        print(f"❌ Error general: {str(e)[:100]}...")
        return False
    
    finally:
        try:
            if 'proceso' in locals():
                proceso.delete()
        except Exception:
            pass


def main():
    """Función principal del test"""
    print("🚀 INICIANDO TESTS DE VALIDACIONES")
    print("=" * 50)
    
    tests_pasados = 0
    total_tests = 0
    
    # Tests de archivos con errores
    archivos_test = [
        ("test_coordenadas_invalidas.xlsx", "coordenadas"),
        ("test_año_invalido.xlsx", "año"),
        ("test_ubicacion_vacia.xlsx", "ubicación"),
        ("test_nombre_vacio.xlsx", "nombre")
    ]
    
    for archivo, tipo_error in archivos_test:
        total_tests += 1
        if test_archivo_excel(archivo, tipo_error):
            tests_pasados += 1
    
    # Test archivo válido
    total_tests += 1
    if test_archivo_valido():
        tests_pasados += 1
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    print(f"Tests pasados: {tests_pasados}/{total_tests}")
    
    if tests_pasados == total_tests:
        print("🎉 ¡TODOS LOS TESTS EXITOSOS!")
        print("✅ Las validaciones están funcionando correctamente")
        return True
    else:
        print("⚠️  Algunos tests fallaron")
        print("❌ Revisar la implementación de las validaciones")
        return False


if __name__ == "__main__":
    exito = main()
    if not exito:
        sys.exit(1)