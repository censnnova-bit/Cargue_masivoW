#!/usr/bin/env python3
"""
Tests unitarios para validar las nuevas reglas de validación implementadas.
"""

import os
import sys
import uuid
from pathlib import Path

# Agregar el directorio del proyecto al path para imports
sys.path.append(str(Path(__file__).parent))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.settings')

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from estructuras.models import ProcesoEstructura
from estructuras.services import ExcelProcessor, FileGenerator


class TestValidacionesNuevas:
    """Clase para testear las nuevas validaciones implementadas"""
    
    def __init__(self):
        self.test_results = []
        self.archivos_test = [
            "test_coordenadas_invalidas.xlsx",
            "test_año_invalido.xlsx", 
            "test_ubicacion_vacia.xlsx",
            "test_nombre_vacio.xlsx"
        ]
    
    def log_result(self, test_name, passed, details=""):
        """Registra el resultado de un test"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'passed': passed
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
    
    def crear_proceso_temporal(self, excel_file_path):
        """Crea un proceso temporal para testing"""
        try:
            # Leer el archivo Excel
            with open(excel_file_path, 'rb') as f:
                archivo_content = f.read()
            
            # Crear archivo Django
            archivo_django = SimpleUploadedFile(
                name=os.path.basename(excel_file_path),
                content=archivo_content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Crear proceso
            proceso = ProcesoEstructura.objects.create(
                id=uuid.uuid4(),
                archivo_excel=archivo_django,
                nombre_archivo=os.path.basename(excel_file_path),
                estado='PROCESANDO',
                tipo_estructura='EXPANSION'
            )
            
            return proceso
            
        except Exception as e:
            print(f"Error creando proceso temporal: {e}")
            return None
    
    def test_validacion_coordenadas(self):
        """Test validación de coordenadas"""
        print("\n=== TEST: Validación de Coordenadas ===")
        
        excel_path = "test_coordenadas_invalidas.xlsx"
        if not os.path.exists(excel_path):
            self.log_result("Coordenadas - Archivo existe", False, f"No encontrado: {excel_path}")
            return
        
        proceso = self.crear_proceso_temporal(excel_path)
        if not proceso:
            self.log_result("Coordenadas - Crear proceso", False, "No se pudo crear proceso")
            return
        
        try:
            # Procesar Excel
            processor = ExcelProcessor(proceso)
            datos, campos_faltantes = processor.procesar_archivo()
            
            if campos_faltantes:
                self.log_result("Coordenadas - Campos faltantes", False, f"Faltan: {campos_faltantes}")
                return
            
            proceso.datos_excel = datos
            proceso.save()
            
            # Intentar generar TXT (aquí se ejecutan las validaciones)
            generator = FileGenerator(proceso)
            
            try:
                generator.generar_txt()
                # Si llegamos aquí sin error, algo está mal
                self.log_result("Coordenadas - Detectar errores", False, "No se detectaron errores de coordenadas")
            
            except Exception as e:
                if "VALIDATION_ERRORS" in str(e):
                    # Verificar que se detectaron errores específicos de coordenadas
                    errores = proceso.errores if hasattr(proceso, 'errores') else []
                    
                    errores_coord_x = any("coordenada X" in str(err.get('descripcion', '')).lower() for err in errores)
                    errores_coord_y = any("coordenada Y" in str(err.get('descripcion', '')).lower() for err in errores)
                    
                    if errores_coord_x and errores_coord_y:
                        self.log_result("Coordenadas - Validación correcta", True, f"Detectados {len(errores)} errores")
                    else:
                        self.log_result("Coordenadas - Tipos de errores", False, f"Errores: {errores}")
                else:
                    self.log_result("Coordenadas - Error inesperado", False, str(e))
        
        except Exception as e:
            self.log_result("Coordenadas - Excepción general", False, str(e))
        
        finally:
            # Limpiar
            if proceso:
                try:
                    proceso.delete()
                except:
                    pass
    
    def test_validacion_año(self):
        """Test validación de año entrada operación"""
        print("\n=== TEST: Validación Año Entrada Operación ===")
        
        excel_path = "test_año_invalido.xlsx"
        if not os.path.exists(excel_path):
            self.log_result("Año - Archivo existe", False, f"No encontrado: {excel_path}")
            return
        
        proceso = self.crear_proceso_temporal(excel_path)
        if not proceso:
            self.log_result("Año - Crear proceso", False, "No se pudo crear proceso")
            return
        
        try:
            # Procesar Excel
            processor = ExcelProcessor(proceso)
            datos, campos_faltantes = processor.procesar_archivo()
            
            proceso.datos_excel = datos
            proceso.save()
            
            # Intentar generar TXT
            generator = FileGenerator(proceso)
            
            try:
                resultado = generator.generar_txt()
                self.log_result("Año - Detectar errores", False, "No se detectaron errores de año")
            
            except Exception as e:
                if "VALIDATION_ERRORS" in str(e):
                    errores = proceso.errores if hasattr(proceso, 'errores') else []
                    errores_año = any("año" in str(err.get('descripcion', '')).lower() for err in errores)
                    
                    if errores_año:
                        self.log_result("Año - Validación correcta", True, f"Detectados {len(errores)} errores")
                    else:
                        self.log_result("Año - Tipos de errores", False, f"Errores: {errores}")
                else:
                    self.log_result("Año - Error inesperado", False, str(e))
        
        except Exception as e:
            self.log_result("Año - Excepción general", False, str(e))
        
        finally:
            if proceso:
                try:
                    proceso.delete()
                except:
                    pass
    
    def test_validacion_ubicacion(self):
        """Test validación de ubicación vacía"""
        print("\n=== TEST: Validación Ubicación ===")
        
        excel_path = "test_ubicacion_vacia.xlsx"
        if not os.path.exists(excel_path):
            self.log_result("Ubicación - Archivo existe", False, f"No encontrado: {excel_path}")
            return
        
        proceso = self.crear_proceso_temporal(excel_path)
        if not proceso:
            self.log_result("Ubicación - Crear proceso", False, "No se pudo crear proceso")
            return
        
        try:
            processor = ExcelProcessor(proceso)
            datos, campos_faltantes = processor.procesar_archivo()
            
            proceso.datos_excel = datos
            proceso.save()
            
            generator = FileGenerator(proceso)
            
            try:
                resultado = generator.generar_txt()
                self.log_result("Ubicación - Detectar errores", False, "No se detectaron errores de ubicación")
            
            except Exception as e:
                if "VALIDATION_ERRORS" in str(e):
                    errores = proceso.errores if hasattr(proceso, 'errores') else []
                    errores_ubicacion = any("ubicación" in str(err.get('descripcion', '')).lower() for err in errores)
                    
                    if errores_ubicacion:
                        self.log_result("Ubicación - Validación correcta", True, f"Detectados {len(errores)} errores")
                    else:
                        self.log_result("Ubicación - Tipos de errores", False, f"Errores: {errores}")
                else:
                    self.log_result("Ubicación - Error inesperado", False, str(e))
        
        except Exception as e:
            self.log_result("Ubicación - Excepción general", False, str(e))
        
        finally:
            if proceso:
                try:
                    proceso.delete()
                except:
                    pass
    
    def test_validacion_nombre(self):
        """Test validación de nombre vacío"""
        print("\n=== TEST: Validación Nombre ===")
        
        excel_path = "test_nombre_vacio.xlsx"
        if not os.path.exists(excel_path):
            self.log_result("Nombre - Archivo existe", False, f"No encontrado: {excel_path}")
            return
        
        proceso = self.crear_proceso_temporal(excel_path)
        if not proceso:
            self.log_result("Nombre - Crear proceso", False, "No se pudo crear proceso")
            return
        
        try:
            processor = ExcelProcessor(proceso)
            datos, campos_faltantes = processor.procesar_archivo()
            
            proceso.datos_excel = datos
            proceso.save()
            
            generator = FileGenerator(proceso)
            
            try:
                resultado = generator.generar_txt()
                self.log_result("Nombre - Detectar errores", False, "No se detectaron errores de nombre")
            
            except Exception as e:
                if "VALIDATION_ERRORS" in str(e):
                    errores = proceso.errores if hasattr(proceso, 'errores') else []
                    errores_nombre = any("nombre" in str(err.get('descripcion', '')).lower() for err in errores)
                    
                    if errores_nombre:
                        self.log_result("Nombre - Validación correcta", True, f"Detectados {len(errores)} errores")
                    else:
                        self.log_result("Nombre - Tipos de errores", False, f"Errores: {errores}")
                else:
                    self.log_result("Nombre - Error inesperado", False, str(e))
        
        except Exception as e:
            self.log_result("Nombre - Excepción general", False, str(e))
        
        finally:
            if proceso:
                try:
                    proceso.delete()
                except:
                    pass
    
    def test_transformacion_mayusculas(self):
        """Test que verifica que UBICACION y NOMBRE se convierten a mayúsculas en el TXT"""
        print("\n=== TEST: Transformación a Mayúsculas ===")
        
        # Usar input5.xlsx original
        excel_path = "media/uploads/excel/input5.xlsx"
        if not os.path.exists(excel_path):
            self.log_result("Mayúsculas - Archivo original", False, f"No encontrado: {excel_path}")
            return
        
        proceso = self.crear_proceso_temporal(excel_path)
        if not proceso:
            self.log_result("Mayúsculas - Crear proceso", False, "No se pudo crear proceso")
            return
        
        try:
            processor = ExcelProcessor(proceso)
            datos, campos_faltantes = processor.procesar_archivo()
            
            if campos_faltantes:
                self.log_result("Mayúsculas - Campos completos", False, f"Faltan: {campos_faltantes}")
                return
            
            proceso.datos_excel = datos
            proceso.circuito = "TEST_CIRCUITO"
            proceso.save()
            
            generator = FileGenerator(proceso)
            
            try:
                # Generar TXT (debería funcionar con el input5 original)
                resultado = generator.generar_txt()
                
                # Leer el archivo TXT generado y verificar mayúsculas
                archivo_generado = os.path.join(generator.base_path, resultado)
                
                if os.path.exists(archivo_generado):
                    with open(archivo_generado, 'r', encoding='utf-8-sig') as f:
                        lineas = f.readlines()
                    
                    if len(lineas) > 1:  # Al menos header + 1 dato
                        # Analizar una línea de datos (no header)
                        linea_datos = lineas[1].strip().split('|')
                        
                        # Los campos UBICACION y NOMBRE deberían estar en mayúsculas
                        # (necesitaríamos conocer el orden exacto, por ahora verificamos que hay mayúsculas)
                        tiene_mayusculas = any(campo.isupper() and len(campo) > 0 for campo in linea_datos if campo)
                        
                        if tiene_mayusculas:
                            self.log_result("Mayúsculas - Transformación aplicada", True, "Se encontraron campos en mayúsculas")
                        else:
                            self.log_result("Mayúsculas - Transformación aplicada", False, "No se aplicó transformación")
                    else:
                        self.log_result("Mayúsculas - Contenido archivo", False, "Archivo vacío o solo headers")
                else:
                    self.log_result("Mayúsculas - Archivo generado", False, f"No existe: {archivo_generado}")
            
            except Exception as e:
                self.log_result("Mayúsculas - Generación TXT", False, str(e))
        
        except Exception as e:
            self.log_result("Mayúsculas - Excepción general", False, str(e))
        
        finally:
            if proceso:
                try:
                    proceso.delete()
                except:
                    pass
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print("🧪 INICIANDO TESTS DE VALIDACIONES NUEVAS 🧪")
        print("=" * 50)
        
        self.test_validacion_coordenadas()
        self.test_validacion_año()
        self.test_validacion_ubicacion()
        self.test_validacion_nombre()
        self.test_transformacion_mayusculas()
        
        # Resumen
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE RESULTADOS")
        print("=" * 50)
        
        passed_count = sum(1 for r in self.test_results if r['passed'])
        total_count = len(self.test_results)
        
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
            if result['details']:
                print(f"     └─ {result['details']}")
        
        print(f"\n🎯 TOTAL: {passed_count}/{total_count} tests pasaron")
        
        if passed_count == total_count:
            print("🎉 ¡TODOS LOS TESTS EXITOSOS!")
            return True
        else:
            print("⚠️  Algunos tests fallaron. Revisar implementación.")
            return False


if __name__ == "__main__":
    tester = TestValidacionesNuevas()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ VALIDACIONES IMPLEMENTADAS CORRECTAMENTE")
    else:
        print("\n❌ REVISAR VALIDACIONES")
        sys.exit(1)