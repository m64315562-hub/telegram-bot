from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

PASSWORD = os.environ.get("BOT_PASSWORD", "7474")
authorized_users = set()
institutions = {}

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get("Body", "").strip()
    user = request.form.get("From")

    resp = MessagingResponse()

    if user not in authorized_users:
        if msg == PASSWORD:
            authorized_users.add(user)
            resp.message("✅ تم الدخول بنجاح\n📂 اكتب اسم المؤسسة")
        else:
            resp.message("❌ كلمة السر غير صحيحة")
        return str(resp)

    if msg.startswith("مؤسسة"):
        if msg not in institutions:
            institutions[msg] = {
                "saudi": None,
                "workers": []
            }

        inst = institutions[msg]
        saudi = inst["saudi"]

        if saudi:
            resp.message(
                f"🏢 {msg}\n"
                f"🇸🇦 السعودة: ✅\n"
                f"👤 السعودي: {saudi}\n"
                f"📌 الحالة: نشط"
            )
        else:
            resp.message(
                f"🏢 {msg}\n"
                f"🇸🇦 السعودة: ❌\n"
                f"📌 بدون سعودة"
            )
        return str(resp)

    if msg.startswith("بحث"):
        key = msg.replace("بحث", "").strip()
        results = [k for k in institutions if key in k]
        if results:
            resp.message("\n".join(results))
        else:
            resp.message("❌ لا توجد نتائج")
        return str(resp)

    resp.message("📌 استخدم:\n- مؤسسة اسم_المؤسسة\n- بحث اسم")
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
