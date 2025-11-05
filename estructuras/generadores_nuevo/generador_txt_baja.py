"""
Generador específico para archivos TXT de estructuras de baja.
"""

from .generador_base import GeneradorBase
from typing import Dict, List, Any


class GeneradorTxtBaja(GeneradorBase):
    """Genera archivos TXT para estructuras de baja"""
    
    def generar(self, datos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera archivo TXT para estructuras de baja
        
        Args:
            datos: Lista de registros a procesar
            
        Returns:
            Diccionario con información del archivo generado
        """
        filename = self.generar_nombre_archivo_con_indice('estructuras_baja', 'txt')
        filepath = self.get_ruta_completa_archivo(filename)
        
        encabezados = [
            'COORDENADA_X', 'COORDENADA_Y',
            'UBICACION', 'ESTADO', 'CODIGO_MATERIAL', 'FECHA_INSTALACION', 
            'FECHA_OPERACION', 'PROYECTO', 'EMPRESA', 'OBSERVACIONES',
            'CLASIFICACION_MERCADO', 'TIPO_PROYECTO', 'ID_MERCADO', 'UC',
            'ESTADO_SALUD', 'OT_MAXIMO', 'CODIGO_MARCACION', 'SALINIDAD',
            'ENLACE',  # Para baja es ENLACE en lugar de FID_ANTERIOR
            'GRUPO', 'TIPO', 'CLASE', 'USO', 'TIPO_ADECUACION',
            'PROPIETARIO', 'PORCENTAJE_PROPIEDAD'
        ]
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            # Escribir encabezados
            f.write('|'.join(encabezados) + '\n')
            
            # Escribir datos
            for registro in datos:
                linea_datos = []
                for campo in encabezados:
                    valor = registro.get(campo, '')
                    linea_datos.append(str(valor) if valor is not None else '')
                
                f.write('|'.join(linea_datos) + '\n')
        
        return {
            'archivo': filename,
            'ruta': filepath,
            'registros': len(datos),
            'tipo': 'TXT_BAJA'
        }