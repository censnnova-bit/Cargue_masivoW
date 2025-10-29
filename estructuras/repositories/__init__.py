"""
Módulo: repositories
Contiene clases para acceso a datos desde diferentes fuentes.
"""

from .oracle_repository import OracleRepository
from .oracle_connection import OracleConnectionHelper

__all__ = ['OracleRepository', 'OracleConnectionHelper']
