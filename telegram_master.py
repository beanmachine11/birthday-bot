import os
import asyncio
from datetime import datetime, timedelta
import json

from telegram import Bot
import gspread
from google.oauth2.service_account import Credentials


# =============================
# CONFIG
# =============================

SPREADSHEET_NAME = "Birthdays"   # Google Sheet FILE name

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDS_JSON")

if not TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN environment variable")

if not CHAT_ID:
    raise ValueError("Missing CHAT_ID environment variable")

if not GOOGLE_CREDS:
    raise ValueError("Missing GOOGLE_CREDS_JSON environment variable")


# =============================
# GOOGLE SHEETS AUTH
# =============================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# creds = Credentials.from_service_account_file("credentials.json", scopes=scope)

creds_dict = json.loads(GOOGLE_CREDS)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open first tab of spreadsheet
sheet = client.open(SPREADSHEET_NAME).sheet1


# =============================
# MAIN LOGIC
# =============================

async def main():
    print("Birthday bot running...")
    bot = Bot(token=TOKEN)
    today = datetime.now().date()

    rows = sheet.get_all_records()

    birthday_today = []
    family_reminders = []

    for row in rows:
        birthday_str = str(row["Birthday"]).strip()

        # Robust parsing (supports DD/MM/YYYY primarily)
        try:
            birthday_full = datetime.strptime(birthday_str, "%d/%m/%Y").date()
        except ValueError:
            try:
                birthday_full = datetime.strptime(birthday_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"Skipping invalid date format: {birthday_str}")
                continue

        birthday_this_year = birthday_full.replace(year=today.year)

        # 🎉 Birthday today
        if birthday_this_year == today - timedelta(days=1):
            birthday_today.append(row["Name"])

        # ⏳ 7-day reminder for Family
        if str(row["Category"]).strip().lower() == "family":
            reminder_date = birthday_this_year - timedelta(days=8)
            if reminder_date == today:
                family_reminders.append(row["Name"])

    messages = []

    if family_reminders:
        messages.append(
            "⏳ Family Birthdays in 1 Week:\n" +
            "\n".join(family_reminders)
        )

    if birthday_today:
        messages.append(
            "🎉 Birthdays Today:\n" +
            "\n".join(birthday_today)
        )

    if messages:
        final_message = "\n\n".join(messages)
        await bot.send_message(chat_id=CHAT_ID, text=final_message)
        print("Notification sent.")
    else:
        print("No birthdays or reminders today.")



if __name__ == "__main__":
    asyncio.run(main())