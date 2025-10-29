"""
Módulo: repositories/oracle_connection.py
Gestiona las conexiones a la base de datos Oracle.
"""

import oracledb
from django.conf import settings
from typing import Dict


class OracleConnectionHelper:
    """
    Helper para gestionar conexiones a Oracle Database.
    Centraliza la lógica de configuración y conexión.
    """
    
    @classmethod
    def get_oracle_config(cls) -> Dict[str, str]:
        """
        Obtiene la configuración de Oracle desde Django settings.
        
        Returns:
            Dict con keys: user, password, dsn
        """
        db_config = settings.DATABASES.get('oracle', {})
        
        if not db_config:
            # Fallback a credenciales directas
            return {
                'user': 'CENS_CONSULTA',
                'password': 'C3N5C0N5ULT4',
                'dsn': 'EPM-PO18:1521/GENESTB'
            }
        
        # Construir DSN desde la configuración
        host = db_config.get('HOST', 'EPM-PO18')
        port = db_config.get('PORT', '1521')
        name = db_config.get('NAME', 'GENESTB')
        
        if ':' in name and '/' in name:
            dsn = name
        else:
            service_name = name.split('/')[-1] if '/' in name else name
            dsn = f"{host}:{port}/{service_name}"
        
        return {
            'user': db_config.get('USER', 'CENS_CONSULTA'),
            'password': db_config.get('PASSWORD', 'C3N5C0N5ULT4'),
            'dsn': dsn
        }
    
    @classmethod
    def get_connection(cls):
        """
        Crea y retorna una conexión a Oracle.
        Debe usarse con 'with'.
        
        Returns:
            oracledb.Connection: Conexión a Oracle
        """
        oracle_config = cls.get_oracle_config()
        return oracledb.connect(**oracle_config)
    
    @classmethod
    def test_connection(cls) -> bool:
        """
        Prueba la conexión a Oracle.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            oracle_config = cls.get_oracle_config()
            with oracledb.connect(**oracle_config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM DUAL")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            print(f"ERROR conexión Oracle: {str(e)}")
            return False
    
    @classmethod
    def is_oracle_enabled(cls) -> bool:
        """
        Verifica si las consultas Oracle están habilitadas.
        
        Returns:
            True si Oracle está habilitado
        """
        return not (hasattr(settings, 'ORACLE_ENABLED') and not settings.ORACLE_ENABLED)
