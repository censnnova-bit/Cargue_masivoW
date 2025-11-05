"""
Validaciones de archivos y estructuras Excel.
Maneja validaciones de formato de archivo y estructura de datos.
"""

from typing import List, Dict, Any
import os


class ValidacionesArchivo:
    """Maneja validaciones relacionadas con archivos y su estructura"""
    
    def __init__(self):
        self.errores = []
    
    def _agregar_error(self, fila: int, descripcion: str, hoja: str = 'General') -> None:
        """Agrega un error a la lista de errores con formato estándar"""
        error = {
            'archivo': 'Archivo',
            'hoja': hoja,
            'fila': fila,
            'descripcion': descripcion
        }
        self.errores.append(error)
    
    def validar_existencia_archivo(self, ruta_archivo: str) -> bool:
        """Valida que el archivo exista en la ruta especificada"""
        if not ruta_archivo:
            self._agregar_error(0, "No se proporcionó una ruta de archivo")
            return False
        
        if not os.path.exists(ruta_archivo):
            self._agregar_error(0, f"El archivo no existe en la ruta: {ruta_archivo}")
            return False
        
        return True
    
    def validar_extension_archivo(self, ruta_archivo: str, extensiones_permitidas: List[str] = None) -> bool:
        """Valida que el archivo tenga una extensión permitida"""
        if extensiones_permitidas is None:
            extensiones_permitidas = ['.xlsx', '.xls']
        
        if not ruta_archivo:
            return False
        
        _, extension = os.path.splitext(ruta_archivo)
        if extension.lower() not in extensiones_permitidas:
            self._agregar_error(
                0, 
                f"Extensión de archivo no permitida: {extension}. Extensiones permitidas: {', '.join(extensiones_permitidas)}"
            )
            return False
        
        return True
    
    def validar_estructura_directorio(self, directorio_salida: str) -> bool:
        """Valida que el directorio de salida exista o se pueda crear"""
        if not directorio_salida:
            self._agregar_error(0, "No se proporcionó un directorio de salida")
            return False
        
        # Crear directorio si no existe
        try:
            os.makedirs(directorio_salida, exist_ok=True)
            return True
        except Exception as e:
            self._agregar_error(0, f"No se pudo crear el directorio de salida: {directorio_salida}. Error: {str(e)}")
            return False
    
    def validar_permisos_escritura(self, ruta_directorio: str) -> bool:
        """Valida que se tengan permisos de escritura en el directorio"""
        if not ruta_directorio or not os.path.exists(ruta_directorio):
            return False
        
        try:
            # Intentar crear un archivo temporal para probar permisos
            archivo_test = os.path.join(ruta_directorio, 'test_permisos.tmp')
            with open(archivo_test, 'w') as f:
                f.write('test')
            os.remove(archivo_test)
            return True
        except Exception as e:
            self._agregar_error(0, f"Sin permisos de escritura en: {ruta_directorio}. Error: {str(e)}")
            return False
    
    def validar_tamaño_archivo(self, ruta_archivo: str, tamaño_max_mb: int = 100) -> bool:
        """Valida que el archivo no exceda el tamaño máximo permitido"""
        if not os.path.exists(ruta_archivo):
            return False
        
        try:
            tamaño_bytes = os.path.getsize(ruta_archivo)
            tamaño_mb = tamaño_bytes / (1024 * 1024)  # Convertir a MB
            
            if tamaño_mb > tamaño_max_mb:
                self._agregar_error(
                    0, 
                    f"El archivo excede el tamaño máximo permitido. Tamaño: {tamaño_mb:.2f} MB, Máximo: {tamaño_max_mb} MB"
                )
                return False
            
            return True
        except Exception as e:
            self._agregar_error(0, f"Error al verificar el tamaño del archivo: {str(e)}")
            return False
    
    def ejecutar_validaciones_archivo(self, ruta_archivo: str, directorio_salida: str = None) -> List[Dict[str, Any]]:
        """
        Ejecuta todas las validaciones de archivo
        
        Args:
            ruta_archivo: Ruta del archivo Excel a validar
            directorio_salida: Directorio donde se guardarán los archivos generados
        
        Returns:
            Lista de errores encontrados
        """
        self.errores = []  # Limpiar errores anteriores
        
        # Validaciones básicas de archivo
        if not self.validar_existencia_archivo(ruta_archivo):
            return self.errores.copy()
        
        self.validar_extension_archivo(ruta_archivo)
        self.validar_tamaño_archivo(ruta_archivo)
        
        # Validaciones de directorio de salida (si se proporciona)
        if directorio_salida:
            self.validar_estructura_directorio(directorio_salida)
            if os.path.exists(directorio_salida):
                self.validar_permisos_escritura(directorio_salida)
        
        return self.errores.copy()
    
    def obtener_errores(self) -> List[Dict[str, Any]]:
        """Retorna la lista actual de errores"""
        return self.errores.copy()
    
    def limpiar_errores(self) -> None:
        """Limpia la lista de errores"""
        self.errores = []


class ValidacionesExcel:
    """Maneja validaciones específicas de estructura y contenido Excel"""
    
    def __init__(self):
        self.errores = []
    
    def _agregar_error(self, fila: int, descripcion: str, hoja: str = 'Excel') -> None:
        """Agrega un error a la lista de errores con formato estándar"""
        error = {
            'archivo': 'Excel',
            'hoja': hoja,
            'fila': fila,
            'descripcion': descripcion
        }
        self.errores.append(error)
    
    def validar_columnas_requeridas(self, columnas_archivo: List[str], columnas_requeridas: List[str], hoja: str = 'Estructuras_N1-N2-N3') -> None:
        """Valida que todas las columnas requeridas estén presentes en el archivo"""
        columnas_faltantes = []
        
        for columna in columnas_requeridas:
            if columna not in columnas_archivo:
                columnas_faltantes.append(columna)
        
        if columnas_faltantes:
            self._agregar_error(
                1,
                f"Columnas faltantes en hoja '{hoja}': {', '.join(columnas_faltantes)}",
                hoja
            )
    
    def validar_hoja_existe(self, nombres_hojas: List[str], hoja_requerida: str) -> bool:
        """Valida que una hoja específica exista en el archivo Excel"""
        if hoja_requerida not in nombres_hojas:
            self._agregar_error(
                0,
                f"La hoja '{hoja_requerida}' no existe en el archivo Excel. Hojas disponibles: {', '.join(nombres_hojas)}",
                'General'
            )
            return False
        return True
    
    def validar_datos_vacios(self, total_registros: int, registros_validos: int, hoja: str = 'Estructuras_N1-N2-N3') -> None:
        """Valida que haya datos válidos para procesar"""
        if total_registros == 0:
            self._agregar_error(
                0,
                f"No se encontraron registros en la hoja '{hoja}'",
                hoja
            )
        elif registros_validos == 0:
            self._agregar_error(
                0,
                f"No se encontraron registros válidos para procesar en la hoja '{hoja}' (de {total_registros} registros totales)",
                hoja
            )
    
    def validar_formato_encabezados(self, encabezados: List[str], hoja: str = 'Estructuras_N1-N2-N3') -> None:
        """Valida el formato de los encabezados de columna"""
        for i, encabezado in enumerate(encabezados, 1):
            if not encabezado or str(encabezado).strip() == '':
                self._agregar_error(
                    1,
                    f"Encabezado vacío en columna {i} de la hoja '{hoja}'",
                    hoja
                )
            elif len(str(encabezado).strip()) > 100:  # Límite razonable para nombres de columna
                self._agregar_error(
                    1,
                    f"Encabezado muy largo en columna {i} ('{str(encabezado)[:50]}...')",
                    hoja
                )
    
    def validar_filas_vacias(self, df, hoja: str = 'Estructuras_N1-N2-N3') -> None:
        """Valida y reporta filas completamente vacías"""
        try:
            # Identificar filas completamente vacías
            filas_vacias = df.isnull().all(axis=1)
            indices_filas_vacias = df.index[filas_vacias].tolist()
            
            if len(indices_filas_vacias) > 0:
                # Reportar como advertencia, no como error crítico
                self._agregar_error(
                    0,
                    f"Se encontraron {len(indices_filas_vacias)} filas completamente vacías en '{hoja}' (filas: {', '.join(str(i+2) for i in indices_filas_vacias[:10])}{'...' if len(indices_filas_vacias) > 10 else ''})",
                    hoja
                )
        except Exception as e:
            self._agregar_error(
                0,
                f"Error al validar filas vacías: {str(e)}",
                hoja
            )
    
    def ejecutar_validaciones_excel(self, df, nombres_hojas: List[str], hoja_objetivo: str = 'Estructuras_N1-N2-N3') -> List[Dict[str, Any]]:
        """
        Ejecuta todas las validaciones de Excel
        
        Args:
            df: DataFrame de pandas con los datos de la hoja
            nombres_hojas: Lista de nombres de hojas en el archivo
            hoja_objetivo: Nombre de la hoja que se está procesando
        
        Returns:
            Lista de errores encontrados
        """
        self.errores = []  # Limpiar errores anteriores
        
        # Validar que la hoja existe
        if not self.validar_hoja_existe(nombres_hojas, hoja_objetivo):
            return self.errores.copy()
        
        if df is not None and not df.empty:
            # Validar estructura del DataFrame
            self.validar_formato_encabezados(df.columns.tolist(), hoja_objetivo)
            self.validar_filas_vacias(df, hoja_objetivo)
            
            # Validar cantidad de datos
            total_registros = len(df)
            registros_no_vacios = len(df.dropna(how='all'))
            self.validar_datos_vacios(total_registros, registros_no_vacios, hoja_objetivo)
        
        return self.errores.copy()
    
    def obtener_errores(self) -> List[Dict[str, Any]]:
        """Retorna la lista actual de errores"""
        return self.errores.copy()
    
    def limpiar_errores(self) -> None:
        """Limpia la lista de errores"""
        self.errores = []