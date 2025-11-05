"""
Módulo de generadores de archivos - Nueva organización
Este módulo complementa la carpeta generadores/ existente con nuevos generadores reorganizados.
"""

from .generador_base import GeneradorBase
from .generador_txt_nuevo import GeneradorTxtNuevo
from .generador_txt_baja import GeneradorTxtBaja
from .generador_xml import GeneradorXML
from .file_manager import FileManager

__all__ = [
    'GeneradorBase',
    'GeneradorTxtNuevo', 
    'GeneradorTxtBaja',
    'GeneradorXML',
    'FileManager'
]