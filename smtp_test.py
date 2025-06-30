import smtplib, ssl
from email.message import EmailMessage

SMTP_SERVER = "smtp.office365.com"       # veya "smtp.office365.com"
SMTP_PORT   = 587
EMAIL_SENDER   = "report@israholding.com.tr"
EMAIL_PASSWORD = "Isra020150!"

RECIPIENT = "ozdassuleyman123@gmail.com"
SUBJECT   = "Arbitrary Subject"
CONTENT   = "This is the arbitrary content of the email."

context = ssl.create_default_context()

try:
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        # Prepare and send the email
        msg = EmailMessage()
        msg["From"] = EMAIL_SENDER
        msg["To"]   = RECIPIENT
        msg["Subject"] = SUBJECT
        msg.set_content(CONTENT)
        server.send_message(msg)
        print("✉️ E-posta gönderildi!")
except smtplib.SMTPAuthenticationError as e:
    print("❌ Auth hatası:", e)
except Exception as e:
    print("⚠️ Başka bir hata:", type(e), e)