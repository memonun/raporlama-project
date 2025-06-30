# test_outlook_connection.py
import os
import socket
import smtplib
import ssl

HOST = os.getenv("SMTP_SERVER", "smtp.office365.com")  # veya ortam değişkeninize bak
USER = os.getenv("EMAIL_SENDER")
PASS = os.getenv("EMAIL_PASSWORD")

def test_dns(host, port):
    try:
        infos = socket.getaddrinfo(host, port)
        print(f"✅ DNS çözümlemesi başarılı: {host}:{port} → {infos[0][4]}")
    except Exception as e:
        print(f"❌ DNS çözümlemesi başarısız: {e}")

def test_smtp_ssl(host, port):
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=10) as server:
            server.login(USER, PASS)
        print("✅ SMTPS (SSL) bağlantısı başarılı")
    except Exception as e:
        print(f"❌ SMTPS (SSL) bağlantısı başarısız: {e}")

def test_smtp_starttls(host, port):
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(USER, PASS)
        print("✅ SMTP (STARTTLS) bağlantısı başarılı")
    except Exception as e:
        print(f"❌ SMTP (STARTTLS) bağlantısı başarısız: {e}")

if __name__ == "__main__":
    print("→ DNS testi (587):")
    test_dns(HOST, 587)  # STARTTLS port
    print("\n→ DNS testi (465):")
    test_dns(HOST, 465)  # SMTPS port
    print("\n→ SMTPS (SSL) testi:")
    test_smtp_ssl(HOST, 465)
    print("\n→ SMTP (STARTTLS) testi:")
    test_smtp_starttls(HOST, 587)