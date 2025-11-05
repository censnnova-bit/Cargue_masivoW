"""
Generador base que contiene funcionalidades comunes para todos los generadores de archivos.
"""

import os
from typing import Dict, List, Any
from datetime import datetime
import glob
from django.conf import settings


class GeneradorBase:
    """
    Clase base para todos los generadores de archivos.
    Contiene funcionalidades comunes como manejo de nombres de archivos,
    limpieza de datos, y utilidades de generación.
    """
    
    def __init__(self, proceso):
        self.proceso = proceso
        self.base_path = os.path.join(settings.MEDIA_ROOT, 'generated')
        os.makedirs(self.base_path, exist_ok=True)
    
    def generar_nombre_archivo_con_indice(self, tipo_archivo: str, extension: str) -> str:
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
    
    def limpiar_fid(self, valor) -> str:
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
    
    def limpiar_valor_para_archivo(self, valor) -> str:
        """
        Limpia un valor para que no contenga caracteres problemáticos en archivos
        """
        if valor is None or str(valor).strip().lower() in ('nan', 'none', ''):
            return ''
        
        # Convertir a string y limpiar
        valor_str = str(valor).strip()
        
        # Remover caracteres problemáticos para archivos de texto
        caracteres_problemáticos = ['\n', '\r', '\t', '|', ';']
        for char in caracteres_problemáticos:
            valor_str = valor_str.replace(char, ' ')
        
        # Limpiar espacios múltiples
        valor_str = ' '.join(valor_str.split())
        
        return valor_str
    
    def formatear_coordenada(self, valor) -> str:
        """Formatea una coordenada a formato decimal con 6 decimales"""
        if not valor or str(valor).strip().lower() in ('nan', 'none', ''):
            return '0.000000'
        
        try:
            coord_float = float(str(valor).replace(',', '.'))
            return f"{coord_float:.6f}"
        except (ValueError, TypeError):
            return '0.000000'
    
    def formatear_fecha(self, valor, formato_salida: str = 'DD/MM/YYYY') -> str:
        """
        Formatea una fecha al formato requerido
        
        Args:
            valor: Valor de fecha en cualquier formato
            formato_salida: Formato de salida ('DD/MM/YYYY' por defecto)
        
        Returns:
            Fecha formateada o fecha por defecto si hay error
        """
        if not valor or str(valor).strip().lower() in ('nan', 'none', ''):
            return '01/01/1900'
        
        valor_str = str(valor).strip()
        
        # Intentar varios formatos de entrada
        formatos_entrada = [
            '%d/%m/%Y',     # DD/MM/YYYY
            '%Y-%m-%d',     # YYYY-MM-DD
            '%d-%m-%Y',     # DD-MM-YYYY
            '%m/%d/%Y',     # MM/DD/YYYY
            '%Y/%m/%d'      # YYYY/MM/DD
        ]
        
        for formato in formatos_entrada:
            try:
                fecha_obj = datetime.strptime(valor_str, formato)
                if formato_salida == 'DD/MM/YYYY':
                    return fecha_obj.strftime('%d/%m/%Y')
                elif formato_salida == 'YYYY-MM-DD':
                    return fecha_obj.strftime('%Y-%m-%d')
                else:
                    return fecha_obj.strftime(formato_salida)
            except ValueError:
                continue
        
        # Si no se pudo parsear, retornar fecha por defecto
        return '01/01/1900'
    
    def aplicar_valores_defecto(self, registro: Dict[str, Any], valores_defecto: Dict[str, str]) -> Dict[str, Any]:
        """
        Aplica valores por defecto a campos vacíos o faltantes
        
        Args:
            registro: Registro de datos
            valores_defecto: Diccionario con valores por defecto
        
        Returns:
            Registro con valores por defecto aplicados
        """
        for campo, valor_defecto in valores_defecto.items():
            if not registro.get(campo) or str(registro.get(campo, '')).strip() == '':
                registro[campo] = valor_defecto
        
        return registro
    
    def validar_campos_numericos(self, registro: Dict[str, Any], campos_numericos: Dict[str, str]) -> Dict[str, Any]:
        """
        Valida y formatea campos numéricos
        
        Args:
            registro: Registro de datos
            campos_numericos: Diccionario con campo -> tipo ('decimal' o 'entero')
        
        Returns:
            Registro con campos numéricos validados
        """
        for campo, tipo in campos_numericos.items():
            if campo in registro and registro[campo]:
                try:
                    valor = str(registro[campo]).replace(',', '.')
                    if tipo == 'decimal':
                        float_val = float(valor)
                        registro[campo] = f"{float_val:.6f}".rstrip('0').rstrip('.')
                    elif tipo == 'entero':
                        registro[campo] = str(int(float(valor)))
                except (ValueError, TypeError):
                    # Asignar valor por defecto si no se puede convertir
                    registro[campo] = '0' if tipo == 'entero' else '0.0'
        
        return registro
    
    def extraer_fid_rep(self, registro: Dict) -> str:
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
                vs = self.limpiar_fid(v)
                if vs:
                    return vs

        # 2. Buscar cualquier clave cuyo nombre normalizado contenga 'fid'
        try:
            for key in registro.keys():
                if not isinstance(key, str):
                    continue
                key_norm = key.lower().replace(' ', '_').replace('-', '_')
                if 'fid' in key_norm:
                    v = registro.get(key)
                    if v is None:
                        continue
                    vs = self.limpiar_fid(v)
                    if vs:
                        return vs
        except Exception:
            pass

        return ''
    
    def signature_registro(self, registro: Dict):
        """
        Construye una firma robusta del registro para detectar duplicados entre NUEVO y BAJA.

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
    
    def get_ruta_completa_archivo(self, nombre_archivo: str) -> str:
        """Retorna la ruta completa del archivo en el directorio de salida"""
        return os.path.join(self.base_path, nombre_archivo)
    
    def crear_encabezado_archivo(self, tipo_archivo: str, campos: List[str]) -> str:
        """
        Crea el encabezado estándar para archivos generados
        
        Args:
            tipo_archivo: Tipo de archivo (TXT, XML, etc.)
            campos: Lista de campos para el encabezado
        
        Returns:
            String con el encabezado formateado
        """
        separador = '|' if tipo_archivo.upper() == 'TXT' else ','
        return separador.join(campos)
    
    def crear_metadata_archivo(self, total_registros: int, tipo_archivo: str) -> Dict[str, Any]:
        """
        Crea metadata del archivo generado
        
        Args:
            total_registros: Número total de registros procesados
            tipo_archivo: Tipo de archivo generado
        
        Returns:
            Diccionario con metadata del archivo
        """
        return {
            'total_registros': total_registros,
            'tipo_archivo': tipo_archivo,
            'timestamp': datetime.now().isoformat(),
            'proceso_id': str(self.proceso.id) if self.proceso else None,
            'circuito': getattr(self.proceso, 'circuito', None)
        }
    
    def procesar_transformaciones_campo(self, registro: Dict[str, Any], transformaciones: Dict[str, callable]) -> Dict[str, Any]:
        """
        Aplica transformaciones específicas a campos del registro
        
        Args:
            registro: Registro a transformar
            transformaciones: Diccionario campo -> función de transformación
        
        Returns:
            Registro con transformaciones aplicadas
        """
        for campo, funcion_transformacion in transformaciones.items():
            if campo in registro:
                try:
                    registro[campo] = funcion_transformacion(registro[campo])
                except Exception as e:
                    print(f"⚠️ Error aplicando transformación a campo {campo}: {e}")
        
        return registro