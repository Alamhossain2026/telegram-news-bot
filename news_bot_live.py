#!/usr/bin/env python3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction
import requests
from datetime import datetime
import os

TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = "76433037270348c392ced8a2c05a93a0"

COUNTRIES = {
    'uae': {'name': 'UAE', 'emoji': '🇦🇪', 'query': 'UAE OR Dubai OR "Abu Dhabi"'},
    'iran': {'name': 'Iran', 'emoji': '🇮🇷', 'query': 'Iran OR Tehran'},
    'israel': {'name': 'Israel', 'emoji': '🇮🇱', 'query': 'Israel OR "Tel Aviv"'}
}
LANGUAGES = {
    'bn': {
        'start': '🤖 স্বাগতম! আমি UAE, Iran এবং Israel এর সর্বশেষ খবর আনি।',
        'news_header': '📰 সর্বশেষ খবর',
        'fetching': '⏳ খবর সংগ্রহ করছি...',
        'no_news': '❌ এই মুহূর্তে কোনো খবর পাওয়া যায়নি।',
        'filter_set': '✅ ফিল্টার সেট করা হয়েছে:',
        'lang_set': '✅ ভাষা সেট করা হয়েছে:',
    },
    'en': {
        'start': '🤖 Welcome! I bring you the latest news from UAE, Iran & Israel.',
        'news_header': '📰 Latest News',
        'fetching': '⏳ Fetching latest news...',
        'no_news': '❌ No news found at the moment.',
        'filter_set': '✅ Filter set to:',
        'lang_set': '✅ Language set to:',
    }
}
class NewsBot:
    def __init__(self):
        self.user_lang = {}
        self.user_filter = {}
    
    def get_text(self, user_id, key):
        lang = self.user_lang.get(user_id, 'en')
        return LANGUAGES[lang].get(key, LANGUAGES['en'][key])
    
    def fetch_news(self, query, limit=5):
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': limit,
                'apiKey': NEWS_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
          articles = []
            if data.get('status') == 'ok':
                for article in data.get('articles', [])[:limit]:
                    articles.append({
                        'title': article.get('title', 'N/A'),
                        'description': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'url': article.get('url', '')
                    })
            
            return articles
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def format_news(self, user_id, articles):
        lang = self.user_lang.get(user_id, 'en')
        
        if not articles:
            return self.get_text(user_id, 'no_news')
        
        text = f"*{self.get_text(user_id, 'news_header')}*\n"
        text += f"_{datetime.now().strftime('%d-%m-%Y %H:%M')}_\n\n"
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'N/A')
            desc = article.get('description', '')[:80] if article.get('description') else ""
            source = article.get('source', 'Unknown')
            url = article.get('url', '')
          text += f"*{i}. {title}*\n"
            if desc:
                text += f"{desc}...\n"
            text += f"📌 {source}\n"
            if url:
                text += f"[🔗 পড়ুন / Read]({url})\n"
            text += "\n"
        
        return text

bot = NewsBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot.user_lang[user_id] = 'en'
    
    keyboard = [
        ['📰 /news', '🌍 /filter'],
        ['🗣️ /lang', '❓ /help']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = bot.get_text(user_id, 'start') + "\n\n"
    text += "📋 *কমান্ড / Commands:*\n"
    text += "/news - সর্বশেষ খবর পান\n"
    text += "/filter - দেশ বেছে নিন\n"
    text += "/lang - ভাষা বদলান\n"
    text += "/help - সাহায্য"
  await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await update.message.reply_text(bot.get_text(user_id, 'fetching'))
    
    try:
        country = bot.user_filter.get(user_id)
        
        if country and country in COUNTRIES:
            query = COUNTRIES[country]['query']
        else:
            query = "UAE OR Iran OR Israel OR Dubai OR Tehran"
        
        articles = bot.fetch_news(query, limit=5)
        message = bot.format_news(user_id, articles)
        
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text("❌ ত্রুটি হয়েছে")
        print(f"Error: {e}")
      async def filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇦🇪 UAE", callback_data="filter_uae"),
         InlineKeyboardButton("🇮🇷 Iran", callback_data="filter_iran")],
        [InlineKeyboardButton("🇮🇱 Israel", callback_data="filter_israel"),
         InlineKeyboardButton("🌍 সব / All", callback_data="filter_all")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🌍 দেশ বেছে নিন / Select Country:",
        reply_markup=reply_markup
    )

async def filter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    country_map = {
        'filter_uae': 'uae',
        'filter_iran': 'iran',
        'filter_israel': 'israel',
        'filter_all': None
    }
bot.user_filter[user_id] = country_map.get(data)
    country_name = COUNTRIES[country_map[data]]['name'] if country_map[data] else 'সব / All'
    
    await query.answer()
    await query.edit_message_text(
        text=f"{bot.get_text(user_id, 'filter_set')} {country_name} ✅"
    )

async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn"),
         InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("ভাষা বেছে নিন / Select Language:", reply_markup=reply_markup)

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    lang_map = {'lang_bn': 'bn', 'lang_en': 'en'}
    bot.user_lang[user_id] = lang_map.get(data, 'en')
    
    lang_name = 'বাংলা' if lang_map[data] == 'bn' else 'English'
    
    await query.answer()
    await query.edit_message_text(
        text=f"{bot.get_text(user_id, 'lang_set')} {lang_name} ✅"
    )
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🤖 *News Bot সাহায্য / Help*

📰 /news - সর্বশেষ খবর পান
🌍 /filter - দেশ ফিল্টার করুন
🗣️ /lang - ভাষা বদলান
❓ /help - এই সাহায্য

*কীভাবে ব্যবহার করবেন:*
1. /lang দিয়ে ভাষা বেছে নিন
2. /filter দিয়ে দেশ বেছে নিন
3. /news দিয়ে খবর পান

✨ *সব খবর রিয়েল টাইম আপডেটেড!*
    """
    await update.message.reply_text(text, parse_mode='Markdown')

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN environment variable প্রয়োজন!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news))
    application.add_handler(CommandHandler("filter", filter_handler))
    application.add_handler(CommandHandler("lang", lang_handler))
    application.add_handler(CommandHandler("help", help_cmd))
application.add_handler(CallbackQueryHandler(filter_callback, pattern='^filter_'))
    application.add_handler(CallbackQueryHandler(lang_callback, pattern='^lang_'))
    
    print("✅ বট চলছে!")
    application.run_polling()

if __name__ == '__main__':
    main()
