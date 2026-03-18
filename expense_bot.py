"""
💰 بوت حاسبة المصاريف - Telegram Expense Tracker Bot
=====================================================
كيف تشغّله:
1. ثبّت المكتبة:  pip install python-telegram-bot
2. حط الـ Token في السطر أدناه
3. شغّل:  python expense_bot.py
"""

import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ← حط التوكن هنا بين الأقواس
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ─────────────────────────────────────────
# قاعدة البيانات
# ─────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("expenses.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            amount    REAL    NOT NULL,
            note      TEXT,
            date      TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_expense(user_id: int, amount: float, note: str):
    conn = sqlite3.connect("expenses.db")
    conn.execute(
        "INSERT INTO expenses (user_id, amount, note, date) VALUES (?, ?, ?, ?)",
        (user_id, amount, note, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()


def get_expenses(user_id: int):
    conn = sqlite3.connect("expenses.db")
    rows = conn.execute(
        "SELECT amount, note, date FROM expenses WHERE user_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_total(user_id: int) -> float:
    conn = sqlite3.connect("expenses.db")
    total = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id=?",
        (user_id,),
    ).fetchone()[0]
    conn.close()
    return total


def clear_expenses(user_id: int):
    conn = sqlite3.connect("expenses.db")
    conn.execute("DELETE FROM expenses WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# أوامر البوت
# ─────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 أهلاً! أنا بوت حاسبة المصاريف 💰\n\n"
        "الأوامر المتاحة:\n"
        "➕ /add <المبلغ> <الوصف>  — يضيف مصروف\n"
        "   مثال: /add 5000 غداء\n\n"
        "📋 /list  — يعرض كل المصاريف\n"
        "🧮 /total — يعرض المجموع الكلي\n"
        "🗑 /clear  — يمسح كل المصاريف\n"
    )
    await update.message.reply_text(msg)


async def add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = ctx.args  # الأرقام والنص بعد /add

    if not args:
        await update.message.reply_text(
            "❌ الصيغة الصحيحة:\n/add <المبلغ> <الوصف>\nمثال: /add 5000 غداء"
        )
        return

    try:
        amount = float(args[0])
    except ValueError:
        await update.message.reply_text("❌ المبلغ لازم يكون رقم. مثال: /add 5000 غداء")
        return

    note = " ".join(args[1:]) if len(args) > 1 else "بدون وصف"
    add_expense(user_id, amount, note)

    await update.message.reply_text(
        f"✅ تم تسجيل المصروف!\n💸 {amount:,.0f} دينار — {note}"
    )


async def list_expenses(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rows = get_expenses(user_id)

    if not rows:
        await update.message.reply_text("📭 ما عندك أي مصاريف مسجّلة بعد.")
        return

    lines = ["📋 *قائمة مصاريفك:*\n"]
    for i, (amount, note, date) in enumerate(rows, 1):
        lines.append(f"{i}. 💸 {amount:,.0f} — {note}  _{date}_")

    total = get_total(user_id)
    lines.append(f"\n🧮 *المجموع: {total:,.0f} دينار*")

    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown"
    )


async def total(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    t = get_total(user_id)
    count = len(get_expenses(user_id))

    await update.message.reply_text(
        f"🧮 *إجمالي مصاريفك*\n\n"
        f"عدد العمليات: {count}\n"
        f"المجموع: *{t:,.0f} دينار*",
        parse_mode="Markdown",
    )


async def clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    clear_expenses(user_id)
    await update.message.reply_text("🗑 تم مسح جميع مصاريفك. ابدأ من جديد! 💪")


# ─────────────────────────────────────────
# تشغيل البوت
# ─────────────────────────────────────────

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("add",    add))
    app.add_handler(CommandHandler("list",   list_expenses))
    app.add_handler(CommandHandler("total",  total))
    app.add_handler(CommandHandler("clear",  clear))

    print("✅ البوت شغّال! اضغط Ctrl+C للإيقاف.")
    app.run_polling()


if __name__ == "__main__":
    main()
