### Paso 2: Crear Entorno Virtual

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

El archivo `.env` debe tener este formato:

```env
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=la_contraseña_que_te_pase
DB_HOST=db.idnlzuhraqnleeijjjja.supabase.co
DB_PORT=5432
SECRET_KEY=genera-una-clave-secreta-aqui-puede-ser-cualquier-texto-largo
```

**Generar SECRET_KEY:**
Puedes usar cualquier texto largo y aleatorio. Ejemplo:
```env
SECRET_KEY=django-insecure-tu-clave-secreta-aqui-123456789-abcdefghijklmnop
```


### Paso 4: Aplicar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto creará las tablas necesarias en la base de datos.

### Paso 5: Crear Tu Superusuario

```bash
python manage.py createsuperuser
```

Sigue las instrucciones:
- **Username:** Elige un nombre de usuario (ej: `tu_nombre`)
- **Email:** (opcional, puedes presionar Enter)
- **Password:** Elige una contraseña segura (no se mostrará mientras escribes)
- **Password (again):** Repite la contraseña

**Importante:** Cada persona debe crear su propio usuario. Los usuarios son independientes.

### Paso 8: Ejecutar el Servidor

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

**La primera vez te pedirá iniciar sesión:**
- Usa el usuario y contraseña que creaste en el Paso 5
- Después del login, entrarás directamente a la pantalla de ventas

## ✅ Verificación

Si todo está bien configurado, deberías poder:

1. ✅ Iniciar sesión con tu usuario
2. ✅ Ver la pantalla de ventas
3. ✅ Ver el menú superior con opciones: Ventas, Cierre, Historial, Admin
4. ✅ Acceder al admin en `/admin`

