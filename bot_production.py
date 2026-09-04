𝐒𝐀𝐉𝐀𝐃 𝐀𝐃𝐄𝐋, [⁨4⁩ سبتمبر ⁨2026⁩ في ⁨8:18 PM⁩
]
return
    context.user_data["awaiting_broadcast"] = True
    await query.message.reply_text("📣 قم بإرسال الرسالة الآن (نص، صورة، ملصق...) للبدء بنشرها لكل المستخدمين:")

elif data.startswith("ban_user_"):
    if not get_permission("ban"):
        await query.answer("❌ لا تملك صلاحية الحظر!", show_alert=True)
        return
    uid = int(data.split("_")[2])
    set_ban_user(uid, True)
    await query.answer("✅ تم حظر المستخدم بنجاح!", show_alert=True)
elif data.startswith("unban_user_"):
    if not get_permission("ban"):
        await query.answer("❌ لا تملك صلاحية إلغاء الحظر!", show_alert=True)
        return
    uid = int(data.split("_")[2])
    set_ban_user(uid, False)
    await query.answer("✅ تم إلغاء حظر المستخدم!", show_alert=True)
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE): user = update.effective_user
if user.id == ADMIN_ID and context.user_data.get("awaiting_broadcast"):
    context.user_data["awaiting_broadcast"] = False
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = cursor.fetchall()
    conn.close()

    success = 0
    failed = 0
    await update.message.reply_text(f"⏳ جاري بدء الإذاعة لـ {len(users)} مستخدم...")

    for (u_id,) in users:
        if u_id == ADMIN_ID:
            continue
        try:
            await update.message.copy(chat_id=u_id)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ **تمت الإذاعة بنجاح!**\n\n"
        f"🟢 الناجحة: {success}\n"
        f"🔴 الفاشلة (حظر أو مغادرة): {failed}",
        parse_mode="Markdown"
    )
    return

if user.id == ADMIN_ID:
    if update.message.reply_to_message:
        if not get_permission("replies"):
            await update.message.reply_text("❌ لا تملك صلاحية الردود حالياً.")
            return
        target_msg = update.message.reply_to_message
        try:
            first_line = target_msg.text or target_msg.caption or ""
            user_id = int(first_line.split("ID:** `")[1].split("`")[0])
            
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=ADMIN_ID,
                message_id=update.message.message_id
            )
            await update.message.reply_text("✅ تم إرسال الرد بنجاح!")
        except Exception as e:
            await update.message.reply_text(f"❌ تعذر استخراج ايدي المستخدم أو إرسال الرد: {e}")
    return

if is_user_banned(user.id):
    await update.message.reply_text("❌ أنت محظور من استخدام البوت.")
    return

show_username = get_setting("show_sender_username") == "1"
sender_info = f"@{user.username}" if (show_username and user.username) else "مخفي"

header_text = (
    f"📩arkdown")
elif data ={user.full_name} ({sender_info})\n"
    f"🆔 ID: `{user.id}`"
)

is_banned = is_user_banned(user.id)
ban_btn_text = "إلغاء الحظر 🔓" if is_banned else "حظر المستخدم 🚫"
ban_cb_data = f"unban_user_{user.id}" if is_banned else f"ban_user_{user.id}"

admin_markup = InlineKeyboardMarkup([
    [InlineKeyboardButton(ban_btn_text, callback_data=ban_cb_data)]
])

await context.bot.send_message(chat_id=ADMIN_ID, text=header_text, parse_mode="Markdown", reply_markup=admin_markup)
await update.message.forward(chat_id=ADMIN_ID)

await update.message.reply_text("تم إرسال رسالتك للمشرف بنجاح!")
def main(): init_db() app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))

print("البوت الجاهز للإنتاج يعمل بنجاح...")
app.run_polling()
if name == "main": main()
