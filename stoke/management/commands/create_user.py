"""
Comando para crear usuarios normales con acceso al admin
Uso: python manage.py create_user username password email
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crea un usuario normal con acceso al admin (is_staff=True)'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('password', type=str, help='Contraseña')
        parser.add_argument('--email', type=str, default='', help='Email (opcional)')
        parser.add_argument('--superuser', action='store_true', help='Crear como superusuario')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        is_superuser = options['superuser']
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'❌ El usuario "{username}" ya existe')
            )
            return
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_staff=True,  # Permite acceso al admin
            is_superuser=is_superuser
        )
        
        if is_superuser:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superusuario "{username}" creado exitosamente')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario normal "{username}" creado exitosamente')
            )
            self.stdout.write(
                self.style.WARNING('   Este usuario puede acceder al admin pero solo puede crear ventas')
            )
