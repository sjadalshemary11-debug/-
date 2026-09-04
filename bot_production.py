import os
import asyncio
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token & Admin ID from environment variables
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# Database setup
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_banned INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            perm_name TEXT PRIMARY KEY,
            is_allowed INTEGER DEFAULT 1
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO permissions (perm_name, is_allowed) VALUES ('broadcast', 1)")
    cursor.execute("INSERT OR IGNORE INTO permissions (perm_name, is_allowed) VALUES ('ban', 1)")
    conn.commit()
    conn.close()

init_db()

def get_permission(perm_name):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_allowed FROM permissions WHERE perm_name = ?", (perm_name,))
    res = cursor.fetchone()
    conn.close()
    return res[0] == 1 if res else True

def set_permission(perm_name, status):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE permissions SET is_allowed = ? WHERE perm_name = ?", (1 if status else 0, perm_name))
    conn.commit()
    conn.close()

def is_user_banned(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] == 1 if res else False

def add_user(user_id, username):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def set_ban_user(user_id, status):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if status else 0, user_id))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_banned(user.id):
        await update.message.reply_text("❌ أنت محظور من استخدام البوت.")
        return

    add_user(user.id, user.username)

    if user.id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("📢 الإذاعة العامة", callback_data="admin_broadcast")],
            [InlineKeyboardButton("⚙️ إعدادات الصلاحيات", callback_data="admin_perms")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("أهلاً بك يا مدير! اختر خياراً:", reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"أهلاً بك {user.first_name}! مرحباً بك في البوت.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_broadcast":
        if not get_permission("broadcast"):
            await query.answer("❌ تم إيقاف صلاحية الإذاعة.", show_alert=True)
            return
        context.user_data["awaiting_broadcast"] = True
        await query.message.reply_text("📣 أرسل الرسالة التي تريد إذاعتها للمستخدمين:")

    elif data == "admin_perms":
        b_perm = get_permission("broadcast")
        keyboard = [
            [InlineKeyboardButton(f"الإذاعة: {'مفعلة ✅' if b_perm else 'معطلة ❌'}", callback_data="toggle_broadcast")],
            [InlineKeyboardButton("🔙 العودة", callback_data="admin_main")]
        ]
        await query.edit_message_text("تعديل الصلاحيات:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "toggle_broadcast":
        cur = get_permission("broadcast")
        set_permission("broadcast", not cur)
        await button_handler(update, context)

    elif data == "admin_main":
        keyboard = [
            [InlineKeyboardButton("📢 الإذاعة العامة", callback_data="admin_broadcast")],
            [InlineKeyboardButton("⚙️ إعدادات الصلاحيات", callback_data="admin_perms")]
        ]
        await query.edit_message_text("أهلاً بك يا مدير! اختر خياراً:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_user_banned(user.id):
        return

    if user.id == ADMIN_ID and context.user_data.get("awaiting_broadcast"):
        context.user_data["awaiting_broadcast"] = False
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()

        success = 0
        failed = 0
        await update.message.reply_text("⏳ جاري إرسال الإذاعة...")

        for (u_id,) in users:
            if u_id == ADMIN_ID:
                continue
            try:
                await update.message.copy(chat_id=u_id)
                success += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1

        await update.message.reply_text(f"✅ تم الانتهاء!\nتم الإرسال لـ: {success}\nفشل الإرسال لـ: {failed}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))
    app.run_polling()

if __name__ == "__main__":
    main()
