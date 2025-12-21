from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import os

app = Flask(__name__)

# ================= إعدادات البيئة =================
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "whatsapp:+14155238886")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

PASSWORD = os.environ.get("BOT_PASSWORD", "7474")
authorized_users = set()
DB_PATH = "institutions.db"

# ================= قاعدة البيانات =================
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, args)
    rv = c.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def add_or_update_institution(name, istqtab, work_permits):
    inst = query_db("SELECT * FROM institutions WHERE name=?", (name,), one=True)
    if inst:
        query_db("UPDATE institutions SET istqtab_balance=?, work_permits=? WHERE name=?",
                 (istqtab, work_permits, name))
        return f"✅ تم تحديث المؤسسة '{name}'"
    else:
        query_db("INSERT INTO institutions (name, istqtab_balance, work_permits, saudization, saud_name, extra) VALUES (?, ?, ?, 0, '', '')",
                 (name, istqtab, work_permits))
        return f"✅ تم إضافة المؤسسة '{name}'"

def get_institutions_list():
    return [i[0] for i in query_db("SELECT name FROM institutions")]

# ================= إرسال أزرار تفاعلية =================
def send_interactive_buttons(to, body, buttons):
    """ buttons = [{'title': 'تم السعودة', 'id': 'saud_instname'}, ...] """
    message = {
        "messaging_product": "whatsapp",
        "to": to.replace("whatsapp:", ""),
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [{"type": "reply", "reply": {"id": b["id"], "title": b["title"]}} for b in buttons]
            }
        }
    }
    client.messages.create(from_=WHATSAPP_NUMBER, to=to, **message)

# ================= استقبال الرسائل =================
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get('Body').strip()
    user = request.form.get('From')
    
    resp = MessagingResponse()

    # تحقق كلمة السر
    if user not in authorized_users:
        if msg == PASSWORD:
            authorized_users.add(user)
            resp.message("✅ تم الدخول\nاكتب اسم المؤسسة أو أرسل:\nإضافة مؤسسة: اسم,رصيد,رخص")
        else:
            resp.message("❌ كلمة السر غير صحيحة")
        return str(resp)

    # إضافة أو تحديث مؤسسة
    if msg.startswith("إضافة مؤسسة:"):
        try:
            parts = msg.replace("إضافة مؤسسة:", "").strip().split(",")
            name = parts[0].strip()
            istqtab = int(parts[1].strip())
            work_permits = int(parts[2].strip())
            resp.message(add_or_update_institution(name, istqtab, work_permits))
        except:
            resp.message("❌ تأكد من الصيغة: إضافة مؤسسة: اسم, رصيد الاستقطاب, رخص العمل")
        return str(resp)

    # التعامل مع أزرار التفاعل
    if msg.startswith("saud_"):  # زر السعودة
        inst_name = msg.replace("saud_", "")
        query_db("UPDATE institutions SET saudization=1 WHERE name=?", (inst_name,))
        resp.message(f"✅ تم تسجيل السعودة للمؤسسة '{inst_name}'")
        return str(resp)

    if msg.startswith("update_"):  # زر تعديل البيانات
        inst_name = msg.replace("update_", "")
        resp.message(f"📌 لتحديث رصيد الاستقطاب أو رخص العمل، أرسل:\nإضافة مؤسسة: {inst_name},رصيد,رخص")
        return str(resp)

    # عرض مؤسسة مع أزرار
    inst_names = get_institutions_list()
    if msg in inst_names:
        text = f"🏢 {msg}\nرصيد الاستقطاب: {query_db('SELECT istqtab_balance FROM institutions WHERE name=?', (msg,), one=True)[0]}\nالسعودة: {'✅' if query_db('SELECT saudization FROM institutions WHERE name=?', (msg,), one=True)[0] else '❌'}\nرخص العمل: {query_db('SELECT work_permits FROM institutions WHERE name=?', (msg,), one=True)[0]}"
        buttons = [
            {"title": "✅ تم السعودة", "id": f"saud_{msg}"},
            {"title": "✏️ تعديل البيانات", "id": f"update_{msg}"}
        ]
        send_interactive_buttons(user, text, buttons)
        return str(resp)

    # قائمة المؤسسات التي تحتاج سعودة
    if msg.lower() == "سعودة":
        insts = query_db("SELECT name FROM institutions WHERE istqtab_balance>0 AND saudization=0")
        if not insts:
            resp.message("📌 لا توجد مؤسسات بحاجة لسعودة هذا الأسبوع")
        else:
            text = "📌 المؤسسات التي تحتاج سعودة هذا الأسبوع:\n"
            for i, (name,) in enumerate(insts, 1):
                text += f"{i}️⃣ {name}\n"
            resp.message(text)
        return str(resp)

    # أي رسالة غير مفهومة
    resp.message("❌ لم أفهم الرسالة. اكتب اسم المؤسسة، 'سعودة' أو 'إضافة مؤسسة: اسم,رصيد,رخص'")
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
