from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django import forms
from .models import Producto, Venta, Categoria, DetalleVenta, CierreCaja


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
    list_display = ['nombre', 'codigo_barras', 'precio', 'stock', 'categoria', 'tamaño', 'activo']
    list_filter = ['categoria', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'codigo_barras']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'codigo_barras', 'categoria', 'tamaño', 'activo')
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


class DetalleVentaInline(admin.TabularInline):
    """Inline para ver detalles de venta"""
    model = DetalleVenta
    readonly_fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']
    extra = 0
    can_delete = False


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'fecha', 'usuario', 'metodo_pago', 'total', 'vuelto']
    list_filter = ['fecha', 'metodo_pago', 'usuario']
    search_fields = ['usuario__username', 'id']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha', 'total', 'vuelto']
    inlines = [DetalleVentaInline]
    
    fieldsets = (
        ('Información de la Venta', {
            'fields': ('fecha', 'usuario', 'metodo_pago', 'total')
        }),
        ('Pago', {
            'fields': ('monto_recibido', 'vuelto', 'recargo_tarjeta')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Las ventas se crean desde la interfaz de ventas"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Las ventas no se pueden modificar"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo los superusuarios pueden eliminar ventas"""
        return request.user.is_superuser


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['venta__fecha', 'producto']
    search_fields = ['producto__nombre', 'venta__id']
    readonly_fields = ['venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'usuario', 'total_ventas', 'cantidad_ventas', 'diferencia']
    list_filter = ['fecha', 'usuario']
    search_fields = ['usuario__username']
    readonly_fields = ['fecha', 'fecha_hora_cierre', 'total_ventas', 'cantidad_ventas', 
                       'total_efectivo', 'total_tarjeta_debito', 'total_tarjeta_credito',
                       'total_transferencia', 'total_mercado_pago', 'diferencia']
    
    fieldsets = (
        ('Información', {
            'fields': ('fecha', 'usuario', 'fecha_hora_cierre')
        }),
        ('Dinero en Caja', {
            'fields': ('dinero_inicial', 'dinero_final', 'diferencia')
        }),
        ('Totales por Método de Pago', {
            'fields': ('total_efectivo', 'total_tarjeta_debito', 'total_tarjeta_credito',
                      'total_transferencia', 'total_mercado_pago')
        }),
        ('Resumen', {
            'fields': ('total_ventas', 'cantidad_ventas')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Los cierres se crean desde la interfaz de cierre de caja"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo superusuarios pueden modificar cierres"""
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
