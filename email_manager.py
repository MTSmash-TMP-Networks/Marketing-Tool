import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import re

def send_email(smtp_server, sender_email, sender_password, recipient_email, subject, body):
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Plain-Text-Version (entfernt HTML-Tags)
    plain_text = re.sub(r'<[^>]+>', '', body)

    part1 = MIMEText(plain_text, 'plain')
    part2 = MIMEText(body, 'html')

    msg.attach(part1)
    msg.attach(part2)

    # Define SMTP ports and methods
    smtp_options = [
        {'port': 465, 'use_ssl': True},  # SSL
        {'port': 587, 'use_ssl': False}, # TLS
        {'port': 25, 'use_ssl': False},  # Plain
    ]

    for option in smtp_options:
        port = option['port']
        use_ssl = option['use_ssl']
        try:
            if use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, port, timeout=10, context=context) as server:
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                    return True
            else:
                with smtplib.SMTP(smtp_server, port, timeout=10) as server:
                    server.ehlo()
                    if port == 587:
                        server.starttls(context=ssl.create_default_context())
                        server.ehlo()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                    return True
        except (smtplib.SMTPException, ConnectionRefusedError, TimeoutError) as e:
            print(f"Fehler beim Verbinden mit {smtp_server} auf Port {port} ({'SSL' if use_ssl else 'TLS/Plain'}): {e}")
            continue  # Versuche den nächsten Port
    # Wenn alle Versuche fehlschlagen
    print(f"Alle Verbindungsversuche zu {smtp_server} sind fehlgeschlagen.")
    return False
