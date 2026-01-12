from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Categoria(models.Model):
    """Categoría de zapatillas (Running, Casual, Deportivas, etc.)"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Modelo de producto (zapatillas)"""
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock}"
    
    def descontar_stock(self, cantidad):
        """Descuenta stock del producto"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            self.save()
            return True
        else:
            raise ValidationError(f'Stock insuficiente. Disponible: {self.stock}, Solicitado: {cantidad}')


class Venta(models.Model):
    """Modelo de venta"""
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Venta #{self.id} - {self.producto.nombre} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
    
    def clean(self):
        """Validar antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0'})
        
        if self.pk is None:  # Solo validar stock para nuevas ventas
            if self.producto.stock < self.cantidad:
                raise ValidationError({
                    'cantidad': f'Stock insuficiente. Disponible: {self.producto.stock}, Solicitado: {self.cantidad}'
                })
    
    def save(self, *args, **kwargs):
        # Validar antes de guardar
        self.full_clean()
        
        # Calcular total antes de guardar
        if not self.total:
            self.total = self.producto.precio * self.cantidad
        
        # Descontar stock automáticamente
        if self.pk is None:  # Solo si es una nueva venta
            self.producto.descontar_stock(self.cantidad)
        
        super().save(*args, **kwargs)
