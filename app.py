from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

PASSWORD = "7474"
authorized_users = set()

# قاعدة بيانات بسيطة في الذاكرة (لاحقًا يمكن تحويلها لـ SQLite)
data = {
    "institutions": {}
}

def create_institution(name):
    if name not in data["institutions"]:
        data["institutions"][name] = {
            "saudization": False,
            "saudi_name": "",
            "workers": {},
            "work_cards": {}
        }

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    from_number = request.form.get('From')
    msg_body = request.form.get('Body').strip()

    resp = MessagingResponse()
    msg = resp.message()

    # التحقق من كلمة السر
    if from_number not in authorized_users:
        if msg_body == PASSWORD:
            authorized_users.add(from_number)
            msg.body("✅ تم الدخول\nاكتب اسم المؤسسة للمتابعة")
        else:
            msg.body("🔒 أدخل كلمة السر للمتابعة")
        return str(resp)

    # بعد المصادقة
    # إذا الرسالة هي إنشاء مؤسسة
    if msg_body.lower().startswith("مؤسسة "):
        inst_name = msg_body[7:].strip()
        create_institution(inst_name)
        msg.body(f"🏢 تم إنشاء/فتح المؤسسة: {inst_name}\n📌 الآن يمكنك إضافة العمال وكروت العمل")
        return str(resp)

    # إذا الرسالة هي إضافة عامل
    if msg_body.lower().startswith("عامل "):
        try:
            inst_name, worker_info = msg_body[6:].split(",", 1)
            inst_name = inst_name.strip()
            worker_name, nationality = worker_info.split(",",1)
            worker_name = worker_name.strip()
            nationality = nationality.strip()
            create_institution(inst_name)
            data["institutions"][inst_name]["workers"][worker_name] = {
                "nationality": nationality,
                "work_card": None,
                "renewed": False
            }
            msg.body(f"👷 تم إضافة العامل: {worker_name} إلى المؤسسة: {inst_name}")
        except:
            msg.body("⚠️ خطأ في الصيغة. مثال صحيح: عامل اسم_المؤسسة,اسم_العامل,الجنسية")
        return str(resp)

    # إذا الرسالة هي إضافة كرت عمل
    if msg_body.lower().startswith("كرت "):
        try:
            inst_name, worker_name, months = msg_body[5:].split(",",2)
            inst_name = inst_name.strip()
            worker_name = worker_name.strip()
            months = months.strip()
            create_institution(inst_name)
            if worker_name in data["institutions"][inst_name]["workers"]:
                data["institutions"][inst_name]["workers"][worker_name]["work_card"] = months
                msg.body(f"🪪 تم تسجيل كرت العمل للعامل: {worker_name} لمدة {months}")
            else:
                msg.body(f"⚠️ العامل {worker_name} غير موجود في المؤسسة {inst_name}")
        except:
            msg.body("⚠️ خطأ في الصيغة. مثال صحيح: كرت اسم_المؤسسة,اسم_العامل,6شهور")
        return str(resp)

    # إذا الرسالة هي السعودية
    if msg_body.lower().startswith("سعودة "):
        try:
            inst_name, saudi_name = msg_body[7:].split(",",1)
            inst_name = inst_name.strip()
            saudi_name = saudi_name.strip()
            create_institution(inst_name)
            data["institutions"][inst_name]["saudization"] = True
            data["institutions"][inst_name]["saudi_name"] = saudi_name
            msg.body(f"🇸🇦 تم تسجيل السعودة للمؤسسة: {inst_name}\nالسعودي: {saudi_name}")
        except:
            msg.body("⚠️ خطأ في الصيغة. مثال صحيح: سعودة اسم_المؤسسة,اسم_السعودي")
        return str(resp)

    # إذا الرسالة هي البحث
    if msg_body.lower().startswith("بحث "):
        search_name = msg_body[4:].strip()
        found = False
        for inst_name, inst_data in data["institutions"].items():
            if search_name in inst_name:
                found = True
                saud = "✅" if inst_data["saudization"] else "❌"
                saudi_name = inst_data["saudi_name"] if inst_data["saudization"] else "لا يوجد"
                workers = "\n".join([f"{w} ({d['nationality']}) - كرت: {d['work_card'] or 'غير مسحوب'}" for w,d in inst_data["workers"].items()])
                msg.body(f"🏢 {inst_name}\n🇸🇦 السعودة: {saud}\n👤 السعودي: {saudi_name}\n👷 العمال:\n{workers}")
                break
        if not found:
            msg.body("⚠️ لم يتم العثور على أي مؤسسة بهذا الاسم")
        return str(resp)

    # أي رسالة أخرى
    msg.body("📌 أمر غير معروف. استخدم:\n- مؤسسة اسم_المؤسسة\n- عامل اسم_المؤسسة,اسم_العامل,الجنسية\n- كرت اسم_المؤسسة,اسم_العامل,6شهور\n- سعودة اسم_المؤسسة,اسم_السعودي\n- بحث اسم_المؤسسة")
    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
