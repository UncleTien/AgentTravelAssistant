import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

def send_itinerary_email(sender_email, receiver_email, subject, body):
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    # Kiểm tra App Password có tồn tại không
    if not app_password:
        print("[❌] Lỗi: Không tìm thấy GMAIL_APP_PASSWORD trong file .env")
        return False

    # Tạo nội dung email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    html_content = MIMEText(body, "html")
    msg.attach(html_content)

    # Gửi email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"[✅] Đã gửi email tới {receiver_email}")
        return True
    except Exception as e:
        print(f"[❌] Gửi email thất bại: {e}")
        return False
