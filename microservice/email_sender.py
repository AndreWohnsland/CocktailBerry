import smtplib
import ssl
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate
from email import encoders


def send_mail(file_name: str, file_to_send):
    sender_address = os.getenv("SENDER_ADDRESS")
    sender_pass = os.getenv("SENDER_PASSWORD")
    receiver_address = os.getenv("RECEIVER_ADRESS")
    context = ssl.create_default_context()

    mail_content = (
        "Hello Cocktail Maker Owner,\n\n"
        f"As you have activated the sending of the export data via email, here is the {file_name} :) \n\n"
        "Enjoy the data!\n"
        "Your local Cocktail Maker"
    )

    message = MIMEMultipart()
    message["From"] = sender_address
    message["To"] = receiver_address
    message["Cc"] = sender_address
    message["Subject"] = f"Your Cocktail Maker Data: {file_name}"
    message["Date"] = formatdate(localtime=True)
    message.attach(MIMEText(mail_content, "plain"))

    attachment = MIMENonMultipart("text", "csv", charset="utf-8")
    attachment.add_header("Content-Disposition", "attachment", filename=file_name)
    attachment.set_payload(file_to_send.read())
    encoders.encode_base64(attachment)
    message.attach(attachment)

    session = smtplib.SMTP("smtp.gmail.com", 587)
    session.ehlo()
    session.starttls(context=context)
    session.ehlo()
    session.login(sender_address, sender_pass)
    text = message.as_string()
    send_res = session.sendmail(sender_address, receiver_address, text)
    session.quit()
    return f"Sending from {sender_address} to {receiver_address} Information from sendmail: {json.dumps(send_res)}"
