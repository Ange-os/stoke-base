### Paso 1: Crear Entorno Virtual

# Crear entorno virtual
python -m venv venv


# Activar entorno virtual
venv\Scripts\activate


**Nota:** Verás `(venv)` al inicio de la línea de comandos cuando esté activado.

### Paso 2: Instalar Dependencias


pip install -r requirements.txt


Esto instalará Django, psycopg2-binary y otras dependencias necesarias.

### Paso 3: Configurar Variables de Entorno

Crea un archivo llamado `.env` en la raíz del proyecto (misma carpeta que `manage.py`).

**IMPORTANTE:** Pide las credenciales de la base de datos a tu socio. No las compartas públicamente.



### Paso 3: Aplicar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará las tablas necesarias en la base de datos.


### Paso 4: Ejecutar el Servidor

```bash
python manage.py runserver
```

Verás un mensaje como:
```
Starting development server at http://127.0.0.1:8000/
```

### Paso 9: Acceder a la Aplicación

Abre tu navegador y ve a:
```
http://127.0.0.1:8000
```
`

