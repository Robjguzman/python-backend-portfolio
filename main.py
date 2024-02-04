from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#newa

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
CORS(app)  # Enable CORS

# Database connection
conn = psycopg2.connect(os.environ.get("DATABASE_URL"))


# Email sending function
def send_email_notification(name, user_email, message):
    try:
        print("Setting up email server...")
        server = smtplib.SMTP_SSL(os.environ.get("EMAIL_SERVICE"), 465)
        server.login(os.environ.get("EMAIL_USERNAME"), os.environ.get("EMAIL_PASSWORD"))

        # Email to the website owner
        owner_email = os.environ.get("OWNER_EMAIL", "robertjguzman15@gmail.com")
        owner_msg = MIMEMultipart()
        owner_msg['From'] = os.environ.get("EMAIL_USERNAME")
        owner_msg['To'] = owner_email
        owner_msg['Subject'] = "New Portfolio Message"
        owner_msg.attach(MIMEText(f"You have received a new message from {name} ({user_email}): {message}", 'plain'))

        # Email to the user
        user_msg = MIMEMultipart()
        user_msg['From'] = os.environ.get("EMAIL_USERNAME")
        user_msg['To'] = user_email
        user_msg['Subject'] = "Your Message Has Been Received"
        user_msg.attach(MIMEText(
            f"Hello {name},\n\nWe have received your message and will get back to you as soon as possible. Here's what you sent us:\n\n{message}",
            'plain'))

        print("Sending emails...")
        server.send_message(owner_msg)
        server.send_message(user_msg)
        server.quit()

        print("Emails sent successfully.")
    except Exception as e:
        print(f"Error occurred in send_email_notification: {e}")


# POST endpoint to receive messages
@app.route("/api/messages", methods=['POST'])
def post_message():
    data = request.json
    name = data['name']
    email = data['email']
    message = data['message']

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts(name, email, message) VALUES (%s, %s, %s) RETURNING *",
            (name, email, message)
        )
        saved_message = cursor.fetchone()
        conn.commit()
        cursor.close()

        print(f"Message saved to PostgreSQL with ID: {saved_message[0]}")

        # Send email notification
        send_email_notification(name, email, message)

        return jsonify({"id": saved_message[0], "name": name, "email": email, "message": message}), 200
    except Exception as e:
        print(f"Error in POST /api/messages: {e}")
        return f"Server error: {e}", 500


# GET endpoint to retrieve messages
@app.route("/api/messages", methods=['GET'])
def get_messages():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts")
        messages = cursor.fetchall()
        conn.commit()
        cursor.close()

        print("Retrieved all messages")
        return jsonify(messages), 200
    except Exception as e:
        print(f"Error in GET /api/messages: {e}")
        return f"Server error: {e}", 500


# Start the server
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
