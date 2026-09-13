

from hydrogram import Client, filters
from hydrogram.errors import (
    FloodWait,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
)
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from hydrogram.raw import functions, types
import os
import json
import asyncio
import time
import re
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Client(
    "report_bot",
    api_id=31244607,
    api_hash="02d3b988051dd895b962450d2fb34fea",
    bot_token="8761976820:AAE0azGjulG4dWt7mBW_S9zV_hXnMAUPAT4",
)

ADMIN_ID = 5011347901

user_states = {}
user_data = {}

START_TEXT = """⚡ **بوت البلاغات والسيطرة** 🕯️

اختر الخدمة المطلوبة من الأزرار أدناه 👇"""

NO_HISTORY_TEXT = """سجل البلاغات 📅

لا توجد عمليات مسجّلة بعد."""

INTERNAL_REPORT_TEXT = """البلاغ الداخلي 👮‍♂️

ما هو البلاغ الداخلي؟ 🤔
هو نظام يمكن البوت من استخدام حسابك الشخصي (بشكل آمن تماماً) لرفع البلاغات الرسمية داخل تيليغرام ضد القنوات أو الحسابات المخالفة تلقائياً.

اربط حسابك مرة واحدة وسيتولى البوت الباقي."""

LINK_PHONE_TEXT = """ربط الحساب 🕯️

⚠️ **تنبيه هام:** يجب تسجيل الدخول بحسابك أولاً لكي تتمكن من استخدام هذه الميزة.

أرسل رقم هاتفك مع رمز الدولة

أمثلة :
• +966501234567
• +964770123456
• +201001234567"""

OTP_TEXT = """كود التحقق أرسل 🕯️

تحقق من رسائل تيليغرام وأرسل الكود

مثال : 1 2 3 4 5"""

TWO_STEP_TEXT = """كلمة المرور الثنائية 👁‍🗨

الحساب مفَعّل عليه التحقق بخطوتين
أرسل كلمة المرور الخاصة بك :"""

TARGET_REPORT_TEXT = """هدف البلاغ 🥷

أرسل معرف أو رابط الحساب / القناة / المجموعة

أمْثلة :
• `@username`
• `https://t.me/channel`
• `https://t.me/c/1234567890/5`
• `-1001234567890`"""

COMMENT_REPORT_TEXT = """تعليق البلاغ 💬

أرسل تعليقاً يُرفق مع البلاغ
أو أرسل `-` لتركه فارغاً"""

COUNT_REPORT_TEXT = """عدد البلاغات 🔢

الهدف : {target}
السبب : {reason}
التعليق : {comment}

أرسل عدد البلاغات :
1 – 999"""

SENDING_REPORT_TEXT = """جاري إرسال البلاغات 🚀

الهدف : {target}
السبب : {reason}
نجح : {success} • فشل : {failed}

{progress_bar} {percent}%"""

RESET_MEMBERS_TEXT = """تصفير أعضاء 💀 - الخطوة 1 من 2

⚠️ **ملاحظة هامة:** يجب أن يكون الحساب المربوط **مشرفاً (Admin)** ولديه صلاحية **طرد الأعضاء** في المجموعة أو القناة المستهدفة لكي تنجح العملية.

أرسل رابط أو معرّف المجموعة / القناة التي تريد طرد أعضائها.

أمثلة :
• `@mygroup`
• `https://t.me/mygroup`
• `https://t.me/+Abcdefg12345`
• `-1001234567890`"""

UNLINKED_TEXT = """تسجيل الدخول 🔑

تم فك ربط وحذف الحساب بنجاح."""

CANCEL_REPORT_MARKUP = InlineKeyboardMarkup(
    [[InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")]]
)

METHOD_1_GUIDE = """🛠️ **شرح إضافة حساب عبر كلمة مرور التطبيق (App Password)**

💡 **الخطوات بالتفصيل:**
1. افتح إعدادات حساب Google الخاص بك واذهب إلى قسم **الأمان**.
2. تأكد من أن خاصية **التحقق بخطوتين** (2-Step Verification) مفعلة لديك.
3. ابحث في إعدادات الأمان عن خيار يسمى **"كلمة مرور التطبيقات"** (App passwords).
4. انشئ كلمة مرور جديدة خاصة بالبوت، وسيعطيك كلمة مرور مكونة من 16 حرفاً، قم بنسخها بدقة.

يرجى الآن إرسال **البريد الإلكتروني** الخاص بك أولاً:"""

METHOD_2_GUIDE = """🔑 **شرح إضافة حساب عبر كلمة المرور العادية**

💡 **توضيح تفصيلي:**
• هذه الطريقة مخصصة لحسابات Outlook أو Hotmail، أو حسابات Gmail التي **غير مفعل** عليها التحقق بخطوتين وتعتمد على كلمة المرور العادية مباشرة.
• *ملاحظة:* إذا كان حسابك مفعلًا عليه التحقق بخطوتين، سيقوم البوت باكتشاف ذلك وإلغاء العملية تلقائياً للحماية.

يرجى الآن إرسال **البريد الإلكتروني** الخاص بك أولاً:"""

DB_FILE = "sessions_data.json"
EMAILS_DB_FILE = "emails_data.json"
MAIN_PHOTO = "https://j.top4top.io/p_3903trolt1.jpg"

def parse_target_input(text):
    text = text.strip()
    if text.startswith("-") or text.isdigit():
        try:
            return int(text)
        except:
            return text
    if "t.me/+" in text or "t.me/joinchat/" in text:
        return text
    if "t.me/" in text:
        parts = text.split("t.me/")
        path = parts[1].split("/")[0].strip()
        if path.isdigit() or path.startswith("-"):
            try:
                return int(path)
            except:
                return path
        if path == "c":
            sub_parts = parts[1].split("/")
            if len(sub_parts) > 1:
                try:
                    return int("-100" + sub_parts[1])
                except:
                    pass
        return "@" + path.replace("@", "")
    if text.startswith("@"):
        return text
    if not text.startswith("http") and " " not in text:
        return "@" + text
    return text

def load_all_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_all_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def load_user_emails(user_id):
    if os.path.exists(EMAILS_DB_FILE):
        try:
            with open(EMAILS_DB_FILE, "r", encoding="utf-8") as f:
                all_emails = json.load(f)
                return all_emails.get(str(user_id), [])
        except:
            return []
    return []

def save_user_email(user_id, email, password):
    all_emails = {}
    if os.path.exists(EMAILS_DB_FILE):
        try:
            with open(EMAILS_DB_FILE, "r", encoding="utf-8") as f:
                all_emails = json.load(f)
        except:
            pass
    
    uid_str = str(user_id)
    if uid_str not in all_emails:
        all_emails[uid_str] = []
    
    for item in all_emails[uid_str]:
        if item.get("email") == email:
            item["password"] = password
            break
    else:
        all_emails[uid_str].append({"email": email, "password": password})
        
    try:
        with open(EMAILS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(all_emails, f, ensure_ascii=False, indent=4)
    except:
        pass

def delete_user_email(user_id, email):
    if os.path.exists(EMAILS_DB_FILE):
        try:
            with open(EMAILS_DB_FILE, "r", encoding="utf-8") as f:
                all_emails = json.load(f)
            uid_str = str(user_id)
            if uid_str in all_emails:
                all_emails[uid_str] = [x for x in all_emails[uid_str] if x.get("email") != email]
                with open(EMAILS_DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(all_emails, f, ensure_ascii=False, indent=4)
        except:
            pass

def get_user_record(user_id):
    data = load_all_data()
    return data.get(str(user_id))

def save_user_record(user_id, phone, session_string):
    data = load_all_data()
    data[str(user_id)] = {
        "phone": phone,
        "session_string": session_string
    }
    save_all_data(data)

def delete_user_record(user_id):
    data = load_all_data()
    if str(user_id) in data:
        del data[str(user_id)]
        save_all_data(data)

def check_user_session(user_id):
    record = get_user_record(user_id)
    return record is not None and "session_string" in record

def cleanup_old_sessions():
    for f in os.listdir("."):
        if (f.startswith("session_") or f.startswith("temp_client_")) and (f.endswith(".session") or f.endswith(".session-journal") or f.endswith(".session-wal") or f.endswith(".session-shm")):
            try:
                os.remove(f)
            except:
                pass

def verify_email_credentials(email, password):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        if "@yahoo." in email.lower():
            smtp_server = "smtp.mail.yahoo.com"
        elif "@outlook." in email.lower() or "@hotmail." in email.lower():
            smtp_server = "smtp.live.com"

        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(email, password)
        server.quit()
        return 'success', None
    except smtplib.SMTPAuthenticationError as e:
        err_str = str(e).lower()
        if any(term in err_str for term in ["application-specific password", "websignon", "2-step", "two-factor", "challenge", "not accepted", "security", "Username and Password not accepted"]):
            return '2fa_enabled', str(e)
        return 'invalid', str(e)
    except Exception as e:
        return 'invalid', str(e)

def send_email_to_target(sender_email, sender_password, target_email, subject, body):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        if "@yahoo." in sender_email.lower():
            smtp_server = "smtp.mail.yahoo.com"
        elif "@outlook." in sender_email.lower() or "@hotmail." in sender_email.lower():
            smtp_server = "smtp.live.com"

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = target_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, target_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"خطأ في إرسال البريد: {e}")
        return False

def get_main_markup(user_id):
    is_linked = check_user_session(user_id)
    login_btn_text = "تسجيل الدخول للحساب" if is_linked else "تسجيل الدخول 🔑"
    
    keyboard = [
        [
            InlineKeyboardButton("رفع بلاغ ⚡", callback_data="report"),
            InlineKeyboardButton("حساباتي 🔵", callback_data="my_accounts"),
        ],
        [
            InlineKeyboardButton("سجل البلاغات 📅", callback_data="history"),
        ],
        [
            InlineKeyboardButton(login_btn_text, callback_data="quick_login"),
        ],
        [
            InlineKeyboardButton("بلاغ داخلي 👮‍♂️", callback_data="internal_report"),
            InlineKeyboardButton("تصفير أعضاء 💀", callback_data="reset_members"),
        ],
        [
            InlineKeyboardButton("جلساتي 📂", callback_data="my_sessions"),
            InlineKeyboardButton("خمط أعضاء 🏴‍☠️", callback_data="steal_members"),
        ],
    ]
    keyboard.append([
        InlineKeyboardButton("المطور 🏴‍☠️", url="https://t.me/its_h_q"),
    ])
    return InlineKeyboardMarkup(keyboard)

history_empty_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")]
    ]
)

cancel_link_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")],
        [InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")]
    ]
)

cancel_target_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("إلغاء 💀", callback_data="internal_report")],
        [InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")]
    ]
)

cancel_comment_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("إلغاء 💀", callback_data="internal_report")],
        [InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")]
    ]
)

cancel_count_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("إلغاء 💀", callback_data="internal_report")],
        [InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")]
    ]
)

cancel_reset_markup = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")],
        [InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")]
    ]
)

reasons_markup = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🚫 لم يعجبني / سبام 🏴‍☠️", callback_data="reason_spam"),
            InlineKeyboardButton("👶 إساءة للأطفال 🏴‍☠️", callback_data="reason_child"),
        ],
        [
            InlineKeyboardButton("⚔️ عنف 🏴‍☠️", callback_data="reason_violence"),
            InlineKeyboardButton("🏴‍☠️ سلع وخدمات", callback_data="reason_illegal"),
        ],
        [
            InlineKeyboardButton("🏴‍☠️ محتوى للكبار", callback_data="reason_adult"),
            InlineKeyboardButton("🪪 معلومات خاصة", callback_data="reason_private"),
        ],
        [
            InlineKeyboardButton("🏴‍☠️ نصب أو احتيال 🎭", callback_data="reason_scam"),
            InlineKeyboardButton("©️ حقوق النشر 🏴‍☠️", callback_data="reason_copyright"),
        ],
        [
            InlineKeyboardButton("🏴‍☠️ أخرى 🏴‍☠️", callback_data="reason_other"),
        ],
        [
            InlineKeyboardButton("💀 إلغاء", callback_data="internal_report"),
            InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")
        ],
    ]
)


@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = None
    try:
        await message.reply_photo(
            photo=MAIN_PHOTO,
            caption=START_TEXT,
            reply_markup=get_main_markup(user_id)
        )
    except:
        await message.reply_text(text=START_TEXT, reply_markup=get_main_markup(user_id))


@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    is_linked = check_user_session(user_id)

    if data == "quick_login":
        await callback_query.answer()
        if is_linked:
            record = get_user_record(user_id)
            phone = record.get("phone") if record else "غير معروف"
            linked_text = f"""تسجيل الدخول 🔑

حسابك مسجل ومرتبط بالفعل بالنظام بنجاح ✅
الرقم المرتبط: +{phone}

يمكنك الآن استخدام ميزات (البلاغ الداخلي، تصفير الأعضاء، وخمط الأعضاء) مباشرة دون الحاجة لتسجيل دخول جديد."""
            
            # تم إزالة زر تسجيل الخروج من هنا بناءً على طلبك
            linked_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")]
                ]
            )
            await callback_query.message.edit_text(text=linked_text, reply_markup=linked_markup)
        else:
            user_states[user_id] = "WAITING_PHONE"
            await callback_query.message.edit_text(text=LINK_PHONE_TEXT, reply_markup=cancel_link_markup)
        return

    if data == "steal_members":
        if not is_linked:
            await callback_query.answer("⚠️ يجب تسجيل الدخول أولاً لاستخدام هذه الميزة!", show_alert=True)
            return

        user_states[user_id] = "WAITING_STEAL_FROM"
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["steal_paused"] = False
        await callback_query.answer()
        
        steal_guide_text = (
            "🏴‍☠️ **قسم خمط ونقل الأعضاء – الشرح وآلية العمل:**\n\n"
            "• **الحالة الأولى (قائمة الأعضاء مفتوحة):** إذا كانت المجموعة تسمح للجميع برؤية الأعضاء، سيقوم البوت بسحب ونقل كافة الأعضاء بشكل طبيعي.\n"
            "• **الحالة الثانية (قائمة الأعضاء مقفولة/مخفية):** إذا كانت المجموعة تخفي الأعضاء، فلن يتمكن البوت من سحب الأعضاء العاديين، وسيقوم حصرياً بسحب وإضافة **المشرفين، المالكين، ورتب القناة** المتاحين فقط.\n\n"
            "👇 **الخطوة 1 من 3:** أرسل معرف، رابط، أو أيدي الكروب / القناة **المصدر** (التي تريد سحب الأعضاء منها):"
        )

        await callback_query.message.edit_text(
            text=steal_guide_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")]])
        )
        return

    if data == "pause_steal":
        if user_id in user_data:
            user_data[user_id]["steal_paused"] = True
        await callback_query.answer("🛑 تم إيقاف عملية الخمط مؤقتاً!", show_alert=True)
        return

    if data == "resume_steal":
        if user_id in user_data:
            user_data[user_id]["steal_paused"] = False
        await callback_query.answer("▶️ تم استئناف عملية الخمط بنجاح!", show_alert=True)
        return

    if data.startswith("reason_"):
        reason_map = {
            "reason_spam": "لم يعجبني / سبام",
            "reason_child": "إساءة للأطفال",
            "reason_violence": "عنف",
            "reason_illegal": "سلع وخدمات",
            "reason_adult": "محتوى للكبار",
            "reason_private": "معلومات خاصة",
            "reason_scam": "نصب أو احتيال",
            "reason_copyright": "حقوق النشر",
            "reason_other": "أخرى"
        }
        chosen_reason = reason_map.get(data, "غير معروف")
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["reason"] = chosen_reason
        user_states[user_id] = "WAITING_COMMENT"
        
        await callback_query.answer()
        await callback_query.message.edit_text(
            COMMENT_REPORT_TEXT,
            reply_markup=cancel_comment_markup,
            disable_web_page_preview=True
        )
        return

    if data == "report":
        user_states[user_id] = None
        await callback_query.answer()
        user_emails = load_user_emails(user_id)
        if not user_emails:
            no_accounts_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("اضيف حساب الحين 📧", callback_data="add_account")],
                    [InlineKeyboardButton("رجوع 🔙", callback_data="back_to_home")],
                ]
            )
            no_accounts_text = """لا توجد حسابات مضافة 🔮\n\nيجب إضافة حساب إيميل أولاً حتى تتمكن من الإرسال.\nاضغط الزر أدناه لإضافة إيميلك."""
            try:
                await callback_query.message.delete()
            except:
                pass
            await client.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=MAIN_PHOTO,
                caption=no_accounts_text,
                reply_markup=no_accounts_markup
            )
        else:
            user_states[user_id] = "REPORT_WAITING_TARGET_EMAILS"
            await callback_query.message.edit_text(
                text="💀 **رفع بلاغ – الخطوة 1 من 4**\n\nأدخل إيميل الجهة التي تريد إرسال البلاغ إليها.\nلأكثر من إيميل افصل بينهم بفاصلة :\n`a@company.com, b@company.com`",
                reply_markup=CANCEL_REPORT_MARKUP,
                disable_web_page_preview=True
            )

    elif data == "my_accounts":
        user_states[user_id] = None
        await callback_query.answer()
        user_emails = load_user_emails(user_id)
        if not user_emails:
            no_accounts_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("اضيف حساب الحين 📧", callback_data="add_account")],
                    [InlineKeyboardButton("رجوع 🔙", callback_data="back_to_home")],
                ]
            )
            no_accounts_text = """لا توجد حسابات مضافة 🔮\n\nيجب إضافة حساب إيميل أولاً حتى تتمكن من الإرسال.\nاضغط الزر أدناه لإضافة إيميلك."""
            try:
                await callback_query.message.delete()
            except:
                pass
            await client.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=MAIN_PHOTO,
                caption=no_accounts_text,
                reply_markup=no_accounts_markup
            )
        else:
            acc_list_text = f"حساباتي المضافة ({len(user_emails)}) 👁‍🗨\n"
            keyboard_btns = []
            for idx, item in enumerate(user_emails, 1):
                email_val = item.get("email")
                acc_list_text += f"\n{idx}. {email_val}"
                keyboard_btns.append([InlineKeyboardButton(f"{email_val} | حذف 🗑", callback_data=f"del_email_{email_val}")])
            
            keyboard_btns.append([InlineKeyboardButton("اضافه حساب جديد ➕", callback_data="add_account")])
            keyboard_btns.append([InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")])
            
            await callback_query.message.edit_text(text=acc_list_text, reply_markup=InlineKeyboardMarkup(keyboard_btns), disable_web_page_preview=True)

    elif data.startswith("del_email_"):
        email_to_del = data.replace("del_email_", "")
        delete_user_email(user_id, email_to_del)
        await callback_query.answer("تم حذف الحساب بنجاح", show_alert=True)
        user_emails = load_user_emails(user_id)
        if not user_emails:
            no_accounts_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("اضيف حساب الحين 📧", callback_data="add_account")],
                    [InlineKeyboardButton("رجوع 🔙", callback_data="back_to_home")],
                ]
            )
            no_accounts_text = "لا توجد حسابات مضافة 🔮"
            try:
                await callback_query.message.delete()
            except:
                pass
            await client.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=MAIN_PHOTO,
                caption=no_accounts_text,
                reply_markup=no_accounts_markup
            )
        else:
            acc_list_text = f"حساباتي ({len(user_emails)})\n"
            keyboard_btns = []
            for idx, item in enumerate(user_emails, 1):
                email_val = item.get("email")
                acc_list_text += f"\n{idx}. {email_val}"
                keyboard_btns.append([InlineKeyboardButton(f"{email_val} | حذف 🗑", callback_data=f"del_email_{email_val}")])
            keyboard_btns.append([InlineKeyboardButton("اضافه حساب جديد ➕", callback_data="add_account")])
            keyboard_btns.append([InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")])
            await callback_query.message.edit_text(text=acc_list_text, reply_markup=InlineKeyboardMarkup(keyboard_btns), disable_web_page_preview=True)

    elif data == "history":
        user_states[user_id] = None
        await callback_query.answer()
        await callback_query.message.edit_text(
            text=NO_HISTORY_TEXT, reply_markup=history_empty_markup
        )

    elif data == "my_sessions":
        user_states[user_id] = None
        await callback_query.answer()
        all_data = load_all_data()
        record = all_data.get(str(user_id))
        phone_val = record.get("phone") if record else "غير معروف"
        
        sessions_text = f"""إدارة الجلسات 📂

• حالتك الحالية: {"🟢 مسجل الدخول" if is_linked else "🔴 غير مسجل"}
• رقمك المرتبط: {f"+{phone_val}" if is_linked else "لا يوجد"}"""

        sessions_buttons = []
        if is_linked:
            sessions_buttons.append([InlineKeyboardButton("تسجيل الخروج 👁‍🗨", callback_data="logout")])
        
        sessions_buttons.append([InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")])
        
        sessions_markup = InlineKeyboardMarkup(sessions_buttons)
        await callback_query.message.edit_text(text=sessions_text, reply_markup=sessions_markup)

    elif data == "internal_report":
        if not is_linked:
            await callback_query.answer("⚠️ يجب تسجيل الدخول أولاً لاستخدام هذه الميزة!", show_alert=True)
            return

        user_states[user_id] = None
        await callback_query.answer()
        record = get_user_record(user_id)
        phone = record.get("phone") if record else "غير معروف"
        linked_text = f"""البلاغ الداخلي 👮‍♂️

الحساب مسجل ومرتبط بنجاح ✅
الرقم: +{phone}
الحالة: جاهز للبلاغ"""

        linked_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("إرسال بلاغ 💀", callback_data="target_report")],
                [InlineKeyboardButton("تسجيل الخروج 👁‍🗨", callback_data="logout")],
                [InlineKeyboardButton("رجوع 🏴‍☠️", callback_data="back_to_home")],
            ]
        )
        await callback_query.message.edit_text(text=linked_text, reply_markup=linked_markup)

    elif data == "target_report":
        if not is_linked:
            await callback_query.answer("⚠️ يجب تسجيل الدخول أولاً!", show_alert=True)
            return

        user_states[user_id] = "WAITING_TARGET"
        await callback_query.answer()
        await callback_query.message.edit_text(
            text=TARGET_REPORT_TEXT, reply_markup=cancel_target_markup, disable_web_page_preview=True
        )

    elif data.startswith("speed_"):
        speed_val = data.replace("speed_", "")
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["speed"] = speed_val
        
        udata = user_data.get(user_id, {})
        emails = udata.get("report_emails", [])
        subject = udata.get("report_subject", "")
        body = udata.get("report_body", "")
        count = udata.get("report_count", 1)
        total_msgs = len(emails) * count

        speed_text_map = {
            "0": "بدون تأخير",
            "0.5": "0.5 ثانية",
            "1": "1 ثانية",
            "2": "2 ثانية",
            "5": "5 ثوان",
            "10": "10 ثوان"
        }
        chosen_speed_text = speed_text_map.get(speed_val, "بدون تأخير")

        summary_text = f"""💀 **ملخص البلاغ**

• الهدف : `{", ".join(emails)}`
• الموضوع : `{subject}`
• الرسالة : `{body}`
• عدد لكل هدف : `{count}`
• التأخير : `{chosen_speed_text}`

المجموع الكلي : {total_msgs} رسالة"""

        summary_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f"تاكيد الارسال ({total_msgs} رساله)", callback_data="confirm_send_report")],
                [InlineKeyboardButton("الغاء", callback_data="back_to_home")]
            ]
        )
        await callback_query.answer()
        await callback_query.message.edit_text(
            summary_text,
            reply_markup=summary_markup,
            disable_web_page_preview=True
        )

    elif data == "confirm_send_report":
        await callback_query.answer()
        user_states[user_id] = None
        
        udata = user_data.get(user_id, {})
        emails = udata.get("report_emails", [])
        count = udata.get("report_count", 1)
        speed_str = udata.get("speed", "0")
        subject = udata.get("report_subject", "")
        body = udata.get("report_body", "")
        
        try:
            delay_time = float(speed_str)
        except:
            delay_time = 0.0
            
        total_msgs = len(emails) * count

        user_emails = load_user_emails(user_id)
        if not user_emails:
            await callback_query.message.edit_text("❌ لا توجد حسابات إيميل مضافة. أضف حساباً أولاً.")
            return

        progress_msg = await callback_query.message.edit_text(
            f"""💀 **جاري الإرسال...**

⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ 0%
0 / {total_msgs} نجح 0 | فشل 0""",
            disable_web_page_preview=True
        )

        success_count = 0
        fail_count = 0

        for i in range(1, total_msgs + 1):
            if delay_time > 0:
                await asyncio.sleep(delay_time)
            else:
                await asyncio.sleep(0.1)
            
            sender_account = random.choice(user_emails)
            sender_email = sender_account.get("email")
            sender_password = sender_account.get("password")
            
            target_email = random.choice(emails)
            
            result = send_email_to_target(
                sender_email=sender_email,
                sender_password=sender_password,
                target_email=target_email,
                subject=subject,
                body=body
            )
            
            if result:
                success_count += 1
            else:
                fail_count += 1

            percent = int((i / total_msgs) * 100)
            filled_blocks = int(percent / 10)
            filled = "⬛" * filled_blocks
            empty = "⬜" * (10 - filled_blocks)
            
            try:
                await progress_msg.edit_text(
                    f"""💀 **جاري الإرسال...**

{filled}{empty} {percent}%
{i} / {total_msgs} نجح {success_count} | فشل {fail_count}""",
                    disable_web_page_preview=True
                )
            except:
                pass

        await callback_query.message.reply_text(
            f"✅ تمت عملية إرسال البلاغات البريدية بنجاح!\n• الإجمالي: {total_msgs} رسالة\n• نجح: {success_count}\n• فشل: {fail_count}",
            disable_web_page_preview=True
        )

    elif data == "reset_members":
        if not is_linked:
            await callback_query.answer("⚠️ يجب تسجيل الدخول أولاً لاستخدام هذه الميزة!", show_alert=True)
            return

        await callback_query.answer()
        user_states[user_id] = "WAITING_RESET_TARGET"
        await callback_query.message.edit_text(
            text=RESET_MEMBERS_TEXT, reply_markup=cancel_reset_markup, disable_web_page_preview=True
        )

    elif data.startswith("rcount_"):
        count_val = int(data.replace("rcount_", ""))
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["reset_count"] = count_val
        user_states[user_id] = None
        
        raw_reset_target = user_data[user_id].get("reset_target", "")
        confirm_text = (
            f"🕯️ **تأكيد عملية تصفير الأعضاء** ⚠️\n\n"
            f"📌 **المجموعة / القناة:** `{raw_reset_target}`\n"
            f"👥 **العدد المحدد للطرد:** `{count_val}` عضو\n\n"
            f"⚠️ *ملاحظة:* تأكد أن الحساب لديه صلاحية الطرد لكي تنجح العملية بالكامل دون أخطاء."
        )

        confirm_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("تأكيد الطرد والبدء 💀", callback_data="confirm_reset_action")],
                [InlineKeyboardButton("إلغاء 🏠", callback_data="back_to_home")]
            ]
        )
        await callback_query.answer()
        await callback_query.message.edit_text(
            confirm_text,
            reply_markup=confirm_markup,
            disable_web_page_preview=True
        )

    elif data == "confirm_reset_action":
        await callback_query.answer()
        user_states[user_id] = None
        
        udata = user_data.get(user_id, {})
        raw_reset_target = udata.get("reset_target", "")
        count = udata.get("reset_count", 10)

        progress_msg = await callback_query.message.edit_text(
            f"""جاري تصفير أعضاء المجموعة 💀

الهدف : `{raw_reset_target}`
تم طرد : 0 • فشل : 0

⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ 0%""",
            disable_web_page_preview=True
        )

        success_count = 0
        fail_count = 0

        record = get_user_record(user_id)
        if not record or "session_string" not in record:
            await progress_msg.edit_text("❌ يجب عليك تسجيل الدخول أولاً لكي يتم استخدام صلاحياتك في طرد الأعضاء!")
            return

        action_client = Client(
            name=f"action_mem_{user_id}",
            api_id=31244607,
            api_hash="02d3b988051dd895b962450d2fb34fea",
            session_string=record["session_string"],
            in_memory=True
        )

        try:
            await action_client.connect()
            parsed_target = parse_target_input(raw_reset_target)
            try:
                if "t.me/+" in str(raw_reset_target) or "t.me/joinchat/" in str(raw_reset_target):
                    chat_obj = await action_client.join_chat(raw_reset_target)
                    target_chat_id = chat_obj.id
                else:
                    chat_obj = await action_client.get_chat(parsed_target)
                    target_chat_id = chat_obj.id
            except Exception as resolve_err:
                try:
                    target_chat_id = int(raw_reset_target)
                except:
                    await progress_msg.edit_text(f"❌ تعذر العثور على المجموعة أو القناة بسبب:\n`{resolve_err}`\n\nتأكد أن الحساب المرتبط منضم للمجموعة أو أن الرابط صحيح.")
                    await action_client.disconnect()
                    return

            for i in range(1, count + 1):
                try:
                    async for member in action_client.get_chat_members(target_chat_id):
                        if not member.user.is_bot and member.status.name not in ["ADMINISTRATOR", "OWNER"]:
                            await action_client.ban_chat_member(target_chat_id, member.user.id)
                            success_count += 1
                            break
                except Exception as e:
                    fail_count += 1
                    if isinstance(e, FloodWait):
                        await asyncio.sleep(e.value)

                if i % max(1, count // 10) == 0 or i == count:
                    percent = int((i / count) * 100)
                    filled_blocks = int(percent / 10)
                    filled = "⬛" * filled_blocks
                    empty = "⬜" * (10 - filled_blocks)
                    
                    try:
                        await progress_msg.edit_text(
                            f"""جاري تصفير أعضاء المجموعة 💀

الهدف : `{raw_reset_target}`
تم طرد : {success_count} • فشل : {fail_count}

{filled}{empty} {percent}%"""
                        )
                    except:
                        pass

                await asyncio.sleep(0.3)
                if success_count >= count:
                    break

            await action_client.disconnect()
        except Exception as e:
            try:
                await action_client.disconnect()
            except:
                pass
            await callback_query.message.reply_text(f"❌ حدث خطأ عام في جلسة الحساب:\n{e}")
            return

        await callback_query.message.reply_text(
            f"✅ تمت عملية تصفير الأعضاء بنجاح!\n• الهدف: `{raw_reset_target}`\n• الأعضاء المطردون: {success_count}\n• فشل: {fail_count}",
            disable_web_page_preview=True
        )

    elif data == "logout":
        user_states[user_id] = None
        delete_user_record(user_id)
        if user_id in user_data:
            del user_data[user_id]

        await callback_query.answer("تم تسجيل الخروج بنجاح")
        await callback_query.message.edit_text(text=UNLINKED_TEXT, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تسجيل الدخول 🔑", callback_data="quick_login")],
            [InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")]
        ]))

    elif data == "add_account":
        user_states[user_id] = None
        if user_id not in user_data:
            user_data[user_id] = {}
        await callback_query.answer()
        
        add_account_guide_short = """اختر الطريقة المناسبة لك لإضافة الإيميل وإرسال البلاغات بكل سهولة وبأمان تام 👇"""
        add_account_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🛠️ الطريقة الأولى (App Password)", callback_data="add_acc_method_1")],
                [InlineKeyboardButton("🔑 الطريقة الثانية (كلمة المرور العادية)", callback_data="add_acc_method_2")],
                [InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home"), InlineKeyboardButton("رجوع 🏠", callback_data="my_accounts")]
            ]
        )
        try:
            await callback_query.message.delete()
        except:
            pass
        await client.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=MAIN_PHOTO,
            caption=add_account_guide_short,
            reply_markup=add_account_markup
        )

    elif data == "add_acc_method_1":
        user_states[user_id] = "WAITING_NEW_EMAIL_M1"
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["email_type"] = "method_1"
        await callback_query.answer()
        cancel_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")],
                [InlineKeyboardButton("رجوع 🏠", callback_data="add_account")]
            ]
        )
        await callback_query.message.edit_text(METHOD_1_GUIDE, reply_markup=cancel_markup, disable_web_page_preview=True)

    elif data == "add_acc_method_2":
        user_states[user_id] = "WAITING_NEW_EMAIL_M2"
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["email_type"] = "method_2"
        await callback_query.answer()
        cancel_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")],
                [InlineKeyboardButton("رجوع 🏠", callback_data="add_account")]
            ]
        )
        await callback_query.message.edit_text(METHOD_2_GUIDE, reply_markup=cancel_markup, disable_web_page_preview=True)

    elif data == "back_to_home":
        user_states[user_id] = None
        await callback_query.answer()
        try:
            await callback_query.message.delete()
        except:
            pass
        await client.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=MAIN_PHOTO,
            caption=START_TEXT,
            reply_markup=get_main_markup(user_id)
        )


@app.on_message(filters.text & ~filters.command("start"))
async def handle_user_input(client: Client, message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    text = message.text.strip()

    if state == "WAITING_STEAL_FROM":
        target_input = text
        wait_msg = await message.reply_text("🔍 جاري فحص والتحقق من الكروب المصدر...")
        
        record = get_user_record(user_id)
        if not record or "session_string" not in record:
            await wait_msg.edit_text("❌ يجب عليك تسجيل الدخول أولاً!")
            return

        temp_client = Client(
            name=f"check_steal_{user_id}",
            api_id=31244607,
            api_hash="02d3b988051dd895b962450d2fb34fea",
            session_string=record["session_string"],
            in_memory=True
        )

        try:
            await temp_client.connect()
            parsed_target = parse_target_input(target_input)
            
            if "t.me/+" in target_input or "t.me/joinchat/" in target_input:
                chat_obj = await temp_client.join_chat(target_input)
            else:
                chat_obj = await temp_client.get_chat(parsed_target)
                
            user_data[user_id]["steal_from"] = chat_obj.id
            await temp_client.disconnect()
            
            await wait_msg.delete()
            user_states[user_id] = "WAITING_STEAL_TO"
            await message.reply_text(
                f"🏴‍☠️ **خمط ونقل الأعضاء – الخطوة 2 من 3**\n\n✅ تم التعرف على المصدر: `{chat_obj.title}`\n\nأدخل معرف، رابط، أو أيدي الكروب / القناة **الهدف** (التي تريد نقل الأعضاء إليها):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")]])
            )
        except Exception as e:
            try:
                await temp_client.disconnect()
            except:
                pass
            await wait_msg.edit_text(f"❌ تعذر العثور على الكروب المصدر أو التأكد منه:\n`{e}`\n\nتأكد أن الأيدي صحيح وأن الحساب منضم إليه.")
        return

    elif state == "WAITING_STEAL_TO":
        target_input = text
        wait_msg = await message.reply_text("🔍 جاري التحقق من الكروب الهدف...")
        
        record = get_user_record(user_id)
        temp_client = Client(
            name=f"check_stealto_{user_id}",
            api_id=31244607,
            api_hash="02d3b988051dd895b962450d2fb34fea",
            session_string=record["session_string"],
            in_memory=True
        )

        try:
            await temp_client.connect()
            parsed_target = parse_target_input(target_input)
            
            if "t.me/+" in target_input or "t.me/joinchat/" in target_input:
                chat_obj = await temp_client.join_chat(target_input)
            else:
                chat_obj = await temp_client.get_chat(parsed_target)
                
            user_data[user_id]["steal_to"] = chat_obj.id
            await temp_client.disconnect()
            
            await wait_msg.delete()
            user_states[user_id] = "WAITING_STEAL_SLEEP"
            await message.reply_text(
                f"🏴‍☠️ **خمط ونقل الأعضاء – الخطوة الأخيرة**\n\n✅ تم التعرف على الهدف: `{chat_obj.title}`\n\nأدخل وقت السكون (الانتظار) بالثواني بين إضافة كل عضو (مثال: `2` أو `3`)، أو اكتب `بدون وقت` للإرسال بأقصى سرعة:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")]])
            )
        except Exception as e:
            try:
                await temp_client.disconnect()
            except:
                pass
            await wait_msg.edit_text(f"❌ تعذر الوصول للكروب الهدف:\n`{e}`\n\nتأكد أن الأيدي أو الرابط صحيح وأن الحساب لديه صلاحيات.")
        return

    elif state == "WAITING_STEAL_SLEEP":
        if text.lower() == 'بدون وقت':
            sleep_time = 0
        else:
            try:
                sleep_time = int(text)
            except ValueError:
                await message.reply_text("❌ يرجى إدخال رقم صحيح بالثواني أو كتابة `بدون وقت`:")
                return

        user_data[user_id]["steal_sleep"] = sleep_time
        user_states[user_id] = None

        from_group = user_data[user_id].get("steal_from")
        to_group = user_data[user_id].get("steal_to")

        steal_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("إيقاف مؤقت 🛑", callback_data="pause_steal"), InlineKeyboardButton("استئناف ▶️", callback_data="resume_steal")],
            [InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")]
        ])

        progress_msg = await message.reply_text(
            f"🚀 **جاري بدء عملية نقل الأعضاء...**\n\n• المصدر: `{from_group}`\n• الهدف: `{to_group}`\n• الانتظار: `{sleep_time} ثانية`",
            reply_markup=steal_markup,
            disable_web_page_preview=True
        )

        record = get_user_record(user_id)
        if not record or "session_string" not in record:
            await progress_msg.edit_text("❌ يجب عليك تسجيل الدخول أولاً لتنفيذ عملية نقل الأعضاء!")
            return

        steal_client = Client(
            name=f"steal_action_{user_id}",
            api_id=31244607,
            api_hash="02d3b988051dd895b962450d2fb34fea",
            session_string=record["session_string"],
            in_memory=True
        )

        success_count = 0
        fail_count = 0

        try:
            await steal_client.connect()
            participants = []
            async for member in steal_client.get_chat_members(from_group):
                if not member.user.is_bot:
                    participants.append(member.user)

            for user in participants:
                while user_data.get(user_id, {}).get("steal_paused", False):
                    await asyncio.sleep(1)

                try:
                    await steal_client.add_chat_members(to_group, user.id)
                    success_count += 1
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                except Exception as e:
                    fail_count += 1
                    if isinstance(e, FloodWait):
                        await asyncio.sleep(e.value)

            await steal_client.disconnect()
        except Exception as e:
            try:
                await steal_client.disconnect()
            except:
                pass
            await progress_msg.edit_text(f"❌ حدث خطأ أثناء نقل الأعضاء:\n`{e}`")
            return

        await progress_msg.edit_text(
            f"✅ **تم الانتهاء من عملية نقل الأعضاء بنجاح!**\n\n• المصدر: `{from_group}`\n• الهدف: `{to_group}`\n• تم نقلهم بنجاح: {success_count}\n• فشل: {fail_count}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")]])
        )
        return

    if state in ["WAITING_NEW_EMAIL_M1", "WAITING_NEW_EMAIL_M2"]:
        if "@" not in text:
            await message.reply_text("❌ البريد الإلكتروني غير صالح. أرسل إيميل صحيح:")
            return
            
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["temp_email"] = text
        
        if state == "WAITING_NEW_EMAIL_M1":
            user_states[user_id] = "WAITING_NEW_PASSWORD_M1"
            prompt_text = f"""🛠️ **إدخال كلمة مرور التطبيق (App Password)**

الإيميل المحدد: `{text}`

الآن يرجى إرسال الـ 16 حرفاً الخاصة بـ كلمة المرور (App Password) :"""
        else:
            user_states[user_id] = "WAITING_NEW_PASSWORD_M2"
            prompt_text = f"""🔑 **إدخال كلمة المرور العادية**

الإيميل المحدد: `{text}`

الآن يرجى إرسال كلمة المرور الخاصة بحسابك (بدون تفعيل تخطي بخطوتين) :"""

        cancel_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("إلغاء 💀", callback_data="back_to_home")],
                [InlineKeyboardButton("رجوع 🏠", callback_data="add_account")]
            ]
        )
        
        await message.reply_text(
            prompt_text,
            reply_markup=cancel_markup,
            disable_web_page_preview=True
        )
        return

    elif state in ["WAITING_NEW_PASSWORD_M1", "WAITING_NEW_PASSWORD_M2"]:
        password = text
        email_val = user_data.get(user_id, {}).get("temp_email", "unknown@gmail.com")
        is_method_1 = (state == "WAITING_NEW_PASSWORD_M1")
        
        wait_msg = await message.reply_text("🔍 جاري فحص الحساب والتأكد من إعدادات الحماية...")
        status, err_msg = verify_email_credentials(email_val, password)
        
        if status == '2fa_enabled':
            user_states[user_id] = None
            if is_method_1:
                error_text = (
                    "❌ **فشلت العملية!**\n\n"
                    "• كلمة مرور التطبيق غير صحيحة أو أن الحساب لا يدعم هذه الطريقة حالياً.\n"
                    "• تأكد من إنشاء كلمة مرور التطبيق بشكل صحيح من إعدادات حسابك.\n"
                    "• أو حاول استخدام **'الطريقة الثانية (كلمة المرور العادية)'**."
                )
            else:
                error_text = (
                    "❌ **فشلت العملية!**\n\n"
                    "• تم اكتشاف أن الحساب **مفعل عليه التحقق بخطوتين (2-Step Verification)** أو يطلب مصادقة أمنية إضافية.\n"
                    "• لا يمكن استخدام 'الطريقة الثانية' مع هذا الحساب.\n"
                    "• يرجى استخدام **'الطريقة الأولى (App Password)'** وتوليد كلمة مرور خاصة بالتطبيقات لتتمكن من إضافته بأمان."
                )
            
            await wait_msg.edit_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")]])
            )
            return
            
        elif status == 'invalid':
            user_states[user_id] = None
            await wait_msg.edit_text(
                f"❌ **كلمة المرور غير صحيحة أو حدث خطأ في المصادقة!**\n\nالخطأ: `{err_msg}`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")]])
            )
            return
            
        try:
            await wait_msg.delete()
        except:
            pass

        save_user_email(user_id, email_val, password)
        user_states[user_id] = None
        
        user_emails = load_user_emails(user_id)
        
        acc_list_text = f"تمت إضافة الحساب بنجاح 👁‍🗨\n\nحساباتي ({len(user_emails)})\n"
        keyboard_btns = []
        for idx, item in enumerate(user_emails, 1):
            e_val = item.get("email")
            acc_list_text += f"\n{idx}. {e_val}"
            keyboard_btns.append([InlineKeyboardButton(f"{e_val} | حذف 🗑", callback_data=f"del_email_{e_val}")])
        
        keyboard_btns.append([InlineKeyboardButton("اضافه حساب جديد ➕", callback_data="add_account")])
        keyboard_btns.append([InlineKeyboardButton("رجوع 🏠", callback_data="back_to_home")])
        
        await message.reply_text(
            acc_list_text,
            reply_markup=InlineKeyboardMarkup(keyboard_btns),
            disable_web_page_preview=True
        )
        return

    elif state == "REPORT_WAITING_TARGET_EMAILS":
        emails = [e.strip() for e in text.split(",") if "@" in e]
        if not emails:
            emails = [text]
        user_data[user_id]["report_emails"] = emails
        user_states[user_id] = "REPORT_WAITING_SUBJECT"
        
        await message.reply_text(
            f"💀 **رفع بلاغ – الخطوة 2 من 4**\n\nتم تحديد `{len(emails)}` إيميل كهدف.\nالآن أدخل موضوع الرسالة :",
            reply_markup=CANCEL_REPORT_MARKUP,
            disable_web_page_preview=True
        )
        return

    elif state == "REPORT_WAITING_SUBJECT":
        user_data[user_id]["report_subject"] = text
        user_states[user_id] = "REPORT_WAITING_BODY"
        
        await message.reply_text(
            "💀 **رفع بلاغ – الخطوة 3 من 4**\n\nالآن أدخل نص الرسالة كاملاً :",
            reply_markup=CANCEL_REPORT_MARKUP,
            disable_web_page_preview=True
        )
        return

    elif state == "REPORT_WAITING_BODY":
        user_data[user_id]["report_body"] = text
        user_states[user_id] = "REPORT_WAITING_COUNT"
        
        await message.reply_text(
            "💀 **رفع بلاغ – الخطوة 4 من 4**\n\nكم رسالة تريد إرسالها لكل إيميل هدف ؟\nأدخل رقماً من 1 إلى 500",
            reply_markup=CANCEL_REPORT_MARKUP,
            disable_web_page_preview=True
        )
        return

    elif state == "REPORT_WAITING_COUNT":
        try:
            count = int(text)
            if not (1 <= count <= 500):
                raise ValueError()
        except ValueError:
            await message.reply_text("❌ يرجى إرسال رقماً صحيحاً بين 1 إلى 500:")
            return

        user_data[user_id]["report_count"] = count
        user_states[user_id] = None

        speed_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("بدون تأخير", callback_data="speed_0"),
                    InlineKeyboardButton("0.5 ثانية", callback_data="speed_0.5"),
                ],
                [
                    InlineKeyboardButton("1 ثانية", callback_data="speed_1"),
                    InlineKeyboardButton("2 ثانیه", callback_data="speed_2"),
                ],
                [
                    InlineKeyboardButton("5 ثوان", callback_data="speed_5"),
                    InlineKeyboardButton("10 ثوان", callback_data="speed_10"),
                ],
                [
                    InlineKeyboardButton("إلغاء", callback_data="back_to_home"),
                ]
            ]
        )

        speed_prompt_text = """سرعة الإرسال ⏱️

اختر التأخير بين كل رسالة والأخرى.

• بدون تأخير - إرسال بأقصى سرعة
• ثانية أو أكثر - أكثر أماناً وأقل احتمالاً للحجب"""

        await message.reply_text(
            speed_prompt_text,
            reply_markup=speed_markup,
            disable_web_page_preview=True
        )
        return

    elif state == "WAITING_PHONE":
        phone_number = re.sub(r'\s+', '', text)
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["phone"] = phone_number.replace("+", "")
        
        sent_msg = await message.reply_text("🕯️ جاري إرسال الكود إلى تيليغرام...")

        try:
            user_client = Client(
                name=f"temp_mem_{user_id}",
                api_id=31244607,
                api_hash="02d3b988051dd895b962450d2fb34fea",
                in_memory=True
            )
            await user_client.connect()
            sent_code = await user_client.send_code(phone_number)
            
            user_data[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            user_data[user_id]["client_instance"] = user_client

            user_states[user_id] = "WAITING_OTP"
            await sent_msg.edit_text(OTP_TEXT)
        except Exception as e:
            user_states[user_id] = None
            await sent_msg.edit_text(f"❌ حدث خطأ أثناء إرسال الكود:\n{e}")

    elif state == "WAITING_OTP":
        code = re.sub(r'\D', '', text)
        data = user_data.get(user_id, {})
        phone = data.get("phone")
        phone_code_hash = data.get("phone_code_hash")
        user_client = data.get("client_instance")

        if not phone or not phone_code_hash or not user_client:
            user_states[user_id] = None
            await message.reply_text("❌ انتهت الجلسة المؤقتة، يرجى إعادة إرسال رقم الهاتف من جديد.")
            return

        sent_msg = await message.reply_text("🕯️ جاري التحقق من الكود وحفظ الجلسة بالنظام...")

        try:
            try:
                await user_client.sign_in(
                    phone_number=f"+{phone}",
                    phone_code_hash=phone_code_hash,
                    phone_code=code,
                )
            except SessionPasswordNeeded:
                user_states[user_id] = "WAITING_2FA"
                await sent_msg.edit_text(TWO_STEP_TEXT)
                return

            session_string = await user_client.export_session_string()
            try:
                await user_client.disconnect()
            except:
                pass

            save_user_record(user_id, phone, session_string)
            user_states[user_id] = None

            linked_text = f"""تسجيل الدخول 🔑

تم تسجيل الدخول بنجاح وحفظ الجلسة ✅
الرقم: +{phone}

أصبح بإمكانك استخدام (البلاغ الداخلي، تصفير الأعضاء، وخمط الأعضاء) فوراً."""

            linked_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")],
                ]
            )
            await sent_msg.edit_text(linked_text, reply_markup=linked_markup)

        except PhoneCodeInvalid:
            await sent_msg.edit_text("❌ الكود غير صحيح، يرجى إرسال الكود الصحيح:")
        except PhoneCodeExpired:
            user_states[user_id] = None
            try:
                await user_client.disconnect()
            except:
                pass
            await sent_msg.edit_text("❌ انتهت صلاحية الكود.\n\nيرجى إعادة المحاولة من القائمة الرئيسية.")
        except Exception as e:
            try:
                await user_client.disconnect()
            except:
                pass
            user_states[user_id] = None
            await sent_msg.edit_text(f"❌ حدث خطأ:\n{e}")

    elif state == "WAITING_2FA":
        password = text
        data = user_data.get(user_id, {})
        phone = data.get("phone")
        user_client = data.get("client_instance")
        sent_msg = await message.reply_text("🕯️ جاري التحقق من كلمة المرور وحفظ الجلسة...")

        try:
            await user_client.check_password(password=password)
            session_string = await user_client.export_session_string()
            try:
                await user_client.disconnect()
            except:
                pass

            save_user_record(user_id, phone, session_string)
            user_states[user_id] = None

            linked_text = f"""تسجيل الدخول 🔑

تم تسجيل الدخول بنجاح وحفظ الجلسة ✅
الرقم: +{phone}

أصبح بإمكانك استخدام (البلاغ الداخلي، تصفير الأعضاء، وخمط الأعضاء) فوراً."""

            linked_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")],
                ]
            )
            await sent_msg.edit_text(linked_text, reply_markup=linked_markup)
        except Exception as e:
            try:
                if user_client:
                    await user_client.disconnect()
            except:
                pass
            user_states[user_id] = None
            await sent_msg.edit_text(f"❌ كلمة المرور غير صحيحة أو حدث خطأ:\n{e}")

    elif state == "WAITING_TARGET":
        target = text
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["target"] = target
        user_states[user_id] = "WAITING_REASON"
        
        reason_menu_text = f"""سبب البلاغ 🏴‍☠️

الهدف : `{target}`
النوع : حساب / قناة / المجموعة

اختر سبب البلاغ :"""

        await message.reply_text(
            reason_menu_text,
            reply_markup=reasons_markup,
            disable_web_page_preview=True
        )

    elif state == "WAITING_COMMENT":
        comment = text if text != "-" else ""
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["comment"] = comment
        user_states[user_id] = "WAITING_COUNT"
        
        target = user_data[user_id].get("target", "غير معروف")
        reason = user_data[user_id].get("reason", "غير معروف")
        comment_display = comment if comment else "لا يوجد تعليق"
        
        await message.reply_text(
            COUNT_REPORT_TEXT.format(
                target=target,
                reason=reason,
                comment=comment_display
            ),
            reply_markup=cancel_count_markup,
            disable_web_page_preview=True
        )

    elif state == "WAITING_COUNT":
        try:
            count = int(text)
            if not (1 <= count <= 999):
                raise ValueError()
        except ValueError:
            await message.reply_text("❌ يرجى إرسال رقم صحيح بين 1 و 999:")
            return

        user_data[user_id]["report_count"] = count
        user_states[user_id] = None
        
        target = user_data[user_id].get("target", "غير معروف")
        reason = user_data[user_id].get("reason", "غير معروف")
        comment = user_data[user_id].get("comment", "")
        
        progress_msg = await message.reply_text(
            SENDING_REPORT_TEXT.format(
                target=target,
                reason=reason,
                success=0,
                failed=0,
                progress_bar="⬛" * 10,
                percent=0
            ),
            disable_web_page_preview=True
        )

        success_count = 0
        failed_count = 0
        total = count

        record = get_user_record(user_id)
        if not record or "session_string" not in record:
            await progress_msg.edit_text("❌ يجب عليك تسجيل الدخول أولاً لكي تتمكن من إرسال البلاغات!")
            return

        action_client = Client(
            name=f"report_action_{user_id}",
            api_id=31244607,
            api_hash="02d3b988051dd895b962450d2fb34fea",
            session_string=record["session_string"],
            in_memory=True
        )

        try:
            await action_client.connect()
            parsed_target = parse_target_input(target)
            peer = await action_client.resolve_peer(parsed_target)
            
            from hydrogram.raw.types import (
                InputReportReasonSpam, 
                InputReportReasonViolence, 
                InputReportReasonPornography, 
                InputReportReasonChildAbuse, 
                InputReportReasonCopyright, 
                InputReportReasonOther
            )
            
            chosen_reason = user_data[user_id].get("reason", "غير معروف")
            if "أطفال" in chosen_reason:
                raw_reason = InputReportReasonChildAbuse()
            elif "عنف" in chosen_reason:
                raw_reason = InputReportReasonViolence()
            elif "الكبار" in chosen_reason:
                raw_reason = InputReportReasonPornography()
            elif "حقوق" in chosen_reason:
                raw_reason = InputReportReasonCopyright()
            elif "نصب" in chosen_reason or "احتيال" in chosen_reason:
                raw_reason = InputReportReasonSpam()
            else:
                raw_reason = InputReportReasonOther()

            for i in range(1, total + 1):
                try:
                    await action_client.invoke(
                        functions.account.ReportPeer(
                            peer=peer,
                            reason=raw_reason,
                            message=comment if comment else chosen_reason
                        )
                    )
                    success_count += 1
                
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    try:
                        await action_client.invoke(
                            functions.account.ReportPeer(
                                peer=peer,
                                reason=raw_reason,
                                message=comment if comment else chosen_reason
                            )
                        )
                        success_count += 1
                    except Exception as ex:
                        failed_count += 1
                
                except Exception as e:
                    failed_count += 1

                percent = int((i / total) * 100)
                filled_blocks = int(percent / 10)
                filled = "⬛" * filled_blocks
                empty = "⬜" * (10 - filled_blocks)

                try:
                    await progress_msg.edit_text(
                        SENDING_REPORT_TEXT.format(
                            target=target,
                            reason=reason,
                            success=success_count,
                            failed=failed_count,
                            progress_bar=filled + empty,
                            percent=percent
                        ),
                        disable_web_page_preview=True
                    )
                except:
                    pass

                await asyncio.sleep(7.0)

            await action_client.disconnect()

        except Exception as e:
            try:
                await action_client.disconnect()
            except:
                pass
            await progress_msg.edit_text(f"❌ حدث خطأ أثناء إرسال البلاغات:\n`{e}`")
            return

        await progress_msg.edit_text(
            f"""✅ **تمت عملية إرسال البلاغات!**

• الهدف : `{target}`
• السبب : `{reason}`
• التعليق : `{comment if comment else "لا يوجد"}`
• نجح (مقبول حقيقياً) : {success_count}
• فشل (مرفوض من السيرفر) : {failed_count}
• المجموع : {total}""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("القائمة الرئيسية 🏠", callback_data="back_to_home")]
            ]),
            disable_web_page_preview=True
        )

    elif state == "WAITING_RESET_TARGET":
        reset_target = text
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["reset_target"] = reset_target
        user_states[user_id] = "WAITING_RESET_COUNT"
        
        reset_step2_text = (
            f"💀 **تصفير الأعضاء – الخطوة 2 من 2** ⚡\n\n"
            f"🎯 **الهدف المحدد:** `{reset_target}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💡 **اختر أو أرسل العدد المطلوب:**\n"
            f"أدخل رقماً صحيحاً من الحزم أدناه أو اكتبه يدوياً (من 1 إلى 100,000 عضو) 👇"
        )

        reset_count_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⚡ 50 عضو", callback_data="rcount_50"),
                    InlineKeyboardButton("⚡ 100 عضو", callback_data="rcount_100"),
                    InlineKeyboardButton("⚡ 500 عضو", callback_data="rcount_500"),
                ],
                [
                    InlineKeyboardButton("🔥 1,000 عضو", callback_data="rcount_1000"),
                    InlineKeyboardButton("🔥 5,000 عضو", callback_data="rcount_5000"),
                ],
                [
                    InlineKeyboardButton("💀 إلغاء العملية", callback_data="back_to_home")
                ]
            ]
        )

        await message.reply_text(
            reset_step2_text,
            reply_markup=reset_count_markup,
            disable_web_page_preview=True
        )

    elif state == "WAITING_RESET_COUNT":
        try:
            count = int(text)
            if not (1 <= count <= 100000):
                raise ValueError()
        except ValueError:
            await message.reply_text("❌ يرجى إرسال رقم صحيح بين 1 و 100,000 فقط:")
            return

        user_states[user_id] = None
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["reset_count"] = count
        
        raw_reset_target = user_data[user_id].get("reset_target", "")
        confirm_text = f"""🕯️ **تأكيد تصفير الأعضاء**

المجموعة / القناة : `{raw_reset_target}`
العدد المحدد : **{count}** عضو سيتم طرده.

⚠️ هذا الإجراء نهائي ولا يمكن التراجع عنه!"""

        confirm_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("تأكيد الطرد 💀", callback_data="confirm_reset_action")],
                [InlineKeyboardButton("إلغاء", callback_data="back_to_home")]
            ]
        )
        await message.reply_text(
            confirm_text,
            reply_markup=confirm_markup,
            disable_web_page_preview=True
        )


if __name__ == "__main__":
    cleanup_old_sessions()
    print("Bot is running with StringSession & In-Memory support (No local session files)...")
    app.run()



