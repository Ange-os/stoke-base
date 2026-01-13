# 👥 Crear Usuarios Normales

Guía para crear usuarios normales que puedan acceder al admin pero con permisos limitados.

## 🔐 Tipos de Usuarios

### Superusuario (Admin)
- ✅ Acceso completo al admin
- ✅ Puede crear, modificar y eliminar productos
- ✅ Puede crear, modificar y eliminar categorías
- ✅ Puede crear, ver y eliminar ventas
- ✅ Puede gestionar usuarios

### Usuario Normal (Vendedor)
- ✅ Puede acceder al admin (con `is_staff=True`)
- ✅ Puede **ver** productos y categorías (solo lectura)
- ✅ Puede **crear** ventas
- ✅ Puede **ver** sus propias ventas
- ❌ **NO puede** modificar productos ni stock
- ❌ **NO puede** modificar categorías
- ❌ **NO puede** modificar ventas existentes
- ❌ **NO puede** eliminar nada

## 📝 Crear Usuario Normal

### Opción 1: Usando el comando personalizado (Recomendado)

```bash
python manage.py create_user nombre_usuario contraseña --email email@ejemplo.com
```

**Ejemplo:**
```bash
python manage.py create_user vendedor1 mi_password123 --email vendedor1@tienda.com
```

Este comando crea automáticamente un usuario con:
- `is_staff=True` (puede acceder al admin)
- `is_superuser=False` (permisos limitados)

### Opción 2: Desde el Admin de Django

1. Inicia sesión como superusuario en `/admin`
2. Ve a **Usuarios** (Users)
3. Haz clic en **Agregar usuario** (Add user)
4. Completa:
   - **Nombre de usuario**: `vendedor1`
   - **Contraseña**: (elige una segura)
   - **Confirmar contraseña**: (repite la contraseña)
5. Haz clic en **Guardar**
6. En la siguiente pantalla:
   - ✅ Marca **Personal del staff** (Staff status)
   - ❌ **NO marques** **Superusuario** (Superuser status)
   - Opcional: Agrega nombre, apellido, email
7. Haz clic en **Guardar**

### Opción 3: Usando el shell de Django

```bash
python manage.py shell
```

Luego ejecuta:

```python
from django.contrib.auth.models import User

# Crear usuario normal con acceso al admin
usuario = User.objects.create_user(
    username='vendedor1',
    password='mi_password123',
    email='vendedor1@tienda.com',
    is_staff=True,      # Permite acceso al admin
    is_superuser=False  # Sin permisos de admin
)

print(f"Usuario {usuario.username} creado exitosamente")
```

## ✅ Verificar que Funciona

1. Cierra sesión del admin (si estás logueado como superusuario)
2. Inicia sesión con el usuario normal que creaste
3. Deberías ver:
   - ✅ **Ventas**: Puedes crear nuevas ventas
   - ✅ **Productos**: Solo puedes ver (no modificar)
   - ✅ **Categorías**: Solo puedes ver (no modificar)
   - ❌ **Usuarios**: No aparece (solo para superusuarios)

## 🔧 Solución de Problemas

### Error: "Por favor introduzca el nombre de usuario y la clave correctos"

**Causa:** El usuario no tiene `is_staff=True`

**Solución:**
1. Inicia sesión como superusuario
2. Ve a **Usuarios** → Selecciona el usuario
3. Marca **Personal del staff** (Staff status)
4. Guarda

O usa el comando:
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
user = User.objects.get(username='nombre_usuario')
user.is_staff = True
user.save()
```

### El usuario puede acceder pero no ve nada

**Causa:** Falta el permiso `is_staff=True`

**Solución:** Ver solución anterior

### El usuario puede modificar productos (no debería)

**Causa:** El usuario tiene `is_superuser=True`

**Solución:**
1. Ve a **Usuarios** → Selecciona el usuario
2. **Desmarca** **Superusuario** (Superuser status)
3. Guarda

## 📋 Resumen de Permisos

| Acción | Superusuario | Usuario Normal |
|--------|--------------|----------------|
| Ver productos | ✅ | ✅ |
| Crear productos | ✅ | ❌ |
| Modificar productos | ✅ | ❌ |
| Eliminar productos | ✅ | ❌ |
| Ver categorías | ✅ | ✅ |
| Crear categorías | ✅ | ❌ |
| Modificar categorías | ✅ | ❌ |
| Crear ventas | ✅ | ✅ |
| Ver ventas | ✅ | ✅ |
| Modificar ventas | ❌ | ❌ |
| Eliminar ventas | ✅ | ❌ |

## 💡 Consejos

- Crea usuarios normales para cada vendedor
- Usa contraseñas seguras
- Los usuarios normales solo pueden crear ventas, no modificar stock
- El stock se descuenta automáticamente al crear una venta
