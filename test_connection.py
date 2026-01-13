"""
Script para probar la conexión a Supabase
Ejecutar: python test_connection.py
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Prueba la conexión a la base de datos"""
    print("🔍 Probando conexión a Supabase...")
    print("-" * 50)
    
    # Obtener variables de entorno
    db_host = os.getenv('DB_HOST', '')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'postgres')
    
    # Mostrar configuración (sin mostrar contraseña completa)
    print(f"Host: {db_host}")
    print(f"Port: {db_port}")
    print(f"User: {db_user}")
    print(f"Database: {db_name}")
    print(f"Password: {'*' * len(db_password) if db_password else '(vacía)'}")
    print("-" * 50)
    
    # Verificar que todas las variables estén configuradas
    if not db_host:
        print("❌ Error: DB_HOST no está configurado en .env")
        return False
    
    if not db_password:
        print("⚠️  Advertencia: DB_PASSWORD está vacía")
    
    try:
        print("🔄 Intentando conectar...")
        connection = psycopg2.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name,
            connect_timeout=10  # Timeout de 10 segundos
        )
        
        print("✅ ¡Conexión exitosa!")
        
        # Probar una consulta simple
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Versión de PostgreSQL: {version[:50]}...")
        
        cursor.close()
        connection.close()
        print("✅ Conexión cerrada correctamente")
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print(f"❌ Error de conexión: {error_msg}")
        
        # Mensajes de ayuda según el error
        if "could not translate host name" in error_msg.lower():
            print("\n💡 Solución: Problema de resolución DNS")
            print("   1. Verifica que el hostname en .env sea correcto")
            print("   2. Verifica tu conexión a internet")
            print("   3. Prueba desde otra red (hotspot del celular)")
            print("   4. Verifica firewall/antivirus")
        elif "password authentication failed" in error_msg.lower():
            print("\n💡 Solución: Contraseña incorrecta")
            print("   1. Verifica la contraseña en .env")
            print("   2. Verifica en Supabase Dashboard → Settings → Database")
        elif "timeout" in error_msg.lower():
            print("\n💡 Solución: Timeout de conexión")
            print("   1. Verifica tu conexión a internet")
            print("   2. Verifica firewall/antivirus")
            print("   3. Prueba desde otra red")
        elif "connection refused" in error_msg.lower():
            print("\n💡 Solución: Conexión rechazada")
            print("   1. Verifica que el puerto sea 5432")
            print("   2. Verifica que Supabase no esté pausado")
            print("   3. Verifica restricciones de IP en Supabase")
        
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print(f"   Tipo: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_connection()
    print("-" * 50)
    if success:
        print("✅ Todo está bien configurado!")
        print("   Puedes continuar con: python manage.py migrate")
    else:
        print("❌ Hay problemas de conectividad")
        print("   Revisa SOLUCION_PROBLEMAS_SUPABASE.md para más ayuda")
