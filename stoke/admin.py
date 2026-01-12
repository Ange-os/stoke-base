from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django import forms
from .models import Producto, Venta, Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']
    list_filter = ['nombre']
    
    def has_add_permission(self, request):
        """Solo superusuarios pueden crear categorías"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Solo superusuarios pueden modificar categorías"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar categorías"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Todos los usuarios staff pueden ver categorías"""
        return request.user.is_staff


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'stock', 'categoria', 'fecha_actualizacion']
    list_filter = ['categoria', 'fecha_creacion']
    search_fields = ['nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'categoria')
        }),
        ('Precio y Stock', {
            'fields': ('precio', 'stock')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Solo superusuarios pueden crear productos"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Solo los superusuarios pueden modificar productos"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Solo los superusuarios pueden eliminar productos"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Todos los usuarios staff pueden ver productos (para seleccionarlos en ventas)"""
        return request.user.is_staff


class VentaAdminForm(forms.ModelForm):
    """Formulario personalizado para validar ventas"""
    class Meta:
        model = Venta
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and cantidad:
            if cantidad <= 0:
                raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0'})
            
            if producto.stock < cantidad:
                raise ValidationError({
                    'cantidad': f'Stock insuficiente. Disponible: {producto.stock}, Solicitado: {cantidad}'
                })
        
        return cleaned_data


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    form = VentaAdminForm
    list_display = ['id', 'fecha', 'usuario', 'producto', 'cantidad', 'total']
    list_filter = ['fecha', 'usuario', 'producto']
    search_fields = ['producto__nombre', 'usuario__username']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información de la Venta', {
            'fields': ('fecha', 'usuario', 'producto', 'cantidad', 'total')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Campos de solo lectura según el usuario"""
        if obj:  # Si la venta ya existe
            # Una vez creada, solo se puede ver (no modificar)
            return ['fecha', 'usuario', 'producto', 'cantidad', 'total']
        else:  # Al crear nueva venta
            # El usuario se asigna automáticamente, fecha y total son calculados
            if request.user.is_superuser:
                return ['fecha', 'total']
            else:
                return ['fecha', 'usuario', 'total']
    
    def save_model(self, request, obj, form, change):
        """Asignar usuario automáticamente al crear venta"""
        if not change:  # Si es una nueva venta
            obj.usuario = request.user
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """Nadie puede modificar ventas una vez creadas"""
        if obj:  # Si la venta ya existe
            return False
        return True  # Pueden crear nuevas ventas
    
    def has_delete_permission(self, request, obj=None):
        """Solo los administradores pueden eliminar ventas"""
        return request.user.is_superuser


# Personalizar permisos de grupos
def setup_permissions():
    """Configura permisos para grupos de usuarios"""
    # Crear grupo de vendedores si no existe
    vendedores_group, created = Group.objects.get_or_create(name='Vendedores')
    
    # Permisos para vendedores: solo pueden agregar ventas
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission
    
    venta_content_type = ContentType.objects.get_for_model(Venta)
    producto_content_type = ContentType.objects.get_for_model(Producto)
    
    # Vendedores pueden ver y agregar ventas, ver productos
    vendedores_group.permissions.add(
        Permission.objects.get(codename='add_venta', content_type=venta_content_type),
        Permission.objects.get(codename='view_venta', content_type=venta_content_type),
        Permission.objects.get(codename='view_producto', content_type=producto_content_type),
    )
