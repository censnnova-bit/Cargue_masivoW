"""
Validador maestro que orquesta todas las validaciones del sistema.
Punto de entrada único para todas las validaciones.
"""

from typing import List, Dict, Any, Tuple
from .validaciones_datos import ValidacionesDatos
from .validaciones_archivo import ValidacionesArchivo, ValidacionesExcel


class ValidadorMaestro:
    """
    Clase maestra que coordina todas las validaciones del sistema.
    Proporciona una interfaz unificada para ejecutar validaciones de archivos, Excel y datos.
    """
    
    def __init__(self):
        self.validador_datos = ValidacionesDatos()
        self.validador_archivo = ValidacionesArchivo()
        self.validador_excel = ValidacionesExcel()
        self.errores_consolidados = []
    
    def ejecutar_validaciones_completas(self, 
                                      ruta_archivo: str, 
                                      df_excel, 
                                      nombres_hojas: List[str],
                                      registros_procesados: List[Tuple],
                                      indices_con_fid_rep: set,
                                      directorio_salida: str = None,
                                      hoja_objetivo: str = 'Estructuras_N1-N2-N3') -> Dict[str, Any]:
        """
        Ejecuta todas las validaciones del sistema de forma coordinada.
        
        Args:
            ruta_archivo: Ruta del archivo Excel
            df_excel: DataFrame de pandas con los datos
            nombres_hojas: Lista de nombres de hojas en el archivo
            registros_procesados: Lista de tuplas (registro, registro_excel, idx_excel)
            indices_con_fid_rep: Set de índices que tienen FID_rep
            directorio_salida: Directorio donde se guardarán los archivos generados
            hoja_objetivo: Nombre de la hoja que se está procesando
        
        Returns:
            Diccionario con resultados de todas las validaciones
        """
        resultado = {
            'errores_archivo': [],
            'errores_excel': [],
            'errores_datos': [],
            'errores_totales': [],
            'validacion_exitosa': True,
            'resumen': {
                'total_errores': 0,
                'errores_por_categoria': {},
                'archivos_validados': 1 if ruta_archivo else 0,
                'registros_procesados': len(registros_procesados)
            }
        }
        
        # 1. Validaciones de archivo (existencia, permisos, etc.)
        if ruta_archivo:
            resultado['errores_archivo'] = self.validador_archivo.ejecutar_validaciones_archivo(
                ruta_archivo, directorio_salida
            )
        
        # 2. Validaciones de estructura Excel
        if df_excel is not None:
            resultado['errores_excel'] = self.validador_excel.ejecutar_validaciones_excel(
                df_excel, nombres_hojas, hoja_objetivo
            )
        
        # 3. Validaciones de datos específicos (las 4 nuevas validaciones)
        if registros_procesados:
            resultado['errores_datos'] = self.validador_datos.ejecutar_validaciones_datos(
                registros_procesados, indices_con_fid_rep
            )
        
        # 4. Consolidar todos los errores
        resultado['errores_totales'] = (
            resultado['errores_archivo'] + 
            resultado['errores_excel'] + 
            resultado['errores_datos']
        )
        
        # 5. Generar resumen
        resultado['resumen']['total_errores'] = len(resultado['errores_totales'])
        resultado['resumen']['errores_por_categoria'] = {
            'archivo': len(resultado['errores_archivo']),
            'excel': len(resultado['errores_excel']),
            'datos': len(resultado['errores_datos'])
        }
        
        # 6. Determinar si la validación fue exitosa
        resultado['validacion_exitosa'] = resultado['resumen']['total_errores'] == 0
        
        # Almacenar errores consolidados
        self.errores_consolidados = resultado['errores_totales']
        
        return resultado
    
    def validar_solo_datos(self, registros_procesados: List[Tuple], indices_con_fid_rep: set) -> List[Dict[str, Any]]:
        """
        Ejecuta solo las validaciones de datos (para compatibilidad con código existente).
        
        Args:
            registros_procesados: Lista de tuplas (registro, registro_excel, idx_excel)
            indices_con_fid_rep: Set de índices que tienen FID_rep
        
        Returns:
            Lista de errores de validación de datos
        """
        return self.validador_datos.ejecutar_validaciones_datos(registros_procesados, indices_con_fid_rep)
    
    def validar_solo_archivo(self, ruta_archivo: str, directorio_salida: str = None) -> List[Dict[str, Any]]:
        """
        Ejecuta solo las validaciones de archivo.
        
        Args:
            ruta_archivo: Ruta del archivo a validar
            directorio_salida: Directorio de salida (opcional)
        
        Returns:
            Lista de errores de validación de archivo
        """
        return self.validador_archivo.ejecutar_validaciones_archivo(ruta_archivo, directorio_salida)
    
    def validar_solo_excel(self, df_excel, nombres_hojas: List[str], hoja_objetivo: str = 'Estructuras_N1-N2-N3') -> List[Dict[str, Any]]:
        """
        Ejecuta solo las validaciones de Excel.
        
        Args:
            df_excel: DataFrame de pandas con los datos
            nombres_hojas: Lista de nombres de hojas
            hoja_objetivo: Hoja que se está procesando
        
        Returns:
            Lista de errores de validación de Excel
        """
        return self.validador_excel.ejecutar_validaciones_excel(df_excel, nombres_hojas, hoja_objetivo)
    
    def obtener_errores_consolidados(self) -> List[Dict[str, Any]]:
        """Retorna todos los errores consolidados de la última ejecución"""
        return self.errores_consolidados.copy()
    
    def obtener_resumen_errores(self) -> Dict[str, Any]:
        """
        Retorna un resumen de los errores por categoría y tipo.
        
        Returns:
            Diccionario con estadísticas de errores
        """
        resumen = {
            'total_errores': len(self.errores_consolidados),
            'por_categoria': {'archivo': 0, 'excel': 0, 'datos': 0, 'general': 0},
            'por_hoja': {},
            'errores_criticos': 0,
            'errores_por_tipo': {}
        }
        
        for error in self.errores_consolidados:
            # Contar por categoría (basado en el campo 'archivo')
            categoria = error.get('archivo', 'general').lower()
            if categoria in resumen['por_categoria']:
                resumen['por_categoria'][categoria] += 1
            else:
                resumen['por_categoria']['general'] += 1
            
            # Contar por hoja
            hoja = error.get('hoja', 'Desconocida')
            resumen['por_hoja'][hoja] = resumen['por_hoja'].get(hoja, 0) + 1
            
            # Identificar errores críticos (basado en palabras clave)
            descripcion = error.get('descripcion', '').lower()
            if any(palabra in descripcion for palabra in ['no existe', 'faltante', 'obligatorio', 'critico']):
                resumen['errores_criticos'] += 1
            
            # Contar por tipo de error (basado en descripcion)
            tipo = self._identificar_tipo_error(descripcion)
            resumen['errores_por_tipo'][tipo] = resumen['errores_por_tipo'].get(tipo, 0) + 1
        
        return resumen
    
    def _identificar_tipo_error(self, descripcion: str) -> str:
        """Identifica el tipo de error basado en la descripción"""
        descripcion = descripcion.lower()
        
        if 'coordenada' in descripcion:
            return 'coordenadas'
        elif 'año' in descripcion or 'fecha' in descripcion:
            return 'fechas'
        elif 'ubicacion' in descripcion or 'nombre' in descripcion:
            return 'campos_obligatorios'
        elif 'archivo' in descripcion or 'directorio' in descripcion:
            return 'archivo'
        elif 'hoja' in descripcion or 'columna' in descripcion:
            return 'estructura_excel'
        elif 'formato' in descripcion or 'numerico' in descripcion:
            return 'formato_datos'
        else:
            return 'general'
    
    def limpiar_validaciones(self) -> None:
        """Limpia todas las validaciones y errores acumulados"""
        self.validador_datos.limpiar_errores()
        self.validador_archivo.limpiar_errores()
        self.validador_excel.limpiar_errores()
        self.errores_consolidados = []
    
    def generar_reporte_errores(self, formato: str = 'texto') -> str:
        """
        Genera un reporte formateado de todos los errores.
        
        Args:
            formato: 'texto', 'html' o 'csv'
        
        Returns:
            Reporte formateado como string
        """
        if formato == 'texto':
            return self._generar_reporte_texto()
        elif formato == 'html':
            return self._generar_reporte_html()
        elif formato == 'csv':
            return self._generar_reporte_csv()
        else:
            return self._generar_reporte_texto()
    
    def _generar_reporte_texto(self) -> str:
        """Genera reporte en formato texto plano"""
        if not self.errores_consolidados:
            return "No se encontraron errores de validación."
        
        reporte = f"REPORTE DE VALIDACIÓN\n{'='*50}\n\n"
        reporte += f"Total de errores encontrados: {len(self.errores_consolidados)}\n\n"
        
        # Agrupar por categoría
        por_categoria = {}
        for error in self.errores_consolidados:
            categoria = error.get('archivo', 'General')
            if categoria not in por_categoria:
                por_categoria[categoria] = []
            por_categoria[categoria].append(error)
        
        # Mostrar errores por categoría
        for categoria, errores in por_categoria.items():
            reporte += f"{categoria.upper()} ({len(errores)} errores)\n{'-'*30}\n"
            for i, error in enumerate(errores, 1):
                hoja = error.get('hoja', 'N/A')
                fila = error.get('fila', 'N/A')
                descripcion = error.get('descripcion', 'Error desconocido')
                reporte += f"{i:2d}. Hoja: {hoja:<20} Fila: {fila:<5} - {descripcion}\n"
            reporte += "\n"
        
        return reporte
    
    def _generar_reporte_html(self) -> str:
        """Genera reporte en formato HTML"""
        if not self.errores_consolidados:
            return "<p>No se encontraron errores de validación.</p>"
        
        html = """
        <html>
        <head><title>Reporte de Validación</title></head>
        <body>
        <h1>Reporte de Validación</h1>
        <p><strong>Total de errores:</strong> {total}</p>
        <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Archivo</th>
            <th>Hoja</th>
            <th>Fila</th>
            <th>Descripción</th>
        </tr>
        """.format(total=len(self.errores_consolidados))
        
        for error in self.errores_consolidados:
            html += f"""
            <tr>
                <td>{error.get('archivo', 'N/A')}</td>
                <td>{error.get('hoja', 'N/A')}</td>
                <td>{error.get('fila', 'N/A')}</td>
                <td>{error.get('descripcion', 'Error desconocido')}</td>
            </tr>
            """
        
        html += """
        </table>
        </body>
        </html>
        """
        
        return html
    
    def _generar_reporte_csv(self) -> str:
        """Genera reporte en formato CSV"""
        if not self.errores_consolidados:
            return "Archivo,Hoja,Fila,Descripcion\nSin errores,N/A,N/A,No se encontraron errores de validación"
        
        csv = "Archivo,Hoja,Fila,Descripcion\n"
        for error in self.errores_consolidados:
            archivo = error.get('archivo', 'N/A')
            hoja = error.get('hoja', 'N/A')
            fila = error.get('fila', 'N/A')
            descripcion = error.get('descripcion', 'Error desconocido').replace('"', '""')
            csv += f'"{archivo}","{hoja}","{fila}","{descripcion}"\n'
        
        return csv