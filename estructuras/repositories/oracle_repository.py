"""
Módulo: repositories/oracle_repository.py
Repositorio para consultas a Oracle Database.
Centraliza todas las consultas a la base de datos Oracle.
"""

from typing import Tuple, Dict, Optional
from .oracle_connection import OracleConnectionHelper


class OracleRepository:
    """
    Repositorio para consultas a Oracle Database.
    Contiene todos los métodos de consulta a Oracle que antes estaban en OracleHelper.
    """
    
    @classmethod
    def obtener_coordenadas_por_fid(cls, fid_codigo: str) -> Tuple[str, str]:
        """
        Consulta Oracle para obtener coordenadas GPS por G3E_FID.
        
        Args:
            fid_codigo: Código FID a buscar
            
        Returns:
            Tuple con (coor_gps_lat, coor_gps_lon) como strings.
            Si no se encuentra o hay error, retorna ('', '')
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para FID {fid_codigo}")
            return ('', '')
            
        try:
            # Normalizar FID
            fid_limpio = str(fid_codigo).strip()
            if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
                return ('', '')
                
            # Limpiar FID: remover .0 si es un número entero
            if fid_limpio.endswith('.0'):
                try:
                    float_val = float(fid_limpio)
                    if float_val.is_integer():
                        fid_limpio = str(int(float_val))
                except (ValueError, OverflowError):
                    pass
            
            # Conectar a Oracle
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    # Configurar timeout
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT g3e_fid, coor_gps_lat, coor_gps_lon
                    FROM ccomun c
                    WHERE g3e_fid = :fid_param
                    """
                    
                    cursor.execute(query, {"fid_param": fid_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        g3e_fid, lat, lon = result
                        lat_str = str(lat) if lat is not None else ''
                        lon_str = str(lon) if lon is not None else ''
                        
                        print(f"✅ Oracle: FID {fid_limpio} -> lat={lat_str}, lon={lon_str}")
                        return (lat_str, lon_str)
                    else:
                        print(f"⚠️ Oracle: No se encontró FID {fid_limpio}")
                        return ('', '')
                        
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                print(f"⏱️ Oracle TIMEOUT para FID {fid_limpio}: Conexión expiró.")
            elif "connection" in error_msg.lower():
                print(f"🔌 Oracle CONEXIÓN para FID {fid_limpio}: No se pudo conectar.")
            else:
                print(f"❌ Oracle ERROR para FID {fid_limpio}: {error_msg}")
            return ('', '')

    @classmethod
    def obtener_fid_desde_codigo_operativo(cls, codigo_operativo: str) -> str:
        """
        Obtiene el FID real desde el código operativo.
        
        Args:
            codigo_operativo: Código operativo (ej: Z238163, Z231390)
            
        Returns:
            str: FID real o '' si no se encuentra
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para código {codigo_operativo}")
            return ''
            
        if not codigo_operativo:
            return ''
            
        codigo_limpio = str(codigo_operativo).strip()
        if not codigo_limpio or codigo_limpio.lower() in ('nan', 'none', ''):
            return ''
            
        print(f"🔍 Buscando FID para código operativo: {codigo_limpio}")
        
        try:
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT c.codigo_operativo, c.g3e_fid
                    FROM ccomun c
                    WHERE codigo_operativo = :codigo_param
                    """
                    
                    cursor.execute(query, {"codigo_param": codigo_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        codigo_op, fid_real = result
                        fid_str = str(fid_real) if fid_real is not None else ''
                        print(f"✅ Oracle: Código {codigo_limpio} -> FID {fid_str}")
                        return fid_str
                    else:
                        print(f"⚠️ Oracle: No se encontró FID para código {codigo_limpio}")
                        return ''
                        
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                print(f"⏱️ Oracle TIMEOUT para código {codigo_limpio}")
            elif "connection" in error_msg.lower():
                print(f"🔌 Oracle CONEXIÓN para código {codigo_limpio}")
            else:
                print(f"❌ Oracle ERROR para código {codigo_limpio}: {error_msg}")
            return ''

    @classmethod
    def obtener_fid_desde_enlace(cls, enlace: str) -> str:
        """
        Obtiene el FID desde el ENLACE.
        
        Args:
            enlace: Identificador/ENLACE (ej: P113, P240)
            
        Returns:
            str: FID o '' si no se encuentra
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para ENLACE {enlace}")
            return ''
            
        if not enlace:
            return ''
            
        enlace_limpio = str(enlace).strip().upper()
        if not enlace_limpio or enlace_limpio.lower() in ('nan', 'none', ''):
            return ''
            
        print(f"🔍 Buscando FID para ENLACE: {enlace_limpio}")
        
        try:
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT g3e_fid
                    FROM ccomun
                    WHERE UPPER(enlace) = :enlace_param
                    """
                    
                    cursor.execute(query, {"enlace_param": enlace_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        fid_real = result[0]
                        fid_str = str(fid_real) if fid_real is not None else ''
                        print(f"✅ Oracle: ENLACE {enlace_limpio} -> FID {fid_str}")
                        return fid_str
                    else:
                        print(f"⚠️ Oracle: No se encontró FID para ENLACE {enlace_limpio}")
                        return ''
                        
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                print(f"⏱️ Oracle TIMEOUT para ENLACE {enlace_limpio}")
            elif "connection" in error_msg.lower():
                print(f"🔌 Oracle CONEXIÓN para ENLACE {enlace_limpio}")
            else:
                print(f"❌ Oracle ERROR para ENLACE {enlace_limpio}: {error_msg}")
            return ''

    @classmethod
    def obtener_datos_completos_por_fid(cls, fid_real: str) -> Dict[str, str]:
        """
        Obtiene datos completos desde Oracle usando FID real.
        
        Args:
            fid_real: FID real
            
        Returns:
            Dict con claves: COOR_GPS_LAT, COOR_GPS_LON, TIPO, TIPO_ADECUACION, 
                           PROPIETARIO, UBICACION, CLASIFICACION_MERCADO
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para FID {fid_real}")
            return {}
            
        if not fid_real:
            return {}
            
        fid_limpio = str(fid_real).strip()
        if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
            return {}
            
        print(f"🔍 Buscando datos completos para FID: {fid_limpio}")
        
        try:
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT 
                        c.coor_gps_lat,
                        c.coor_gps_lon,
                        c.estado,
                        c.estado,
                        c.empresa_origen,
                        c.ubicacion,
                        c.clasificacion_mercado
                    FROM ccomun c
                    WHERE c.g3e_fid = :fid_param
                    """
                    
                    cursor.execute(query, {"fid_param": fid_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        lat, lon, estado, estado_salud, empresa_origen, ubicacion, clasif_mercado = result
                        
                        datos = {
                            'COOR_GPS_LAT': str(lat) if lat is not None else '',
                            'COOR_GPS_LON': str(lon) if lon is not None else '',
                            'TIPO': str(estado) if estado is not None else '',
                            'TIPO_ADECUACION': str(estado_salud) if estado_salud is not None else '',
                            'PROPIETARIO': str(empresa_origen) if empresa_origen is not None else '',
                            'UBICACION': str(ubicacion) if ubicacion is not None else '',
                            'CLASIFICACION_MERCADO': str(clasif_mercado) if clasif_mercado is not None else ''
                        }
                        
                        print(f"✅ Oracle datos completos FID {fid_limpio}")
                        return datos
                    else:
                        print(f"⚠️ Oracle: No se encontraron datos para FID {fid_limpio}")
                        return {}
                        
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                print(f"⏱️ Oracle TIMEOUT para FID {fid_limpio}")
            elif "connection" in error_msg.lower():
                print(f"🔌 Oracle CONEXIÓN para FID {fid_limpio}")
            else:
                print(f"❌ Oracle ERROR para FID {fid_limpio}: {error_msg}")
            return {}

    @classmethod
    def obtener_datos_txt_nuevo_por_fid(cls, fid_real: str) -> Dict[str, str]:
        """
        Obtiene datos específicos para TXT nuevo desde Oracle.
        Consulta tablas: eposte_at, ccomun, cpropietario.
        
        Args:
            fid_real: FID real
            
        Returns:
            Dict con claves: COORDENADA_X, COORDENADA_Y, TIPO, TIPO_ADECUACION,
                           PROPIETARIO, UBICACION, CLASIFICACION_MERCADO
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            print(f"DEBUG Oracle: Consultas Oracle deshabilitadas para FID {fid_real}")
            return {}
            
        if not fid_real:
            return {}
            
        fid_limpio = str(fid_real).strip()
        if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
            return {}
            
        print(f"🔍 Buscando datos TXT nuevo para FID: {fid_limpio}")
        
        try:
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT 
                        c.coor_gps_lon,
                        c.coor_gps_lat,
                        p.tipo,
                        p.tipo_adecuacion,
                        pr.propietario_1,
                        c.ubicacion,
                        c.clasificacion_mercado
                    FROM ccomun c
                        LEFT JOIN eposte_at p ON c.g3e_fid = p.g3e_fid
                        LEFT JOIN cpropietario pr ON c.g3e_fid = pr.g3e_fid
                    WHERE c.g3e_fid = :fid_param
                    """
                    
                    cursor.execute(query, {"fid_param": fid_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        lon, lat, tipo, tipo_adec, propietario, ubicacion, clasif_mercado = result
                        
                        datos = {
                            'COORDENADA_X': str(lon) if lon is not None else '',
                            'COORDENADA_Y': str(lat) if lat is not None else '',
                            'TIPO': str(tipo) if tipo is not None else '',
                            'TIPO_ADECUACION': str(tipo_adec) if tipo_adec is not None else '',
                            'PROPIETARIO': str(propietario) if propietario is not None else '',
                            'UBICACION': str(ubicacion) if ubicacion is not None else '',
                            'CLASIFICACION_MERCADO': str(clasif_mercado) if clasif_mercado is not None else ''
                        }
                        
                        print(f"✅ Oracle TXT nuevo FID {fid_limpio}")
                        return datos
                    else:
                        print(f"⚠️ Oracle: No se encontraron datos TXT nuevo para FID {fid_limpio}")
                        return {}
                        
        except Exception as e:
            error_msg = str(e)
            if "timed out" in error_msg.lower():
                print(f"⏱️ Oracle TIMEOUT para FID {fid_limpio}")
            elif "connection" in error_msg.lower():
                print(f"🔌 Oracle CONEXIÓN para FID {fid_limpio}")
            else:
                print(f"❌ Oracle ERROR para FID {fid_limpio}: {error_msg}")
            return {}

    @classmethod
    def obtener_datos_txt_baja_por_fid(cls, fid_real: str) -> Dict[str, str]:
        """
        Obtiene datos específicos para TXT baja desde Oracle.
        Utiliza la misma query que txt_nuevo.
        
        Args:
            fid_real: FID real
            
        Returns:
            Dict con datos de baja
        """
        # Usa la misma query que txt_nuevo
        return cls.obtener_datos_txt_nuevo_por_fid(fid_real)

    @classmethod
    def consultar_conductor_por_codigo(cls, codigo_conductor: str) -> Optional[Dict[str, str]]:
        """
        Consulta datos de conductor por código.
        
        Args:
            codigo_conductor: Código del conductor
            
        Returns:
            Dict con datos del conductor o None
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            return None
            
        if not codigo_conductor:
            return None
            
        codigo_limpio = str(codigo_conductor).strip()
        if not codigo_limpio or codigo_limpio.lower() in ('nan', 'none', ''):
            return None
            
        print(f"🔍 Consultando conductor: {codigo_limpio}")
        
        try:
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT codigo_conductor, tipo_conductor, calibre
                    FROM econ_pri_at
                    WHERE codigo_conductor = :codigo_param
                    """
                    
                    cursor.execute(query, {"codigo_param": codigo_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        codigo, tipo, calibre = result
                        datos = {
                            'CODIGO_CONDUCTOR': str(codigo) if codigo else '',
                            'TIPO_CONDUCTOR': str(tipo) if tipo else '',
                            'CALIBRE': str(calibre) if calibre else ''
                        }
                        print(f"✅ Oracle: Conductor {codigo_limpio} encontrado")
                        return datos
                    else:
                        print(f"⚠️ Oracle: No se encontró conductor {codigo_limpio}")
                        return None
                        
        except Exception as e:
            print(f"❌ Oracle ERROR consultando conductor {codigo_limpio}: {str(e)}")
            return None

    @classmethod
    def obtener_coordenadas_nodo_por_fid(cls, fid_nodo: str) -> Tuple[str, str]:
        """
        Obtiene coordenadas de un nodo por FID.
        
        Args:
            fid_nodo: FID del nodo
            
        Returns:
            Tuple (coord_x, coord_y)
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            return ('', '')
            
        if not fid_nodo:
            return ('', '')
            
        fid_limpio = str(fid_nodo).strip()
        if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
            return ('', '')
            
        print(f"🔍 Buscando coordenadas nodo FID: {fid_limpio}")
        
        try:
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT coor_gps_lon, coor_gps_lat
                    FROM ccomun
                    WHERE g3e_fid = :fid_param
                    """
                    
                    cursor.execute(query, {"fid_param": fid_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        lon, lat = result
                        lon_str = str(lon) if lon is not None else ''
                        lat_str = str(lat) if lat is not None else ''
                        print(f"✅ Oracle: Nodo FID {fid_limpio} -> ({lon_str}, {lat_str})")
                        return (lon_str, lat_str)
                    else:
                        print(f"⚠️ Oracle: No se encontró nodo FID {fid_limpio}")
                        return ('', '')
                        
        except Exception as e:
            print(f"❌ Oracle ERROR nodo FID {fid_limpio}: {str(e)}")
            return ('', '')

    @classmethod
    def consultar_norma_por_fid(cls, fid: str) -> Dict[str, str]:
        """
        Consulta datos de norma por FID.
        
        Args:
            fid: FID de la estructura
            
        Returns:
            Dict con datos de norma
        """
        if not OracleConnectionHelper.is_oracle_enabled():
            return {}
            
        if not fid:
            return {}
            
        fid_limpio = str(fid).strip()
        if not fid_limpio or fid_limpio.lower() in ('nan', 'none', ''):
            return {}
            
        print(f"🔍 Consultando norma para FID: {fid_limpio}")
        
        try:
            with OracleConnectionHelper.get_connection() as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.callTimeout = 5000
                    except AttributeError:
                        pass
                    
                    query = """
                    SELECT 
                        n.NORMA,
                        n.GRUPO,
                        n.CIRCUITO,
                        n.CODIGO_TRAFO,
                        n.MACRONORMA,
                        n.CANTIDAD,
                        n.TIPO_ADECUACION
                    FROM NORMA n
                    WHERE n.G3E_FID = :fid
                    AND ROWNUM = 1
                    """
                    
                    cursor.execute(query, {'fid': fid_limpio})
                    result = cursor.fetchone()
                    
                    if result:
                        columns = [col[0] for col in cursor.description]
                        datos = dict(zip(columns, result))
                        print(f"✅ Oracle: Norma encontrada para FID {fid_limpio}")
                        return datos
                    else:
                        print(f"⚠️ Oracle: No se encontró norma para FID {fid_limpio}")
                        return {}
                        
        except Exception as e:
            print(f"❌ Oracle ERROR consultando norma FID {fid_limpio}: {str(e)}")
            return {}
