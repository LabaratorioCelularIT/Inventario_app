import smtplib
from email.message import EmailMessage

def enviar_codigo_verificacion(destinatario, codigo):
    remitente = 'tucorreo@gmail.com'
    contraseña = 'CONTRASEÑA_DE_APLICACIÓN'

    mensaje = EmailMessage()
    mensaje['Subject'] = 'Código de verificación - Celulares Crédito Fácil'
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje.set_content(f'Tu código de verificación es: {codigo}')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, contraseña)
            smtp.send_message(mensaje)
        return True
    except Exception as e:
        print("Error al enviar correo:", e)
        return False
