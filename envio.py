import socket, smtplib, ssl, time

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "chimecoo@gmail.com"
EMAIL_HOST_PASSWORD = "wdyf malc txrp sipz"

def test_smtp_connection():
    print("🔍 Diagnóstico de conexión SMTP a Gmail\n")

    # Paso 1: prueba de red y puerto
    start = time.time()
    try:
        print(f"🌐 Probando acceso al puerto {EMAIL_PORT}...")
        sock = socket.create_connection((EMAIL_HOST, EMAIL_PORT), timeout=10)
        print("✅ Puerto abierto y accesible")
        sock.close()
    except Exception as e:
        print("❌ No se puede abrir conexión al servidor:", e)
        return
    print(f"⏱️  Tiempo de respuesta: {round(time.time()-start,2)} s\n")

    # Paso 2: handshake TLS y login
    try:
        print("🔄 Iniciando conexión segura (TLS)...")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.starttls(context=ssl.create_default_context())
        print("✅ TLS negociado correctamente")
        print("🔑 Intentando login…")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("✅ Login SMTP exitoso")
        server.quit()
    except Exception as e:
        print("❌ Error durante TLS o autenticación:", e)

if __name__ == "__main__":
    test_smtp_connection()
