# app.py
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pytesseract
from PIL import Image
import io
import base64

app = Flask(__name__)

# -----------------------------------
# إعدادات البوت
PASSWORD = "7474"
authorized_users = set()

# قاعدة بيانات مؤقتة (يمكن تحويلها لاحقًا إلى SQLite)
institutions = {}
# هيكل البيانات:
# institutions = {
#     "مؤسسة محمد حزام الرشيدي": {
#         "saudi": {"name": "مها عبدالله العتيبي", "status": "نشط"},
#         "workers": [
#             {"name": "صالح علي محمد أبوعصيده", "nationality": "يمني", "work_card": "12 مسحوب", "renewed": True},
#             ...
#         ]
#     }
# }

# -----------------------------------
# وظائف المساعدة

def extract_text_from_image(image_data):
    """يستقبل صورة base64 ويعيد النص المكتوب فيها"""
    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='ara')  # عربي
        return text.strip()
    except Exception as e:
        print("OCR Error:", e)
        return None

def format_institution(inst_name):
    inst = institutions.get(inst_name)
    if not inst:
        return "❌ المؤسسة غير موجودة"
    
    msg = f"🏢 {inst_name}\n"
    saudi = inst.get("saudi")
    if saudi:
        msg += f"🇸🇦 السعودة: ✅\n👤 السعودي: {saudi['name']}\n📌 الحالة: {saudi['status']}\n"
    else:
        msg += "🇸🇦 السعودة: ❌\n📌 بدون سعودة\n"
    
    workers = inst.get("workers", [])
    msg += f"👷 عدد العمال: {len(workers)}\n"
    
    work_cards = [w['work_card'] for w in workers if 'مسحوب' in w['work_card']]
    msg += f"🪪 كروت العمل المسحوبة: {len(work_cards)}/{len(workers)}"
    
    return msg

# -----------------------------------
# Route الرئيسي للبوت
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body", "").strip()
    num_media = int(request.form.get("NumMedia", 0))
    from_user = request.form.get("From")

    resp = MessagingResponse()

    # التحقق من كلمة السر
    if from_user not in authorized_users:
        if incoming_msg == PASSWORD:
            authorized_users.add(from_user)
            resp.message("✅ تم الدخول بنجاح\n📂 اكتب اسم المؤسسة للمتابعة")
        else:
            resp.message("❌ كلمة السر غير صحيحة")
        return str(resp)

    # التحقق من أوامر بسيطة
    # 1- عرض مؤسسة
    if incoming_msg.startswith("مؤسسة "):
        inst_name = incoming_msg.strip()
        if inst_name not in institutions:
            institutions[inst_name] = {}  # إنشاء جديد
        msg = format_institution(inst_name)
        resp.message(msg + "\n\n⬇️ اختر إجراء:\n➕ إضافة معلومات\n👷 العمال\n🪪 كروت العمل\n✏️ تعديل")
        return str(resp)

    # 2- إضافة معلومات (سعودة/عامل/كرت عمل)
    if incoming_msg.startswith("➕ إضافة معلومات"):
        resp.message("اختر نوع الإضافة:\n🇸🇦 السعودة\n👷 عامل جديد\n🪪 كرت عمل")
        return str(resp)

    # 3- قراءة صورة هوية (OCR)
    if num_media > 0:
        media_url = request.form.get("MediaUrl0")
        media_content_type = request.form.get("MediaContentType0")
        # دعم الصور فقط
        if "image" in media_content_type:
            # تنزيل الصورة
            import requests
            r = requests.get(media_url)
            text = extract_text_from_image(base64.b64encode(r.content).decode())
            if text:
                # نفترض أن الاسم الأول في النص
                resp.message(f"تم التعرف على الاسم: {text}\n✅ تم تسجيله كسعودي في المؤسسة")
            else:
                resp.message("❌ لم أتمكن من التعرف على الاسم، أرسله يدويًا")
            return str(resp)

    # 4- البحث السريع
    if incoming_msg.startswith("بحث "):
        query = incoming_msg.replace("بحث ", "").strip()
        # بحث بالمؤسسات
        results = []
        for inst_name in institutions.keys():
            if query in inst_name:
                results.append(format_institution(inst_name))
        if results:
            resp.message("\n\n".join(results))
        else:
            resp.message("❌ لم أجد أي مؤسسة بهذا الاسم")
        return str(resp)

    # أي رسالة أخرى
    resp.message(f"📂 تم استلام: {incoming_msg}\n❗ لإضافة أوامر استخدم الأزرار")
    return str(resp)

# -----------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
