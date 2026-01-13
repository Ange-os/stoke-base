from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Categoria(models.Model):
    """Categoría de productos (Bebidas, Golosinas, Cigarrillos, etc.)"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Modelo de producto para kiosco"""
    nombre = models.CharField(max_length=200)
    codigo_barras = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Código de barras del producto")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    tamaño = models.CharField(max_length=50, blank=True, null=True, help_text="Tamaño o presentación (ej: 500ml, 1L, etc.)")
    activo = models.BooleanField(default=True, help_text="Producto activo para ventas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo_barras']),
            models.Index(fields=['nombre']),
        ]
    
    def __str__(self):
        tamaño_str = f" - {self.tamaño}" if self.tamaño else ""
        return f"{self.nombre}{tamaño_str} - ${self.precio}"
    
    def descontar_stock(self, cantidad):
        """Descuenta stock del producto"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            self.save()
            return True
        else:
            raise ValidationError(f'Stock insuficiente. Disponible: {self.stock}, Solicitado: {cantidad}')


class Venta(models.Model):
    """Modelo de venta para kiosco"""
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta_debito', 'Tarjeta Débito'),
        ('tarjeta_credito', 'Tarjeta Crédito'),
        ('transferencia', 'Transferencia'),
        ('mercado_pago', 'Mercado Pago'),
    ]
    
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ventas')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Monto recibido del cliente (solo para efectivo)")
    vuelto = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Vuelto a entregar (solo para efectivo)")
    recargo_tarjeta = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Recargo aplicado por pago con tarjeta")
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['metodo_pago']),
        ]
    
    def __str__(self):
        return f"Venta #{self.id} - ${self.total} - {self.get_metodo_pago_display()} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
    
    def calcular_vuelto(self):
        """Calcula el vuelto si es pago en efectivo"""
        if self.metodo_pago == 'efectivo' and self.monto_recibido:
            self.vuelto = max(0, self.monto_recibido - self.total)
            return self.vuelto
        return 0
    
    def save(self, *args, **kwargs):
        # Calcular vuelto automáticamente si es efectivo
        if self.metodo_pago == 'efectivo':
            self.calcular_vuelto()
        
        super().save(*args, **kwargs)


class DetalleVenta(models.Model):
    """Detalle de productos en una venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
        ordering = ['venta', 'id']
    
    def __str__(self):
        return f"{self.venta} - {self.producto.nombre} x{self.cantidad}"
    
    def clean(self):
        """Validar antes de guardar"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a 0'})
        
        if self.pk is None:  # Solo validar stock para nuevos detalles
            if self.producto.stock < self.cantidad:
                raise ValidationError({
                    'cantidad': f'Stock insuficiente. Disponible: {self.producto.stock}, Solicitado: {self.cantidad}'
                })
    
    def save(self, *args, **kwargs):
        # Validar antes de guardar
        self.full_clean()
        
        # Calcular subtotal
        if not self.subtotal:
            self.subtotal = self.precio_unitario * self.cantidad
        
        # Descontar stock automáticamente
        if self.pk is None:  # Solo si es un nuevo detalle
            self.producto.descontar_stock(self.cantidad)
        
        super().save(*args, **kwargs)


class CierreCaja(models.Model):
    """Cierre de caja diario"""
    fecha = models.DateField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cierres_caja')
    fecha_hora_cierre = models.DateTimeField(auto_now_add=True)
    
    # Dinero en caja
    dinero_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Dinero inicial en caja")
    dinero_final = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Dinero final en caja")
    
    # Totales por método de pago
    total_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tarjeta_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_tarjeta_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_mercado_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Resumen
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cantidad_ventas = models.IntegerField(default=0)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Diferencia entre dinero final esperado y real")
    observaciones = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Cierre de Caja'
        verbose_name_plural = 'Cierres de Caja'
        ordering = ['-fecha_hora_cierre']
        unique_together = ['fecha', 'usuario']  # Un cierre por usuario por día
    
    def __str__(self):
        return f"Cierre {self.fecha} - ${self.total_ventas} - {self.cantidad_ventas} ventas"
    
    def calcular_totales(self):
        """Calcula los totales desde las ventas del día"""
        from django.utils import timezone
        from django.db.models import Sum, Count, Q
        
        inicio_dia = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        ventas = Venta.objects.filter(
            fecha__gte=inicio_dia,
            fecha__lte=fin_dia,
            usuario=self.usuario
        )
        
        self.cantidad_ventas = ventas.count()
        self.total_ventas = ventas.aggregate(Sum('total'))['total__sum'] or 0
        
        self.total_efectivo = ventas.filter(metodo_pago='efectivo').aggregate(Sum('total'))['total__sum'] or 0
        self.total_tarjeta_debito = ventas.filter(metodo_pago='tarjeta_debito').aggregate(Sum('total'))['total__sum'] or 0
        self.total_tarjeta_credito = ventas.filter(metodo_pago='tarjeta_credito').aggregate(Sum('total'))['total__sum'] or 0
        self.total_transferencia = ventas.filter(metodo_pago='transferencia').aggregate(Sum('total'))['total__sum'] or 0
        self.total_mercado_pago = ventas.filter(metodo_pago='mercado_pago').aggregate(Sum('total'))['total__sum'] or 0
        
        # Calcular diferencia
        dinero_esperado = self.dinero_inicial + self.total_efectivo
        self.diferencia = self.dinero_final - dinero_esperado
