"""
Generador de archivos XML.
"""

from .generador_base import GeneradorBase
from typing import Dict, List, Any


class GeneradorXML(GeneradorBase):
    """Genera archivos XML para normas"""
    
    def generar_norma_nuevo(self, datos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera archivo XML para normas nuevas
        
        Args:
            datos: Lista de registros a procesar
            
        Returns:
            Diccionario con información del archivo generado
        """
        filename = self.generar_nombre_archivo_con_indice('norma_nuevo', 'xml')
        filepath = self.get_ruta_completa_archivo(filename)
        
        # Generar XML básico (estructura simplificada para el ejemplo)
        xml_content = self._generar_contenido_xml(datos, 'NUEVO')
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(xml_content)
        
        return {
            'archivo': filename,
            'ruta': filepath,
            'registros': len(datos),
            'tipo': 'XML_NORMA_NUEVO'
        }
    
    def generar_norma_baja(self, datos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera archivo XML para normas de baja
        
        Args:
            datos: Lista de registros a procesar
            
        Returns:
            Diccionario con información del archivo generado
        """
        filename = self.generar_nombre_archivo_con_indice('norma_baja', 'xml')
        filepath = self.get_ruta_completa_archivo(filename)
        
        xml_content = self._generar_contenido_xml(datos, 'BAJA')
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(xml_content)
        
        return {
            'archivo': filename,
            'ruta': filepath,
            'registros': len(datos),
            'tipo': 'XML_NORMA_BAJA'
        }
    
    def _generar_contenido_xml(self, datos: List[Dict[str, Any]], tipo: str) -> str:
        """
        Genera el contenido XML para los datos proporcionados
        
        Args:
            datos: Lista de registros
            tipo: Tipo de XML ('NUEVO' o 'BAJA')
            
        Returns:
            String con contenido XML
        """
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append(f'<normas tipo="{tipo}">')
        
        for i, registro in enumerate(datos):
            xml_lines.append(f'  <norma id="{i+1}">')
            
            # Campos principales para XML de norma
            campos_xml = [
                'NORMA', 'GRUPO', 'CIRCUITO', 'CODIGO_TRAFO',
                'MACRONORMA', 'CANTIDAD', 'TIPO_ADECUACION'
            ]
            
            for campo in campos_xml:
                valor = self.limpiar_valor_para_archivo(registro.get(campo, ''))
                xml_lines.append(f'    <{campo.lower()}>{valor}</{campo.lower()}>')
            
            xml_lines.append('  </norma>')
        
        xml_lines.append('</normas>')
        
        return '\n'.join(xml_lines)