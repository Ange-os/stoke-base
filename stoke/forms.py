from django import forms
from .models import Venta, CierreCaja, Producto


class VentaForm(forms.ModelForm):
    """Formulario para crear venta"""
    class Meta:
        model = Venta
        fields = ['metodo_pago', 'total', 'monto_recibido', 'recargo_tarjeta']
        widgets = {
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'monto_recibido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'recargo_tarjeta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class CierreCajaForm(forms.ModelForm):
    """Formulario para cierre de caja"""
    class Meta:
        model = CierreCaja
        fields = ['dinero_inicial', 'dinero_final', 'observaciones']
        widgets = {
            'dinero_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dinero_final': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CargaCSVForm(forms.Form):
    """Formulario para carga de productos desde CSV"""
    archivo_csv = forms.FileField(
        label='Archivo CSV',
        help_text='Selecciona un archivo CSV con los productos',
        widget=forms.FileInput(attrs={'accept': '.csv', 'class': 'form-control'})
    )
