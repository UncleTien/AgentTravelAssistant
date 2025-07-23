import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_itinerary_email(sender_email, receiver_email, subject, body):
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    message = Mail(
        from_email=sender_email,
        to_emails=receiver_email,
        subject=subject,
        html_content=body
    )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(str(e))
        return False