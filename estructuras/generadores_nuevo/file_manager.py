"""
FileManager - Coordinador principal de generación de archivos.
Integra validaciones y generadores para crear archivos TXT y XML.
"""

import os
from typing import Dict, List, Any, Tuple
from .generador_base import GeneradorBase
from ..validaciones import ValidadorMaestro


class FileManager(GeneradorBase):
    """
    Manejador principal de archivos que coordina validaciones y generación.
    Reemplaza la lógica dispersa en FileGenerator con un enfoque modular.
    """
    
    def __init__(self, proceso):
        super().__init__(proceso)
        self.validador = ValidadorMaestro()
        self.errores_acumulados = []
    
    def _add_err(self, fila: int, descripcion: str, hoja: str = 'Estructuras_N1-N2-N3') -> None:
        """Función auxiliar para mantener compatibilidad con código existente"""
        error = {
            'archivo': 'Excel',
            'hoja': hoja,
            'fila': fila,
            'descripcion': descripcion
        }
        self.errores_acumulados.append(error)
    
    def _normalize_col_name(self, nombre: str) -> str:
        """Normaliza nombres de columnas para comparaciones"""
        if not isinstance(nombre, str):
            return ''
        return nombre.lower().replace(' ', '_').replace('-', '_').replace('\n', '_')
    
    def _extraer_codigo_operativo(self, registro: Dict, registro_excel: Dict) -> str:
        """
        Extrae código operativo de un registro (patrón Z+dígitos)
        Busca en todos los campos del registro
        """
        import re
        
        # Patrón para códigos operativos: Z seguido de dígitos
        patron = re.compile(r'^Z\d+$', re.IGNORECASE)
        
        # Buscar en registro procesado
        for valor in registro.values():
            if valor and isinstance(valor, (str, int)):
                valor_str = str(valor).strip().upper()
                if patron.match(valor_str):
                    return valor_str
        
        # Buscar en registro Excel crudo
        for valor in registro_excel.values():
            if valor and isinstance(valor, (str, int)):
                valor_str = str(valor).strip().upper()
                if patron.match(valor_str):
                    return valor_str
        
        return ''
    
    def _indices_con_fid_rep_exactos(self) -> Tuple[set, List[Dict]]:
        """
        Obtiene índices de filas del Excel que tienen valor no vacío en la
        columna EXACTA 'Código FID_rep'. Ignora otras columnas parecidas.
        """
        from ..services import ExcelProcessor
        
        try:
            processor = ExcelProcessor(self.proceso)
            raw_datos, _ = processor.procesar_archivo()
        except Exception:
            raw_datos = getattr(self.proceso, 'datos_excel', []) or []

        indices = set()
        for i, reg in enumerate(raw_datos):
            if not isinstance(reg, dict):
                continue
            
            # Variantes textuales del mismo encabezado
            variantes = (
                'Código FID_rep', 'Codigo FID_rep', 'CODIGO_FID_REP', 'codigo_fid_rep'
            )
            
            for k in variantes:
                if k in reg:
                    v = reg.get(k)
                    s = '' if v is None else str(v).strip()
                    if s and s.lower() not in ('nan', 'none'):
                        indices.add(i)
                    break
        
        return indices, raw_datos
    
    def _get_datos_completos(self) -> List[Dict[str, Any]]:
        """Combina datos del Excel con datos procesados (clasificación y propietario)"""
        if not getattr(self.proceso, 'datos_excel', None):
            raise Exception("No hay datos originales del Excel")
        
        datos_salida = []
        
        # Si tenemos datos_norma (datos procesados), usarlos como base
        if getattr(self.proceso, 'datos_norma', None):
            print(f"Combinando datos_excel ({len(self.proceso.datos_excel)}) con datos_norma ({len(self.proceso.datos_norma)})")
            
            for i, registro_excel in enumerate(self.proceso.datos_excel):
                # Empezar con los datos originales del Excel
                registro_completo = registro_excel.copy()
                
                # Si hay datos procesados correspondientes, usar campos específicos de allí
                if i < len(self.proceso.datos_norma):
                    registro_norma = self.proceso.datos_norma[i]
                    
                    # Campos que deben venir de datos_norma (procesados)
                    campos_procesados = [
                        'TIPO', 'CLASE', 'USO', 'PROPIETARIO', 
                        'PORCENTAJE_PROPIEDAD', 'FECHA_OPERACION',
                        'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'ESTADO_SALUD'
                    ]
                    
                    for campo in campos_procesados:
                        if campo in registro_norma:
                            registro_completo[campo] = registro_norma[campo]
                    
                    # TIPO_PROYECTO: Priorizar datos_excel
                    if 'TIPO_PROYECTO' in registro_excel and registro_excel['TIPO_PROYECTO']:
                        registro_completo['TIPO_PROYECTO'] = registro_excel['TIPO_PROYECTO']
                    elif 'TIPO_PROYECTO' in registro_norma and registro_norma['TIPO_PROYECTO']:
                        registro_completo['TIPO_PROYECTO'] = registro_norma['TIPO_PROYECTO']
                
                # Agregar circuito del proceso
                if getattr(self.proceso, 'circuito', None):
                    registro_completo['CIRCUITO'] = self.proceso.circuito
                
                datos_salida.append(registro_completo)
        else:
            # Fallback: solo datos del Excel con valores por defecto
            print("No hay datos_norma, usando solo datos_excel con valores por defecto")
            datos_salida = self.proceso.datos_excel.copy()
            
            for registro in datos_salida:
                if getattr(self.proceso, 'circuito', None):
                    registro['CIRCUITO'] = self.proceso.circuito
                
                # Valores por defecto básicos
                defaults = {
                    'TIPO': 'SECUNDARIO',
                    'CLASE': 'POSTE',
                    'USO': 'DISTRIBUCION ENERGIA',
                    'PORCENTAJE_PROPIEDAD': '100'
                }
                
                # Aplicar propietario definido si aplica
                if getattr(self.proceso, 'propietario_definido', None):
                    registro['PROPIETARIO'] = self.proceso.propietario_definido
                
                # Aplicar valores por defecto solo si el campo no existe o está vacío
                for campo, valor_default in defaults.items():
                    if campo not in registro or not registro[campo]:
                        registro[campo] = valor_default
        
        return datos_salida
    
    def _preparar_datos_finales(self, datos_completos: List[Dict]) -> List[Dict]:
        """
        Prepara los datos finales aplicando transformaciones y normalizaciones
        """

        
        datos_finales = []
        
        for registro in datos_completos:
            # Aplicar limpieza y normalización
            registro_limpio = {}
            
            for campo, valor in registro.items():
                # Limpiar valor para archivos de texto
                valor_limpio = self.limpiar_valor_para_archivo(valor)
                registro_limpio[campo] = valor_limpio
            
            # Aplicar valores por defecto para campos críticos
            campos_criticos = {
                'COORDENADA_X': '0.000000',
                'COORDENADA_Y': '0.000000',
                'GRUPO': 'ESTRUCTURAS EYT',
                'TIPO': 'SECUNDARIO',
                'CLASE': 'POSTE',
                'USO': 'DISTRIBUCION ENERGIA',
                'ESTADO': 'ACTIVO',
                'PROPIETARIO': 'SIN_PROPIETARIO',
                'PORCENTAJE_PROPIEDAD': '100',
                'TIPO_PROYECTO': 'EXPANSION',
                'FECHA_INSTALACION': '01/01/1900',
                'FECHA_OPERACION': '01/01/1900',
                'ID_MERCADO': '161',
                'SALINIDAD': 'NO',
                'EMPRESA': 'CENS'
            }
            
            for campo, valor_defecto in campos_criticos.items():
                if not registro_limpio.get(campo) or str(registro_limpio.get(campo, '')).strip() == '':
                    registro_limpio[campo] = valor_defecto
            
            # Formatear coordenadas
            if 'COORDENADA_X' in registro_limpio:
                registro_limpio['COORDENADA_X'] = self.formatear_coordenada(registro_limpio['COORDENADA_X'])
            if 'COORDENADA_Y' in registro_limpio:
                registro_limpio['COORDENADA_Y'] = self.formatear_coordenada(registro_limpio['COORDENADA_Y'])
            
            # Formatear fechas
            if 'FECHA_INSTALACION' in registro_limpio:
                registro_limpio['FECHA_INSTALACION'] = self.formatear_fecha(registro_limpio['FECHA_INSTALACION'])
            if 'FECHA_OPERACION' in registro_limpio:
                registro_limpio['FECHA_OPERACION'] = self.formatear_fecha(registro_limpio['FECHA_OPERACION'])
            
            datos_finales.append(registro_limpio)
        
        return datos_finales
    
    def ejecutar_validaciones_integradas(self, datos_finales: List[Dict], raw_datos_excel: List[Dict], idx_map: List[int]) -> List[Dict]:
        """
        Ejecuta todas las validaciones integradas sobre los datos procesados
        """
        self.errores_acumulados = []
        
        # Obtener índices con FID_rep para contexto
        indices_con_fid_rep, _ = self._indices_con_fid_rep_exactos()
        
        # Preparar registros para validación (formato esperado por ValidadorMaestro)
        registros_procesados = []
        for i, registro in enumerate(datos_finales):
            idx_excel = idx_map[i] if i < len(idx_map) else i
            registro_excel = raw_datos_excel[idx_excel] if idx_excel < len(raw_datos_excel) else {}
            registros_procesados.append((registro, registro_excel, idx_excel))
        
        # Ejecutar validaciones de datos usando ValidadorMaestro
        errores_datos = self.validador.validar_solo_datos(registros_procesados, indices_con_fid_rep)
        
        # Ejecutar validaciones adicionales específicas del archivo TXT
        errores_adicionales = self._validaciones_txt_especificas(datos_finales, raw_datos_excel, idx_map)
        
        # Combinar todos los errores
        todos_los_errores = errores_datos + errores_adicionales + self.errores_acumulados
        
        return todos_los_errores
    
    def _validaciones_txt_especificas(self, datos_finales: List[Dict], raw_datos_excel: List[Dict], idx_map: List[int]) -> List[Dict]:
        """
        Validaciones específicas para archivos TXT que no están en ValidadorMaestro
        """
        errores_especificos = []
        
        # Validación de ENLACE/Identificador
        vistos = {}
        for i, registro in enumerate(datos_finales):
            idx_excel = idx_map[i] if i < len(idx_map) else i
            fila_excel = idx_excel + 2  # Ajuste para numeración
            
            # Extraer ENLACE del registro
            enlace_raw = ''
            if idx_excel < len(raw_datos_excel):
                raw_row = raw_datos_excel[idx_excel]
                if isinstance(raw_row, dict):
                    # Buscar en campos específicos
                    for literal in ['Identificador', 'ENLACE', 'Enlace']:
                        if literal in raw_row and raw_row.get(literal) not in (None, ''):
                            enlace_raw = str(raw_row.get(literal)).lstrip('\ufeff').strip()
                            break
            
            # Si no se encontró en raw, usar del registro procesado
            if not enlace_raw:
                enlace_raw = str(registro.get('ENLACE', '')).strip()
            
            # Validaciones de ENLACE
            if not enlace_raw:
                self._add_err(fila_excel, f"el Enlace/Identificador de la linea {fila_excel} se encuentra vacio, por favor corrijalo para hacer el cargue masivo")
                continue
            
            if not str(enlace_raw).startswith('P'):
                self._add_err(fila_excel, f"el Enlace/Identificador de la linea {fila_excel} debe empezar por P")
                continue
            
            if enlace_raw in vistos:
                f1 = vistos[enlace_raw]
                f2 = fila_excel
                self._add_err(fila_excel, f"no pueden haber dos enlaces/identificadores iguales: fila {f1} y fila {f2} con '{enlace_raw}'")
                continue
            
            vistos[enlace_raw] = fila_excel
            registro['ENLACE'] = enlace_raw
        
        # Validación de UC (Unidad Constructiva)
        for i, registro in enumerate(datos_finales):
            idx_excel = idx_map[i] if i < len(idx_map) else i
            fila_excel = idx_excel + 2
            
            uc_val = registro.get('UC', '')
            uc_raw = '' if uc_val is None else str(uc_val).lstrip('\ufeff').strip()
            
            if not uc_raw:
                self._add_err(fila_excel, f"la Unidad Constructiva de la linea {fila_excel} se encuentra vacia, por favor corrijala para hacer el cargue masivo")
                continue
            
            if not uc_raw.startswith('N'):
                self._add_err(fila_excel, f"la Unidad Constructiva de la linea {fila_excel} debe empezar por N")
        
        # Convertir errores acumulados al formato esperado
        for error in self.errores_acumulados:
            errores_especificos.append(error)
        
        return errores_especificos
    
    def generar_archivo_txt_coordinado(self, tipo_archivo: str = 'estructuras_nuevo') -> Dict[str, Any]:
        """
        Método principal que coordina la generación de archivos TXT con validaciones integradas
        
        Args:
            tipo_archivo: Tipo de archivo a generar ('estructuras_nuevo' o 'estructuras_baja')
        
        Returns:
            Diccionario con información del archivo generado y estadísticas
        """
        resultado = {
            'exito': False,
            'archivo_generado': None,
            'ruta_archivo': None,
            'total_registros': 0,
            'errores_validacion': [],
            'mensaje': ''
        }
        
        try:
            # 1. Obtener datos completos
            datos_salida = self._get_datos_completos()
            
            if not datos_salida:
                raise Exception("No hay datos transformados para generar archivo TXT")
            
            # 2. Preparar datos finales
            datos_finales = self._preparar_datos_finales(datos_salida)
            
            # 3. Cargar datos crudos del Excel para validaciones
            from ..services import ExcelProcessor
            
            try:
                processor = ExcelProcessor(self.proceso)
                raw_datos_excel, _ = processor.procesar_archivo()
            except Exception as e:
                print(f"⚠️ No se pudieron cargar datos crudos del Excel: {e}")
                raw_datos_excel = []
            
            # 4. Crear mapeo de índices
            idx_map = list(range(len(datos_finales)))
            
            # 5. Ejecutar todas las validaciones
            errores_validacion = self.ejecutar_validaciones_integradas(datos_finales, raw_datos_excel, idx_map)
            
            # 6. Si hay errores, guardar y abortar
            if errores_validacion:
                try:
                    self.proceso.errores = errores_validacion
                    self.proceso.estado = 'ERROR'
                    self.proceso.save()
                except Exception:
                    pass
                
                resultado['errores_validacion'] = errores_validacion
                resultado['mensaje'] = f"Se encontraron {len(errores_validacion)} errores de validación"
                return resultado
            
            # 7. Generar archivo si no hay errores
            filename = self.generar_nombre_archivo_con_indice(tipo_archivo, 'txt')
            filepath = os.path.join(self.base_path, filename)
            
            # 8. Definir encabezados según tipo de archivo
            encabezados = self._get_encabezados_txt(tipo_archivo)
            campos_orden = encabezados  # Mismo orden para mantener consistencia
            
            # 9. Escribir archivo
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                # Escribir encabezados
                f.write('|'.join(encabezados) + '\n')
                
                # Escribir datos
                for registro in datos_finales:
                    linea_datos = []
                    for campo in campos_orden:
                        valor = registro.get(campo, '')
                        linea_datos.append(str(valor) if valor is not None else '')
                    
                    f.write('|'.join(linea_datos) + '\n')
            
            # 10. Configurar resultado exitoso
            resultado.update({
                'exito': True,
                'archivo_generado': filename,
                'ruta_archivo': filepath,
                'total_registros': len(datos_finales),
                'mensaje': f'Archivo {filename} generado exitosamente con {len(datos_finales)} registros'
            })
            
            print(f"✅ {resultado['mensaje']}")
            
            return resultado
            
        except Exception as e:
            error_msg = str(e)
            if error_msg == "VALIDATION_ERRORS":
                resultado['mensaje'] = "Errores de validación detectados"
            else:
                resultado['mensaje'] = f"Error generando archivo TXT: {error_msg}"
            
            print(f"❌ {resultado['mensaje']}")
            return resultado
    
    def _get_encabezados_txt(self, tipo_archivo: str) -> List[str]:
        """
        Retorna los encabezados apropiados según el tipo de archivo TXT
        """
        if tipo_archivo == 'estructuras_baja':
            # Encabezados para archivo de baja
            return [
                'COORDENADA_X', 'COORDENADA_Y',
                'UBICACION', 'ESTADO', 'CODIGO_MATERIAL', 'FECHA_INSTALACION', 
                'FECHA_OPERACION', 'PROYECTO', 'EMPRESA', 'OBSERVACIONES',
                'CLASIFICACION_MERCADO', 'TIPO_PROYECTO', 'ID_MERCADO', 'UC',
                'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION', 'SALINIDAD',
                'ENLACE',  # Para baja es ENLACE en lugar de FID_ANTERIOR
                'GRUPO', 'TIPO', 'CLASE', 'USO', 'TIPO_ADECUACION',
                'PROPIETARIO', 'PORCENTAJE_PROPIEDAD'
            ]
        else:
            # Encabezados para archivo nuevo (default)
            return [
                'COORDENADA_X', 'COORDENADA_Y',
                'UBICACION', 'ESTADO', 'CODIGO_MATERIAL', 'FECHA_INSTALACION', 
                'FECHA_OPERACION', 'PROYECTO', 'EMPRESA', 'OBSERVACIONES',
                'CLASIFICACION_MERCADO', 'TIPO_PROYECTO', 'ID_MERCADO', 'UC',
                'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION', 'SALINIDAD',
                'FID_ANTERIOR',  # Para nuevo es FID_ANTERIOR
                'GRUPO', 'TIPO', 'CLASE', 'USO', 'TIPO_ADECUACION',
                'PROPIETARIO', 'PORCENTAJE_PROPIEDAD'
            ]