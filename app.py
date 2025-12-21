from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

PASSWORD = "7474"
authorized_users = set()

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get("Body", "").strip()
    user = request.form.get("From")

    resp = MessagingResponse()

    if user not in authorized_users:
        if msg == PASSWORD:
            authorized_users.add(user)
            resp.message("✅ تم الدخول بنجاح")
        else:
            resp.message("❌ كلمة السر غير صحيحة")
        return str(resp)

    resp.message(f"📂 تم استلام: {msg}")
    return str(resp)

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
