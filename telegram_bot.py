import telegram
from traceback import print_exc
from config import tg_bot_token

# Get @atlas_alert_bot
tg_alerts_bot = telegram.Bot(token=tg_bot_token)


# ---Telegram Bot Functions---
def send_telegram_message(bot, message, chat_id, disable_link_preview=True):
    for _ in range(3):
        try:
            bot.send_message(chat_id=chat_id, text=message,
                             parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=disable_link_preview)
            break  # If successful
        except Exception:
            print_exc()


def telegram_message_to_groups(message, chat_ids, bot=tg_alerts_bot):
    for chat_id in chat_ids:
        send_telegram_message(bot, message, chat_id)
