from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3

app = Flask(__name__)

# كلمة السر للدخول
PASSWORD = "7474"
authorized_users = set()

DB_PATH = "institutions.db"

# دالة مساعدة للوصول لقاعدة البيانات
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, args)
    rv = c.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# دالة لإظهار بيانات المؤسسة
def format_institution(name):
    inst = query_db("SELECT * FROM institutions WHERE name=?", (name,), one=True)
    if not inst:
        return f"❌ المؤسسة '{name}' غير موجودة"
    id_, name, istqtab, work_permits, saudization, saud_name, _ = inst
    saud_status = "✅" if saudization else "❌"
    saud_button = "[تمّت السعودة]" if not saudization else ""
    return f"🏢 {name}\n\n1️⃣ رصيد الاستقطاب: {istqtab}\n\n2️⃣ السعودة: {saud_status} {saud_button}\n\n3️⃣ رخص العمل: {work_permits}"

# قائمة المؤسسات التي تحتاج سعودة
def institutions_need_saudization():
    insts = query_db("SELECT name FROM institutions WHERE istqtab_balance>0 AND saudization=0")
    if not insts:
        return "📌 لا توجد مؤسسات بحاجة لسعودة هذا الأسبوع"
    text = "📌 المؤسسات التي تحتاج سعودة هذا الأسبوع:\n\n"
    for i, (name,) in enumerate(insts, 1):
        text += f"{i}️⃣ {name}\n"
    return text

# استقبال الرسائل من Twilio
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    msg = request.form.get('Body').strip()
    user = request.form.get('From')

    resp = MessagingResponse()
    reply = resp.message()

    # تحقق كلمة السر
    if user not in authorized_users:
        if msg == PASSWORD:
            authorized_users.add(user)
            reply.body("✅ تم الدخول\nاكتب اسم المؤسسة")
        else:
            reply.body("❌ كلمة السر غير صحيحة")
        return str(resp)

    # أوامر البوت
    if msg.lower() == "سعودة":
        reply.body(institutions_need_saudization())
        return str(resp)

    # تسجيل السعودة
    if msg.startswith("تمّت السعودة"):
        name = msg.replace("تمّت السعودة","").strip()
        query_db("UPDATE institutions SET saudization=1 WHERE name=?", (name,))
        reply.body(f"✅ تم تسجيل السعودة للمؤسسة '{name}'")
        return str(resp)

    # البحث عن مؤسسة
    inst_names = [i[0] for i in query_db("SELECT name FROM institutions")]
    if msg in inst_names:
        reply.body(format_institution(msg))
        return str(resp)

    # أي رسالة غير مفهومة
    reply.body("❌ لم أفهم الرسالة. اكتب اسم المؤسسة أو 'سعودة'")
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
