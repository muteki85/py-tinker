# Laravel Tinker Tool

Una aplicación gráfica para interactuar con proyectos Laravel. Permite ejecutar código PHP dentro del contexto de una aplicación Laravel, consultar modelos Eloquent y visualizar resultados de manera eficiente.

## Características

- **Ejecución de código PHP**: Ejecuta cualquier código PHP dentro del contexto de tu aplicación Laravel
- **Consulta de modelos Eloquent**: Interfaz gráfica para consultar modelos de manera rápida y sencilla
- **Vista de tabla**: Visualiza los resultados JSON de las consultas en formato tabular
- **Exportación a CSV**: Exporta los resultados de las consultas a archivos CSV
- **Transformador de código**: Convierte automáticamente consultas breves como `User::all()` a `echo formatOutput(App\Models\User::all());`
- **Explorador de archivos**: Navega por la estructura de archivos de tu proyecto Laravel
- **Comandos Artisan**: Ejecuta comandos Artisan directamente desde la interfaz
- **Registro de logs**: Historial completo de todas las operaciones realizadas

## Requisitos

- Python 3.6+
- tkinter (incluido en las instalaciones estándar de Python)
- ttkbootstrap
- PHP 7.2+ instalado y accesible desde la línea de comandos
- Un proyecto Laravel válido

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/muteki85/py-tinker.git
cd py-tinker
```

2. Instala las dependencias:
```bash
pip install ttkbootstrap
```

3. Ejecuta la aplicación:
```bash
python laravel_tinker_tool.py
```

## Uso

### Conectar a un proyecto Laravel

1. Inicia la aplicación
2. Haz clic en el botón "Buscar" para seleccionar tu directorio de proyecto Laravel
3. La estructura de archivos se cargará en el panel izquierdo

### Ejecutar código PHP

1. Escribe tu código PHP en el editor
2. Haz clic en "Ejecutar"
3. Los resultados se mostrarán en el panel de logs

### Consultar modelos Eloquent

#### Usando el transformador

Simplemente escribe expresiones como:
```php
User::all()
```

Y el transformador automáticamente lo convertirá a:
```php
echo formatOutput(App\Models\User::all());
```

#### Usando el diálogo de consulta

1. Haz clic en "Consulta Modelo" en la barra de botones o en el menú Laravel
2. Selecciona un modelo de la lista desplegable
3. Elige el tipo de consulta (all, first, find, etc.)
4. Ingresa parámetros adicionales si es necesario
5. Haz clic en "Ejecutar Consulta"

### Visualización en tabla

Cuando una consulta devuelve datos en formato JSON, aparecerá un botón azul "[Ver datos en tabla]". Al hacer clic en él, se abrirá una ventana con los datos en formato tabla.

También puedes acceder al último resultado JSON desde el menú Vista → "Mostrar último resultado en tabla".

### Ejecutar comandos Artisan

Usa el menú Laravel para ejecutar comandos comunes como:
- Ejecutar Migraciones
- Ver Rutas

### Exportar datos

- **Logs**: Menú Logs → Exportar Logs
- **Resultados de tabla**: Botón "Exportar CSV" en la ventana de tabla

## Configuración

En el menú Configuración puedes:
- Habilitar/deshabilitar el transformador automático de código

