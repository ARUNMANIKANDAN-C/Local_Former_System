import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailSender:
    def __init__(self):
        self.sender_email = "amrita.team.b11@gmail.com"
        self.app_password = open("../app.txt").read()  or "add_your_key"# ← Insert your Gmail App Password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, to_email: str, subject: str, body: str):
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = to_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            print("✅ Email sent successfully!")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")


if __name__ == "__main__":
    sender = GmailSender()
    sender.send_email(
        to_email="temp@gmail.com",
        subject="Hello from Python Class",
        body="This email was sent using a Python class wrapper around smtplib!"
    )
