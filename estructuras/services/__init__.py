"""
FACHADA MODULAR - Reemplaza monolito de 5,401 líneas
=====================================================

Este módulo expone la API pública sin depender del monolito.
Todas las funcionalidades están delegadas a componentes modulares.

Backup del código original: ../services_monolito_original.py (5,401 líneas)
"""

import logging
import os
from typing import Optional, Dict, Any, List

from django.conf import settings

# ============================================================================
# IMPORTS DESDE ARQUITECTURA MODULAR
# ============================================================================

# Pipeline principal
from .pipeline_estructuras import procesar_excel

# Alias para compatibilidad con API antigua (views.py espera este nombre)
procesar_estructura_completo = procesar_excel

# Clasificador
from ..classifiers.clasificador_estructuras import ClasificadorEstructuras

# Utilidades
from ..utils.data_utils import DataUtils
from ..utils.archivos import generar_nombre_archivo

# Repositorios Oracle
from ..repositories.oracle_helper import OracleHelper

# Ingestion
from ..ingestion.lector_excel import ExcelProcessor

# Generadores especializados
from ..generadores.txt_estructuras import TXTEstructurasGenerator
from ..generadores.xml_estructuras import XMLEstructurasGenerator
from ..generadores.txt_norma import TXTNormaGenerator
from ..generadores.xml_norma import XMLNormaGenerator

logger = logging.getLogger(__name__)


# ============================================================================
# CLASE FILEGENATOR - FACHADA DE GENERACIÓN DE ARCHIVOS
# ============================================================================

class FileGenerator:
    """Fachada que orquesta la generación de archivos TXT y XML"""
    
    def __init__(self, proceso_or_id, df=None, config=None):
        """
        Inicializa el generador.
        
        Args:
            proceso_or_id: Instancia de ProcesoEstructura o ID del proceso
            df: DataFrame de pandas (opcional, para compatibilidad)
            config: Configuración opcional
        """
        self.df = df
        self.config = config or {}
        self.archivos_generados = []
        
        # Compatibilidad: acepta objeto Proceso o proceso_id
        if hasattr(proceso_or_id, 'id'):
            # Es un objeto ProcesoEstructura
            self.proceso = proceso_or_id
            self.proceso_id = str(proceso_or_id.id)
        else:
            # Es un ID (UUID/str), buscar el objeto
            from ..models import ProcesoEstructura
            try:
                self.proceso = ProcesoEstructura.objects.get(id=proceso_or_id)
                self.proceso_id = str(proceso_or_id)
            except ProcesoEstructura.DoesNotExist:
                # Si no existe, crear objeto mock para tests
                self.proceso = None
                self.proceso_id = str(proceso_or_id)
        
        # Generadores especializados (solo si tenemos proceso válido)
        if self.proceso:
            self.txt_estructuras_gen = TXTEstructurasGenerator(self.proceso)
            self.xml_estructuras_gen = XMLEstructurasGenerator(self.proceso)
            self.txt_norma_gen = TXTNormaGenerator(self.proceso)
            self.xml_norma_gen = XMLNormaGenerator(self.proceso)
        else:
            # Modo degradado sin generadores
            self.txt_estructuras_gen = None
            self.xml_estructuras_gen = None
            self.txt_norma_gen = None
            self.xml_norma_gen = None
        
        logger.info(f"FileGenerator inicializado: {self.proceso_id}")
    
    def generar_archivos(self, tipo_estructura: str) -> Dict[str, Any]:
        """Generar archivos TXT y XML según tipo"""
        if not self.proceso:
            raise ValueError("No hay proceso válido. FileGenerator requiere un ProcesoEstructura.")
        
        logger.info(f"Generando: {tipo_estructura}")
        
        if tipo_estructura == "ESTRUCTURAS":
            return self._generar_estructuras()
        elif tipo_estructura == "NORMAS":
            return self._generar_normas()
        else:
            raise ValueError(f"Tipo no soportado: {tipo_estructura}")
    
    def _generar_estructuras(self) -> Dict[str, Any]:
        """Generar archivos para estructuras"""
        resultado = {
            'txt_new': None,
            'xml_new': None,
            'txt_baja': None,
            'xml_baja': None,
            'estadisticas': {}
        }
        
        try:
            # Los generadores devuelven solo el filename, no un diccionario
            txt_new_filename = self.txt_estructuras_gen.generar_txt()
            resultado['txt_new'] = txt_new_filename if txt_new_filename else None
            
            # Generar TXT baja si hay datos (puede no existir si no hay registros de baja)
            try:
                txt_baja_filename = self.txt_estructuras_gen.generar_txt_baja()
                resultado['txt_baja'] = txt_baja_filename if txt_baja_filename else None
            except Exception as e:
                # Si no hay registros para baja o el método no existe, dejar como None
                logger.info(f"TXT baja no generado: {str(e)}")
                resultado['txt_baja'] = None
            
            xml_new_filename = self.xml_estructuras_gen.generar_xml()
            resultado['xml_new'] = xml_new_filename if xml_new_filename else None
            
            # Generar XML baja si hay datos (puede no existir si no hay registros de baja)
            try:
                xml_baja_filename = self.xml_estructuras_gen.generar_xml_baja()
                resultado['xml_baja'] = xml_baja_filename if xml_baja_filename else None
            except Exception as e:
                # Si no hay registros para baja o el método no existe, dejar como None
                logger.info(f"XML baja no generado: {str(e)}")
                resultado['xml_baja'] = None
            
            self.archivos_generados.extend(filter(None, [
                resultado['txt_new'], resultado['xml_new'],
                resultado['txt_baja'], resultado['xml_baja']
            ]))
            
            logger.info(f"Estructuras: {len(self.archivos_generados)} archivos")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise
        
        return resultado
    
    def _generar_normas(self) -> Dict[str, Any]:
        """Generar archivos para normas"""
        resultado = {
            'txt': None,
            'xml': None,
            'estadisticas': {}
        }
        
        try:
            # Los generadores devuelven solo el filename, no un diccionario
            txt_filename = self.txt_norma_gen.generar_txt()
            resultado['txt'] = txt_filename if txt_filename else None
            
            xml_filename = self.xml_norma_gen.generar_xml()
            resultado['xml'] = xml_filename if xml_filename else None
            
            self.archivos_generados.extend(filter(None, [
                resultado['txt'], resultado['xml']
            ]))
            
            logger.info(f"Normas: {len(self.archivos_generados)} archivos")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise
        
        return resultado
    
    def generar_y_guardar(self, tipo_estructura: str) -> Dict[str, Any]:
        """Generar archivos Y guardar rutas en BD automáticamente"""
        if not self.proceso:
            raise ValueError("No hay proceso válido para guardar archivos")
        
        # Generar archivos
        resultado = self.generar_archivos(tipo_estructura)
        
        # Mapear y guardar en archivos_generados del proceso
        if not self.proceso.archivos_generados:
            self.proceso.archivos_generados = {}
        
        if tipo_estructura == "ESTRUCTURAS":
            # Mapear estructuras: txt_new -> txt, xml_new -> xml
            if 'txt_new' in resultado and resultado['txt_new']:
                self.proceso.archivos_generados['txt'] = resultado['txt_new']
            if 'xml_new' in resultado and resultado['xml_new']:
                self.proceso.archivos_generados['xml'] = resultado['xml_new']
            if 'txt_baja' in resultado and resultado['txt_baja']:
                self.proceso.archivos_generados['txt_baja'] = resultado['txt_baja']
            if 'xml_baja' in resultado and resultado['xml_baja']:
                self.proceso.archivos_generados['xml_baja'] = resultado['xml_baja']
                
        elif tipo_estructura == "NORMAS":
            # Mapear normas: txt -> norma_txt, xml -> norma_xml
            if 'txt' in resultado and resultado['txt']:
                self.proceso.archivos_generados['norma_txt'] = resultado['txt']
            if 'xml' in resultado and resultado['xml']:
                self.proceso.archivos_generados['norma_xml'] = resultado['xml']
        
        # Guardar en base de datos
        self.proceso.save()
        logger.info(f"✅ Rutas guardadas en proceso {self.proceso_id}: {list(self.proceso.archivos_generados.keys())}")
        
        return resultado
    
    def generar_txt(self, tipo_estructura: Optional[str] = None) -> Dict[str, Any]:
        """Generar solo TXT"""
        if tipo_estructura == "ESTRUCTURAS":
            return self.txt_estructuras_gen.generar_txt()
        elif tipo_estructura == "NORMAS":
            return self.txt_norma_gen.generar_txt()
        else:
            raise ValueError(f"Tipo no soportado: {tipo_estructura}")
    
    def generar_xml(self, tipo_estructura: Optional[str] = None) -> Dict[str, Any]:
        """Generar solo XML"""
        if tipo_estructura == "ESTRUCTURAS":
            return self.xml_estructuras_gen.generar_xml()
        elif tipo_estructura == "NORMAS":
            return self.xml_norma_gen.generar_xml()
        else:
            raise ValueError(f"Tipo no soportado: {tipo_estructura}")
    
    # ========================================================================
    # MÉTODOS ESPECÍFICOS PARA NORMA Y LÍNEA
    # ========================================================================
    
    def generar_norma_txt(self) -> str:
        """Genera archivo TXT de normas"""
        try:
            from ..generadores.txt_norma import TXTNormaGenerator
            gen = TXTNormaGenerator(self.proceso)
            filename = gen.generar_norma_txt()
            logger.info(f"Norma TXT generado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generando Norma TXT: {e}", exc_info=True)
            raise
    
    def generar_norma_xml(self) -> str:
        """Genera archivo XML de normas"""
        try:
            from ..generadores.xml_norma import XMLNormaGenerator
            gen = XMLNormaGenerator(self.proceso)
            filename = gen.generar_norma_xml()
            logger.info(f"Norma XML generado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generando Norma XML: {e}", exc_info=True)
            raise
    
    def generar_txt_linea(self) -> str:
        """Genera archivo TXT de línea/conductores NUEVO"""
        try:
            from ..generadores.txt_linea import TXTLineaGenerator
            gen = TXTLineaGenerator(self.proceso)
            filename = gen.generar_txt_linea()
            logger.info(f"Línea TXT NUEVO generado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generando Línea TXT: {e}", exc_info=True)
            raise
    
    def generar_txt_baja_linea(self) -> str:
        """Genera archivo TXT de línea/conductores BAJA"""
        try:
            from ..generadores.txt_linea import TXTLineaGenerator
            gen = TXTLineaGenerator(self.proceso)
            filename = gen.generar_txt_baja_linea()
            logger.info(f"Línea TXT BAJA generado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generando Línea TXT BAJA: {e}", exc_info=True)
            raise
    
    def generar_xml_linea(self) -> str:
        """Genera archivo XML de línea/conductores NUEVO"""
        try:
            from ..generadores.xml_linea import XMLLineaGenerator
            gen = XMLLineaGenerator(self.proceso)
            filename = gen.generar_xml_linea()
            logger.info(f"Línea XML NUEVO generado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generando Línea XML: {e}", exc_info=True)
            raise
    
    def generar_xml_baja_linea(self) -> str:
        """Genera archivo XML de línea/conductores BAJA"""
        try:
            from ..generadores.xml_linea import XMLLineaGenerator
            gen = XMLLineaGenerator(self.proceso)
            filename = gen.generar_xml_baja_linea()
            logger.info(f"Línea XML BAJA generado: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generando Línea XML BAJA: {e}", exc_info=True)
            raise
    
    def get_archivos_generados(self) -> List[str]:
        """Obtener archivos generados"""
        return [f for f in self.archivos_generados if f]
    
    def limpiar_archivos_temporales(self) -> int:
        """Eliminar archivos temporales"""
        count = 0
        for archivo in self.get_archivos_generados():
            if archivo and os.path.exists(archivo):
                try:
                    os.remove(archivo)
                    count += 1
                except Exception as e:
                    logger.warning(f"No se pudo eliminar {archivo}: {e}")
        
        logger.info(f"Archivos eliminados: {count}")
        return count


# ============================================================================
# COMPATIBILIDAD CON API ANTIGUA
# ============================================================================

class DataTransformer:
    """Transformer - Compatibilidad"""
    def __init__(self):
        from ..transformers.data_transformer import DataTransformer as MT
        self._t = MT()
    def __getattr__(self, name):
        return getattr(self._t, name)


class DataMapper:
    """Mapper - Compatibilidad"""
    @staticmethod
    def mapear_campos(df, mapeo):
        return DataUtils.mapear_campos(df, mapeo)


# ============================================================================
# EXPORTS - API PÚBLICA
# ============================================================================

__all__ = [
    # Función principal del pipeline
    'procesar_estructura_completo',
    
    # Clases principales
    'FileGenerator',
    'ClasificadorEstructuras',
    
    # Utilidades
    'DataUtils',
    'OracleHelper',
    'ExcelProcessor',
    
    # Transformadores (compatibilidad)
    'DataTransformer',
    'DataMapper',
    
    # Generadores especializados (uso avanzado)
    'TXTEstructurasGenerator',
    'XMLEstructurasGenerator',
    'TXTNormaGenerator',
    'XMLNormaGenerator',
]

# ============================================================================
