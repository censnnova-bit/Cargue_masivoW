import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os
import re
from django.conf import settings
import oracledb
# XML utilities are imported where needed inside functions to keep module
# imports minimal and avoid unused import warnings.
from .constants import (
    ESTRUCTURAS_CAMPOS, MAPEO_EXCEL_A_SALIDA, REGLAS_CLASIFICACION, 
    CATALOGO_MATERIALES, MAPEO_UC_MATERIAL, ESTADOS_SALUD
)
from .models import ProcesoEstructura

# NUEVAS IMPORTACIONES PARA SISTEMA MODULAR
from .validaciones import ValidadorMaestro
from .generadores_nuevo import FileManager

class DataUtils:
    """Utilidades centralizadas para procesamiento de datos"""
    
    # Constantes centralizadas
    VALORES_DEFECTO = {
        'GRUPO': 'ESTRUCTURAS EYT',
        'TIPO': 'PRIMARIO',
        'CLASE': 'POSTE',
        'USO': 'DISTRIBUCION ENERGIA',
        'PORCENTAJE_PROPIEDAD': '100',
        'TIPO_PROYECTO': 'T2',
        'FECHA_DEFAULT': '01/01/2000',
        'ESTADO_DEFAULT': 'OPERACION',
        'ID_MERCADO': '161',
        'SALINIDAD': 'NO'
    }
    
    @staticmethod
    def formatear_fecha(fecha) -> str:
        """
        Formatea una fecha para mostrar solo la fecha sin la hora en formato DD/MM/YYYY
        """
        if not fecha or str(fecha).strip() == '':
            return ''
        
        try:
            fecha_str = str(fecha).strip()
            
            # Si ya está en formato DD/MM/YYYY, retornar tal como está
            import re
            if re.match(r'^\d{2}/\d{2}/\d{4}$', fecha_str):
                return fecha_str
            
            # Si es un objeto datetime de pandas
            if hasattr(fecha, 'strftime'):
                return fecha.strftime('%d/%m/%Y')
            
            # Si es una fecha de Excel (número serial)
            if isinstance(fecha, (int, float)):
                from datetime import datetime, timedelta
                # Fecha base de Excel: 1900-01-01
                fecha_base = datetime(1900, 1, 1)
                fecha_calculada = fecha_base + timedelta(days=fecha - 2)  # -2 por diferencia en Excel
                return fecha_calculada.strftime('%d/%m/%Y')
            
            # Si es string con formato diferente, intentar parsear
            if isinstance(fecha, str):
                # Remover hora si existe
                if ' ' in fecha_str:
                    fecha_str = fecha_str.split(' ')[0]
                
                # Intentar diferentes formatos
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
                for formato in formatos:
                    try:
                        fecha_obj = datetime.strptime(fecha_str, formato)
                        return fecha_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
            
            # Si no se puede convertir, devolver string vacío
            return ''
            
        except Exception:
            return ''
    
    @staticmethod
    def limpiar_valor_para_txt(valor):
        """
        Limpia un valor para que no contenga caracteres problemáticos en el archivo TXT.
        Para valores vacíos/nulos devuelve cadena vacía (respetar Excel, no escribir 'NULL').
        """
        if valor is None:
            return ''
        
        # Convertir a string
        valor_str = str(valor)
        
        # Reemplazar caracteres problemáticos
        valor_str = valor_str.replace('\n', ' ').replace('\r', ' ').replace('|', '-')
        
        # Limpiar espacios al inicio y final
        valor_str = valor_str.strip()
        
        # Si después de limpiar queda vacío o contiene solo 'nan', 'none', etc., devolver vacío
        if not valor_str or valor_str.lower() in ('nan', 'none', 'null'):
            return ''
        
        # Limitar longitud máxima (algunos sistemas tienen límites)
        if len(valor_str) > 255:
            valor_str = valor_str[:252] + '...'
        
        return valor_str
    
    @staticmethod
    def normalizar_codigo_material(valor) -> str:
        """
        Normaliza CODIGO_MATERIAL a cadena de dígitos:
        - Si viene como 200067.0 o '200067.0', lo convierte a '200067'.
        - Acepta int/float/str; devuelve '' si no se puede normalizar a dígitos.
        """
        if valor is None:
            return ''
        try:
            # Si es numérico y entero, devolver entero como string
            if isinstance(valor, (int,)):
                return str(valor)
            if isinstance(valor, float):
                if float(valor).is_integer():
                    return str(int(valor))
                # Si tiene decimales reales, no es válido para código de material
                return str(valor)
            # Tratar como string
            s = str(valor).strip()
            if not s:
                return ''
            # Reemplazar coma decimal por punto si aplica
            s2 = s.replace(',', '.')
            # Patrón entero con .0 opcional
            import re as _re
            if _re.fullmatch(r"\d+", s2):
                return s2
            if _re.fullmatch(r"\d+\.0+", s2):
                return s2.split('.')[0]
            return s
        except Exception:
            return ''
    

class OracleHelper:
    """
    Helper para consultas a Oracle Database.
    
    NOTA: Esta clase ahora delega todas las consultas a OracleRepository.
    Se mantiene por compatibilidad con código existente.
    """
    
    # Importar el repositorio
    from estructuras.repositories import OracleRepository, OracleConnectionHelper
    
    @classmethod
    def get_oracle_config(cls):
        """Obtiene la configuración de Oracle desde Django settings"""
        return cls.OracleConnectionHelper.get_oracle_config()
    
    @classmethod
    def get_connection(cls):
        """
        Crea y retorna una conexión a Oracle.
        Delega a OracleConnectionHelper.
        """
        return cls.OracleConnectionHelper.get_connection()
    
    @classmethod
    def test_connection(cls) -> bool:
        """
        Prueba la conexión a Oracle.
        Delega a OracleConnectionHelper.
        """
        return cls.OracleConnectionHelper.test_connection()
    
    @classmethod
    def obtener_coordenadas_por_fid(cls, fid_codigo: str) -> Tuple[str, str]:
        """
        Consulta Oracle para obtener coordenadas GPS por G3E_FID.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.obtener_coordenadas_por_fid(fid_codigo)

    @classmethod
    def obtener_fid_desde_codigo_operativo(cls, codigo_operativo: str) -> str:
        """
        Obtiene el FID real desde el código operativo.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.obtener_fid_desde_codigo_operativo(codigo_operativo)

    @classmethod
    def obtener_fid_desde_enlace(cls, enlace: str) -> str:
        """
        Obtiene el FID desde el ENLACE.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.obtener_fid_desde_enlace(enlace)

    @classmethod
    def obtener_datos_completos_por_fid(cls, fid_real: str) -> Dict[str, str]:
        """
        Obtiene datos completos desde Oracle usando FID real.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.obtener_datos_completos_por_fid(fid_real)

    @classmethod
    def obtener_datos_txt_nuevo_por_fid(cls, fid_real: str) -> Dict[str, str]:
        """
        Obtiene datos específicos para TXT nuevo desde Oracle.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.obtener_datos_txt_nuevo_por_fid(fid_real)

    @classmethod
    def obtener_datos_txt_baja_por_fid(cls, fid_real: str) -> Dict[str, str]:
        """
        Obtiene datos específicos para TXT baja desde Oracle.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.obtener_datos_txt_baja_por_fid(fid_real)
    
    @classmethod
    def consultar_conductor_por_codigo(cls, codigo_conductor: str) -> Optional[Dict[str, str]]:
        """
        Consulta datos de conductor por código.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.consultar_conductor_por_codigo(codigo_conductor)
    
    @classmethod
    def obtener_coordenadas_nodo_por_fid(cls, fid_nodo: str) -> Tuple[str, str]:
        """
        Obtiene coordenadas de un nodo por FID.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.obtener_coordenadas_nodo_por_fid(fid_nodo)
    
    @classmethod
    def consultar_norma_por_fid(cls, fid: str) -> Dict[str, str]:
        """
        Consulta datos de norma por FID.
        Delega a OracleRepository.
        """
        return cls.OracleRepository.consultar_norma_por_fid(fid)

    @classmethod
    def obtener_datos_norma_por_fid(cls, fid_real: str) -> Dict[str, str]:
        """
        Obtiene campos útiles para el archivo de Norma a partir del FID real.

        Intenta traer:
        - CIRCUITO: desde CCOMUN si existe alguna columna relacionada (CIRCUITO / NOMBRE_CIRCUITO).
        - CODIGO_TRAFO: desde EPOSTE_AT si existe alguna columna relacionada (CODIGO_TRAFO / COD_TRAFO / CODIGO_TRANSFORMADOR).
        - TIPO_ADECUACION: desde EPOSTE_AT (TIPO_ADECUACION) si existe.

        Si no hay conexión o no existen las columnas, retorna {}.
        """
        resultado: Dict[str, str] = {}
        # Verificar si Oracle está habilitado
        if hasattr(settings, 'ORACLE_ENABLED') and not settings.ORACLE_ENABLED:
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para obtener_datos_norma_por_fid({fid_real})")
            return resultado

        if not fid_real:
            return resultado

        fid_limpio = str(fid_real).strip()
        if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
            return resultado

        try:
            oracle_config = cls.get_oracle_config()
            with oracledb.connect(**oracle_config) as connection:
                with connection.cursor() as cursor:
                    # Configurar timeout
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass

                    # 1) Detectar columnas disponibles para CIRCUITO en CCOMUN
                    circuito_col = None
                    try:
                        cursor.execute(
                            """
                            SELECT UPPER(COLUMN_NAME)
                            FROM USER_TAB_COLUMNS
                            WHERE UPPER(TABLE_NAME) = 'CCOMUN'
                            """
                        )
                        cols = {row[0] for row in (cursor.fetchall() or [])}
                        for candidato in ['CIRCUITO', 'NOMBRE_CIRCUITO', 'CIRCUITO_NOMBRE', 'CIRCUITO_ID', 'ID_CIRCUITO']:
                            if candidato in cols:
                                circuito_col = candidato
                                break
                    except Exception as e_cols:
                        print(f"DEBUG Oracle: No fue posible leer columnas de CCOMUN: {e_cols}")

                    if circuito_col:
                        try:
                            cursor.execute(
                                f"SELECT {circuito_col} FROM CCOMUN WHERE G3E_FID = :fid_param",
                                {"fid_param": fid_limpio}
                            )
                            row = cursor.fetchone()
                            circuito_val = str(row[0]).strip() if row and row[0] is not None else ''
                            if circuito_val:
                                resultado['CIRCUITO'] = circuito_val
                        except Exception as e_circ:
                            print(f"DEBUG Oracle: Error consultando CIRCUITO ({circuito_col}) en CCOMUN: {e_circ}")

                    # 2) Detectar columnas disponibles para CODIGO_TRAFO, TIPO_ADECUACION, NORMA, MACRONORMA, CANTIDAD en EPOSTE_AT
                    trafo_col = None
                    tipo_adecuacion_col = None
                    norma_col = None
                    macronorma_col = None
                    cantidad_col = None
                    try:
                        cursor.execute(
                            """
                            SELECT UPPER(COLUMN_NAME)
                            FROM USER_TAB_COLUMNS
                            WHERE UPPER(TABLE_NAME) = 'EPOSTE_AT'
                            """
                        )
                        cols_p = {row[0] for row in (cursor.fetchall() or [])}
                        for candidato in ['CODIGO_TRAFO', 'COD_TRAFO', 'CODIGO_TRANSFORMADOR']:
                            if candidato in cols_p:
                                trafo_col = candidato
                                break
                        for candidato in ['TIPO_ADECUACION']:
                            if candidato in cols_p:
                                tipo_adecuacion_col = candidato
                                break
                        for candidato in ['NORMA', 'CODIGO_NORMA', 'NORMA_ID']:
                            if candidato in cols_p:
                                norma_col = candidato
                                break
                        for candidato in ['MACRONORMA', 'MACRO_NORMA', 'CODIGO_MACRONORMA']:
                            if candidato in cols_p:
                                macronorma_col = candidato
                                break
                        for candidato in ['CANTIDAD', 'CANT', 'ALTURA']:
                            if candidato in cols_p:
                                cantidad_col = candidato
                                break
                    except Exception as e_cols2:
                        print(f"DEBUG Oracle: No fue posible leer columnas de EPOSTE_AT: {e_cols2}")

                    # Construir query dinámica si hay alguna columna disponible
                    if any([trafo_col, tipo_adecuacion_col, norma_col, macronorma_col, cantidad_col]):
                        try:
                            select_cols = []
                            if trafo_col:
                                select_cols.append(trafo_col)
                            if tipo_adecuacion_col:
                                select_cols.append(tipo_adecuacion_col)
                            if norma_col:
                                select_cols.append(norma_col)
                            if macronorma_col:
                                select_cols.append(macronorma_col)
                            if cantidad_col:
                                select_cols.append(cantidad_col)
                            cols_sql = ', '.join(select_cols)
                            cursor.execute(
                                f"SELECT {cols_sql} FROM EPOSTE_AT WHERE G3E_FID = :fid_param",
                                {"fid_param": fid_limpio}
                            )
                            row = cursor.fetchone()
                            if row:
                                idx = 0
                                if trafo_col:
                                    val = row[idx]
                                    idx += 1
                                    if val is not None and str(val).strip():
                                        resultado['CODIGO_TRAFO'] = str(val).strip()
                                if tipo_adecuacion_col:
                                    val = row[idx]
                                    idx += 1
                                    if val is not None and str(val).strip():
                                        resultado['TIPO_ADECUACION'] = str(val).strip()
                                if norma_col:
                                    val = row[idx]
                                    idx += 1
                                    if val is not None and str(val).strip():
                                        resultado['NORMA'] = str(val).strip()
                                if macronorma_col:
                                    val = row[idx]
                                    idx += 1
                                    if val is not None and str(val).strip():
                                        resultado['MACRONORMA'] = str(val).strip()
                                if cantidad_col:
                                    val = row[idx]
                                    # idx += 1  # último opcional
                                    if val is not None and str(val).strip():
                                        resultado['CANTIDAD'] = str(int(val)) if str(val).strip().isdigit() else str(val).strip()
                        except Exception as e_ep:
                            print(f"DEBUG Oracle: Error consultando EPOSTE_AT ({cols_sql}): {e_ep}")

        except Exception as e:
            print(f"❌ Oracle ERROR obtener_datos_norma_por_fid({fid_limpio}): {e}")
        return resultado

    @classmethod
    def obtener_uc_por_fid(cls, fid_real: str) -> str:
        """
        Obtiene la Unidad Constructiva (UC) desde Oracle usando el FID real.
        Si no existe o no hay conexión, retorna cadena vacía.
        """
        # Verificar si Oracle está habilitado
        if hasattr(settings, 'ORACLE_ENABLED') and not settings.ORACLE_ENABLED:
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para UC por FID {fid_real}")
            return ''

        if not fid_real:
            return ''

        fid_limpio = str(fid_real).strip()
        if fid_limpio.endswith('.0'):
            try:
                f = float(fid_limpio)
                if f.is_integer():
                    fid_limpio = str(int(f))
            except Exception:
                pass

        if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
            return ''

        try:
            oracle_config = cls.get_oracle_config()
            with oracledb.connect(**oracle_config) as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass

                    # 1) Intentar CCOMUN.UC
                    try:
                        cursor.execute(
                            """
                            SELECT c.uc
                            FROM ccomun c
                            WHERE c.g3e_fid = :fid_param
                            """,
                            {"fid_param": fid_limpio}
                        )
                        row = cursor.fetchone()
                        uc = str(row[0]).strip() if row and row[0] is not None else ''
                        if uc:
                            print(f"✅ Oracle: UC (CCOMUN) para FID {fid_limpio} = {uc}")
                            return uc
                    except Exception as e1:
                        print(f"DEBUG Oracle: fallo consulta UC en CCOMUN para FID {fid_limpio}: {e1}")

                    # 2) Fallback: intentar EPOSTE_AT con columnas posibles
                    uc_col = None
                    try:
                        cursor.execute(
                            """
                            SELECT COUNT(*)
                            FROM USER_TAB_COLUMNS
                            WHERE UPPER(TABLE_NAME) = 'EPOSTE_AT' AND UPPER(COLUMN_NAME) = 'UC'
                            """
                        )
                        has_uc = (cursor.fetchone() or [0])[0] > 0
                        if has_uc:
                            uc_col = 'UC'
                        else:
                            cursor.execute(
                                """
                                SELECT COUNT(*)
                                FROM USER_TAB_COLUMNS
                                WHERE UPPER(TABLE_NAME) = 'EPOSTE_AT' AND UPPER(COLUMN_NAME) = 'UNIDAD_CONSTRUCTIVA'
                                """
                            )
                            has_uc2 = (cursor.fetchone() or [0])[0] > 0
                            if has_uc2:
                                uc_col = 'UNIDAD_CONSTRUCTIVA'
                    except Exception as ecols:
                        print(f"DEBUG Oracle: fallo obteniendo metadatos de columnas para EPOSTE_AT: {ecols}")

                    if uc_col:
                        try:
                            cursor.execute(
                                f"""
                                SELECT p.{uc_col}
                                FROM eposte_at p
                                WHERE p.g3e_fid = :fid_param
                                """,
                                {"fid_param": fid_limpio}
                            )
                            row = cursor.fetchone()
                            uc = str(row[0]).strip() if row and row[0] is not None else ''
                            if uc:
                                print(f"✅ Oracle: UC (EPOSTE_AT.{uc_col}) para FID {fid_limpio} = {uc}")
                                return uc
                            else:
                                print(f"⚠️ Oracle: UC no encontrada en EPOSTE_AT para FID {fid_limpio}")
                        except Exception as e2:
                            print(f"DEBUG Oracle: fallo consulta UC en EPOSTE_AT para FID {fid_limpio}: {e2}")

                    # Si nada funcionó, regresar vacío
                    return ''
        except Exception as e:
            print(f"❌ Oracle ERROR obtener_uc_por_fid({fid_limpio}): {e}")
            return ''

    @classmethod
    def obtener_norma_por_fid(cls, fid: str) -> Dict[str, str]:
        """
        Obtiene datos de norma por FID desde BD (ccomun JOIN norma).
        Retorna dict con: NORMA, GRUPO, CIRCUITO, CODIGO_TRAFO, MACRONORMA, CANTIDAD, TIPO_ADECUACION
        Si no hay datos o error, retorna {}.
        """
        if hasattr(settings, 'ORACLE_ENABLED') and not settings.ORACLE_ENABLED:
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para obtener_norma_por_fid({fid})")
            return {}

        if not fid:
            return {}
        
        fid_limpio = str(fid).strip()
        if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
            return {}

        try:
            oracle_config = cls.get_oracle_config()
            with oracledb.connect(**oracle_config) as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass

                    # Query para obtener datos de norma por FID
                    # TODOS los campos están en la tabla norma (n)
                    query = """
                    SELECT 
                        n.norma,
                        n.grupo,
                        n.circuito,
                        n.codigo_trafo,
                        n.macronorma,
                        n.cantidad,
                        n.tipo_adecuacion
                    FROM ccomun c
                    JOIN norma n ON c.g3e_fid = n.g3e_fid
                    WHERE c.g3e_fid = :fid_param
                    """
                    
                    cursor.execute(query, {"fid_param": fid_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        norma, grupo, circuito, codigo_trafo, macronorma, cantidad, tipo_adec = result
                        
                        datos = {
                            'NORMA': str(norma).strip() if norma is not None else '',
                            'GRUPO': str(grupo).strip() if grupo is not None else '',
                            'CIRCUITO': str(circuito).strip() if circuito is not None else '',
                            'CODIGO_TRAFO': str(codigo_trafo).strip() if codigo_trafo is not None else '',
                            'MACRONORMA': str(macronorma).strip() if macronorma is not None else '',
                            'CANTIDAD': str(int(cantidad)) if cantidad is not None and str(cantidad).strip() != '' else '',
                            'TIPO_ADECUACION': str(tipo_adec).strip() if tipo_adec is not None else ''
                        }
                        
                        print(f"✅ Oracle obtener_norma_por_fid({fid_limpio}): NORMA={datos['NORMA']}, CIRCUITO={datos['CIRCUITO']}, CANTIDAD={datos['CANTIDAD']}")
                        return datos
                    else:
                        print(f"⚠️ Oracle: No se encontraron datos de norma para FID {fid_limpio}")
                        return {}
                        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Oracle ERROR obtener_norma_por_fid({fid_limpio}): {error_msg}")
            return {}


class ExcelProcessor:
    """Procesa archivos Excel extrayendo y normalizando datos de estructura"""
    
    def __init__(self, proceso):
        self.proceso = proceso
        self.tipo_estructura = getattr(proceso, 'tipo_estructura', 'EXPANSION')
        self.estructura_config = ESTRUCTURAS_CAMPOS.get(self.tipo_estructura, {})
        self.clasificador = ClasificadorEstructuras()
    
    def procesar_archivo(self) -> Tuple[List[Dict], List[str]]:
        """
        Procesa el archivo Excel del proceso y retorna datos y campos faltantes
        
        Returns:
            Tuple[List[Dict], List[str]]: (datos_procesados, campos_faltantes)
        """
        try:
            archivo_path = self.proceso.archivo_excel.path
            print(f"Procesando archivo: {archivo_path}")
            
            # Leer todas las hojas del Excel
            df_dict = pd.read_excel(archivo_path, sheet_name=None)
            
            # Determinar qué hoja usar basado en el modo de clasificación
            if self.proceso.clasificacion_confirmada:
                # FORZAR USO DE LA HOJA ESTRUCTURAS PARA DEBUG
                nombre_hoja = None
                
                # Buscar específicamente la hoja de estructuras
                if 'Estructuras_N1-N2-N3' in df_dict:
                    nombre_hoja = 'Estructuras_N1-N2-N3'
                    print(f"FORZANDO uso de hoja de estructuras: '{nombre_hoja}'")
                else:
                    # Fallback al algoritmo original si no existe esa hoja
                    mejor_puntaje = 0
                    print(f"Buscando la hoja correcta entre {len(df_dict)} hojas disponibles...")
                    
                    # Buscar en todas las hojas la que tenga más columnas de normas
                    for hoja_nombre, df_temp in df_dict.items():
                        try:
                            columnas_hoja = [str(col).strip() for col in df_temp.columns]
                            print(f"Revisando hoja '{hoja_nombre}' con {len(columnas_hoja)} columnas")
                            
                            # Calcular puntaje basado en columnas clave encontradas
                            puntaje = 0
                            
                            for col in columnas_hoja:
                                col_lower = str(col).lower().strip()
                                # Buscar coincidencias más flexibles
                                if ('norma' in col_lower or 
                                    'poblacion' in col_lower or 'población' in col_lower or 'municipio' in col_lower or
                                    'unidad' in col_lower and 'constructiva' in col_lower or
                                    'codigo' in col_lower and 'inventario' in col_lower or
                                    'material' in col_lower or
                                    'altura' in col_lower):
                                    puntaje += 1
                                    print(f"    Columna clave encontrada: '{col}'")
                            
                            print(f"  Hoja '{hoja_nombre}': puntaje {puntaje}/6 columnas clave")
                            
                            if puntaje > mejor_puntaje:
                                mejor_puntaje = puntaje
                                nombre_hoja = hoja_nombre
                                print(f"  Nueva mejor hoja: '{nombre_hoja}' con puntaje {puntaje}")
                        
                        except Exception as e:
                            print(f"  Error revisando hoja '{hoja_nombre}': {e}")
                            continue
                    
                    # Si no encuentra hoja específica, usar la primera
                    if not nombre_hoja:
                        nombre_hoja = list(df_dict.keys())[0]
                        print(f"No se encontró hoja específica, usando la primera: '{nombre_hoja}'")
                        
                    print(f"Hoja seleccionada: '{nombre_hoja}' (puntaje: {mejor_puntaje}/6)")
            else:
                # Buscar hoja de datos específica
                hoja_datos = self.estructura_config['ARCHIVOS_FUENTE']['hoja_datos']
                if hoja_datos in df_dict:
                    nombre_hoja = hoja_datos
                else:
                    # Fallback: usar la primera hoja
                    nombre_hoja = list(df_dict.keys())[0]
                    print(f"Hoja '{hoja_datos}' no encontrada, usando '{nombre_hoja}'")
            
            # Leer la hoja sin headers para investigar
            datos_df_raw = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=None)
            print("Primeras 5 filas del Excel:")
            for i in range(min(5, len(datos_df_raw))):
                print(f"Fila {i}: {list(datos_df_raw.iloc[i].values)}")
            
            # Intentar diferentes estrategias para encontrar headers
            datos_df = None
            header_row = None
            
            # Estrategia 1: Headers en fila 0 (default)
            try:
                temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=0)
                # Verificar si tiene headers válidos (no solo "Unnamed" y no todos nan)
                valid_headers = [col for col in temp_df.columns if not col.startswith('Unnamed:') and str(col) != 'nan']
                if len(valid_headers) > 3:  # Al menos 3 headers válidos
                    datos_df = temp_df
                    header_row = 0
                    print("Headers encontrados en fila 0")
            except Exception:
                pass
            
            # Estrategia 2: Headers en fila 1
            if datos_df is None:
                try:
                    temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=1)
                    # Verificar si tiene headers válidos
                    valid_headers = [col for col in temp_df.columns if not col.startswith('Unnamed:') and str(col) != 'nan']
                    if len(valid_headers) > 3:  # Al menos 3 headers válidos
                        datos_df = temp_df
                        header_row = 1
                        print("Headers encontrados en fila 1")
                except Exception:
                    pass
            
            # Estrategia 3: Headers en fila 2
            if datos_df is None:
                try:
                    temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=2)
                    if not all(col.startswith('Unnamed:') for col in temp_df.columns):
                        datos_df = temp_df
                        header_row = 2
                        print("Headers encontrados en fila 2")
                except Exception:
                    pass
            
            # Si no encontramos headers válidos, usar fila 0 como fallback
            if datos_df is None:
                datos_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=0)
                header_row = 0
                print("Usando fila 0 como headers (fallback)")
            
            print(f"Datos de hoja '{nombre_hoja}': {len(datos_df)} filas (header en fila {header_row})")
            # Guardar metadata detectada para uso posterior
            try:
                self.header_row_detected = header_row
                self.sheet_used = nombre_hoja
            except Exception:
                pass
            
            # Normalizar nombres de columnas
            datos_df.columns = [self._normalizar_columna(col) for col in datos_df.columns]
            print(f"Columnas encontradas: {list(datos_df.columns)}")
            
            # Verificar campos requeridos
            campos_faltantes = self._verificar_campos(datos_df.columns)
            
            if campos_faltantes:
                print(f"Campos faltantes: {campos_faltantes}")
                print(f"Se encontraron: {list(datos_df.columns)}")
                return [], campos_faltantes
            
            # Convertir a lista de diccionarios y limpiar NaN
            datos = []
            for _, row in datos_df.iterrows():
                registro = {}
                for col, val in row.items():
                    if pd.isna(val):
                        registro[col] = ""
                    else:
                        # Formatear fechas directamente al leer del Excel
                        if self._es_campo_fecha(col) and val:
                            # Si es un campo de fecha, formatear inmediatamente
                            registro[col] = self._formatear_fecha_excel(val)
                        else:
                            registro[col] = str(val).strip()
                datos.append(registro)
            
            print(f"Registros procesados: {len(datos)}")
            
            return datos, []
            
        except Exception as e:
            print(f"Error procesando Excel: {str(e)}")
            raise Exception(f"Error procesando Excel: {str(e)}")
    
    def _normalizar_columna(self, columna: str) -> str:
        """Normaliza nombres de columnas manteniendo errores tipográficos del Excel"""
        return str(columna).strip()
    
    def _verificar_campos(self, columnas_excel: List[str]) -> List[str]:
        """Verifica qué campos obligatorios faltan"""
        # Usar validación permisiva por defecto (mapeo de equivalencias)
        # Mapeo de equivalencias de nombres de campos (ACTUALIZADO con columnas reales del Excel)
        equivalencias = {
            'Norma': ['Norma', 'NORMA', 'norma'],
            'UC': ['UC', 'Unidad_Constructiva', 'Unidad Constructiva', 'UNIDAD_CONSTRUCTIVA', 
                   'unidad_constructiva', 'unidad constructiva', 'Unnamed: 25'],
            'Poblacion': ['Poblacion', 'POBLACION', 'poblacion', 'Población', 'MUNICIPIOS', 'Municipios', 'Municipio', 'municipio'],
            'CODIGO_MATERIAL': ['Codigo Inventario', 'CODIGO_INVENTARIO', 'Unnamed: 23', 'Material', 'MATERIAL']
        }
        
        # Solo verificar campos básicos
        campos_basicos = ['Norma', 'UC', 'Poblacion']
        campos_faltantes = []
        
        print(f"DEBUG: Verificando campos básicos: {campos_basicos}")
        print(f"DEBUG: Columnas del Excel: {columnas_excel}")
        
        for campo in campos_basicos:
            campo_encontrado = False
            posibles_nombres = equivalencias.get(campo, [campo])
            print(f"DEBUG: Buscando campo '{campo}' en posibles nombres: {posibles_nombres}")
            
            for col in columnas_excel:
                if str(col).strip() in posibles_nombres:
                    print(f"DEBUG: Campo '{campo}' encontrado como '{col}'")
                    campo_encontrado = True
                    break
            
            if not campo_encontrado:
                print(f"DEBUG: Campo '{campo}' NO encontrado")
                campos_faltantes.append(campo)
        
        return campos_faltantes
    
    def _es_campo_fecha(self, nombre_columna: str) -> bool:
        """Verifica si una columna es un campo de fecha"""
        nombre_lower = nombre_columna.lower()
        return 'fecha' in nombre_lower or 'instalacion' in nombre_lower
    
    def _formatear_fecha_excel(self, fecha) -> str:
        """
        Formatea fechas leídas directamente del Excel a formato DD/MM/YYYY
        """
        return DataUtils.formatear_fecha(fecha)

class DataTransformer:
    """Transformador de datos del Excel de entrada a estructura de salida"""
    
    def __init__(self, tipo_estructura: str):
        self.tipo_estructura = tipo_estructura
        self.mapeo = MAPEO_EXCEL_A_SALIDA.get(tipo_estructura, {})
        self.estructura_config = ESTRUCTURAS_CAMPOS[tipo_estructura]
        self.clasificador = ClasificadorEstructuras()
    
    def _normalizar_nombres_campos(self, registro: Dict) -> Dict:
        """Normaliza los nombres de campos para que coincidan con el mapeo esperado"""
        equivalencias = {
            'Unidad_Constructiva': 'UC',
            'Unidad Constructiva': 'UC',
            'Unnamed: 25': 'UC',  # Para archivos con encabezados genéricos
            'Unnamed: 23': 'CODIGO_INVENTARIO',  # Para código de inventario
            'Unnamed: 0': 'COORDENADA_X',  # Para coordenada X
            'Unnamed: 1': 'COORDENADA_Y',  # Para coordenada Y
            'UNIDAD_CONSTRUCTIVA': 'UC',
            'unidad_constructiva': 'UC',
            'unidad constructiva': 'UC',
            'Código FID_rep': 'Código FID_rep',
            'FID_ANTERIOR': 'FID_ANTERIOR',
            'Tipo_accion_sal': 'Tipo_accion_sal',
            'Tipo_accion_ent': 'Tipo_accion_ent',
            # Nuevo: mapear 'Tipo inversión' del Excel para TIPO_PROYECTO
            'Tipo inversión': 'TIPO_INVERSION_ROMANO',
            'Tipo inversion': 'TIPO_INVERSION_ROMANO',
            'TIPO INVERSION': 'TIPO_INVERSION_ROMANO',
            'TIPO INVERSIÓN': 'TIPO_INVERSION_ROMANO',
            'tipo inversion': 'TIPO_INVERSION_ROMANO',
            'tipo inversión': 'TIPO_INVERSION_ROMANO',
            # NUEVO: soportar el campo del Excel 'CodigoMaterial'
            'CodigoMaterial': 'CODIGO_MATERIAL',
            'CODIGOMATERIAL': 'CODIGO_MATERIAL',
            'codigoMaterial': 'CODIGO_MATERIAL',
            'codigo_material': 'CODIGO_MATERIAL',
        }
        
        registro_normalizado = {}
        for campo, valor in registro.items():
            # Usar el nombre normalizado si existe, sino usar el original
            campo_normalizado = equivalencias.get(campo, campo)
            registro_normalizado[campo_normalizado] = valor
        
        return registro_normalizado
    
    def transformar_datos(self, datos_excel: List[Dict]) -> List[Dict]:
        """Transforma datos del Excel a la estructura de salida"""
        datos_transformados = []
        
        for registro_excel in datos_excel:
            # Normalizar nombres de campos en el registro
            registro_normalizado = self._normalizar_nombres_campos(registro_excel)
            registro_salida = {}
            
            # Mapear campos según el tipo de estructura
            for campo_excel, campo_salida in self.mapeo.items():
                valor = registro_normalizado.get(campo_excel, "")
                
                # Formatear fechas durante el mapeo
                if campo_salida in ['FECHA_INSTALACION', 'FECHA_OPERACION'] and valor:
                    valor = self.clasificador._formatear_fecha(str(valor))
                
                registro_salida[campo_salida] = valor

            # NUEVO: si el Excel trae la columna 'CodigoMaterial', reflejarla SIEMPRE (aunque esté vacía)
            # y marcar que proviene del Excel con un flag para evitar fallback por UC cuando esté vacía.
            if 'CODIGO_MATERIAL' in registro_normalizado:
                cm_excel_val = registro_normalizado.get('CODIGO_MATERIAL', '')
                registro_salida['CODIGO_MATERIAL'] = DataUtils.normalizar_codigo_material(cm_excel_val)
                registro_salida['_CODIGO_MATERIAL_FROM_EXCEL'] = True
            else:
                registro_salida['_CODIGO_MATERIAL_FROM_EXCEL'] = False

            # NUEVO: si el Excel trae 'Tipo inversión' (en romano), convertir a Tn y colocar en TIPO_PROYECTO
            try:
                tipo_inv_excel = registro_normalizado.get('TIPO_INVERSION_ROMANO', '')
                if tipo_inv_excel:
                    tipo_excel_convertido = self.clasificador._convertir_tipo_proyecto(str(tipo_inv_excel))
                    if tipo_excel_convertido:
                        registro_salida['TIPO_PROYECTO'] = tipo_excel_convertido
                        # Guardar un respaldo para preservar este valor tras la clasificación
                        registro_salida['_TIPO_PROYECTO_EXCEL'] = tipo_excel_convertido
            except Exception:
                pass
            
            # Agregar campos faltantes con valores por defecto
            for campo_salida in self.estructura_config['CAMPOS_SALIDA_DATOS']:
                if campo_salida not in registro_salida:
                    registro_salida[campo_salida] = ""
            
            # APLICAR REGLAS DE CLASIFICACIÓN
            registro_salida = self.clasificador.clasificar_estructura(registro_salida)
            
            # REGLA ESPECIAL: EMPRESA debe tener el mismo valor que PROPIETARIO para todos los tipos
            propietario = registro_salida.get('PROPIETARIO', '')
            registro_salida['EMPRESA'] = propietario

            # Guardar índice relativo para mensajes (se complementará luego con header_row)
            if '_row_index' not in registro_salida:
                try:
                    registro_salida['_row_index'] = len(datos_transformados)  # índice base 0
                except Exception:
                    pass
            
            datos_transformados.append(registro_salida)
        
        return datos_transformados
    
    def obtener_estadisticas_clasificacion(self, datos_transformados: List[Dict]) -> Dict:
        """Obtiene estadísticas de la clasificación aplicada"""
        return self.clasificador.obtener_resumen_clasificacion(datos_transformados)

class DataMapper:
    """Mapeador de datos Excel a estructura de norma"""
    
    def __init__(self, tipo_estructura: str):
        self.tipo_estructura = tipo_estructura
        self.estructura_config = ESTRUCTURAS_CAMPOS[tipo_estructura]
    
    def mapear_a_norma(self, datos_excel: List[Dict], circuito: str = "") -> List[Dict]:
        """Mapea datos del Excel al formato de norma"""
        
        datos_norma = []
        
        for registro in datos_excel:
            norma_registro = {
                'ENLACE': registro.get('ENLACE', ''),  # Campo Identificador mapeado a ENLACE
                'NORMA': registro.get('NORMA', ''),  # Campo Norma del Excel
                'CIRCUITO': circuito,
                'CODIGO_TRAFO': registro.get('CODIGO_TRAFO', ''),  # Opcional
                'CANTIDAD': self._calcular_cantidad(registro),
                'FECHA_INSTALACION': registro.get('FECHA_INSTALACION', ''),
                'TIPO_ADECUACION': registro.get('TIPO_ADECUACION', ''),  # "retencion o suspensión"
                'OBSERVACIONES': registro.get('OBSERVACIONES', ''),  # Campo observaciones
                'UC': registro.get('UC', ''),  # IMPORTANTE: Preservar UC para clasificación
                'ESTADO_SALUD': registro.get('ESTADO_SALUD', ''),  # IMPORTANTE: Preservar estado de salud
                'NIVEL_TENSION': registro.get('NIVEL_TENSION', ''),  # IMPORTANTE: Preservar nivel de tensión
            }
            
            # Agregar GRUPO solo para EXPANSION
            if self.tipo_estructura == 'EXPANSION':
                norma_registro['GRUPO'] = 'NODO ELECTRICO'
            
            datos_norma.append(norma_registro)
        
        return datos_norma
    
    def _calcular_cantidad(self, datos_excel: Dict) -> str:
        """Calcula CANTIDAD basado directamente en el campo Altura del Excel (mapeado como CANTIDAD)"""
        # El campo Altura del Excel ya viene mapeado como CANTIDAD
        if 'CANTIDAD' in datos_excel and datos_excel['CANTIDAD']:
            try:
                # Convertir a número y luego a string para limpiar formato
                cantidad_valor = float(datos_excel['CANTIDAD'])
                return str(int(cantidad_valor))  # Convertir a entero para eliminar decimales
            except (ValueError, TypeError):
                pass
        
        # Si no hay valor de CANTIDAD, devolver valor por defecto
        return '1'

# Función principal del servicio
def procesar_estructura_completo(proceso_id: str) -> None:
    """Función principal que orquesta todo el procesamiento"""
    proceso = ProcesoEstructura.objects.get(id=proceso_id)
    
    try:
        print(f"Iniciando procesamiento del proceso {proceso_id}")
        
        # 1. Procesar Excel
        proceso.estado = 'PROCESANDO'
        proceso.save()
        
        processor = ExcelProcessor(proceso)
        datos, campos_faltantes_excel = processor.procesar_archivo()
        
        if campos_faltantes_excel:
            proceso.estado = 'ERROR'
            proceso.errores = [f"Campos faltantes en Excel: {', '.join(campos_faltantes_excel)}"]
            proceso.save()
            print(f"Error: campos faltantes {campos_faltantes_excel}")
            return
        
        # 2. Transformar datos a estructura de salida
        # Para clasificación automática, usamos EXPANSION como tipo base
        transformer = DataTransformer('EXPANSION')
        datos_transformados = transformer.transformar_datos(datos)
        
        # 3. Almacenar datos transformados en el proceso
        proceso.registros_totales = len(datos_transformados)
        proceso.datos_excel = datos_transformados
        
        # 4. Mapear a norma (usando el circuito del proceso)
        # Para clasificación automática, usamos EXPANSION como tipo base
        mapper = DataMapper('EXPANSION')
        datos_norma = mapper.mapear_a_norma(datos_transformados, proceso.circuito or "")
        
        # 5. Aplicar clasificación inicial
        clasificador = ClasificadorEstructuras()
        datos_clasificados = []
        for registro in datos_norma:
            registro_clasificado = clasificador.clasificar_estructura(registro)
            datos_clasificados.append(registro_clasificado)
        
        proceso.datos_norma = datos_clasificados
        
        # 6. Detectar campos faltantes para completar
        campos_faltantes = {'CIRCUITO': list(range(len(datos_transformados)))}  # Siempre falta circuito
        
        # ESTADO_SALUD siempre se debe completar por el usuario ya que no suele venir en archivos Excel
        # o viene como información técnica incorrecta (como "Nivel de Tension")
        campos_faltantes['ESTADO_SALUD'] = list(range(len(datos_transformados)))
        
        proceso.campos_faltantes = campos_faltantes
        proceso.registros_procesados = proceso.registros_totales
        proceso.estado = 'COMPLETANDO_DATOS'
        proceso.save()
        
        print(f"Procesamiento completado: {len(datos_transformados)} registros transformados")
        
    except Exception as e:
        proceso.estado = 'ERROR'
        proceso.errores = [str(e)]
        proceso.save()
        print(f"Error en procesamiento: {str(e)}")
        raise


class FileGenerator:
    """Genera archivos TXT y XML a partir de datos transformados"""
    
    def __init__(self, proceso):
        self.proceso = proceso
        self.base_path = os.path.join(settings.MEDIA_ROOT, 'generated')
        os.makedirs(self.base_path, exist_ok=True)
        self.clasificador = ClasificadorEstructuras()
        
        # NUEVOS COMPONENTES MODULARES
        self.validador_maestro = ValidadorMaestro()
        self.file_manager = FileManager(proceso)

    def generar_txt_modular(self):
        """
        Nueva implementación modular de generar_txt que usa el sistema de validaciones
        y generadores reorganizados. Mantiene toda la funcionalidad del método original
        pero con código más organizado y mantenible.
        """
        try:
            # Usar el FileManager para la generación coordinada
            resultado = self.file_manager.generar_archivo_txt_coordinado('estructuras_nuevo')
            
            if not resultado['exito']:
                if resultado['errores_validacion']:
                    # Si hay errores de validación, lanzar excepción específica
                    raise Exception("VALIDATION_ERRORS")
                else:
                    raise Exception(resultado['mensaje'])
            
            return resultado['archivo_generado']
            
        except Exception as e:
            # Mantener compatibilidad con manejo de errores existente
            msg = str(e)
            if msg.lower().startswith('error generando archivo txt'):
                msg = msg.split(':', 1)[-1].strip()
            raise Exception(f"error generando archivo TXT : {msg}")

    def generar_txt_baja_modular(self):
        """Genera archivo TXT de baja usando el sistema modular optimizado"""
        from .generadores.txt_estructuras import GeneradorTxtBaja
        generador = GeneradorTxtBaja(self.proceso, self.base_path)
        return generador.generar()

    def generar_xml_modular(self):
        """
        Nueva implementación modular de generar_xml que usa el sistema de validaciones
        y generadores reorganizados. Mantiene toda la funcionalidad del método original
        pero con código más organizado y mantenible.
        """
        try:
            # Usar el FileManager para la generación coordinada de XML
            resultado = self.file_manager.generar_archivo_xml_coordinado('estructuras')
            
            if not resultado['exito']:
                if resultado['errores_validacion']:
                    # Si hay errores de validación, lanzar excepción específica
                    raise Exception("VALIDATION_ERRORS")
                else:
                    raise Exception(resultado['mensaje'])
            
            return resultado['archivo_generado']
            
        except Exception as e:
            # Mantener compatibilidad con manejo de errores existente
            msg = str(e)
            if msg.lower().startswith('error generando archivo xml'):
                msg = msg.split(':', 1)[-1].strip()
            raise Exception(f"error generando archivo XML : {msg}")

    def generar_xml_baja_modular(self):
        """Genera archivo XML de baja usando el sistema modular optimizado"""
        from .generadores.xml_estructuras import GeneradorXMLBaja
        generador = GeneradorXMLBaja(self.proceso, self.base_path)
        return generador.generar()

    def _generar_nombre_archivo_con_indice(self, tipo_archivo: str, extension: str) -> str:
        """
        Genera un nombre de archivo único con índice incremental.
        
        Formato: {tipo}_{timestamp}_{contador}.{extension}
        Ejemplos: 
            - estructuras_nuevo_20251014_001.txt
            - estructuras_baja_20251014_001.txt
            - norma_nuevo_20251014_001.xml
        
        Args:
            tipo_archivo: Tipo de archivo ('estructuras_nuevo', 'estructuras_baja', 'norma_nuevo', 'norma_baja')
            extension: Extensión del archivo ('txt' o 'xml')
            
        Returns:
            Nombre de archivo único con índice incremental
        """
        from datetime import datetime
        import glob
        
        # Timestamp actual: solo fecha YYYYMMDD
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Buscar archivos existentes con el mismo patrón para determinar el siguiente índice
        # Patrón: tipo_timestamp_*.extension
        patron = os.path.join(self.base_path, f"{tipo_archivo}_{timestamp}_*.{extension}")
        archivos_existentes = glob.glob(patron)
        
        # Extraer índices de archivos existentes
        indices_existentes = []
        for archivo in archivos_existentes:
            try:
                # Extraer el número de índice del nombre del archivo
                basename = os.path.basename(archivo)
                # Formato: tipo_timestamp_XXX.extension
                partes = basename.replace(f'.{extension}', '').split('_')
                if len(partes) >= 3:
                    indice = int(partes[-1])
                    indices_existentes.append(indice)
            except (ValueError, IndexError):
                continue
        
        # Determinar el siguiente índice
        if indices_existentes:
            siguiente_indice = max(indices_existentes) + 1
        else:
            siguiente_indice = 1
        
        # Formatear índice con 3 dígitos (001, 002, etc.)
        indice_formateado = f"{siguiente_indice:03d}"
        
        # Construir nombre de archivo final
        nombre_archivo = f"{tipo_archivo}_{timestamp}_{indice_formateado}.{extension}"
        
        print(f"📁 Generando archivo: {nombre_archivo}")
        
        return nombre_archivo

    def _limpiar_fid(self, valor) -> str:
        """
        Limpia y normaliza un valor FID eliminando decimales innecesarios (.0)
        """
        if valor is None:
            return ''
        
        vs = str(valor).strip()
        if vs.lower() in ('', 'nan', 'none'):
            return ''
            
        # Si es un número con .0 al final, remover el .0
        if vs.endswith('.0'):
            try:
                # Verificar que realmente es un número entero
                float_val = float(vs)
                if float_val.is_integer():
                    return str(int(float_val))
            except (ValueError, OverflowError):
                pass
        
        return vs

    def _extraer_fid_rep(self, registro: Dict) -> str:
        """
        Extrae el valor de 'Código FID_rep' de un registro probando varias claves
        y normalizando el resultado. Retorna cadena vacía si no existe o es inválido.
        """
        # 1. Comprobar claves explícitas comunes
        explicit_keys = ['Código FID_rep', 'Codigo FID_rep', 'CODIGO_FID_REP', 'codigo_fid_rep', 'FID_ANTERIOR', 'FID']
        for k in explicit_keys:
            if k in registro:
                v = registro.get(k)
                if v is None:
                    continue
                vs = self._limpiar_fid(v)
                if vs:
                    return vs

        # 2. Buscar cualquier clave cuyo nombre normalizado contenga 'fid' (aceptar variantes)
        try:
            for key in registro.keys():
                if not isinstance(key, str):
                    continue
                key_norm = self._normalize_col_name(key)
                if 'fid' in key_norm:
                    v = registro.get(key)
                    if v is None:
                        continue
                    vs = self._limpiar_fid(v)
                    if vs:
                        return vs
        except Exception:
            pass

        return ''

    def _signature_registro(self, registro: Dict):
        """Construye una firma robusta del registro para detectar duplicados entre NUEVO y BAJA.

        Prioriza UC; si no hay UC, usa (COORDENADA_X, COORDENADA_Y, PROYECTO);
        si no hay PROYECTO, usa (COORDENADA_X, COORDENADA_Y, ENLACE).
        Si solo hay coordenadas, usa (COORDENADA_X, COORDENADA_Y).

        Retorna una tupla que identifica el registro, o None si no hay datos suficientes.
        """
        if not isinstance(registro, dict):
            return None

        def norm(v):
            try:
                return str(v).strip()
            except Exception:
                return ''

        uc = norm(registro.get('UC'))
        x = norm(registro.get('COORDENADA_X'))
        y = norm(registro.get('COORDENADA_Y'))
        proyecto = norm(registro.get('PROYECTO'))
        enlace = norm(registro.get('ENLACE'))

        if uc:
            return ('UC', uc)
        if x and y and proyecto:
            return ('XYP', x, y, proyecto)
        if x and y and enlace:
            return ('XYE', x, y, enlace)
        if x and y:
            return ('XY', x, y)
        return None

    def _indices_con_fid_rep_exactos(self):
        """
        Obtiene índices de filas del Excel que tienen valor no vacío en la
        columna EXACTA 'Código FID_rep'. Ignora otras columnas parecidas
        (p. ej. 'Código FID\nGIT').

        Returns:
            Tuple[Set[int], List[Dict]]: (índices_con_fid, datos_excel_crudos)
        """
        try:
            processor = ExcelProcessor(self.proceso)
            raw_datos, _ = processor.procesar_archivo()
        except Exception:
            raw_datos = self.proceso.datos_excel or []

        indices = set()
        for i, reg in enumerate(raw_datos):
            if not isinstance(reg, dict):
                continue
            # Variantes textuales del mismo encabezado
            variantes = (
                'Código FID_rep', 'Codigo FID_rep', 'CODIGO_FID_REP', 'codigo_fid_rep'
            )
            hit = False
            for k in variantes:
                if k in reg:
                    v = reg.get(k)
                    s = '' if v is None else str(v).strip()
                    if s and s.lower() not in ('nan', 'none'):
                        indices.add(i)
                    hit = True
                    break
            if hit:
                continue
            # Si no encontró variantes exactas, no toma ninguna columna con 'fid' genérico
        return indices, raw_datos
    
    def _limpiar_valor_para_txt(self, valor):
        """
        Limpia un valor para que no contenga caracteres problemáticos en el archivo TXT
        """
        return DataUtils.limpiar_valor_para_txt(valor)
    
    def _validar_campos_criticos(self, registro):
        """
        Valida que los campos críticos tengan valores válidos usando utilidades centralizadas
        """
        # Usar valores por defecto centralizados
        campos_criticos = {
            'COORDENADA_X': '0',
            'COORDENADA_Y': '0', 
            'LONGITUD': '0',
            'LATITUD': '0',
            'GRUPO': DataUtils.VALORES_DEFECTO['GRUPO'],
            'TIPO': DataUtils.VALORES_DEFECTO['TIPO'],
            'CLASE': 'SIN_CLASE',
            'USO': 'SIN_USO',
            'ESTADO': 'ACTIVO',
            'PROPIETARIO': 'SIN_PROPIETARIO',
            'PORCENTAJE_PROPIEDAD': DataUtils.VALORES_DEFECTO['PORCENTAJE_PROPIEDAD'],
            'TIPO_PROYECTO': DataUtils.VALORES_DEFECTO['TIPO_PROYECTO'],
            'FECHA_INSTALACION': DataUtils.VALORES_DEFECTO['FECHA_DEFAULT'],
            'FECHA_OPERACION': DataUtils.VALORES_DEFECTO['FECHA_DEFAULT']
        }
        
        for campo, valor_defecto in campos_criticos.items():
            if not registro.get(campo) or str(registro.get(campo, '')).strip() == '':
                registro[campo] = valor_defecto
        
        return registro
    
    def _validar_tipos_datos(self, registro):
        """
        Valida que los campos tengan los tipos de datos correctos para carga masiva
        """
        # Campos que deben ser numéricos
        campos_numericos = {
            'COORDENADA_X': 'decimal',
            'COORDENADA_Y': 'decimal', 
            'LONGITUD': 'decimal',
            'LATITUD': 'decimal',
            'PORCENTAJE_PROPIEDAD': 'entero',
            'CANTIDAD': 'entero'
        }
        
        # Campos que deben ser fechas
        campos_fecha = {
            'FECHA_INSTALACION': 'DD/MM/YYYY',
            'FECHA_OPERACION': 'DD/MM/YYYY'
        }
        
        # Validar campos numéricos
        for campo, tipo in campos_numericos.items():
            if campo in registro and registro[campo]:
                try:
                    valor = str(registro[campo]).replace(',', '.')
                    if tipo == 'decimal':
                        float(valor)
                    elif tipo == 'entero':
                        int(float(valor))
                    # Normalizar formato decimal
                    if tipo == 'decimal':
                        registro[campo] = f"{float(valor):.6f}".rstrip('0').rstrip('.')
                    else:
                        registro[campo] = str(int(float(valor)))
                except (ValueError, TypeError):
                    # Asignar valor por defecto si no se puede convertir
                    registro[campo] = '0' if tipo == 'entero' else '0.0'
        
        # Validar campos de fecha usando utilidad centralizada
        for campo, formato in campos_fecha.items():
            if campo in registro and registro[campo]:
                registro[campo] = DataUtils.formatear_fecha(registro[campo])
        
        return registro
    
    def _get_datos_completos(self):
        """Combina datos del Excel con datos procesados (clasificación y propietario)"""
        if not self.proceso.datos_excel:
            raise Exception("No hay datos originales del Excel")
        
        datos_salida = []
        
        # Si tenemos datos_norma (datos procesados), usarlos como base
        if self.proceso.datos_norma:
            print(f"Combinando datos_excel ({len(self.proceso.datos_excel)}) con datos_norma ({len(self.proceso.datos_norma)})")
            
            for i, registro_excel in enumerate(self.proceso.datos_excel):
                # Empezar con los datos originales del Excel
                registro_completo = registro_excel.copy()
                
                # Si hay datos procesados correspondientes, usar campos específicos de allí
                if i < len(self.proceso.datos_norma):
                    registro_norma = self.proceso.datos_norma[i]
                    
                    # Campos que deben venir de datos_norma (procesados)
                    # NOTA: GRUPO NO se incluye aquí porque para TXT de expansión debe venir del Excel
                    campos_procesados = [
                        'TIPO', 'CLASE', 'USO', 'PROPIETARIO', 
                        'PORCENTAJE_PROPIEDAD', 'FECHA_OPERACION',
                        'CODIGO_MATERIAL', 'FECHA_INSTALACION', 'ESTADO_SALUD'
                    ]
                    
                    for campo in campos_procesados:
                        if campo in registro_norma:
                            registro_completo[campo] = registro_norma[campo]
                    
                    # TIPO_PROYECTO: Priorizar datos_excel (ya convertido correctamente)
                    if 'TIPO_PROYECTO' in registro_excel and registro_excel['TIPO_PROYECTO']:
                        registro_completo['TIPO_PROYECTO'] = registro_excel['TIPO_PROYECTO']
                    elif 'TIPO_PROYECTO' in registro_norma and registro_norma['TIPO_PROYECTO']:
                        registro_completo['TIPO_PROYECTO'] = registro_norma['TIPO_PROYECTO']
                    
                    # IMPORTANTE: Preservar UC del Excel original para re-clasificación
                    # Asegurar que UC esté disponible para la clasificación
                    if 'UC' in registro_excel and registro_excel['UC']:
                        registro_completo['UC'] = registro_excel['UC']
                
                # Agregar circuito del proceso
                if self.proceso.circuito:
                    registro_completo['CIRCUITO'] = self.proceso.circuito
                
                datos_salida.append(registro_completo)
        else:
            # Fallback: solo datos del Excel con valores por defecto
            print("No hay datos_norma, usando solo datos_excel con valores por defecto")
            datos_salida = self.proceso.datos_excel.copy()
            
            # Aplicar valores por defecto
            for i, registro in enumerate(datos_salida):
                if self.proceso.circuito:
                    registro['CIRCUITO'] = self.proceso.circuito
                
                # Valores por defecto básicos
                defaults = {
                    # 'GRUPO': 'ESTRUCTURAS EYT',  # COMENTADO: Para EXPANSION usar valor del Excel
                    'TIPO': 'SECUNDARIO',  # Por defecto según reglas de negocio
                    'CLASE': 'POSTE',
                    'USO': 'DISTRIBUCION ENERGIA',
                    'PORCENTAJE_PROPIEDAD': '100'
                }
                
                # Aplicar propietario definido por el usuario (solo para ciertos tipos)
                # NOTA: Para estructuras clasificadas como EXPANSION, PROPIETARIO debe venir del campo "Nombre" del Excel
                # Como ahora tenemos clasificación automática, verificamos si hay estructuras de expansión
                tiene_expansion = any(
                    'EXPANSION' in str(registro.get('TIPO_PROYECTO', '')).upper() 
                    for registro in datos_salida
                )
                if self.proceso.propietario_definido and not tiene_expansion:
                    registro['PROPIETARIO'] = self.proceso.propietario_definido
                
                # Aplicar valores por defecto solo si el campo no existe o está vacío
                for campo, valor_default in defaults.items():
                    if campo not in registro or not registro[campo]:
                        registro[campo] = valor_default
        
        print(f"Datos completos preparados: {len(datos_salida)} registros")
        if datos_salida and 'PROPIETARIO' in datos_salida[0]:
            print(f"Propietario en datos finales: {datos_salida[0]['PROPIETARIO']}")
        
        return datos_salida

    def _preparar_datos_finales(self, datos_salida):
        """
        Prepara los datos finales aplicando todas las transformaciones necesarias
        antes de generar los archivos.
        
        Este método centraliza toda la lógica de preparación final siguiendo
        el principio de responsabilidad única.
        """
        datos_preparados = []
        
        for registro in datos_salida:
            registro_final = registro.copy()
            
            # 1. Aplicar ESTADO_SALUD del proceso si fue definido por el usuario
            if (hasattr(self.proceso, 'estado_salud_definido') and 
                self.proceso.estado_salud_definido and 
                self.proceso.estado_salud_definido != 'None'):
                registro_final['ESTADO_SALUD'] = self.proceso.estado_salud_definido
            elif not registro_final.get('ESTADO_SALUD'):
                # Si ESTADO_SALUD está vacío y no fue definido por el usuario, 
                # marcar que se requiere completar
                print("ADVERTENCIA: ESTADO_SALUD vacío en registro, se requiere completar por el usuario")
            
            # 1b. Aplicar ESTADO del proceso - usar Excel si es válido, si no el del usuario
            estado_excel = registro_final.get('ESTADO', '').strip()
            estados_validos = ['CONSTRUCCION', 'RETIRADO', 'OPERACION']
            
            if estado_excel and estado_excel in estados_validos:
                # Si el Excel trae un estado válido, usarlo
                registro_final['ESTADO'] = estado_excel
            elif (hasattr(self.proceso, 'estado_estructura_definido') and 
                  self.proceso.estado_estructura_definido and 
                  self.proceso.estado_estructura_definido != 'None'):
                # Si no hay estado válido en Excel, usar el seleccionado por el usuario
                registro_final['ESTADO'] = self.proceso.estado_estructura_definido
            else:
                # Si no hay ninguno, usar OPERACION por defecto
                registro_final['ESTADO'] = 'OPERACION'
            
            # 2. Asegurar TIPO_PROYECTO - preservar valor de datos_excel si existe
            # Si vino del Excel 'Tipo inversión', siempre priorizarlo sobre la clasificación
            if registro_final.get('_TIPO_PROYECTO_EXCEL'):
                registro_final['TIPO_PROYECTO'] = registro_final.get('_TIPO_PROYECTO_EXCEL')
            elif not registro_final.get('TIPO_PROYECTO'):
                # Fallback: generar desde UC si no hay valor
                uc = registro_final.get('UC', '')
                if uc:
                    tipo_proyecto = self.clasificador._generar_tipo_proyecto_desde_nivel_tension(uc)
                    if tipo_proyecto:
                        registro_final['TIPO_PROYECTO'] = tipo_proyecto
            
            # 3. Asegurar que las fechas estén en el formato correcto
            for campo_fecha in ['FECHA_INSTALACION', 'FECHA_OPERACION']:
                if campo_fecha in registro_final and registro_final[campo_fecha]:
                    registro_final[campo_fecha] = self.clasificador._formatear_fecha(
                        registro_final[campo_fecha]
                    )
            
            # 4. Asegurar ID_MERCADO siempre sea 161 (valor constante del sistema)
            registro_final['ID_MERCADO'] = '161'
            
            # 5. Limpiar campos que deben ir vacíos
            # OT_MAXIMO debe ir vacío ya que el Excel no trae información válida para este campo
            registro_final['OT_MAXIMO'] = ''
            
            # 5b. Asegurar SALINIDAD siempre sea "NO" (valor constante del sistema)
            registro_final['SALINIDAD'] = 'NO'
            
            # 6. Preservar CLASIFICACION_MERCADO que ya viene mapeado desde el campo Poblacion del Excel
            # El campo CLASIFICACION_MERCADO ya se mapeó correctamente desde "Poblacion" en la transformación inicial
            # Solo necesitamos asegurar que se preserve el valor existente
            if not registro_final.get('CLASIFICACION_MERCADO'):
                registro_final['CLASIFICACION_MERCADO'] = ''
            
            # 6b. Corregir TIPO_ADECUACION para quitar tildes (requerimiento del aplicativo)
            tipo_adecuacion = registro_final.get('TIPO_ADECUACION', '')
            if tipo_adecuacion:
                conversiones_tipo_adecuacion = {
                    'RETENCIÓN': 'RETENCION',
                    'SUSPENSIÓN': 'SUSPENSION',
                    'retención': 'RETENCION',
                    'suspensión': 'SUSPENSION',
                    'Retención': 'RETENCION',
                    'Suspensión': 'SUSPENSION'
                }
                registro_final['TIPO_ADECUACION'] = conversiones_tipo_adecuacion.get(
                    tipo_adecuacion, tipo_adecuacion.upper()
                )
            
            # 7. EMPRESA: para TXT NUEVO debe ser fijo 'CENS'
            # Nota: Este método también es usado por BAJA, pero el valor se aplica/forza más adelante
            registro_final['EMPRESA'] = 'CENS'
            
            # 8. REGLA CRÍTICA: GRUPO debe ser siempre "ESTRUCTURAS EYT" (no viene del Excel)
            registro_final['GRUPO'] = 'ESTRUCTURAS EYT'
            
            # 9. Aplicar valores por defecto para campos críticos vacíos
            valores_defecto = {
                'TIPO': 'PRIMARIO',  # Cambiado de SECUNDARIO a PRIMARIO
                'CLASE': 'POSTE',
                'USO': 'DISTRIBUCION ENERGIA',
                'PORCENTAJE_PROPIEDAD': '100',
                'ESTADO': '',  # Campo ESTADO debe estar vacío según el formato
            }
            
            for campo, valor_defecto in valores_defecto.items():
                if campo not in registro_final or not registro_final[campo]:
                    registro_final[campo] = valor_defecto
            
            datos_preparados.append(registro_final)
        
        return datos_preparados

    def _extraer_codigo_operativo(self, registro_transformado: Dict, registro_excel: Dict) -> str:
        """
        Extrae un código operativo válido del tipo 'Z' seguido solo por dígitos (p.ej. Z238163)
        desde cualquier campo tanto del registro transformado como del registro crudo del Excel.

        - Evita falsos positivos (p.ej., 'ZULC1').
        - Acepta que el código esté embebido en otra cadena (lo extrae por regex).
        - Prioriza campos típicos y luego escanea todo el registro.

        Returns: código (str) o '' si no encuentra.
        """
        # Acepta formatos como: Z123456, Z-123456, Z 123456 (con espacios o guiones), y normaliza a Z####
        patron = re.compile(r"Z\s*-?\s*(\d{3,})", re.IGNORECASE)

        def normalizar(v):
            if v is None:
                return ''
            try:
                s = str(v).strip()
            except Exception:
                return ''
            return s

        # 1) Revisar campos más probables en EXCEL y TRANSFORMADO
        candidatos = []
        claves_excel = ['Código FID_rep', 'Codigo FID_rep', 'CODIGO_FID_REP', 'FID_REP', 'FID_ANTERIOR', 'FID', 'ENLACE', 'PROYECTO', 'COORDENADA_X', 'COORDENADA_Y']
        for k in claves_excel:
            if isinstance(registro_excel, dict) and k in registro_excel:
                candidatos.append(normalizar(registro_excel.get(k)))
            if isinstance(registro_transformado, dict) and k in registro_transformado:
                candidatos.append(normalizar(registro_transformado.get(k)))

        # 2) Si no se encontró en campos típicos, escanear TODOS los valores
        if isinstance(registro_excel, dict):
            for v in registro_excel.values():
                candidatos.append(normalizar(v))
        if isinstance(registro_transformado, dict):
            for v in registro_transformado.values():
                candidatos.append(normalizar(v))

        # 3) Buscar primer match del patrón Z+digitos
        for val in candidatos:
            if not val:
                continue
            m = patron.search(val)
            if m:
                # Normalizar a 'Z' + solo dígitos
                return f"Z{m.group(1)}".upper().strip()
        return ''

    def generar_txt(self, usar_modular=False):
        """
        Genera archivo TXT con los datos transformados (estructura completa) - SOLO REGISTROS SIN FID_rep
        
        Args:
            usar_modular (bool): Si True, usa la nueva implementación modular. 
                               Por defecto False para mantener compatibilidad.
        """
        # MIGRADO: Redirigir siempre al método modular optimizado
        return self.generar_txt_modular()

    def _normalize_col_name(self, s):
        if s is None:
            return ''
        ns = str(s)
        ns = ns.replace('\n', ' ').replace('\r', ' ')
        ns = ns.replace('_', ' ')
        ns = re.sub(r"\s+", ' ', ns)
        ns = ns.strip().lower()
        trans = str.maketrans('áéíóúÁÉÍÓÚ', 'aeiouAEIOU')
        ns = ns.translate(trans)
        return ns

    def generar_txt_baja(self):
        """
        Genera archivo TXT con datos filtrados por 'Código FID_rep' válido,
        siguiendo exactamente el mismo flujo que generar_txt()
        """
        # MIGRADO: Redirigir al generador modular optimizado
        return self.generar_txt_baja_modular()

    def generar_xml_baja(self):
        """
        Genera archivo XML de configuración para BAJA, alineado con el TXT BAJA.
        Estructura exacta de campos (en este orden):
        - G3E_FID
        - COOR_GPS_LON
        - COOR_GPS_LAT
        Para cada campo: Componente=CCOMUN y Atributo=igual al nombre del campo.
        """
        # MIGRADO: Redirigir al generador modular optimizado
        return self.generar_xml_baja_modular()
            

    
    def _validar_archivo_txt(self, filepath):
        """
        Valida que el archivo TXT generado esté correctamente formateado para carga masiva
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                raise Exception("El archivo está vacío")
            
            # Verificar que todas las líneas tengan el mismo número de campos
            header_fields = lines[0].strip().split('|')
            num_fields = len(header_fields)
            
            # Validaciones específicas para carga masiva
            errores = []
            
            for i, line in enumerate(lines[1:], start=2):
                line_clean = line.strip()
                if not line_clean:  # Saltar líneas vacías
                    continue
                    
                fields = line_clean.split('|')
                
                # Verificar número de campos
                if len(fields) != num_fields:
                    errores.append(f"Línea {i}: tiene {len(fields)} campos, se esperaban {num_fields}")
                
                # Verificar que no haya saltos de línea dentro de los campos
                for j, field in enumerate(fields):
                    if '\n' in field or '\r' in field:
                        errores.append(f"Línea {i}, Campo {header_fields[j]}: contiene saltos de línea")
                    
                    # Verificar que no haya pipes dentro de los campos
                    if '|' in field.replace('|', ''):  # Esto detecta pipes adicionales
                        errores.append(f"Línea {i}, Campo {header_fields[j]}: contiene separadores pipe internos")
                
                # Validar campos críticos específicos (según tipo de archivo)
                try:
                    header_clean = [h.lstrip('\ufeff') for h in header_fields]
                    es_baja_g3e = header_clean == ['G3E_FID'] or header_clean == ['G3E_FID', 'ESTADO'] or header_clean == ['G3E_FID', 'ESTADO', 'FECHA_FUERA_OPERACION']
                    es_baja_ant = header_clean and header_clean[0] == 'FID_ANTERIOR'
                    
                    # Detectar archivos LÍNEA/CONDUCTOR por headers característicos
                    # Buscar si alguno de los headers clave de LÍNEA está presente
                    keywords_linea = ['coor_gps_lat', 'coor_gps_lon', 'Identificador_1', 'Identificador_2', 'Coordenada_Y2', 'Coordenada_X2']
                    es_linea = any(keyword in header_clean for keyword in keywords_linea)
                    es_norma = 'NORMA' in header_clean
                    
                    # DEBUG: Mostrar detección solo para primera línea
                    if i == 2:  # Primera línea de datos
                        print("🔍 DEBUG Validación TXT:")
                        print(f"   Headers: {header_clean[:10]}...")
                        print(f"   es_baja_g3e={es_baja_g3e}, es_baja_ant={es_baja_ant}")
                        print(f"   es_linea={es_linea}, es_norma={es_norma}")

                    if es_baja_g3e:
                        # BAJA nuevo formato: una, dos o tres columnas (G3E_FID[, ESTADO[, FECHA_FUERA_OPERACION]]) sin validar coordenadas
                        if len(header_clean) == 1 and len(fields) != 1:
                            errores.append(f"Línea {i}: se esperaba 1 campo (G3E_FID) y se encontraron {len(fields)}")
                        if len(header_clean) == 2 and len(fields) != 2:
                            errores.append(f"Línea {i}: se esperaban 2 campos (G3E_FID|ESTADO) y se encontraron {len(fields)}")
                        if len(header_clean) == 3 and len(fields) != 3:
                            errores.append(f"Línea {i}: se esperaban 3 campos (G3E_FID|ESTADO|FECHA_FUERA_OPERACION) y se encontraron {len(fields)}")
                    elif es_baja_ant:
                        # Formato antiguo de BAJA con coordenadas: mantener validación existente
                        if len(fields) >= 3:
                            lat = fields[1]
                            lon = fields[2]
                            if lat and lon:
                                float(lat.replace(',', '.'))
                                float(lon.replace(',', '.'))
                    elif es_linea:
                        # Archivos LÍNEA/CONDUCTOR: validar campos específicos
                        # Buscar índices de campos críticos (nombres de BD Oracle)
                        idx_id1 = header_clean.index('Identificador_1') if 'Identificador_1' in header_clean else -1
                        idx_id2 = header_clean.index('Identificador_2') if 'Identificador_2' in header_clean else -1
                        idx_lat = header_clean.index('coor_gps_lat') if 'coor_gps_lat' in header_clean else -1
                        idx_lon = header_clean.index('coor_gps_lon') if 'coor_gps_lon' in header_clean else -1
                        idx_uc = header_clean.index('uc') if 'uc' in header_clean else -1
                        
                        # Validar identificadores no vacíos
                        if idx_id1 >= 0 and idx_id1 < len(fields):
                            if not fields[idx_id1] or fields[idx_id1].strip() == '':
                                errores.append(f"Línea {i}: Identificador_1 está vacío")
                        
                        if idx_id2 >= 0 and idx_id2 < len(fields):
                            if not fields[idx_id2] or fields[idx_id2].strip() == '':
                                errores.append(f"Línea {i}: Identificador_2 está vacío")
                        
                        # Validar coordenadas si existen (formato decimal válido)
                        if idx_lat >= 0 and idx_lat < len(fields) and fields[idx_lat]:
                            try:
                                float(fields[idx_lat].replace(',', '.'))
                            except ValueError:
                                errores.append(f"Línea {i}: coor_gps_lat no es un número válido")
                        
                        if idx_lon >= 0 and idx_lon < len(fields) and fields[idx_lon]:
                            try:
                                float(fields[idx_lon].replace(',', '.'))
                            except ValueError:
                                errores.append(f"Línea {i}: coor_gps_lon no es un número válido")
                        
                        # Validar UC no vacía (la regla de DESMANTELADO se valida antes de generar el archivo)
                        if idx_uc >= 0 and idx_uc < len(fields):
                            if not fields[idx_uc] or fields[idx_uc].strip() == '':
                                # UC vacía solo es válida si es DESMANTELADO (sin identificadores)
                                tiene_id1 = idx_id1 >= 0 and idx_id1 < len(fields) and fields[idx_id1] and fields[idx_id1].strip()
                                tiene_id2 = idx_id2 >= 0 and idx_id2 < len(fields) and fields[idx_id2] and fields[idx_id2].strip()
                                if tiene_id1 or tiene_id2:
                                    errores.append(f"Línea {i}: uc vacía pero tiene identificadores (no es DESMANTELADO)")
                    elif es_norma:
                        # Archivos NORMA: validar campos específicos
                        # No validar coordenadas en archivos NORMA
                        pass
                    else:
                        # Archivos ESTRUCTURAS normales: validar coordenadas X/Y
                        coord_x = fields[0] if fields and fields[0] else '0'
                        coord_y = fields[1] if len(fields) > 1 and fields[1] else '0'
                        float(coord_x.replace(',', '.'))
                        float(coord_y.replace(',', '.'))
                except (ValueError, IndexError):
                    if not es_linea and not es_norma:  # Solo reportar error de coordenadas si NO es LÍNEA ni NORMA
                        errores.append(f"Línea {i}: coordenadas inválidas")
            
            # Verificar encoding UTF-8
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    f.read()
            except UnicodeDecodeError:
                errores.append("El archivo contiene caracteres no UTF-8")
            
            # Verificar tamaño del archivo (no debe ser excesivamente grande)
            import os
            file_size = os.path.getsize(filepath)
            if file_size > 50 * 1024 * 1024:  # 50MB
                errores.append(f"El archivo es muy grande ({file_size/1024/1024:.1f}MB), podría causar problemas en carga masiva")
            
            if errores:
                raise Exception(f"Errores de validación encontrados: {'; '.join(errores[:5])}")  # Mostrar solo los primeros 5
            
            return True
            
        except Exception as e:
            raise Exception(f"Error validando archivo TXT: {str(e)}")
    
    def generar_resumen_archivo(self, filepath):
        """
        Genera un resumen del archivo para verificación antes de carga masiva
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return {"error": "Archivo vacío"}
            
            header_fields = lines[0].strip().split('|')
            num_registros = len(lines) - 1  # Excluir header
            
            # Análisis básico
            resumen = {
                "archivo": os.path.basename(filepath),
                "total_registros": num_registros,
                "total_campos": len(header_fields),
                "campos": header_fields,
                "tamaño_archivo_kb": round(os.path.getsize(filepath) / 1024, 2),
                "encoding": "UTF-8",
                "separador": "|"
            }
            
            # Muestra de los primeros 3 registros
            registros_muestra = []
            for i, line in enumerate(lines[1:4], start=1):  # Primeros 3 registros
                if line.strip():
                    fields = line.strip().split('|')
                    registro_dict = {}
                    for j, field in enumerate(fields):
                        if j < len(header_fields):
                            registro_dict[header_fields[j]] = field[:50] + '...' if len(field) > 50 else field
                    registros_muestra.append(f"Registro {i}: {registro_dict}")
            
            resumen["muestra_registros"] = registros_muestra
            
            return resumen
            
        except Exception as e:
            return {"error": f"Error generando resumen: {str(e)}"}
    
    def generar_norma_txt(self):
        """
        Genera archivo TXT de norma con datos desde BD para bajas y Excel para el resto.
        
        ENLACE|NORMA|GRUPO|CIRCUITO|CODIGO_TRAFO|MACRONORMA|CANTIDAD|TIPO_ADECUACION
        
        Para BAJAS (detectadas por código operativo Z... en hoja Estructuras):
        - Resuelve FID desde código operativo
        - Consulta BD (ccomun JOIN norma) por FID
        - Hace merge campo a campo: si BD trae valor no vacío, lo usa; sino conserva Excel
        
        Para NO-BAJAS: usa valores del Excel directamente
        """
        # MIGRADO: Redirigir al generador modular optimizado
        return self.generar_norma_txt_modular()

            # 1) Intentar leer hoja de Normas explícita del Excel como fuente preferida
            registros_norma = []
            try:
                archivo_path = self.proceso.archivo_excel.path
                # Candidatos de nombre de hoja
                hojas_candidatas = []
                try:
                    hojas = pd.ExcelFile(archivo_path).sheet_names
                    hojas_candidatas = [
                        h for h in hojas if str(h).strip().lower() in (
                            'norma de expansion', 'normas', 'norma', 'norma de reposicion', 'norma de reposición'
                        )
                    ]
                except Exception:
                    hojas_candidatas = []

                if hojas_candidatas:
                    nombre_hoja_norma = hojas_candidatas[0]
                    # Detectar fila de encabezado 0-2
                    df_norma = None
                    for header_row in [0, 1, 2]:
                        try:
                            temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja_norma, header=header_row)
                            valid_headers = [c for c in temp_df.columns if not str(c).startswith('Unnamed:') and str(c).strip().lower() != 'nan']
                            if len(valid_headers) >= 3:
                                df_norma = temp_df
                                break
                        except Exception:
                            continue
                    if df_norma is None:
                        df_norma = pd.read_excel(archivo_path, sheet_name=nombre_hoja_norma, header=0)

                    # Normalizar y mapear
                    for _, row in df_norma.iterrows():
                        def g(*keys):
                            for k in keys:
                                if k in df_norma.columns and pd.notna(row.get(k)) and str(row.get(k)).strip():
                                    return str(row.get(k)).strip()
                            return ''

                        reg = {
                            'ENLACE': g('Identificador', 'ENLACE', 'Pm', 'PM', 'Identificador PM'),
                            'NORMA': g('Norma', 'NORMA'),
                            'GRUPO': g('GRUPO', 'Grupo'),
                            'CIRCUITO': g('CIRCUITO', 'Circuito') or getattr(self.proceso, 'circuito', '') or '',
                            'CODIGO_TRAFO': g('Codigo. Transformador (1T,2T,3T,4T,5T)', 'CODIGO_TRAFO', 'Codigo Trafo'),
                            'MACRONORMA': g('MACRONORMA', 'Macronorma'),
                            'CANTIDAD': g('Altura', 'CANTIDAD'),
                            'TIPO_ADECUACION': g('Disposicion', 'TIPO_ADECUACION'),
                        }
                        # Solo agregar si al menos NORMA o ENLACE están presentes
                        if reg['NORMA'] or reg['ENLACE']:
                            registros_norma.append(reg)
            except Exception as e:
                print(f"DEBUG leer hoja Norma: {e}")

            # 1b) Fallback: usar datos_norma procesados o mapear desde datos_excel
            if not registros_norma:
                if self.proceso.datos_norma:
                    registros_norma = self._preparar_datos_norma_finales(self.proceso.datos_norma)
                else:
                    if not self.proceso.datos_excel:
                        raise Exception("No hay datos para generar archivo de norma")
                    mapper = DataMapper(self.tipo_estructura)
                    registros_norma = self._preparar_datos_norma_finales(
                        mapper.mapear_a_norma(self.proceso.datos_excel, getattr(self.proceso, 'circuito', '') or '')
                    )

            # 2) Detectar bajas: buscar código operativo Z###### en hoja "Estructuras_N1-N2-N3"
            enlace_a_codigo_op = {}
            try:
                archivo_path = self.proceso.archivo_excel.path
                print(f"[TXT Norma] Leyendo archivo Excel para detectar bajas: {archivo_path}")
                
                # Leer todas las hojas
                df_dict = pd.read_excel(archivo_path, sheet_name=None)
                
                # Buscar la hoja de estructuras
                nombre_hoja_estructuras = None
                if 'Estructuras_N1-N2-N3' in df_dict:
                    nombre_hoja_estructuras = 'Estructuras_N1-N2-N3'
                else:
                    # Buscar hojas que contengan "Estructura" en el nombre
                    for hoja in df_dict.keys():
                        if 'estructura' in str(hoja).lower():
                            nombre_hoja_estructuras = hoja
                            break
                
                if nombre_hoja_estructuras:
                    print(f"[TXT Norma] Hoja de estructuras encontrada: '{nombre_hoja_estructuras}'")
                    
                    # Leer la hoja de estructuras SIN PROCESAR ENCABEZADOS primero para detectar formato
                    df_test = pd.read_excel(archivo_path, sheet_name=nombre_hoja_estructuras, nrows=2)
                    tiene_encabezados = not all('Unnamed:' in str(col) for col in df_test.columns)
                    
                    if not tiene_encabezados:
                        print("[TXT Norma] ⚠️ Excel sin encabezados detectado. Leyendo con header=None")
                        # Leer sin encabezados
                        df_estructuras = pd.read_excel(archivo_path, sheet_name=nombre_hoja_estructuras, header=None)
                    else:
                        # Leer con encabezados normales
                        df_estructuras = pd.read_excel(archivo_path, sheet_name=nombre_hoja_estructuras)
                        df_estructuras.columns = [str(col).strip() for col in df_estructuras.columns]
                    
                    print(f"[TXT Norma] Total filas en estructuras: {len(df_estructuras)}")
                    
                    # Iterar todas las filas y buscar código operativo Z##### en CUALQUIER celda
                    for idx, row in df_estructuras.iterrows():
                        enlace = None
                        codigo_op = None
                        
                        # Buscar en todas las celdas de la fila
                        for col_idx, val in enumerate(row):
                            if pd.isna(val):
                                continue
                            
                            try:
                                val_str = str(val).strip().upper()
                            except Exception:
                                continue
                            
                            if not val_str:
                                continue
                            
                            # Buscar código operativo Z##### (mínimo 5 dígitos)
                            if not codigo_op:
                                m = re.search(r"Z\s*-?\s*(\d{5,})", val_str)
                                if m:
                                    codigo_op = f"Z{m.group(1)}"
                            
                            # Buscar ENLACE (formato PXX, PXXX, etc.)
                            if not enlace:
                                # Patrón: P seguido de dígitos, puede estar al inicio o con espacios
                                m_enlace = re.match(r"^P\d+$", val_str)
                                if m_enlace:
                                    enlace = val_str
                        
                        # Si encontramos ambos en la misma fila, mapear
                        if enlace and codigo_op:
                            enlace_a_codigo_op[enlace] = codigo_op
                            print(f"[TXT Norma] ✓ Detectado BAJA: ENLACE={enlace} -> codigo_op={codigo_op}")
                
                else:
                    print("[TXT Norma] ADVERTENCIA: No se encontró hoja de estructuras. No se detectarán bajas.")
            
            except Exception as e:
                print(f"[TXT Norma] ERROR al detectar bajas: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"[TXT Norma] Total bajas detectadas: {len(enlace_a_codigo_op)}")

            # 3) Escribir archivo con merge BD para bajas Y validación campo por campo para no-bajas
            # ORDEN IGUAL QUE XML NORMA (sin ENLACE)
            campos_orden = ['NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO', 'MACRONORMA', 'CANTIDAD', 'TIPO_ADECUACION']

            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write('|'.join(campos_orden) + '\n')

                for reg in registros_norma:
                    # Base: datos del Excel
                    reg_out = {c: str(reg.get(c, '') or '').strip() for c in campos_orden}
                    
                    enlace_upper = reg_out.get('ENLACE', '').strip().upper()
                    codigo_op = enlace_a_codigo_op.get(enlace_upper)
                    
                    # CASO 1: Si es BAJA (tiene código operativo) - merge BD completo
                    if codigo_op:
                        try:
                            # Resolver FID desde código operativo
                            fid_real = OracleHelper.obtener_fid_desde_codigo_operativo(codigo_op)
                            if fid_real:
                                # Consultar BD
                                datos_bd = OracleHelper.obtener_norma_por_fid(fid_real) or {}
                                # Merge campo a campo: BD tiene prioridad si no vacío
                                for campo in ['NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO', 'MACRONORMA', 'CANTIDAD', 'TIPO_ADECUACION']:
                                    val_bd = str(datos_bd.get(campo, '') or '').strip()
                                    if val_bd:
                                        reg_out[campo] = val_bd
                                print(f"[TXT Norma] BAJA ENLACE={reg_out['ENLACE']}: merge BD aplicado")
                            else:
                                print(f"[TXT Norma] BAJA ENLACE={enlace_upper}: no se resolvió FID para {codigo_op}")
                        except Exception as e:
                            print(f"[TXT Norma] ERROR enriqueciendo BAJA {enlace_upper}: {e}")
                    
                    # CASO 2: Si NO es BAJA - validación campo por campo con BD
                    else:
                        try:
                            # Buscar FID desde ENLACE
                            fid_desde_enlace = OracleHelper.obtener_fid_desde_enlace(enlace_upper)
                            
                            if fid_desde_enlace:
                                # Consultar datos de norma en BD
                                datos_bd = OracleHelper.obtener_norma_por_fid(fid_desde_enlace) or {}
                                
                                # Validación campo por campo: solo cambiar si Excel != BD
                                cambios = []
                                for campo in ['NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO', 'MACRONORMA', 'CANTIDAD', 'TIPO_ADECUACION']:
                                    val_excel = reg_out.get(campo, '').strip()
                                    val_bd = str(datos_bd.get(campo, '') or '').strip()
                                    
                                    # Solo reemplazar si:
                                    # 1. BD tiene valor (no vacío)
                                    # 2. Excel != BD
                                    if val_bd and val_excel != val_bd:
                                        cambios.append(f"{campo}: '{val_excel}' → '{val_bd}'")
                                        reg_out[campo] = val_bd
                                
                                if cambios:
                                    print(f"[TXT Norma] VALIDACIÓN ENLACE={enlace_upper}: {', '.join(cambios)}")
                            else:
                                # No existe en BD, usar valores del Excel
                                print(f"[TXT Norma] ENLACE={enlace_upper}: no encontrado en BD, usando datos del Excel")
                        except Exception as e:
                            print(f"[TXT Norma] ERROR validando ENLACE {enlace_upper}: {e}")
                    
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
                    
                    if not reg_out.get('MACRONORMA'):
                        reg_out['MACRONORMA'] = ''

                    # Escribir línea
                    valores = [self._limpiar_valor_para_txt(reg_out.get(c, '')) for c in campos_orden]
                    f.write('|'.join(valores) + '\n')

            # Validación básica
            self._validar_archivo_norma_txt(filepath)
            return filename
        except Exception as e:
            raise Exception(f"Error generando archivo TXT de norma: {str(e)}")
    
    def _validar_archivo_norma_txt(self, filepath):
        """
        Valida que el archivo TXT de norma esté correctamente formateado
        """
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                
            if len(lines) < 2:
                raise Exception("El archivo no tiene contenido suficiente")
            
            # Validar que cada línea tenga el número correcto de pipes
            num_campos = len(lines[0].strip().split('|'))
            
            for i, line in enumerate(lines[1:], start=2):
                line_stripped = line.strip()
                if not line_stripped:  # Ignorar líneas vacías
                    continue
                    
                campos = line_stripped.split('|')
                if len(campos) != num_campos:
                    print(f"Advertencia línea {i}: esperados {num_campos} campos, encontrados {len(campos)}")
                    print(f"Línea problemática: {line_stripped[:100]}...")
                    
        except Exception as e:
            print(f"Error validando archivo TXT de norma: {str(e)}")
    
    def _debe_incluir_fid_anterior(self, datos_finales):
        """
        Determina si se debe incluir la columna FID_ANTERIOR en el TXT de expansión
        
        Reglas:
        - Si es T2 o T4: La columna FID_ANTERIOR desaparece (no se incluye)
        - Si es T1 o T3: La columna FID_ANTERIOR debe estar presente
        
        Returns:
            bool: True si debe incluir FID_ANTERIOR, False si no
        """
        if not datos_finales:
            return False
        
        # Verificar TIPO_PROYECTO en los datos
        for registro in datos_finales:
            tipo_proyecto = registro.get('TIPO_PROYECTO', '').strip().upper()
            
            # Si encuentra T1 o T3, debe incluir FID_ANTERIOR
            if tipo_proyecto in ['T1', 'T3']:
                return True
            # Si encuentra T2 o T4, no debe incluir FID_ANTERIOR
            elif tipo_proyecto in ['T2', 'T4']:
                return False
        
        # Por defecto, incluir FID_ANTERIOR si no se puede determinar
        return True
    
    def _preparar_datos_norma_finales(self, datos_norma):
        """Prepara los datos de norma aplicando transformaciones específicas"""
        datos_preparados = []
        
        for registro in datos_norma:
            registro_final = registro.copy()
            
            # 1. Corregir GRUPO para norma - debe ser "NODO ELECTRICO" para expansión
            # Con clasificación automática, verificamos el TIPO_PROYECTO del registro
            tipo_proyecto = registro_final.get('TIPO_PROYECTO', '')
            if 'EXPANSION' in str(tipo_proyecto).upper():
                registro_final['GRUPO'] = 'NODO ELECTRICO'
            
            # 2. Corregir TIPO_ADECUACION para quitar tildes
            tipo_adecuacion = registro_final.get('TIPO_ADECUACION', '')
            if tipo_adecuacion:
                conversiones_tipo_adecuacion = {
                    'RETENCIÓN': 'RETENCION',
                    'SUSPENSIÓN': 'SUSPENSION',
                    'retención': 'RETENCION',
                    'suspensión': 'SUSPENSION',
                    'Retención': 'RETENCION',
                    'Suspensión': 'SUSPENSION'
                }
                registro_final['TIPO_ADECUACION'] = conversiones_tipo_adecuacion.get(
                    tipo_adecuacion, tipo_adecuacion.upper()
                )
            
            # 3. Asegurar formato de fecha
            fecha = registro_final.get('FECHA_INSTALACION', '')
            if fecha:
                registro_final['FECHA_INSTALACION'] = self.clasificador._formatear_fecha(fecha)
            
            # 4. Limpiar campos que no deben ir en norma pero podrían estar presentes
            campos_norma_validos = [
                'ENLACE', 'NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO',
                'CANTIDAD','MACRONORMA', 'FECHA_INSTALACION', 'TIPO_ADECUACION', 'OBSERVACIONES'
            ]
            
            # Solo mantener campos válidos para norma
            registro_norma_limpio = {}
            for campo in campos_norma_validos:
                registro_norma_limpio[campo] = registro_final.get(campo, '')
            
            datos_preparados.append(registro_norma_limpio)
        
        return datos_preparados

    def generar_norma_xml(self):
        """Genera archivo XML específico para la norma con estructura de configuración exacta"""
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom import minidom
            
            filename = self._generar_nombre_archivo_con_indice('norma_nuevo', 'xml')
            filepath = os.path.join(self.base_path, filename)
            
            # Crear estructura XML
            root = Element('Configuracion')
            
            # Agregar elementos básicos
            elemento = SubElement(root, 'Elemento')
            elemento.text = 'Poste'
            
            comp_repetitiva = SubElement(root, 'ComponenteRepetitiva')
            comp_repetitiva.text = 'Norma'
            
            # Crear sección de campos
            campos = SubElement(root, 'Campos')
            
            # Configuración de campos para norma XML (SIN ENLACE)
            # NORMA|GRUPO|CIRCUITO|CODIGO_TRAFO|MACRONORMA|CANTIDAD|TIPO_ADECUACION
            campos_config = [
                {'nombre': 'NORMA', 'componente': 'NORMA', 'atributo': 'NORMA'},
                {'nombre': 'GRUPO', 'componente': 'NORMA', 'atributo': 'GRUPO'},
                {'nombre': 'CIRCUITO', 'componente': 'NORMA', 'atributo': 'CIRCUITO'},
                {'nombre': 'CODIGO_TRAFO', 'componente': 'NORMA', 'atributo': 'CODIGO_TRAFO'},
                {'nombre': 'MACRONORMA', 'componente': 'NORMA', 'atributo': 'MACRONORMA'},
                {'nombre': 'CANTIDAD', 'componente': 'NORMA', 'atributo': 'CANTIDAD'},
                {'nombre': 'TIPO_ADECUACION', 'componente': 'NORMA', 'atributo': 'TIPO_ADECUACION'},
            ]
            
            # Agregar cada campo
            for i, campo_config in enumerate(campos_config):
                campo_elem = SubElement(campos, f'Campo{i}')
                
                nombre = SubElement(campo_elem, 'Nombre')
                nombre.text = campo_config['nombre']
                
                componente = SubElement(campo_elem, 'Componente')
                componente.text = campo_config['componente']
                
                atributo = SubElement(campo_elem, 'Atributo')
                atributo.text = campo_config['atributo']
            
            # Formatear XML
            rough_string = tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")
            
            # Eliminar la declaración XML <?xml version="1.0" ?>
            lines = pretty_xml.split('\n')
            if lines[0].startswith('<?xml'):
                lines = lines[1:]  # Eliminar la primera línea con la declaración XML
            pretty_xml_sin_declaracion = '\n'.join(lines)
            
            # Escribir archivo
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(pretty_xml_sin_declaracion)
            
            return filename
            
        except Exception as e:
            raise Exception(f"Error generando archivo XML de norma: {str(e)}")
    
    def _get_tipo_campo_norma(self, campo):
        """Determina el tipo de dato para campos de norma en XML"""
        if campo in ['CANTIDAD']:
            return 'numero'
        elif campo in ['FECHA_INSTALACION']:
            return 'fecha'
        else:
            return 'texto'

    def generar_xml(self):
        """Genera archivo XML NUEVO alineado 1:1 con la estructura del TXT NUEVO (solo registros sin FID)."""
        # MIGRADO: Redirigir al método modular optimizado
        return self.generar_xml_modular()

    # ============================================================================
    # FUNCIONES PARA CONDUCTORES (LÍNEA)
    # ============================================================================

    def generar_txt_linea(self):
        """
        Genera archivo TXT con datos de conductores (NUEVO) desde la hoja 'Conductor_N1-N2-N3'.
        
        Reglas de negocio:
        - NUEVO: NO tiene "Código FID GIT" O (tiene ambos "Código FID GIT" y "Unidad Constructiva")
        - Se excluyen registros con "Código FID GIT" pero SIN "Unidad Constructiva" (van a BAJA)
        - Validación: "Unidad Constructiva" NO puede estar vacía (excepto para DESMANTELADOS)
        - Para REPOSICIÓN (tiene ambos campos), validar contra BD y reemplazar campos si difieren
        """
        try:
            filename = self._generar_nombre_archivo_con_indice('conductores_linea', 'txt')
            filepath = os.path.join(self.base_path, filename)
            
            # 1. Leer datos desde la hoja "Conductor_N1-N2-N3"
            datos_conductor = self._leer_hoja_conductores()
            
            if not datos_conductor:
                raise Exception("No hay datos en la hoja 'Conductor_N1-N2-N3'")
            
            print(f"DEBUG generar_txt_linea: {len(datos_conductor)} registros leídos desde 'Conductor_N1-N2-N3'")
            
            # 2. Filtrar registros para NUEVO (excluir los que van a BAJA)
            datos_nuevo = []
            for i, registro in enumerate(datos_conductor):
                fid_git = self._extraer_campo_conductor(registro, 'codigo_fid_git')
                unidad_constructiva = self._extraer_campo_conductor(registro, 'unidad_constructiva')
                
                # DEBUG: Mostrar valores extraídos para cada registro
                print(f"🔍 Registro {i+1}: FID_GIT='{fid_git}', UC='{unidad_constructiva}'")
                
                # REGLA: Excluir si tiene FID pero NO tiene UC (estos van a BAJA)
                if fid_git and not unidad_constructiva:
                    print(f"   ❌ EXCLUIDO (tiene FID '{fid_git}' pero NO tiene UC) -> va a BAJA")
                    continue
                
                # VALIDACIÓN: UC no puede estar vacía (excepto DESMANTELADOS que ya fueron excluidos)
                if not fid_git and not unidad_constructiva:
                    print("   ⚠️ EXCLUIDO (sin FID y sin UC) - validación")
                    continue
                
                # Si llegamos aquí, es NUEVO
                print("   ✅ INCLUIDO como NUEVO")
                datos_nuevo.append(registro)
            
            print(f"DEBUG generar_txt_linea: {len(datos_nuevo)} registros clasificados como NUEVO de {len(datos_conductor)} totales")
            
            if not datos_nuevo:
                raise Exception("No hay registros NUEVO para generar archivo TXT Línea")
            
            # 3. Enriquecer datos de REPOSICIÓN desde Oracle
            datos_finales = self._enriquecer_conductores_reposicion(datos_nuevo)
            
            # 4. Mapear campos del Excel a campos de salida (nombres de BD Oracle)
            datos_mapeados = []
            for registro in datos_finales:
                # Mapear a nombres de columnas de BD Oracle (econ_pri_at + ccomun + cpropietario)
                reg_mapeado = {
                    # Campos de Excel que mantienen su nombre
                    'Tipo': self._extraer_campo_conductor(registro, 'tipo'),
                    'Clase': self._extraer_campo_conductor(registro, 'clase'),
                    'Calibre': self._extraer_campo_conductor(registro, 'calibre'),
                    'Número de conductores': self._extraer_campo_conductor(registro, 'numero_conductores'),
                    'Nivel de Tension': self._extraer_campo_conductor(registro, 'nivel_tension'),
                    'Fases': self._extraer_campo_conductor(registro, 'fases'),
                    'Identificador_1': self._extraer_campo_específico(registro, 'Identificador_1'),
                    'Identificador_2': self._extraer_campo_específico(registro, 'Identificador_2'),
                    
                    # Campos mapeados a nombres de BD Oracle
                    'coor_gps_lat': self._extraer_campo_conductor(registro, 'coordenada_y1'),  # Latitud Nodo 1
                    'coor_gps_lon': self._extraer_campo_conductor(registro, 'coordenada_x1'),  # Longitud Nodo 1
                    'Coordenada_Y2': self._extraer_campo_conductor(registro, 'coordenada_y2'),  # Latitud Nodo 2
                    'Coordenada_X2': self._extraer_campo_conductor(registro, 'coordenada_x2'),  # Longitud Nodo 2
                    'estado': '',  # Estado operativo - pendiente definir
                    'ubicacion': self._extraer_campo_conductor(registro, 'ubicacion'),
                    'codigo_material': self._extraer_campo_conductor(registro, 'codigo_material'),
                    'fecha_instalacion': self._extraer_campo_conductor(registro, 'fecha_instalacion'),
                    'fecha_operacion': '',  # Pendiente
                    'proyecto': self._extraer_campo_conductor(registro, 'proyecto'),
                    'empresa_origen': '',  # Pendiente
                    'observaciones': '',
                    'tipo_proyecto': self._extraer_campo_conductor(registro, 'tipo_proyecto'),
                    'id_mercado': '',
                    'clasificacion_mercado': '',
                    'uc': self._extraer_campo_conductor(registro, 'unidad_constructiva'),
                    'estado_salud': '',  # Pendiente
                    'ot_maximo': '',
                    'codigo_marcacion': '',
                    'salinidad': '',
                    'uso': 'DISTRIBUCION ENERGIA',  # Valor por defecto
                    'propietario_1': self.proceso.propietario_definido if hasattr(self.proceso, 'propietario_definido') and self.proceso.propietario_definido else '',
                    'porcentaje_prop_1': '100',
                    
                    # Campos adicionales
                    'Circuito': self.proceso.circuito if hasattr(self.proceso, 'circuito') and self.proceso.circuito else '',
                    'Municipio': self._extraer_campo_conductor(registro, 'municipio'),
                    'Poblacion': self._extraer_campo_conductor(registro, 'poblacion'),
                    'Codigo Inventario': self._extraer_campo_conductor(registro, 'codigo_inventario'),
                    'Longitud': '',  # Pendiente: calcular longitud del conductor
                }
                datos_mapeados.append(reg_mapeado)
            
            # 5. Definir encabezados en orden (nombres exactos de BD Oracle + campos Excel)
            encabezados = [
                # Campos de identificación y tipo
                'Tipo', 'Clase', 'codigo_material', 'Calibre',
                'Número de conductores', 'uso', 'Nivel de Tension',
                
                # Fechas
                'fecha_instalacion', 'fecha_operacion',
                
                # Estado y operación
                'estado', 'estado_salud', 'ot_maximo',
                
                # Propiedad
                'propietario_1', 'porcentaje_prop_1',
                
                # Ubicación y geografía
                'Circuito', 'Municipio', 'Poblacion', 'ubicacion',
                
                # Coordenadas de nodos
                'coor_gps_lat', 'coor_gps_lon',  # Nodo 1
                'Coordenada_Y2', 'Coordenada_X2',  # Nodo 2
                
                # Identificadores de nodos
                'Identificador_1', 'Identificador_2',
                
                # Características físicas
                'Longitud', 'Fases',
                
                # Clasificación
                'uc', 'tipo_proyecto', 'id_mercado', 'clasificacion_mercado',
                
                # Marcación y otros
                'codigo_marcacion', 'salinidad', 'Codigo Inventario',
                
                # Proyecto y observaciones
                'proyecto', 'empresa_origen', 'observaciones'
            ]
            
            # 6. Escribir archivo TXT
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                # Escribir encabezados
                f.write('|'.join(encabezados) + '\n')
                
                # Escribir datos
                for i, registro in enumerate(datos_mapeados):
                    valores = []
                    for campo in encabezados:
                        valor = registro.get(campo, '')
                        # Limpiar el valor
                        valor_limpio = self._limpiar_valor_para_txt(valor)
                        valores.append(valor_limpio)
                    f.write('|'.join(valores) + '\n')
            
            # 7. Validar el archivo generado
            self._validar_archivo_txt(filepath)
            
            print(f"✅ Archivo TXT Línea NUEVO generado exitosamente: {filename} con {len(datos_mapeados)} registros")
            return filename
            
        except Exception as e:
            raise Exception(f"Error generando archivo TXT Línea: {str(e)}")

    def generar_txt_baja_linea(self):
        """
        Genera archivo TXT de BAJA para conductores desde la hoja 'Conductor_N1-N2-N3'.
        
        Reglas de negocio:
        - BAJA: Tiene "Código FID GIT" pero NO tiene "Unidad Constructiva"
        - Campos: G3E_FID, ESTADO, FECHA_FUERA_OPERACION
        - ESTADO: Siempre "RETIRADO"
        - FECHA_FUERA_OPERACION: 
          * DESMANTELADO (sin Identificador): Fecha de hoy
          * REPOSICIÓN (con Identificador): Fecha Instalación del Excel
        """
        try:
            filename = self._generar_nombre_archivo_con_indice('conductores_linea_baja', 'txt')
            filepath = os.path.join(self.base_path, filename)
            
            # 1. Leer datos desde la hoja "Conductor_N1-N2-N3"
            datos_conductor = self._leer_hoja_conductores()
            
            if not datos_conductor:
                raise Exception("No hay datos en la hoja 'Conductor_N1-N2-N3'")
            
            print(f"DEBUG generar_txt_baja_linea: {len(datos_conductor)} registros leídos")
            
            # 2. Filtrar registros para BAJA (tiene FID pero NO UC)
            datos_baja = []
            for i, registro in enumerate(datos_conductor):
                fid_git = self._extraer_campo_conductor(registro, 'codigo_fid_git')
                unidad_constructiva = self._extraer_campo_conductor(registro, 'unidad_constructiva')
                
                # DEBUG: Mostrar valores extraídos
                print(f"🔍 Registro {i+1} BAJA: FID_GIT='{fid_git}', UC='{unidad_constructiva}'")
                
                # REGLA: Incluir solo si tiene FID pero NO tiene UC
                if fid_git and not unidad_constructiva:
                    print(f"   ✅ INCLUIDO como BAJA (FID: '{fid_git}', UC: vacía)")
                    datos_baja.append(registro)
                else:
                    print("   ❌ EXCLUIDO (por que no cumple regla: FID sin UC)")
            
            print(f"DEBUG generar_txt_baja_linea: {len(datos_baja)} registros clasificados como BAJA")
            
            if not datos_baja:
                print("⚠️ WARNING: No hay registros BAJA para generar archivo TXT Línea BAJA")
                # Retornar archivo vacío o lanzar excepción según preferencia
                raise Exception("No hay registros BAJA para generar archivo TXT Línea BAJA")
            
            # 3. Resolver G3E_FID (convertir código operativo a FID si es necesario)
            oracle_disponible = OracleHelper.test_connection()
            
            for i, registro in enumerate(datos_baja):
                codigo_git = self._extraer_campo_conductor(registro, 'codigo_fid_git')
                
                if codigo_git:
                    codigo_norm = str(codigo_git).strip()
                    
                    # Si el código empieza con 'Z', es código operativo y debe convertirse
                    if oracle_disponible and codigo_norm.upper().startswith('Z'):
                        fid_real = OracleHelper.obtener_fid_desde_codigo_operativo(codigo_norm)
                        if fid_real:
                            registro['G3E_FID'] = str(fid_real)
                            print(f"✅ Código operativo '{codigo_norm}' convertido a FID '{fid_real}'")
                        else:
                            # Si no se puede resolver, usar el código tal cual
                            registro['G3E_FID'] = self._limpiar_fid(codigo_norm)
                            print(f"⚠️ No se pudo resolver código operativo '{codigo_norm}', usando tal cual")
                    else:
                        # Si no empieza con Z, asumir que ya es FID
                        registro['G3E_FID'] = self._limpiar_fid(codigo_norm)
            
            # 4. Determinar FECHA_FUERA_OPERACION según tipo
            from datetime import datetime
            fecha_hoy = datetime.now().strftime('%d/%m/%Y')
            
            for i, registro in enumerate(datos_baja):
                # Siempre RETIRADO
                registro['ESTADO'] = 'RETIRADO'
                
                # Verificar si es REPOSICIÓN o DESMANTELADO
                identificador = self._extraer_campo_conductor(registro, 'identificador')
                
                if identificador and str(identificador).strip():
                    # REPOSICIÓN: usar Fecha Instalación
                    fecha_instalacion = self._extraer_campo_conductor(registro, 'fecha_instalacion')
                    registro['FECHA_FUERA_OPERACION'] = fecha_instalacion if fecha_instalacion else fecha_hoy
                    print(f"✅ REPOSICIÓN: FID {registro.get('G3E_FID')} -> FECHA={registro['FECHA_FUERA_OPERACION']}")
                else:
                    # DESMANTELADO: usar fecha de hoy
                    registro['FECHA_FUERA_OPERACION'] = fecha_hoy
                    print(f"✅ DESMANTELADO: FID {registro.get('G3E_FID')} -> FECHA={fecha_hoy}")
            
            # 5. Escribir archivo TXT
            encabezados = ['G3E_FID', 'ESTADO', 'FECHA_FUERA_OPERACION']
            
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                # Escribir encabezados
                f.write('|'.join(encabezados) + '\n')
                
                # Escribir datos
                for registro in datos_baja:
                    valores = []
                    for campo in encabezados:
                        valor = registro.get(campo, '')
                        valor_limpio = self._limpiar_valor_para_txt(valor)
                        valores.append(valor_limpio)
                    f.write('|'.join(valores) + '\n')
            
            # 6. Validar archivo generado
            self._validar_archivo_txt(filepath)
            
            print(f"✅ Archivo TXT Línea BAJA generado exitosamente: {filename} con {len(datos_baja)} registros")
            return filename
            
        except Exception as e:
            raise Exception(f"Error generando archivo TXT Línea BAJA: {str(e)}")

    def generar_xml_linea(self):
        """
        Genera archivo XML de configuración para LÍNEA (conductores NUEVO).
        Alineado 1:1 con generar_txt_linea() - DEBE coincidir exactamente con los encabezados del TXT.
        
        Encabezados TXT Línea:
        Tipo|Clase|codigo_material|Calibre|Número de conductores|uso|Nivel de Tension|
        fecha_instalacion|fecha_operacion|estado|estado_salud|ot_maximo|propietario_1|porcentaje_prop_1|
        Circuito|Municipio|Poblacion|ubicacion|coor_gps_lat|coor_gps_lon|Coordenada_Y2|Coordenada_X2|
        Identificador_1|Identificador_2|Longitud|Fases|uc|tipo_proyecto|id_mercado|clasificacion_mercado|
        codigo_marcacion|salinidad|Codigo Inventario|proyecto|empresa_origen|observaciones
        """
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom import minidom
            
            filename = self._generar_nombre_archivo_con_indice('conductores_linea', 'xml')
            filepath = os.path.join(self.base_path, filename)
            
            # 1. Contar registros NUEVO (NO FID O (FID+UC))
            datos_conductor = self._leer_hoja_conductores()
            registros_nuevo = 0
            
            if datos_conductor:
                for registro in datos_conductor:
                    fid_git = self._extraer_campo_conductor(registro, 'codigo_fid_git')
                    unidad_constructiva = self._extraer_campo_conductor(registro, 'unidad_constructiva')
                    
                    # NUEVO: NO tiene FID O (tiene ambos FID y UC)
                    if not fid_git or (fid_git and unidad_constructiva):
                        registros_nuevo += 1
            
            print(f"DEBUG: XML Línea - {registros_nuevo} registros NUEVO")
            
            # 2. Crear estructura XML según especificación
            root = Element('Configuracion')
            
            # Elemento principal
            elemento = SubElement(root, 'Elemento')
            elemento.text = 'Poste'
            
            # Contenedor de campos
            campos = SubElement(root, 'Campos')
            
            # 3. Definición de campos EXACTAMENTE como en TXT Línea
            # IMPORTANTE: Orden y nombres deben coincidir 1:1 con los encabezados del TXT
            # Campos que vienen de Oracle (tabla econ_pri_at + ccomun + cpropietario)
            campos_config = [
                # Campos de identificación y tipo (no están en Oracle, vienen del Excel)
                {'nombre': 'Tipo', 'componente': '', 'atributo': ''},
                {'nombre': 'Clase', 'componente': '', 'atributo': ''},
                {'nombre': 'codigo_material', 'componente': 'CCOMUN', 'atributo': 'CODIGO_MATERIAL'},
                {'nombre': 'Calibre', 'componente': '', 'atributo': ''},
                {'nombre': 'Número de conductores', 'componente': '', 'atributo': ''},
                {'nombre': 'uso', 'componente': 'ECON_PRI_AT', 'atributo': 'USO'},
                {'nombre': 'Nivel de Tension', 'componente': '', 'atributo': ''},
                
                # Fechas
                {'nombre': 'fecha_instalacion', 'componente': 'CCOMUN', 'atributo': 'FECHA_INSTALACION'},
                {'nombre': 'fecha_operacion', 'componente': 'CCOMUN', 'atributo': 'FECHA_OPERACION'},
                
                # Estado y operación
                {'nombre': 'estado', 'componente': 'CCOMUN', 'atributo': 'ESTADO'},
                {'nombre': 'estado_salud', 'componente': 'CCOMUN', 'atributo': 'ESTADO_SALUD'},
                {'nombre': 'ot_maximo', 'componente': 'CCOMUN', 'atributo': 'OT_MAXIMO'},
                
                # Propiedad
                {'nombre': 'propietario_1', 'componente': 'CPROPIETARIO', 'atributo': 'PROPIETARIO_1'},
                {'nombre': 'porcentaje_prop_1', 'componente': 'CPROPIETARIO', 'atributo': 'PORCENTAJE_PROP_1'},
                
                # Ubicación y geografía (no están en Oracle, vienen del Excel)
                {'nombre': 'Circuito', 'componente': '', 'atributo': ''},
                {'nombre': 'Municipio', 'componente': '', 'atributo': ''},
                {'nombre': 'Poblacion', 'componente': '', 'atributo': ''},
                {'nombre': 'ubicacion', 'componente': 'CCOMUN', 'atributo': 'UBICACION'},
                
                # Coordenadas de nodos
                {'nombre': 'coor_gps_lat', 'componente': 'CCOMUN', 'atributo': 'COOR_GPS_LAT'},
                {'nombre': 'coor_gps_lon', 'componente': 'CCOMUN', 'atributo': 'COOR_GPS_LON'},
                {'nombre': 'Coordenada_Y2', 'componente': '', 'atributo': ''},  # Nodo 2 - Excel
                {'nombre': 'Coordenada_X2', 'componente': '', 'atributo': ''},  # Nodo 2 - Excel
                
                # Identificadores de nodos (no están en Oracle, vienen del Excel)
                {'nombre': 'Identificador_1', 'componente': '', 'atributo': ''},
                {'nombre': 'Identificador_2', 'componente': '', 'atributo': ''},
                
                # Características físicas (no están en Oracle, vienen del Excel)
                {'nombre': 'Longitud', 'componente': '', 'atributo': ''},
                {'nombre': 'Fases', 'componente': '', 'atributo': ''},
                
                # Clasificación
                {'nombre': 'uc', 'componente': 'CCOMUN', 'atributo': 'UC'},
                {'nombre': 'tipo_proyecto', 'componente': 'CCOMUN', 'atributo': 'TIPO_PROYECTO'},
                {'nombre': 'id_mercado', 'componente': 'CCOMUN', 'atributo': 'ID_MERCADO'},
                {'nombre': 'clasificacion_mercado', 'componente': 'CCOMUN', 'atributo': 'CLASIFICACION_MERCADO'},
                
                # Marcación y otros
                {'nombre': 'codigo_marcacion', 'componente': 'CCOMUN', 'atributo': 'CODIGO_MARCACION'},
                {'nombre': 'salinidad', 'componente': 'CCOMUN', 'atributo': 'SALINIDAD'},
                {'nombre': 'Codigo Inventario', 'componente': '', 'atributo': ''},  # Excel
                
                # Proyecto y observaciones
                {'nombre': 'proyecto', 'componente': 'CCOMUN', 'atributo': 'PROYECTO'},
                {'nombre': 'empresa_origen', 'componente': 'CCOMUN', 'atributo': 'EMPRESA_ORIGEN'},
                {'nombre': 'observaciones', 'componente': 'CCOMUN', 'atributo': 'OBSERVACIONES'},
                
                # G3E_GEOMETRY como último campo (placeholder de geometría)
                {'nombre': 'G3E_GEOMETRY', 'componente': '', 'atributo': ''},
            ]

            # 4. Agregar cada campo con su número correcto
            for i, campo_config in enumerate(campos_config):
                campo_elem = SubElement(campos, f'Campo{i}')

                nombre = SubElement(campo_elem, 'Nombre')
                nombre.text = campo_config['nombre']

                componente = SubElement(campo_elem, 'Componente')
                componente.text = campo_config['componente']

                atributo = SubElement(campo_elem, 'Atributo')
                atributo.text = campo_config['atributo']

            # 5. Formatear XML con indentación bonita
            rough_string = tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            # Eliminar la declaración XML <?xml version="1.0" ?>
            lines = pretty_xml.split('\n')
            if lines[0].startswith('<?xml'):
                lines = lines[1:]
            while lines and lines[-1].strip() == '':
                lines.pop()

            pretty_xml_sin_declaracion = '\n'.join(lines)

            # 6. Escribir archivo con UTF-8 BOM
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(pretty_xml_sin_declaracion)

            print(f"✅ Archivo XML Línea generado exitosamente: {filename} (configuración para {registros_nuevo} registros)")
            return filename

        except Exception as e:
            raise Exception(f"Error generando archivo XML Línea: {str(e)}")

    def generar_xml_baja_linea(self):
        """
        Genera archivo XML de configuración para BAJA LÍNEA (conductores).
        Alineado con generar_txt_baja_linea(), para registros BAJA (FID sin UC).
        
        Campos para BAJA:
        - G3E_FID: CCOMUN
        - ESTADO: CCOMUN (siempre "RETIRADO")
        - FECHA_FUERA_OPERACION: CCOMUN
        """
        try:
            from xml.etree.ElementTree import Element, SubElement, tostring
            from xml.dom import minidom
            
            filename = self._generar_nombre_archivo_con_indice('conductores_linea_baja', 'xml')
            filepath = os.path.join(self.base_path, filename)
            
            # 1. Contar registros BAJA (tiene FID pero NO UC)
            datos_conductor = self._leer_hoja_conductores()
            registros_baja = 0
            
            if datos_conductor:
                for registro in datos_conductor:
                    fid_git = self._extraer_campo_conductor(registro, 'codigo_fid_git')
                    unidad_constructiva = self._extraer_campo_conductor(registro, 'unidad_constructiva')
                    
                    # BAJA: tiene FID pero NO UC
                    if fid_git and not unidad_constructiva:
                        registros_baja += 1
            
            print(f"DEBUG: XML Baja Línea - {registros_baja} registros BAJA")
            
            # 2. Crear estructura XML según especificación
            root = Element('Configuracion')
            
            # Elemento principal
            elemento = SubElement(root, 'Elemento')
            elemento.text = 'Poste'
            
            # Contenedor de campos
            campos = SubElement(root, 'Campos')
            
            # 3. Definición de campos para BAJA LÍNEA (igual que BAJA estructuras)
            campos_config = [
                {'nombre': 'G3E_FID', 'componente': 'CCOMUN', 'atributo': 'G3E_FID'},
                {'nombre': 'ESTADO', 'componente': 'CCOMUN', 'atributo': 'ESTADO'},
                {'nombre': 'FECHA_FUERA_OPERACION', 'componente': 'CCOMUN', 'atributo': 'FECHA_FUERA_OPERACION'},
            ]

            # 4. Agregar cada campo con su número correcto
            for i, campo_config in enumerate(campos_config):
                campo_elem = SubElement(campos, f'Campo{i}')

                nombre = SubElement(campo_elem, 'Nombre')
                nombre.text = campo_config['nombre']

                componente = SubElement(campo_elem, 'Componente')
                componente.text = campo_config['componente']

                atributo = SubElement(campo_elem, 'Atributo')
                atributo.text = campo_config['atributo']

            # 5. Formatear XML con indentación bonita
            rough_string = tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            # Eliminar la declaración XML <?xml version="1.0" ?>
            lines = pretty_xml.split('\n')
            if lines[0].startswith('<?xml'):
                lines = lines[1:]
            while lines and lines[-1].strip() == '':
                lines.pop()

            pretty_xml_sin_declaracion = '\n'.join(lines)

            # 6. Escribir archivo con UTF-8 BOM
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(pretty_xml_sin_declaracion)

            print(f"✅ Archivo XML Baja Línea generado exitosamente: {filename} (configuración para {registros_baja} registros)")
            return filename

        except Exception as e:
            raise Exception(f"Error generando archivo XML Baja Línea: {str(e)}")

    def _leer_hoja_conductores(self) -> List[Dict]:
        """
        Lee datos desde la hoja 'Conductor_N1-N2-N3' del Excel.
        
        Returns:
            Lista de diccionarios con los datos de conductores
        """
        try:
            archivo_path = self.proceso.archivo_excel.path
            
            # Leer todas las hojas
            df_dict = pd.read_excel(archivo_path, sheet_name=None)
            
            # Buscar la hoja de conductores
            nombre_hoja = None
            for hoja in df_dict.keys():
                if 'conductor' in hoja.lower() and ('n1' in hoja.lower() or 'n2' in hoja.lower() or 'n3' in hoja.lower()):
                    nombre_hoja = hoja
                    break
            
            if not nombre_hoja:
                raise Exception("No se encontró la hoja 'Conductor_N1-N2-N3' en el archivo Excel")
            
            print(f"📄 Leyendo hoja de conductores: '{nombre_hoja}'")
            
            # Intentar diferentes estrategias para encontrar headers (igual que estructuras)
            # Para conductores, buscamos headers que contengan nombres de campos esperados
            df = None
            header_row = None
            
            # Palabras clave que identifican headers reales de conductores
            keywords_conductor = ['coordenada', 'identificador', 'código', 'fid', 'unidad', 'constructiva',
                                 'longitud', 'latitud', 'calibre', 'tensión', 'propietario']
            
            # Función helper para contar headers válidos de conductor
            def contar_headers_conductor(columns):
                """Cuenta cuántos headers contienen palabras clave de conductor"""
                count = 0
                for col in columns:
                    col_str = str(col).lower().replace('\n', ' ').replace('_', ' ')
                    if any(keyword in col_str for keyword in keywords_conductor):
                        count += 1
                return count
            
            # Estrategia 1: Headers en fila 0
            try:
                temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=0)
                valid_count = contar_headers_conductor(temp_df.columns)
                print(f"🔍 Fila 0: {valid_count} headers de conductor encontrados")
                if valid_count >= 5:  # Al menos 5 campos esperados
                    df = temp_df
                    header_row = 0
                    print("✅ Headers de conductor encontrados en fila 0")
            except Exception as e:
                print(f"⚠️ Error leyendo fila 0: {e}")
            
            # Estrategia 2: Headers en fila 1
            if df is None:
                try:
                    temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=1)
                    valid_count = contar_headers_conductor(temp_df.columns)
                    print(f"🔍 Fila 1: {valid_count} headers de conductor encontrados")
                    if valid_count >= 5:
                        df = temp_df
                        header_row = 1
                        print("✅ Headers de conductor encontrados en fila 1")
                except Exception as e:
                    print(f"⚠️ Error leyendo fila 1: {e}")
            
            # Estrategia 3: Headers en fila 2
            if df is None:
                try:
                    temp_df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=2)
                    valid_count = contar_headers_conductor(temp_df.columns)
                    print(f"🔍 Fila 2: {valid_count} headers de conductor encontrados")
                    if valid_count >= 5:
                        df = temp_df
                        header_row = 2
                        print("✅ Headers de conductor encontrados en fila 2")
                except Exception as e:
                    print(f"⚠️ Error leyendo fila 2: {e}")
            
            # Si no encontramos headers válidos, usar fila 2 como fallback (más probable para conductores)
            if df is None:
                print("⚠️ No se detectaron headers automáticamente, usando fila 2 como fallback")
                df = pd.read_excel(archivo_path, sheet_name=nombre_hoja, header=2)
                header_row = 2
            
            print(f"📊 Columnas encontradas en '{nombre_hoja}' (header en fila {header_row}):")
            for idx, col in enumerate(df.columns[:10], 1):  # Mostrar solo primeras 10
                print(f"   {idx}. {col}")
            if len(df.columns) > 10:
                print(f"   ... y {len(df.columns) - 10} columnas más")
            print(f"📊 Total de filas: {len(df)}")
            
            # Mostrar ejemplo del primer registro (si existe)
            if len(df) > 0:
                print("📋 Ejemplo primer registro:")
                primer_registro = df.iloc[0]
                # Buscar campos clave
                campos_clave = ['Código FID\nGIT', 'Código FID GIT', 'Unidad Constructiva', 'Identificador_1']
                for col in df.columns:
                    if any(clave.lower().replace('\n', '').replace(' ', '') in str(col).lower().replace('\n', '').replace(' ', '') 
                           for clave in campos_clave):
                        valor = primer_registro[col] if not pd.isna(primer_registro[col]) else 'VACÍO'
                        print(f"   {col}: '{valor}'")
            
            # Convertir a lista de diccionarios
            datos = []
            for _, row in df.iterrows():
                registro = {}
                for col, val in row.items():
                    if pd.isna(val):
                        registro[col] = ""
                    else:
                        registro[col] = str(val).strip()
                datos.append(registro)
            
            return datos
            
        except Exception as e:
            raise Exception(f"Error leyendo hoja de conductores: {str(e)}")

    def _extraer_campo_conductor(self, registro: Dict, campo_tipo: str) -> str:
        """
        Extrae un campo específico del registro de conductor,
        buscando por diferentes variantes de nombres.
        
        Args:
            registro: Diccionario con datos del conductor
            campo_tipo: Tipo de campo a extraer
                - 'codigo_fid_git': Código FID GIT
                - 'unidad_constructiva': Unidad Constructiva
                - 'identificador': Identificador (Identificador_1 o Identificador_2)
                - 'fecha_instalacion': Fecha Instalación
                - 'coordenada_x1': Coordenada X1 (Longitud)
                - 'coordenada_y1': Coordenada Y1 (Latitud)
                - 'coordenada_x2': Coordenada X2 (Longitud 2)
                - 'coordenada_y2': Coordenada Y2 (Latitud 2)
                - 'nivel_tension': Nivel de Tensión
                - 'municipio': Municipio
                - 'fases': Fases
                - 'numero_conductores': Número de conductores
                - 'clase': CLASE
                - 'poblacion': POBLACION
                - 'tipo': TIPO
                - 'material': MATERIAL
                - 'calibre': CALIBRE
                
        Returns:
            Valor del campo o cadena vacía si no se encuentra
        """
        variantes = {
            'codigo_fid_git': [
                'Código FID\nGIT', 'Código FID GIT', 'Codigo FID GIT', 
                'CODIGO_FID_GIT', 'código fid git', 'codigo fid git', 
                'FID_GIT', 'FID GIT', 'Código FID_rep'
            ],
            'unidad_constructiva': [
                'Unidad Constructiva', 'UNIDAD_CONSTRUCTIVA',
                'unidad constructiva', 'UC', 'UNIDAD CONSTRUCTIVA'
            ],
            'identificador': [
                'Identificador_1', 'Identificador_2', 'Identificador', 
                'IDENTIFICADOR', 'identificador', 'ID', 'Id', 'ENLACE'
            ],
            'fecha_instalacion': [
                'Fecha Instalacion\nDD/MM/YYYY', 'Fecha Instalacion DD/MM/YYYY', 
                'Fecha Instalación', 'FECHA_INSTALACION', 'Fecha Instalacion', 
                'fecha instalacion'
            ],
            'coordenada_x1': [
                'Coordenada_X1\nLONGITUD', 'Coordenada_X1 LONGITUD', 
                'Coordenada_X1', 'COORDENADA_X1', 'coordenada x1', 
                'Coordenada X1', 'LONGITUD'
            ],
            'coordenada_y1': [
                'Coordenada_Y1\nLATITUD', 'Coordenada_Y1 LATITUD',
                'Coordenada_Y1', 'COORDENADA_Y1', 'coordenada y1',
                'Coordenada Y1', 'LATITUD'
            ],
            'coordenada_x2': [
                'Coordenada_X2\nLONGITUD2', 'Coordenada_X2 LONGITUD2',
                'Coordenada_X2', 'COORDENADA_X2', 'coordenada x2',
                'Coordenada X2', 'LONGITUD2'
            ],
            'coordenada_y2': [
                'Coordenada_Y2\nLATITUD3', 'Coordenada_Y2 LATITUD3',
                'Coordenada_Y2', 'COORDENADA_Y2', 'coordenada y2',
                'Coordenada Y2', 'LATITUD3'
            ],
            'nivel_tension': [
                'Nivel de Tension', 'Nivel de Tensión', 'NIVEL_TENSION',
                'nivel tension', 'Nivel Tension'
            ],
            'municipio': [
                'Municipio', 'MUNICIPIO', 'municipio'
            ],
            'fases': [
                'Fases', 'FASES', 'fases'
            ],
            'numero_conductores': [
                'Número de conductores', 'Numero de conductores',
                'NUMERO_CONDUCTORES', 'numero conductores'
            ],
            'clase': [
                'CLASE', 'Clase', 'clase'
            ],
            'poblacion': [
                'POBLACION', 'Poblacion', 'poblacion', 'Población'
            ],
            'tipo': [
                'TIPO', 'Tipo', 'tipo'
            ],
            'material': [
                'MATERIAL', 'Material', 'material'
            ],
            'calibre': [
                'CALIBRE', 'Calibre', 'calibre'
            ]
        }
        
        # Buscar el campo en el registro
        nombres_posibles = variantes.get(campo_tipo, [])
        
        for nombre in nombres_posibles:
            if nombre in registro:
                valor = registro[nombre]
                if valor and str(valor).strip() and str(valor).strip().lower() not in ('nan', 'none', 'null', ''):
                    return str(valor).strip()
        
        # Búsqueda flexible (normalizada) - quitar saltos de línea y espacios
        for key, value in registro.items():
            if isinstance(key, str):
                # Normalizar: quitar saltos de línea, espacios extras, guiones bajos
                key_norm = key.lower().replace('\n', '').replace(' ', '').replace('_', '').strip()
                for nombre in nombres_posibles:
                    nombre_norm = nombre.lower().replace('\n', '').replace(' ', '').replace('_', '').strip()
                    if key_norm == nombre_norm:
                        if value and str(value).strip() and str(value).strip().lower() not in ('nan', 'none', 'null', ''):
                            return str(value).strip()
        
        return ''

    def _extraer_campo_específico(self, registro: Dict, nombre_campo: str) -> str:
        """
        Extrae un campo específico del registro por nombre exacto.
        
        Args:
            registro: Diccionario con datos
            nombre_campo: Nombre exacto del campo a buscar
            
        Returns:
            Valor del campo o cadena vacía si no se encuentra
        """
        # Búsqueda exacta primero
        if nombre_campo in registro:
            valor = registro[nombre_campo]
            if valor and str(valor).strip() and str(valor).strip().lower() not in ('nan', 'none', 'null', ''):
                return str(valor).strip()
        
        # Búsqueda normalizada (sin espacios, saltos de línea)
        nombre_norm = nombre_campo.lower().replace('\n', '').replace(' ', '').replace('_', '').strip()
        for key, value in registro.items():
            if isinstance(key, str):
                key_norm = key.lower().replace('\n', '').replace(' ', '').replace('_', '').strip()
                if key_norm == nombre_norm:
                    if value and str(value).strip() and str(value).strip().lower() not in ('nan', 'none', 'null', ''):
                        return str(value).strip()
        
        return ''

    def _enriquecer_conductores_reposicion(self, datos: List[Dict]) -> List[Dict]:
        """
        Enriquece los datos de conductores que son REPOSICIÓN,
        validando contra la BD y reemplazando coordenadas si difieren.
        
        Para REPOSICIÓN (tiene FID + UC):
        - Convierte código operativo a FID si empieza con Z
        - Consulta coordenadas en Oracle
        - Reemplaza coordenadas del Excel con las de BD
        
        Args:
            datos: Lista de registros de conductores
            
        Returns:
            Lista de registros enriquecidos con coordenadas de BD
        """
        oracle_disponible = OracleHelper.test_connection()
        
        if not oracle_disponible:
            print("⚠️ WARNING: Oracle no disponible, usando coordenadas del Excel")
            return datos
        
        datos_enriquecidos = []
        registros_enriquecidos = 0
        
        for i, registro in enumerate(datos):
            fid_git = self._extraer_campo_conductor(registro, 'codigo_fid_git')
            unidad_constructiva = self._extraer_campo_conductor(registro, 'unidad_constructiva')
            
            # Solo enriquecer si es REPOSICIÓN (tiene ambos campos)
            if fid_git and unidad_constructiva:
                print(f"🔍 REPOSICIÓN detectada en registro {i+1}: FID='{fid_git}', UC='{unidad_constructiva}'")
                
                # Convertir código operativo a FID si es necesario
                fid_real = fid_git
                if fid_git.upper().startswith('Z'):
                    fid_convertido = OracleHelper.obtener_fid_desde_codigo_operativo(fid_git)
                    if fid_convertido:
                        fid_real = str(fid_convertido)
                        print(f"  ✅ Código operativo '{fid_git}' → FID '{fid_real}'")
                    else:
                        print(f"  ⚠️ No se pudo convertir código operativo '{fid_git}' a FID")
                
                # Consultar coordenadas del conductor en Oracle
                try:
                    datos_oracle = self._consultar_conductor_oracle(fid_real)
                    
                    if datos_oracle:
                        # Comparar y reemplazar coordenadas (nombres de BD Oracle)
                        lat_excel = registro.get('coor_gps_lat', '')
                        lon_excel = registro.get('coor_gps_lon', '')
                        lat_oracle = datos_oracle.get('coor_gps_lat', '')
                        lon_oracle = datos_oracle.get('coor_gps_lon', '')
                        
                        print(f"  📊 Coordenadas Excel: LAT={lat_excel}, LON={lon_excel}")
                        print(f"  📊 Coordenadas Oracle: LAT={lat_oracle}, LON={lon_oracle}")
                        
                        # Reemplazar con datos de Oracle si existen
                        if lat_oracle:
                            registro['coor_gps_lat'] = lat_oracle
                        if lon_oracle:
                            registro['coor_gps_lon'] = lon_oracle
                        
                        # También actualizar coordenadas del Nodo 2 si vienen de Oracle
                        lat2_oracle = datos_oracle.get('Coordenada_Y2', '')
                        lon2_oracle = datos_oracle.get('Coordenada_X2', '')
                        if lat2_oracle:
                            registro['Coordenada_Y2'] = lat2_oracle
                        if lon2_oracle:
                            registro['Coordenada_X2'] = lon2_oracle
                        
                        registros_enriquecidos += 1
                        print("  ✅ Coordenadas actualizadas desde BD")
                    else:
                        print(f"  ⚠️ No se encontraron datos en Oracle para FID '{fid_real}'")
                
                except Exception as e:
                    print(f"  ❌ Error consultando Oracle para FID '{fid_real}': {str(e)}")
            
            datos_enriquecidos.append(registro)
        
        if registros_enriquecidos > 0:
            print("\n📊 Resumen enriquecimiento Oracle:")
            print(f"   ✅ {registros_enriquecidos} registros REPOSICIÓN enriquecidos con coordenadas de BD")
        
        return datos_enriquecidos
    
    def _consultar_conductor_oracle(self, codigo: str):
        """
        Consulta datos de un conductor en Oracle por su código.
        
        Query basada en la proporcionada:
        SELECT coordenadas y otros campos desde econ_pri_at, ccomun, cpropietario
        
        Args:
            codigo: Código del conductor (ej: 'L129251', 'AMVLS75784', 'GLVL38505')
            
        Returns:
            Dict con datos del conductor o None si no existe
        """
        try:
            # Query para obtener datos completos del conductor
            # Basada en: econ_pri_at JOIN ccomun JOIN cpropietario
            # IMPORTANTE: Buscar por cp.codigo (código operativo como 'L129251')
            # Usa USING (g3e_fid) para simplificar los JOINs
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
            
            with OracleHelper.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, {'codigo': codigo})
                    row = cursor.fetchone()
                    
                    if row:
                        # Extraer columnas
                        columns = [col[0] for col in cursor.description]
                        datos = dict(zip(columns, row))
                        
                        # Mapear todos los 21 campos de Oracle
                        result = {}
                        
                        # Coordenadas (críticas para reposición)
                        if datos.get('COOR_GPS_LAT'):
                            result['coor_gps_lat'] = str(datos['COOR_GPS_LAT'])
                        if datos.get('COOR_GPS_LON'):
                            result['coor_gps_lon'] = str(datos['COOR_GPS_LON'])
                        
                        # Campos de estado y ubicación
                        if datos.get('ESTADO'):
                            result['estado'] = str(datos['ESTADO'])
                        if datos.get('UBICACION'):
                            result['ubicacion'] = str(datos['UBICACION'])
                        if datos.get('CODIGO_MATERIAL'):
                            result['codigo_material'] = str(datos['CODIGO_MATERIAL'])
                        
                        # Fechas
                        if datos.get('FECHA_INSTALACION'):
                            result['fecha_instalacion'] = str(datos['FECHA_INSTALACION'])
                        if datos.get('FECHA_OPERACION'):
                            result['fecha_operacion'] = str(datos['FECHA_OPERACION'])
                        
                        # Proyecto y empresa
                        if datos.get('PROYECTO'):
                            result['proyecto'] = str(datos['PROYECTO'])
                        if datos.get('EMPRESA_ORIGEN'):
                            result['empresa_origen'] = str(datos['EMPRESA_ORIGEN'])
                        if datos.get('OBSERVACIONES'):
                            result['observaciones'] = str(datos['OBSERVACIONES'])
                        if datos.get('TIPO_PROYECTO'):
                            result['tipo_proyecto'] = str(datos['TIPO_PROYECTO'])
                        
                        # Mercado
                        if datos.get('ID_MERCADO'):
                            result['id_mercado'] = str(datos['ID_MERCADO'])
                        if datos.get('CLASIFICACION_MERCADO'):
                            result['clasificacion_mercado'] = str(datos['CLASIFICACION_MERCADO'])
                        
                        # UC y estado
                        if datos.get('UC'):
                            result['uc'] = str(datos['UC'])
                        if datos.get('ESTADO_SALUD'):
                            result['estado_salud'] = str(datos['ESTADO_SALUD'])
                        if datos.get('OT_MAXIMO'):
                            result['ot_maximo'] = str(datos['OT_MAXIMO'])
                        
                        # Otros campos técnicos
                        if datos.get('CODIGO_MARCACION'):
                            result['codigo_marcacion'] = str(datos['CODIGO_MARCACION'])
                        if datos.get('SALINIDAD'):
                            result['salinidad'] = str(datos['SALINIDAD'])
                        if datos.get('USO'):
                            result['uso'] = str(datos['USO'])
                        
                        # Propietario
                        if datos.get('PROPIETARIO_1'):
                            result['propietario_1'] = str(datos['PROPIETARIO_1'])
                        if datos.get('PORCENTAJE_PROP_1'):
                            result['porcentaje_prop_1'] = str(datos['PORCENTAJE_PROP_1'])
                        
                        return result
                    else:
                        return None
                        
        except Exception as e:
            print(f"❌ Error consultando conductor en Oracle: {str(e)}")
            return None

class ClasificadorEstructuras:
    """Aplica las reglas de clasificación de estructuras según las reglas de negocio"""
    
    def __init__(self):
        pass
    
    def clasificar_estructura(self, registro: Dict) -> Dict:
        """
        Aplica las reglas de clasificación a un registro
        
        Reglas de negocio:
        1. GRUPO siempre debe ser "ESTRUCTURAS EYT" (para todas las estructuras)
        2. CLASE siempre debe ser "POSTE" (para todas las estructuras)
        3. USO siempre debe ser "DISTRIBUCION ENERGIA" (para todas las estructuras)
        4. TIPO se determina únicamente por la Unidad Constructiva (UC):
           - Si UC empieza con N1 -> TIPO = "SECUNDARIO"
           - Si UC empieza con N2, N3, N4 -> TIPO = "PRIMARIO"
           - Valor por defecto: "SECUNDARIO"
        5. TIPO_PROYECTO: convertir números romanos (I, II, III, IV) a formato T+número (T1, T2, T3, T4)
        """
        registro_clasificado = registro.copy()
        
        # Inicializar lista de observaciones
        observaciones_clasificacion = []
        
        # Regla 1: GRUPO siempre debe ser "ESTRUCTURAS EYT" (para todas las estructuras)
        registro_clasificado['GRUPO'] = 'ESTRUCTURAS EYT'
        
        # Regla 2: CLASE siempre debe ser "POSTE" (para todas las estructuras)
        registro_clasificado['CLASE'] = 'POSTE'
        
        # Regla 3: USO siempre debe ser "DISTRIBUCION ENERGIA" (para todas las estructuras)
        registro_clasificado['USO'] = 'DISTRIBUCION ENERGIA'
        
        # Regla 3b: PORCENTAJE_PROPIEDAD siempre debe ser "100" (para todas las estructuras)
        registro_clasificado['PORCENTAJE_PROPIEDAD'] = '100'
        
        # Para PROPIETARIO: clasificar el nombre del Excel a una categoría predefinida
        propietario_nombre = registro.get('PROPIETARIO', '')
        propietario_clasificado = self._clasificar_propietario(propietario_nombre)
        registro_clasificado['PROPIETARIO'] = propietario_clasificado
        
        # Regla 4: Clasificar TIPO basado únicamente en Unidad Constructiva (UC)
        uc = registro.get('UC', '').strip().upper()
        tipo_clasificado = self._clasificar_tipo_por_uc(uc)
        registro_clasificado['TIPO'] = tipo_clasificado
        
        # Regla 5: Generar TIPO_PROYECTO basado en NIVEL_TENSION o UC
        nivel_tension = registro.get('NIVEL_TENSION', '').strip()
        uc = registro.get('UC', '').strip()
        
        # Usar NIVEL_TENSION primero, si no está disponible usar UC
        valor_para_mapeo = nivel_tension if nivel_tension else uc
        
        tipo_proyecto_generado = self._generar_tipo_proyecto_desde_nivel_tension(valor_para_mapeo)
        if tipo_proyecto_generado:
            registro_clasificado['TIPO_PROYECTO'] = tipo_proyecto_generado
            observaciones_clasificacion.append(f"TIPO_PROYECTO generado como '{tipo_proyecto_generado}' basado en {'NIVEL_TENSION' if nivel_tension else 'UC'}: {valor_para_mapeo}")
        else:
            # Fallback: Convertir TIPO_PROYECTO de números romanos a formato T+número si existe
            tipo_proyecto_original = registro.get('TIPO_PROYECTO', '').strip()
            tipo_proyecto_convertido = self._convertir_tipo_proyecto(tipo_proyecto_original)
            registro_clasificado['TIPO_PROYECTO'] = tipo_proyecto_convertido
        
        # Regla 6: FECHA_OPERACION debe ser igual a FECHA_INSTALACION (solo fecha, sin hora)
        fecha_instalacion = registro.get('FECHA_INSTALACION', '')
        if fecha_instalacion:
            # Formatear fecha para mostrar solo fecha sin hora
            fecha_formateada = self._formatear_fecha(fecha_instalacion)
            registro_clasificado['FECHA_INSTALACION'] = fecha_formateada
            registro_clasificado['FECHA_OPERACION'] = fecha_formateada
        
        # Regla 7: CODIGO_MATERIAL
        # Priorizar el valor que llegue desde el Excel (si existe y no está vacío)
        cm_excel = DataUtils.normalizar_codigo_material(registro.get('CODIGO_MATERIAL', ''))
        from_excel_flag = bool(registro.get('_CODIGO_MATERIAL_FROM_EXCEL', False))
        if cm_excel:
            registro_clasificado['CODIGO_MATERIAL'] = cm_excel
        else:
            # Si el campo venía del Excel pero está vacío, NO rellenar por UC (queremos forzar validación de vacío)
            if not from_excel_flag:
                codigo_material = self._asignar_codigo_material(uc)
                if codigo_material:
                    registro_clasificado['CODIGO_MATERIAL'] = DataUtils.normalizar_codigo_material(codigo_material)
        
        # Regla 8: Convertir ESTADO_SALUD de números a descriptivos
        estado_salud_convertido = self._convertir_estado_salud(registro.get('ESTADO_SALUD', ''))
        if estado_salud_convertido:
            registro_clasificado['ESTADO_SALUD'] = estado_salud_convertido
        
        # Agregar observaciones de clasificación (solo si no hay observaciones del Excel original)
        observaciones_clasificacion.append(f"TIPO clasificado como {tipo_clasificado} basado en UC: {uc}")
        observaciones_clasificacion.append("GRUPO forzado a 'ESTRUCTURAS EYT'")
        observaciones_clasificacion.append("CLASE forzada a 'POSTE'")
        observaciones_clasificacion.append("USO forzado a 'DISTRIBUCION ENERGIA'")
        observaciones_clasificacion.append("PORCENTAJE_PROPIEDAD forzado a '100'")
        # Registrar observación solo si se asignó por UC (no si vino de Excel)
        if not cm_excel:
            codigo_material = registro_clasificado.get('CODIGO_MATERIAL', '')
            if codigo_material:
                observaciones_clasificacion.append(f"CODIGO_MATERIAL asignado como '{codigo_material}' basado en UC: {uc}")
        if estado_salud_convertido and estado_salud_convertido != registro.get('ESTADO_SALUD', ''):
            observaciones_clasificacion.append(f"ESTADO_SALUD convertido de '{registro.get('ESTADO_SALUD', '')}' a '{estado_salud_convertido}'")
        if tipo_proyecto_generado:
            observaciones_clasificacion.append(f"TIPO_PROYECTO generado como '{tipo_proyecto_generado}' basado en {'NIVEL_TENSION' if nivel_tension else 'UC'}: {valor_para_mapeo}")
        elif tipo_proyecto_original != tipo_proyecto_convertido:
            observaciones_clasificacion.append(f"TIPO_PROYECTO convertido de '{tipo_proyecto_original}' a '{tipo_proyecto_convertido}'")
        if fecha_instalacion:
            observaciones_clasificacion.append("FECHA_OPERACION igualada a FECHA_INSTALACION")
        
        # Solo agregar observaciones de clasificación si no hay observaciones del Excel original
        if not registro.get('OBSERVACIONES', '').strip():
            # Si no hay observaciones del Excel, dejar el campo vacío (no agregar observaciones de clasificación)
            registro_clasificado['OBSERVACIONES'] = ''
        # Si ya hay observaciones del Excel original, mantenerlas sin agregar observaciones de clasificación
        
        # Guardar observaciones de clasificación en un campo separado para debugging/auditoría
        registro_clasificado['OBSERVACION_CLASIFICACION_SISTEMA'] = "; ".join(observaciones_clasificacion)
        
        # Agregar metadatos de clasificación
        registro_clasificado['FECHA_CLASIFICACION'] = datetime.now().isoformat()
        registro_clasificado['VERSION_REGLAS'] = '2.5'
        
        return registro_clasificado
    
    def _convertir_tipo_proyecto(self, tipo_proyecto: str) -> str:
        """
        Convierte números romanos a formato T+número para TIPO_PROYECTO
        
        I -> T1, II -> T2, III -> T3, IV -> T4
        """
        if not tipo_proyecto:
            return tipo_proyecto
        
        # Normalizar y extraer únicamente la parte romana por si vienen caracteres como '|II|'
        tipo_limpio = str(tipo_proyecto).strip().upper()
        try:
            import re as _re
            coincidencias = _re.findall(r"[IVXLCDM]+", tipo_limpio)
            romano_extraido = max(coincidencias, key=len) if coincidencias else tipo_limpio
        except Exception:
            romano_extraido = tipo_limpio

        conversion_map = REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']
        if romano_extraido in conversion_map:
            return conversion_map[romano_extraido]

        # Fallback: convertir romano a entero genérico si no está en el mapa y formar T<n>
        try:
            valor = self._roman_to_int(romano_extraido)
            if valor > 0:
                return f"T{valor}"
        except Exception:
            pass

        # Si no se pudo convertir, mantener el valor original
        return tipo_proyecto

    def _roman_to_int(self, s: str) -> int:
        valores = { 'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000 }
        total = 0
        prev = 0
        s = (s or '').strip().upper()
        for ch in reversed(s):
            v = valores.get(ch, 0)
            if v < prev:
                total -= v
            else:
                total += v
                prev = v
        return total
    
    def _generar_tipo_proyecto_desde_nivel_tension(self, nivel_tension: str) -> str:
        """
        Genera TIPO_PROYECTO basado en NIVEL_TENSION
        
        N3L75 -> T1, N3L79 -> T3, etc.
        """
        if not nivel_tension:
            return REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']['VALOR_DEFECTO']
        
        nivel_limpio = nivel_tension.strip().upper()
        mapeo_nivel = REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']['MAPEO_NIVEL_TENSION']
        
        # Buscar coincidencia exacta primero
        if nivel_limpio in mapeo_nivel:
            return mapeo_nivel[nivel_limpio]
        
        # Buscar coincidencia por patrón (ej: N1L, N2L, N3L, N4L)
        for patron, tipo_proyecto in mapeo_nivel.items():
            if patron.endswith('L') and nivel_limpio.startswith(patron):
                return tipo_proyecto
        
        return REGLAS_CLASIFICACION['CONVERSION_TIPO_PROYECTO']['VALOR_DEFECTO']  # No se encontró mapeo
    
    def _clasificar_propietario(self, nombre_propietario: str) -> str:
        """
        Clasifica el nombre del propietario del Excel a una categoría predefinida
        
        Args:
            nombre_propietario: Nombre del propietario tal como viene en el Excel
            
        Returns:
            Categoría del propietario: 'CENS', 'PARTICULAR', 'ESTADO', o 'COMPARTIDO'
        """
        if not nombre_propietario:
            return 'PARTICULAR'  # Valor por defecto
        
        nombre_limpio = nombre_propietario.strip().upper()
        
        # Reglas de clasificación basadas en el nombre del propietario
        if any(keyword in nombre_limpio for keyword in ['CENS', 'CENTRALES', 'ELECTRICA']):
            return 'CENS'
        elif any(keyword in nombre_limpio for keyword in ['ESTADO', 'GOBIERNO', 'PUBLICO', 'MINISTERIO']):
            return 'ESTADO'
        elif any(keyword in nombre_limpio for keyword in ['COMPARTIDO', 'CONSORCIO', 'SOCIEDAD']):
            return 'COMPARTIDO'
        else:
            # Por defecto, clasificar como PARTICULAR para nombres de empresas privadas
            return 'PARTICULAR'
    
    def _formatear_fecha(self, fecha) -> str:
        """
        Formatea una fecha para mostrar solo la fecha sin la hora en formato DD/MM/YYYY
        """
        return DataUtils.formatear_fecha(fecha)
    
    def verificar_propietarios_en_excel(self, registros: List[Dict]) -> Dict:
        """
        Verifica si hay propietarios definidos en el Excel
        
        Returns:
            Dict con información sobre propietarios encontrados
        """
        propietarios_encontrados = set()
        registros_con_propietario = 0
        registros_sin_propietario = 0
        
        for registro in registros:
            propietario = registro.get('PROPIETARIO', '')
            # Convertir a string y limpiar espacios, manejar valores no string
            if propietario is not None:
                propietario = str(propietario).strip()
            else:
                propietario = ''
                
            if propietario:
                propietarios_encontrados.add(propietario)
                registros_con_propietario += 1
            else:
                registros_sin_propietario += 1
        
        return {
            'tiene_propietarios': len(propietarios_encontrados) > 0,
            'propietarios_unicos': list(propietarios_encontrados),
            'registros_con_propietario': registros_con_propietario,
            'registros_sin_propietario': registros_sin_propietario,
            'total_registros': len(registros),
            'propietario_unico': list(propietarios_encontrados)[0] if len(propietarios_encontrados) == 1 else None
        }
    
    def aplicar_propietario_a_todos(self, registros: List[Dict], propietario: str) -> List[Dict]:
        """
        Aplica el mismo propietario a todos los registros
        
        Args:
            registros: Lista de registros a actualizar
            propietario: Propietario a aplicar (debe ser uno de los predefinidos)
        
        Returns:
            Lista de registros actualizados
        """
        propietarios_validos = REGLAS_CLASIFICACION['PROPIETARIOS_VALIDOS']['VALORES_ACEPTADOS']
        
        if propietario not in propietarios_validos:
            raise ValueError(f"Propietario '{propietario}' no es válido. Debe ser uno de: {propietarios_validos}")
        
        registros_actualizados = []
        for registro in registros:
            registro_actualizado = registro.copy()
            registro_actualizado['PROPIETARIO'] = propietario
            # PORCENTAJE_PROPIEDAD ya se aplica en clasificar_estructura
            registros_actualizados.append(registro_actualizado)
        
        return registros_actualizados
    
    def aplicar_propietario_a_proceso(self, proceso, propietario: str) -> None:
        """
        Aplica el propietario seleccionado a todos los registros del proceso
        
        Args:
            proceso: Instancia del modelo ProcesoEstructura
            propietario: Propietario a aplicar (debe ser uno de los predefinidos)
        """
        propietarios_validos = REGLAS_CLASIFICACION['PROPIETARIOS_VALIDOS']['VALORES_ACEPTADOS']
        
        if propietario not in propietarios_validos:
            raise ValueError(f"Propietario '{propietario}' no es válido. Debe ser uno de: {propietarios_validos}")
        
        # Aplicar propietario a todos los registros de datos_norma
        if proceso.datos_norma:
            datos_actualizados = []
            for registro in proceso.datos_norma:
                registro_actualizado = registro.copy()
                registro_actualizado['PROPIETARIO'] = propietario
                registro_actualizado['PORCENTAJE_PROPIEDAD'] = '100'
                datos_actualizados.append(registro_actualizado)
            
            proceso.datos_norma = datos_actualizados
            print(f"Propietario '{propietario}' aplicado a {len(datos_actualizados)} registros")
        else:
            print("No hay datos_norma para actualizar")
        
        # Marcar que el propietario ya fue definido y guardar el valor
        proceso.propietario_definido = propietario  # Guardar el propietario seleccionado
        proceso.requiere_definir_propietario = False  # Ya no se requiere definir propietario
        proceso.save()
        print(f"Proceso actualizado: propietario_definido='{proceso.propietario_definido}', requiere_definir_propietario={proceso.requiere_definir_propietario}")
    
    def verificar_y_marcar_campos_requeridos(self, proceso) -> Dict:
        """
        Verifica qué campos requieren ser completados por el usuario
        y marca el proceso accordingly.
        
        Returns:
            Dict con información sobre campos que requieren completarse
        """
        campos_requeridos = {
            'propietario': False,
            'estado_salud': False,
            'detalles': {}
        }
        
        # Verificar PROPIETARIO
        if not proceso.propietario_definido:
            campos_requeridos['propietario'] = True
            proceso.requiere_definir_propietario = True
        
        # Verificar ESTADO_SALUD
        estado_salud_vacio = False
        if proceso.datos_excel:
            for registro in proceso.datos_excel:
                if not registro.get('ESTADO_SALUD') or registro.get('ESTADO_SALUD').strip() == '':
                    estado_salud_vacio = True
                    break
        
        if estado_salud_vacio and not (proceso.estado_salud_definido and proceso.estado_salud_definido != 'None'):
            campos_requeridos['estado_salud'] = True
            campos_requeridos['detalles']['estado_salud'] = 'ESTADO_SALUD está vacío en los datos del Excel'
        
        # Guardar cambios si es necesario
        proceso.save()
        
        return campos_requeridos
    
    def _clasificar_tipo_por_uc(self, uc: str) -> str:
        """
        Clasifica el TIPO basado en la Unidad Constructiva (UC)
        
        Lógica:
        - N1 -> SECUNDARIO
        - N2, N3, N4 -> PRIMARIO
        - Valor por defecto: SECUNDARIO
        """
        if not uc:
            return REGLAS_CLASIFICACION['CLASIFICACION_TIPO_POR_UC']['VALOR_DEFECTO']
        
        # Buscar patrones en las reglas
        for regla in REGLAS_CLASIFICACION['CLASIFICACION_TIPO_POR_UC']['REGLAS_PRIORITARIAS']:
            patron = regla['PATRON']
            if re.match(patron, uc):
                return regla['TIPO']
        
        # Si no coincide con ningún patrón, usar valor por defecto
        return REGLAS_CLASIFICACION['CLASIFICACION_TIPO_POR_UC']['VALOR_DEFECTO']
    
    def clasificar_lote(self, registros: List[Dict]) -> List[Dict]:
        """Aplica clasificación a un lote de registros"""
        registros_clasificados = []
        estadisticas = {
            'total_procesados': len(registros),
            'clasificados_como_poste': 0,
            'estructuras_eyt': 0
        }
        
        for registro in registros:
            registro_clasificado = self.clasificar_estructura(registro)
            registros_clasificados.append(registro_clasificado)
            
            # Estadísticas
            if registro_clasificado.get('TIPO_CLASIFICADO') == 'POSTE':
                estadisticas['clasificados_como_poste'] += 1
            if registro_clasificado.get('CATEGORIA_ESTRUCTURA') == 'ESTRUCTURAS EYT':
                estadisticas['estructuras_eyt'] += 1
        
        return registros_clasificados, estadisticas
    
    def obtener_estadisticas(self, registros: List[Dict]) -> Dict:
        """Genera estadísticas de clasificación para la UI"""
        estadisticas = {
            'total_registros': len(registros),
            'por_tipo_estructura': {},
            'clasificaciones_aplicadas': []
        }
        
        # Contar por tipo de estructura actual
        tipos_contador = {}
        grupos_contador = {}
        clasificaciones_tipo = {}
        
        for registro in registros:
            # Contar tipos actuales
            tipo_actual = registro.get('TIPO', 'SIN_TIPO')
            tipos_contador[tipo_actual] = tipos_contador.get(tipo_actual, 0) + 1
            
            # Contar grupos actuales
            grupo_actual = registro.get('GRUPO', 'SIN_GRUPO')
            grupos_contador[grupo_actual] = grupos_contador.get(grupo_actual, 0) + 1
            
            # Verificar si hubo cambio de TIPO por regla de clasificación
            if registro.get('OBSERVACION_CLASIFICACION'):
                clasificaciones_tipo['GRUPO_to_POSTE'] = clasificaciones_tipo.get('GRUPO_to_POSTE', 0) + 1
        
        estadisticas['por_tipo_estructura'] = tipos_contador
        estadisticas['por_grupo_estructura'] = grupos_contador
        
        # Convertir clasificaciones a formato para UI
        for key, cantidad in clasificaciones_tipo.items():
            if key == 'GRUPO_to_POSTE':
                estadisticas['clasificaciones_aplicadas'].append({
                    'tipo_original': 'Estructura con GRUPO',
                    'tipo_nuevo': 'POSTE',
                    'cantidad': cantidad
                })
        
        # Agregar estadística fija para GRUPO -> ESTRUCTURAS EYT
        if grupos_contador.get('ESTRUCTURAS EYT', 0) > 0:
            estadisticas['clasificaciones_aplicadas'].append({
                'tipo_original': 'Todas las estructuras',
                'tipo_nuevo': 'ESTRUCTURAS EYT',
                'cantidad': grupos_contador.get('ESTRUCTURAS EYT', 0)
            })
        
        return estadisticas
    
    def obtener_resumen_clasificacion(self, registros: List[Dict]) -> Dict:
        """Genera un resumen de la clasificación aplicada"""
        resumen = {
            'total_registros': len(registros),
            'tipos_encontrados': {},
            'grupos_encontrados': {},
            'clasificaciones_aplicadas': {}
        }
        
        for registro in registros:
            # Contar tipos originales
            tipo_original = registro.get('TIPO', 'SIN_TIPO')
            resumen['tipos_encontrados'][tipo_original] = resumen['tipos_encontrados'].get(tipo_original, 0) + 1
            
            # Contar grupos
            grupo = registro.get('GRUPO', 'SIN_GRUPO')
            resumen['grupos_encontrados'][grupo] = resumen['grupos_encontrados'].get(grupo, 0) + 1
            
            # Contar clasificaciones aplicadas
            clasificacion = registro.get('TIPO_CLASIFICADO', 'SIN_CLASIFICACION')
            resumen['clasificaciones_aplicadas'][clasificacion] = resumen['clasificaciones_aplicadas'].get(clasificacion, 0) + 1
        
        return resumen
    
    def _asignar_codigo_material(self, uc: str) -> str:
        """
        Asigna CODIGO_MATERIAL basado en el UC (Unidad Constructiva) usando mapeo jerárquico
        
        Sistema de mapeo jerárquico:
        1. Mapeos directos específicos (para UCs conocidos)
        2. Mapeo por patrones regex (extrae altura y carga)
        3. Mapeo por defecto basado en tipo de estructura
        
        Args:
            uc: Unidad Constructiva (ej: N3L75, N2L79, etc.)
            
        Returns:
            Código de material del catálogo o cadena vacía si no se encuentra
        """
        
        if not uc or uc is None:
            return ''
        
        uc_limpio = str(uc).strip().upper()
        
        if not uc_limpio:
            return ''
        
        # 1. Buscar en mapeos directos específicos
        mapeos_directos = MAPEO_UC_MATERIAL.get('MAPEOS_DIRECTOS', {})
        if uc_limpio in mapeos_directos:
            codigo_directo = mapeos_directos[uc_limpio]
            if codigo_directo in CATALOGO_MATERIALES:
                return codigo_directo
        
        # 2. Buscar por patrones regex
        reglas_patron = MAPEO_UC_MATERIAL.get('REGLAS_POR_PATRON', [])
        for regla in reglas_patron:
            patron = regla.get('patron', '')
            if not patron:
                continue
                
            match = re.match(patron, uc_limpio)
            if match:
                # Para patron N[nivel]L[carga]
                if 'mapeo' in regla:
                    carga = match.group(1)
                    mapeo_cargas = regla['mapeo']
                    if carga in mapeo_cargas:
                        codigo_patron = mapeo_cargas[carga]
                        if codigo_patron in CATALOGO_MATERIALES:
                            return codigo_patron
                
                # Para patron con altura explícita
                if 'alturas' in regla:
                    altura = match.group(1)
                    mapeo_alturas = regla['alturas']
                    if altura in mapeo_alturas:
                        # Tomar el primer código disponible para esa altura
                        codigos_altura = mapeo_alturas[altura]
                        for codigo_altura in codigos_altura:
                            if codigo_altura in CATALOGO_MATERIALES:
                                return codigo_altura
        
        # 3. Mapeo por defecto basado en clasificación de tipo
        tipo_estructura = self._clasificar_tipo_por_uc(uc_limpio)
        mapeo_defecto = MAPEO_UC_MATERIAL.get('MAPEO_POR_DEFECTO', {})
        
        if tipo_estructura in mapeo_defecto:
            codigo_defecto = mapeo_defecto[tipo_estructura]
            if codigo_defecto in CATALOGO_MATERIALES:
                return codigo_defecto
        
        # 4. Si no se encuentra nada, devolver cadena vacía
        return ''
    
    def _convertir_estado_salud(self, estado_salud) -> str:
        """
        Convierte valores de estado de salud de números a descriptivos
        
        Conversiones:
        1 -> BUENO
        2 -> REGULAR  
        3 -> MALO
        
        Solo se permiten los estados: BUENO, REGULAR, MALO
        También maneja valores ya descriptivos y devuelve cadena vacía
        para valores no reconocidos o nulos.
        """
        
        if not estado_salud or str(estado_salud).strip().upper() in ['', 'NAN', 'NONE']:
            return ''
        
        estado_str = str(estado_salud).strip().upper()
        
        # Buscar en el mapeo de estados
        estado_convertido = ESTADOS_SALUD.get(estado_str, '')
        
        # Solo permitir estados válidos: BUENO, REGULAR, MALO
        if estado_convertido in ['BUENO', 'REGULAR', 'MALO']:
            return estado_convertido
        
        # Si el valor no es válido, retornar vacío para que el usuario lo complete
        return ''
