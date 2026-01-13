from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
import csv
import io

from .models import Producto, Venta, DetalleVenta, CierreCaja, Categoria
from .forms import VentaForm, CierreCajaForm, CargaCSVForm


@login_required
def ventas(request):
    """Interfaz de ventas tipo calculadora"""
    # Optimizado: solo cargar productos activos, sin prefetch innecesario
    productos = Producto.objects.filter(activo=True).select_related('categoria').order_by('nombre')[:50]  # Limitar a 50 para mejor rendimiento
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Crear venta
            venta = Venta.objects.create(
                usuario=request.user,
                metodo_pago=data.get('metodo_pago', 'efectivo'),
                total=data.get('total', 0),
                monto_recibido=data.get('monto_recibido'),
                recargo_tarjeta=data.get('recargo_tarjeta', 0),
                observaciones='Venta manual' if data.get('es_manual') else ''
            )
            
            # Crear detalles de venta (solo si hay productos reales) - Optimizado con bulk_create
            detalles = data.get('detalles', [])
            if detalles:
                # Obtener todos los productos de una vez
                producto_ids = [d['producto_id'] for d in detalles if d.get('producto_id')]
                productos_dict = {p.id: p for p in Producto.objects.filter(id__in=producto_ids)}
                
                # Crear todos los detalles de una vez
                detalles_venta = []
                for detalle_data in detalles:
                    producto_id = detalle_data.get('producto_id')
                    if producto_id and producto_id in productos_dict:
                        producto = productos_dict[producto_id]
                        detalles_venta.append(DetalleVenta(
                            venta=venta,
                            producto=producto,
                            cantidad=detalle_data['cantidad'],
                            precio_unitario=producto.precio,
                            subtotal=producto.precio * detalle_data['cantidad']
                        ))
                
                # Crear todos los detalles de una vez (más rápido)
                if detalles_venta:
                    DetalleVenta.objects.bulk_create(detalles_venta)
                    
                    # Actualizar stock de todos los productos de una vez
                    for detalle_venta in detalles_venta:
                        detalle_venta.producto.stock -= detalle_venta.cantidad
                    Producto.objects.bulk_update([d.producto for d in detalles_venta], ['stock'])
            # Si es venta manual sin productos, la venta se guarda sin detalles
            
            return JsonResponse({
                'success': True,
                'venta_id': venta.id,
                'vuelto': float(venta.vuelto) if venta.metodo_pago == 'efectivo' else 0
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return render(request, 'stoke/ventas.html', {
        'productos': productos
    })


@login_required
def buscar_producto(request):
    """Buscar producto por código de barras o nombre"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'productos': []})
    
    productos = Producto.objects.filter(
        Q(codigo_barras__iexact=query) | 
        Q(nombre__icontains=query),
        activo=True
    )[:10]
    
    resultados = [{
        'id': p.id,
        'nombre': p.nombre,
        'precio': float(p.precio),
        'stock': p.stock,
        'codigo_barras': p.codigo_barras or '',
        'tamaño': p.tamaño or '',
        'categoria': p.categoria.nombre if p.categoria else ''
    } for p in productos]
    
    return JsonResponse({'productos': resultados})


@login_required
def cierre_caja(request):
    """Vista de cierre de caja"""
    hoy = timezone.now().date()
    
    # Obtener o crear cierre del día
    cierre, created = CierreCaja.objects.get_or_create(
        fecha=hoy,
        usuario=request.user,
        defaults={'dinero_inicial': 0}
    )
    
    if request.method == 'POST':
        form = CierreCajaForm(request.POST, instance=cierre)
        if form.is_valid():
            cierre = form.save(commit=False)
            cierre.calcular_totales()
            cierre.save()
            messages.success(request, 'Cierre de caja guardado exitosamente')
            return redirect('cierre_caja')
    else:
        # Calcular totales automáticamente
        cierre.calcular_totales()
        cierre.save()
        form = CierreCajaForm(instance=cierre)
    
    # Ventas del día
    inicio_dia = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    ventas_dia = Venta.objects.filter(
        fecha__gte=inicio_dia,
        fecha__lte=fin_dia,
        usuario=request.user
    ).order_by('-fecha')
    
    return render(request, 'stoke/cierre_caja.html', {
        'cierre': cierre,
        'form': form,
        'ventas_dia': ventas_dia
    })


@login_required
def historial_ventas(request):
    """Historial de ventas"""
    ventas = Venta.objects.filter(usuario=request.user).order_by('-fecha')[:100]
    
    return render(request, 'stoke/historial_ventas.html', {
        'ventas': ventas
    })


@login_required
def cargar_csv(request):
    """Cargar productos desde archivo CSV"""
    if not request.user.is_superuser:
        messages.error(request, 'Solo los administradores pueden cargar productos')
        return redirect('stoke:ventas')
    
    if request.method == 'POST':
        form = CargaCSVForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_csv']
            
            # Leer el archivo CSV
            try:
                # Decodificar el archivo
                contenido = archivo.read().decode('utf-8-sig')
                reader = csv.DictReader(io.StringIO(contenido))
                
                productos_creados = 0
                productos_actualizados = 0
                errores = []
                
                for fila_num, fila in enumerate(reader, start=2):  # Empezar en 2 porque la fila 1 es el encabezado
                    try:
                        # Campos esperados: nombre, codigo_barras, precio, stock, categoria, tamaño
                        nombre = fila.get('nombre', '').strip()
                        codigo_barras = fila.get('codigo_barras', '').strip() or None
                        precio = fila.get('precio', '').strip()
                        stock = fila.get('stock', '0').strip()
                        categoria_nombre = fila.get('categoria', '').strip()
                        tamaño = fila.get('tamaño', '').strip() or None
                        
                        if not nombre:
                            errores.append(f"Fila {fila_num}: Falta el nombre del producto")
                            continue
                        
                        if not precio:
                            errores.append(f"Fila {fila_num}: Falta el precio")
                            continue
                        
                        try:
                            precio = float(precio)
                            stock = int(stock) if stock else 0
                        except ValueError:
                            errores.append(f"Fila {fila_num}: Precio o stock inválido")
                            continue
                        
                        # Obtener o crear categoría
                        categoria = None
                        if categoria_nombre:
                            categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                        
                        # Crear o actualizar producto
                        if codigo_barras:
                            producto, created = Producto.objects.update_or_create(
                                codigo_barras=codigo_barras,
                                defaults={
                                    'nombre': nombre,
                                    'precio': precio,
                                    'stock': stock,
                                    'categoria': categoria,
                                    'tamaño': tamaño,
                                    'activo': True
                                }
                            )
                        else:
                            # Si no hay código de barras, buscar por nombre
                            producto, created = Producto.objects.get_or_create(
                                nombre=nombre,
                                codigo_barras__isnull=True,
                                defaults={
                                    'precio': precio,
                                    'stock': stock,
                                    'categoria': categoria,
                                    'tamaño': tamaño,
                                    'activo': True
                                }
                            )
                            if not created:
                                # Actualizar producto existente
                                producto.precio = precio
                                producto.stock = stock
                                producto.categoria = categoria
                                producto.tamaño = tamaño
                                producto.activo = True
                                producto.save()
                        
                        if created:
                            productos_creados += 1
                        else:
                            productos_actualizados += 1
                            
                    except Exception as e:
                        errores.append(f"Fila {fila_num}: {str(e)}")
                
                # Mensajes de resultado
                if productos_creados > 0 or productos_actualizados > 0:
                    mensaje = f"✅ {productos_creados} productos creados, {productos_actualizados} actualizados"
                    messages.success(request, mensaje)
                
                if errores:
                    mensaje_errores = f"⚠️ {len(errores)} errores encontrados. Ver detalles en la consola."
                    messages.warning(request, mensaje_errores)
                    # Guardar errores en la sesión para mostrarlos
                    request.session['csv_errores'] = errores[:10]  # Solo los primeros 10
                
                return redirect('stoke:cargar_csv')
                
            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
    else:
        form = CargaCSVForm()
    
    errores = request.session.pop('csv_errores', [])
    
    return render(request, 'stoke/cargar_csv.html', {
        'form': form,
        'errores': errores
    })
