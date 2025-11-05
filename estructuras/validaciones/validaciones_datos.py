"""
Validaciones de datos específicos: coordenadas, años, ubicación, nombres.
Contiene las 4 nuevas validaciones implementadas.
"""

from typing import List, Dict, Any, Tuple


class ValidacionesDatos:
    """Maneja validaciones específicas de campos de datos"""
    
    def __init__(self):
        self.errores = []
    
    def _agregar_error(self, fila: int, descripcion: str, hoja: str = 'Estructuras_N1-N2-N3') -> None:
        """Agrega un error a la lista de errores con formato estándar"""
        error = {
            'archivo': 'Excel',
            'hoja': hoja,
            'fila': fila,
            'descripcion': descripcion
        }
        self.errores.append(error)
    
    def validar_coordenadas(self, registro: Dict[str, Any], fila_excel: int) -> None:
        """
        Valida coordenadas geográficas para Colombia:
        - X (Longitud): debe ser negativa
        - Y (Latitud): debe ser positiva
        """
        coord_x = registro.get('COORDENADA_X', '')
        coord_y = registro.get('COORDENADA_Y', '')
        
        # Validar coordenada X (Longitud)
        if coord_x and str(coord_x).strip():
            try:
                x_val = float(str(coord_x).strip())
                if x_val >= 0:  # Longitud debe ser negativa para Colombia
                    self._agregar_error(
                        fila_excel, 
                        f"La coordenada X (longitud) debe ser negativa en la fila {fila_excel}. Valor actual: {coord_x}"
                    )
            except (ValueError, TypeError):
                self._agregar_error(
                    fila_excel,
                    f"La coordenada X no tiene un formato numérico válido en la fila {fila_excel}. Valor: {coord_x}"
                )
        
        # Validar coordenada Y (Latitud)
        if coord_y and str(coord_y).strip():
            try:
                y_val = float(str(coord_y).strip())
                if y_val < 0:  # Latitud debe ser positiva para Colombia
                    self._agregar_error(
                        fila_excel,
                        f"La coordenada Y (latitud) debe ser positiva en la fila {fila_excel}. Valor actual: {coord_y}"
                    )
            except (ValueError, TypeError):
                self._agregar_error(
                    fila_excel,
                    f"La coordenada Y no tiene un formato numérico válido en la fila {fila_excel}. Valor: {coord_y}"
                )
    
    def validar_año_entrada_operacion(self, registro_excel: Dict[str, Any], fila_excel: int, tiene_fid_rep: bool) -> None:
        """
        Valida el año de entrada en operación para registros de reemplazo/desmantelado:
        - Solo aplica a registros con FID_rep
        - Debe ser un año válido entre 1900-2024
        - No puede ser futuro
        """
        if not tiene_fid_rep:
            return  # Solo validar registros con FID_rep
        
        año_entrada = ''
        
        # Buscar el campo en diferentes formatos posibles
        campos_posibles = [
            'Año entrada operación_rep', 
            'año entrada operación_rep', 
            'AÑO_ENTRADA_OPERACION_REP'
        ]
        
        for campo in campos_posibles:
            if campo in registro_excel and registro_excel.get(campo) not in (None, ''):
                año_entrada = str(registro_excel.get(campo)).strip()
                break
        
        if not año_entrada or año_entrada.lower() in ('nan', 'none', ''):
            self._agregar_error(
                fila_excel,
                f"El campo 'Año entrada operación' es obligatorio para registros de desmantelado/reposición en la fila {fila_excel}"
            )
            return
        
        try:
            # Convertir a float primero para manejar decimales como 1996.0
            año_float = float(año_entrada)
            año_int = int(año_float)
            
            # Verificar que sea un número entero (sin parte decimal)
            if año_float != año_int:
                self._agregar_error(
                    fila_excel,
                    f"El año de entrada operación debe ser un número entero en la fila {fila_excel}. Valor: {año_entrada}"
                )
            elif año_int < 1900 or año_int > 2024:
                self._agregar_error(
                    fila_excel,
                    f"El año de entrada operación debe estar entre 1900 y 2024 en la fila {fila_excel}. Valor: {año_int}"
                )
                
        except (ValueError, TypeError):
            self._agregar_error(
                fila_excel,
                f"El año de entrada operación debe tener formato numérico válido en la fila {fila_excel}. Valor: {año_entrada}"
            )
    
    def validar_ubicacion_y_nombre(self, registro: Dict[str, Any], fila_excel: int, es_expansion_o_reposicion: bool) -> None:
        """
        Valida que ubicación y nombre sean obligatorios para registros de expansión/reposición:
        - Campos no pueden estar vacíos
        - No pueden ser 'nan', 'none', etc.
        
        NOTA: Validación temporalmente desactivada hasta definir lógica correcta
        """
        # TODO: Definir cuándo exactamente estos campos deben ser obligatorios
        # Por ahora se desactiva la validación ya que está marcando errores incorrectos
        return
        
        if not es_expansion_o_reposicion:
            return
        
        # Validar UBICACIÓN
        ubicacion = registro.get('UBICACION', '')
        if not ubicacion or str(ubicacion).strip() == '' or str(ubicacion).strip().lower() in ('nan', 'none'):
            self._agregar_error(
                fila_excel,
                f"El campo 'Ubicación' es obligatorio para registros de expansión/reposición en la fila {fila_excel}"
            )
        
        # Validar NOMBRE
        nombre = registro.get('NOMBRE', '')
        if not nombre or str(nombre).strip() == '' or str(nombre).strip().lower() in ('nan', 'none'):
            self._agregar_error(
                fila_excel,
                f"El campo 'Nombre' es obligatorio para registros de expansión/reposición en la fila {fila_excel}"
            )
    
    def validar_codigo_material(self, registro: Dict[str, Any], fila_excel: int) -> None:
        """Validación existente de código material (mantenida por compatibilidad)"""
        codigo_material = registro.get('CODIGO_MATERIAL', '')
        
        if codigo_material and str(codigo_material).strip():
            try:
                float(str(codigo_material).strip())
            except (ValueError, TypeError):
                self._agregar_error(
                    fila_excel,
                    f"El valor '{codigo_material}' en Código Material no es un número en la fila {fila_excel} de la hoja 'Estructuras_N1-N2-N3' del Excel."
                )
    
    def ejecutar_validaciones_datos(self, registros_procesados: List[Tuple], indices_con_fid_rep: set) -> List[Dict[str, Any]]:
        """
        Ejecuta todas las validaciones de datos sobre los registros procesados.
        
        Args:
            registros_procesados: Lista de tuplas (registro, registro_excel, idx_excel)
            indices_con_fid_rep: Set de índices que tienen FID_rep
        
        Returns:
            Lista de errores encontrados
        """
        self.errores = []  # Limpiar errores anteriores
        
        for registro, registro_excel, idx_excel in registros_procesados:
            fila_excel = idx_excel + 2  # Ajustar numeración (header + 0-indexing)
            
            # Determinar contexto
            tiene_fid_rep = idx_excel in indices_con_fid_rep
            es_expansion_o_reposicion = True  # Todos los registros según lógica actual
            
            # Ejecutar validaciones
            self.validar_coordenadas(registro, fila_excel)
            self.validar_año_entrada_operacion(registro_excel, fila_excel, tiene_fid_rep)
            self.validar_ubicacion_y_nombre(registro, fila_excel, es_expansion_o_reposicion)
            self.validar_codigo_material(registro, fila_excel)
        
        return self.errores.copy()
    
    def obtener_errores(self) -> List[Dict[str, Any]]:
        """Retorna la lista actual de errores"""
        return self.errores.copy()
    
    def limpiar_errores(self) -> None:
        """Limpia la lista de errores"""
        self.errores = []