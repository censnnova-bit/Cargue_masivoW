"""
Módulo: generadores/txt_norma.py
Genera archivos TXT de normas con datos desde Excel y BD Oracle.
"""
import os
import re
from typing import List, Dict
from django.conf import settings
import pandas as pd

from estructuras.generadores.base import (
    generar_nombre_archivo_con_indice,
    limpiar_valor_para_txt
)
from estructuras.repositories import OracleRepository, OracleConnectionHelper


class TXTNormaGenerator:
    """
    Generador de archivos TXT de normas.
    
    Flujo:
    1. Leer hoja de Normas del Excel (preferido) o mapear desde datos_norma
    2. Detectar bajas por código operativo Z##### en hoja de Estructuras
    3. Para BAJAS: Merge datos BD con Excel (BD tiene prioridad)
    4. Para NO-BAJAS: Validar contra BD y reemplazar solo si difieren
    5. Escribir TXT: NORMA|GRUPO|CIRCUITO|CODIGO_TRAFO|MACRONORMA|CANTIDAD|TIPO_ADECUACION
    """
    
    def __init__(self, proceso, tipo_estructura='EXPANSION'):
        """
        Inicializa el generador.
        
        Args:
            proceso: Instancia del modelo ProcesoEstructura
            tipo_estructura: Tipo de estructura
        """
        self.proceso = proceso
        self.tipo_estructura = tipo_estructura
        self.base_path = os.path.join(settings.MEDIA_ROOT, 'generated')
        
        # Crear directorio si no existe
        os.makedirs(self.base_path, exist_ok=True)
    
    def generar_norma_txt(self) -> str:
        """
        Genera archivo TXT de normas.
        
        Returns:
            Nombre del archivo generado
        """
        try:
            filename = generar_nombre_archivo_con_indice(self.proceso, 'norma_nuevo', 'txt')
            filepath = os.path.join(self.base_path, filename)
            
            # 1. Leer datos de normas desde Excel
            registros_norma = self._leer_datos_norma()
            
            if not registros_norma:
                raise Exception("No hay datos para generar archivo de norma")
            
            print(f"DEBUG: {len(registros_norma)} registros de norma leídos")
            
            # 2. Detectar bajas (ENLACE -> código operativo Z#####)
            enlace_a_codigo_op = self._detectar_bajas()
            
            print(f"DEBUG: {len(enlace_a_codigo_op)} bajas detectadas")
            
            # 3. Escribir archivo con merge BD para bajas
            self._escribir_txt_norma(filepath, registros_norma, enlace_a_codigo_op)
            
            print(f"✅ TXT Norma generado: {filename} con {len(registros_norma)} registros")
            return filename
        
        except Exception as e:
            raise Exception(f"Error generando archivo TXT de norma: {str(e)}")
    
    def _leer_datos_norma(self) -> List[Dict]:
        """
        Lee datos de normas desde hoja Excel dedicada o desde datos procesados.
        
        Prioridad:
        1. Hoja "Norma de expansion" o "Normas" del Excel
        2. proceso.datos_norma
        3. Mapear desde proceso.datos_excel
        
        Returns:
            Lista de registros de norma
        """
        # Intentar leer desde hoja de Normas del Excel
        try:
            archivo_path = self.proceso.archivo_excel.path
            df_dict = pd.read_excel(archivo_path, sheet_name=None)
            
            # Buscar hoja de normas
            nombres_hoja = [
                h for h in df_dict.keys()
                if str(h).strip().lower() in ('norma de expansion', 'normas', 'norma', 
                                              'norma de reposicion', 'norma de reposición')
            ]
            
            if nombres_hoja:
                nombre_hoja = nombres_hoja[0]
                print(f"📄 Leyendo hoja de normas: '{nombre_hoja}'")
                
                # Detectar header (fila 0, 1 o 2)
                df_norma = None
                for header_row in [0, 1, 2]:
                    try:
                        temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=header_row)
                        valid_headers = [c for c in temp_df.columns 
                                       if not str(c).startswith('Unnamed:') and str(c).strip().lower() != 'nan']
                        if len(valid_headers) >= 3:
                            df_norma = temp_df
                            break
                    except Exception:
                        continue
                
                if df_norma is None:
                    df_norma = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=0)
                
                # Convertir a registros
                registros = []
                for _, row in df_norma.iterrows():
                    def obtener(*keys):
                        for k in keys:
                            if k in df_norma.columns and pd.notna(row.get(k)) and str(row.get(k)).strip():
                                return str(row.get(k)).strip()
                        return ''
                    
                    reg = {
                        'ENLACE': obtener('Identificador', 'ENLACE', 'Pm', 'PM', 'Identificador PM'),
                        'NORMA': obtener('Norma', 'NORMA'),
                        'GRUPO': obtener('GRUPO', 'Grupo'),
                        'CIRCUITO': obtener('CIRCUITO', 'Circuito') or getattr(self.proceso, 'circuito', '') or '',
                        'CODIGO_TRAFO': obtener('Codigo. Transformador (1T,2T,3T,4T,5T)', 'CODIGO_TRAFO', 'Codigo Trafo'),
                        'MACRONORMA': obtener('MACRONORMA', 'Macronorma'),
                        'CANTIDAD': obtener('Altura', 'CANTIDAD'),
                        'TIPO_ADECUACION': obtener('Disposicion', 'TIPO_ADECUACION'),
                    }
                    
                    # Solo agregar si tiene al menos NORMA o ENLACE
                    if reg['NORMA'] or reg['ENLACE']:
                        registros.append(reg)
                
                if registros:
                    return registros
        
        except Exception as e:
            print(f"DEBUG: Error leyendo hoja de normas: {e}")
        
        # Fallback: usar datos procesados
        if hasattr(self.proceso, 'datos_norma') and self.proceso.datos_norma:
            return self._preparar_datos_norma(self.proceso.datos_norma)
        
        # Último fallback: mapear desde datos_excel
        if self.proceso.datos_excel:
            from estructuras.transformers.data_transformer import DataMapper
            mapper = DataMapper(self.tipo_estructura)
            circuito = getattr(self.proceso, 'circuito', '') or ''
            datos_mapeados = mapper.mapear_a_norma(self.proceso.datos_excel, circuito)
            return self._preparar_datos_norma(datos_mapeados)
        
        return []
    
    def _detectar_bajas(self) -> Dict[str, str]:
        """
        Detecta bajas buscando códigos operativos Z##### en la hoja de Estructuras.
        
        Returns:
            Dict mapeando ENLACE -> código_operativo
        """
        enlace_a_codigo = {}
        
        try:
            archivo_path = self.proceso.archivo_excel.path
            df_dict = pd.read_excel(archivo_path, sheet_name=None)
            
            # Buscar hoja de estructuras
            nombre_hoja = None
            if 'Estructuras_N1-N2-N3' in df_dict:
                nombre_hoja = 'Estructuras_N1-N2-N3'
            else:
                for hoja in df_dict.keys():
                    if 'estructura' in str(hoja).lower():
                        nombre_hoja = hoja
                        break
            
            if not nombre_hoja:
                print("⚠️ No se encontró hoja de estructuras para detectar bajas")
                return enlace_a_codigo
            
            print(f"📄 Detectando bajas desde hoja: '{nombre_hoja}'")
            
            # Leer hoja sin procesar headers
            df_test = pd.read_excel(archivo_path, sheet_name=nombre_hoja, nrows=2)
            tiene_encabezados = not all('Unnamed:' in str(col) for col in df_test.columns)
            
            if not tiene_encabezados:
                df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=None)
            else:
                df = pd.read_excel(archivo_path, sheet_name=nombre_hoja)
            
            # Buscar códigos operativos y enlaces
            for _, row in df.iterrows():
                enlace = None
                codigo_op = None
                
                # Buscar en todas las celdas
                for val in row:
                    if pd.isna(val):
                        continue
                    
                    val_str = str(val).strip().upper()
                    
                    # Buscar código operativo Z##### (min 5 dígitos)
                    if not codigo_op:
                        match = re.search(r"Z\s*-?\s*(\d{5,})", val_str)
                        if match:
                            codigo_op = f"Z{match.group(1)}"
                    
                    # Buscar ENLACE (formato PXX, PXXX, etc.)
                    if not enlace:
                        if re.match(r"^P\d+$", val_str):
                            enlace = val_str
                
                # Si encontramos ambos, mapear
                if enlace and codigo_op:
                    enlace_a_codigo[enlace] = codigo_op
                    print(f"   ✓ BAJA detectada: {enlace} -> {codigo_op}")
        
        except Exception as e:
            print(f"⚠️ Error detectando bajas: {e}")
        
        return enlace_a_codigo
    
    def _escribir_txt_norma(self, filepath: str, registros: List[Dict], bajas: Dict[str, str]):
        """
        Escribe archivo TXT de normas con merge BD para bajas.
        
        Args:
            filepath: Ruta del archivo
            registros: Lista de registros de norma
            bajas: Dict mapeando ENLACE -> código_operativo
        """
        
        campos_orden = ['NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO', 'MACRONORMA', 'CANTIDAD', 'TIPO_ADECUACION']
        
        oracle_disponible = OracleConnectionHelper.test_connection()
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            # Escribir encabezados
            f.write('|'.join(campos_orden) + '\n')
            
            # Escribir datos
            for reg in registros:
                reg_out = {c: str(reg.get(c, '') or '').strip() for c in campos_orden}
                
                enlace_upper = reg.get('ENLACE', '').strip().upper()
                codigo_op = bajas.get(enlace_upper)
                
                # Si es BAJA, hacer merge con BD
                if codigo_op and oracle_disponible:
                    try:
                        # Resolver FID desde código operativo
                        fid_real = OracleRepository.obtener_fid_desde_codigo_operativo(codigo_op)
                        
                        if fid_real:
                            # Consultar datos de norma en BD
                            datos_bd = self._consultar_norma_oracle(fid_real)
                            
                            if datos_bd:
                                # Merge: BD tiene prioridad si no vacío
                                for campo in campos_orden:
                                    val_bd = str(datos_bd.get(campo, '') or '').strip()
                                    if val_bd:
                                        reg_out[campo] = val_bd
                                
                                print(f"   ✅ BAJA {enlace_upper}: merge BD aplicado")
                    
                    except Exception as e:
                        print(f"   ⚠️ Error enriqueciendo BAJA {enlace_upper}: {e}")
                
                # Si NO es BAJA, validar contra BD (opcional)
                elif enlace_upper and oracle_disponible:
                    try:
                        # Buscar FID desde ENLACE
                        fid = OracleRepository.obtener_fid_desde_enlace(enlace_upper)
                        
                        if fid:
                            datos_bd = self._consultar_norma_oracle(fid)
                            
                            if datos_bd:
                                # Solo reemplazar si Excel != BD
                                cambios = []
                                for campo in campos_orden:
                                    val_excel = reg_out[campo]
                                    val_bd = str(datos_bd.get(campo, '') or '').strip()
                                    
                                    if val_bd and val_excel != val_bd:
                                        cambios.append(f"{campo}: '{val_excel}' → '{val_bd}'")
                                        reg_out[campo] = val_bd
                                
                                if cambios:
                                    print(f"   🔄 VALIDACIÓN {enlace_upper}: {', '.join(cambios)}")
                    
                    except Exception as e:
                        print(f"   ⚠️ Error validando {enlace_upper}: {e}")
                
                # Valores por defecto
                if not reg_out.get('CANTIDAD'):
                    reg_out['CANTIDAD'] = '1'
                else:
                    # Normalizar cantidad (10.0 -> 10)
                    try:
                        val = reg_out['CANTIDAD']
                        if '.' in val and val.replace('.', '').isdigit():
                            reg_out['CANTIDAD'] = val.split('.')[0]
                    except Exception:
                        pass
                
                # Escribir línea
                valores = [limpiar_valor_para_txt(reg_out.get(c, '')) for c in campos_orden]
                f.write('|'.join(valores) + '\n')
        
        # Validar archivo
        self._validar_archivo_txt(filepath)
    
    def _consultar_norma_oracle(self, fid: str) -> Dict:
        """
        Consulta datos de norma desde Oracle por FID.
        
        Args:
            fid: FID de la estructura
            
        Returns:
            Dict con datos de norma desde BD
        """
        try:
            # Query simplificada para obtener datos de norma
            query = """
                SELECT 
                    n.NORMA,
                    n.GRUPO,
                    n.CIRCUITO,
                    n.CODIGO_TRAFO,
                    n.MACRONORMA,
                    n.CANTIDAD,
                    n.TIPO_ADECUACION
                FROM NORMA n
                WHERE n.G3E_FID = :fid
                AND ROWNUM = 1
            """
            
            with OracleConnectionHelper.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, {'fid': fid})
                    row = cursor.fetchone()
                    
                    if row:
                        columns = [col[0] for col in cursor.description]
                        return dict(zip(columns, row))
            
            return {}
        
        except Exception as e:
            print(f"❌ Error consultando norma en Oracle: {e}")
            return {}
    
    def _preparar_datos_norma(self, datos: List[Dict]) -> List[Dict]:
        """
        Prepara datos de norma aplicando transformaciones.
        
        Args:
            datos: Datos de norma raw
            
        Returns:
            Datos preparados
        """
        preparados = []
        
        for registro in datos:
            reg = registro.copy()
            
            # GRUPO para norma: "NODO ELECTRICO" si es expansión
            tipo_proyecto = reg.get('TIPO_PROYECTO', '')
            if 'EXPANSION' in str(tipo_proyecto).upper():
                reg['GRUPO'] = 'NODO ELECTRICO'
            
            # Corregir TIPO_ADECUACION (quitar tildes)
            tipo_adec = reg.get('TIPO_ADECUACION', '')
            if tipo_adec:
                conversiones = {
                    'RETENCIÓN': 'RETENCION',
                    'SUSPENSIÓN': 'SUSPENSION',
                    'retención': 'RETENCION',
                    'suspensión': 'SUSPENSION',
                }
                reg['TIPO_ADECUACION'] = conversiones.get(tipo_adec, tipo_adec.upper())
            
            preparados.append(reg)
        
        return preparados
    
    def _validar_archivo_txt(self, filepath: str):
        """
        Valida que el archivo TXT esté correctamente formateado.
        """
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                raise Exception("Archivo sin contenido suficiente")
            
            num_campos = len(lines[0].strip().split('|'))
            
            for i, line in enumerate(lines[1:], start=2):
                if not line.strip():
                    continue
                
                campos = line.strip().split('|')
                if len(campos) != num_campos:
                    print(f"⚠️ Advertencia línea {i}: esperados {num_campos} campos, encontrados {len(campos)}")
            
            print(f"✓ Archivo TXT Norma validado: {num_campos} campos, {len(lines)-1} registros")
        
        except Exception as e:
            print(f"⚠️ Error validando archivo TXT Norma: {e}")
