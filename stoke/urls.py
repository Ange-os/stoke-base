from django.urls import path
from . import views

app_name = 'stoke'

urlpatterns = [
    path('ventas/', views.ventas, name='ventas'),
    path('buscar-producto/', views.buscar_producto, name='buscar_producto'),
    path('cierre-caja/', views.cierre_caja, name='cierre_caja'),
    path('historial/', views.historial_ventas, name='historial_ventas'),
    path('cargar-csv/', views.cargar_csv, name='cargar_csv'),
]
