import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

msg = EmailMessage()
msg["Subject"] = "Test Email from Redshift"
msg["From"] = os.environ["MAIL_USERNAME"]
msg["To"] = 'mlstockton@gmail.com'
msg.set_content("This is a test email.")

with smtplib.SMTP("smtp.fastmail.com", 587) as server:
    server.starttls()
    server.login(os.environ["MAIL_USERNAME"], os.environ["MAIL_PASSWORD"])
    server.send_message(msg)

print("Email sent.")
