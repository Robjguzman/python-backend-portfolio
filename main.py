from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import psycopg2
import smtplib
from email.message import EmailMessage

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

@app.route("/", methods=["POST"])
def save_contact():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    cursor.execute(
        "INSERT INTO contacts(name, email, message) VALUES (%s, %s, %s) RETURNING id;",
        (name, email, message)
    )
    saved_id = cursor.fetchone()[0]
    conn.commit()

    send_email_notification(name, email, message)

    return jsonify({"id": saved_id, "name": name, "email": email, "message": message})

@app.route("/api/messages", methods=["POST"])
def save_api_message():
    data = request.get_json()
    message = data.get("message")
    status = data.get("status")

    cursor.execute(
        "INSERT INTO api_messages(message, status) VALUES (%s, %s) RETURNING id;",
        (message, status)
    )
    saved_id = cursor.fetchone()[0]
    conn.commit()

    return jsonify({"id": saved_id, "message": message, "status": status})

@app.route("/api/messages", methods=["GET"])
def get_all_messages():
    cursor.execute("SELECT * FROM api_messages ORDER BY created_at DESC;")
    messages = cursor.fetchall()
    return jsonify(messages)

def send_email_notification(name, user_email, message):
    msg_owner = EmailMessage()
    msg_owner.set_content(f"You received a message from {name} ({user_email}): {message}")
    msg_owner["Subject"] = "New Portfolio Message"
    msg_owner["From"] = os.getenv("EMAIL_USERNAME")
    msg_owner["To"] = "robertjguzman15@gmail.com"

    msg_user = EmailMessage()
    msg_user.set_content(f"Hi {name},\n\nThanks for reaching out! Here's your message:\n\n{message}")
    msg_user["Subject"] = "We Received Your Message"
    msg_user["From"] = os.getenv("EMAIL_USERNAME")
    msg_user["To"] = user_email

    with smtplib.SMTP_SSL(os.getenv("EMAIL_SERVICE"), 465) as smtp:
        smtp.login(os.getenv("EMAIL_USERNAME"), os.getenv("EMAIL_PASSWORD"))
        smtp.send_message(msg_owner)
        smtp.send_message(msg_user)

if __name__ == "__main__":
    app.run(port=5004)
