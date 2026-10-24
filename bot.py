from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8888662238:AAH0t1HZXAXfhvjn4aGvF76gwb2AZ7PSR3I"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات یادآور کالیبراسیون هستم.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()