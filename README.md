# Sistema de Cargue Masivo de Estructuras

Sistema web Django para procesamiento y carga masiva de estructuras eléctricas del Grupo EPM.

## 🚀 Características

- **Carga de Excel**: Procesa archivos Excel con estructuras, conductores y normas
- **Clasificación Automática**: Clasifica estructuras en NUEVO, BAJA o CAMBIO
- **Enriquecimiento Oracle**: Consulta automática de datos desde Oracle
- **Generación de Archivos**: Genera archivos TXT y XML para carga masiva en GIS
- **8 Tipos de Exportación**:
  - TXT Estructuras Nuevas
  - XML Configuración Nuevas
  - TXT Estructuras Baja
  - XML Configuración Baja
  - TXT Norma
  - XML Norma
  - TXT Línea (Conductor)
  - XML Línea (Conductor)

## 📋 Requisitos

- Python 3.13+
- Django 5.2.5
- Oracle Client (cx_Oracle)
- Pandas
- OpenPyXL

## 🔧 Instalación

```bash
# Clonar repositorio
git clone https://github.com/censnnova-bit/Cargue_masivoW.git
cd Cargue_masivoW

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate

# Iniciar servidor de desarrollo
python manage.py runserver
```

## 🌐 Uso

1. Acceder a http://127.0.0.1:8000/
2. Cargar archivo Excel con estructuras
3. Esperar procesamiento automático
4. Descargar archivos generados desde la página del proceso

## 📁 Estructura del Proyecto

```
Cargue_Masivo/
├── estructuras/           # Aplicación principal
│   ├── models.py         # Modelo ProcesoEstructura
│   ├── views.py          # Vistas web
│   ├── services.py       # Lógica de negocio
│   ├── generadores/      # Generadores de archivos
│   └── templates/        # Plantillas HTML
├── media/                # Archivos subidos y generados
├── mi_proyecto/          # Configuración Django
└── manage.py
```

## 🔒 Configuración Oracle

Configurar conexión en `settings.py`:

```python
DATABASES = {
    'oracle': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'TNS_NAME',
        'USER': 'usuario',
        'PASSWORD': 'contraseña',
        'HOST': 'host',
        'PORT': '1521',
    }
}
```

## 📝 Estado del Proyecto

**Versión**: 1.0  
**Fecha**: Octubre 2025  
**Estado**: ✅ Funcional - Todos los botones de descarga operativos

### Último Commit
```
d47d5e8 - correccion de errores para el funcionamiento de los txt y xml
```

## 👥 Contribución

Proyecto interno del Grupo EPM.

## 📄 Licencia

Uso interno - Grupo EPM
