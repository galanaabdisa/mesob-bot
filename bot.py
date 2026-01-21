import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token
TOKEN = os.getenv('BOT_TOKEN')

def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"organizations": []}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇪🇹 Afaan Oromoo", callback_data='lang_or')],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data='lang_am')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')]
    ]
    await update.message.reply_text(
        "🏛️ *MESOB Agaro Service Bot*\n\nPlease select language:\nAfaan filadhu:\nቋንቋ ይምረጡ:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return 'LANGUAGE'

async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    
    data = load_data()
    orgs = data['organizations']
    
    keyboard = []
    for org in orgs:
        name = org[f'name_{lang}']
        keyboard.append([InlineKeyboardButton(name, callback_data=f'org_{org["id"]}')])
    
    keyboard.append([InlineKeyboardButton("🔍 Search", callback_data='search')])
    
    if lang == 'or':
        text = "🏢 Dhaabbilee MESOB:\n\nMaqaa filadhu:"
    elif lang == 'am':
        text = "🏢 በMESOB ያሉ ድርጅቶች:\n\nስም ይምረጡ:"
    else:
        text = "🏢 MESOB Organizations:\n\nSelect name:"
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return 'ORGANIZATION'

async def organization_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'search':
        lang = context.user_data.get('lang', 'en')
        if lang == 'or':
            text = "Maqaa dhaabbataa barreessi:"
        elif lang == 'am':
            text = "የድርጅት ስም ይፃፉ:"
        else:
            text = "Enter organization name:"
        await query.edit_message_text(text)
        return 'SEARCH'
    
    org_id = int(query.data.split('_')[1])
    data = load_data()
    org = next((o for o in data['organizations'] if o['id'] == org_id), None)
    
    if org:
        lang = context.user_data.get('lang', 'en')
        services = org.get(f'services_{lang}', org.get('services_or', []))
        
        services_text = "\n".join([f"• {s}" for s in services])
        
        back_text = "🔙 Deebi'i" if lang == 'or' else "🔙 ተመለስ" if lang == 'am' else "🔙 Back"
        keyboard = [[InlineKeyboardButton(back_text, callback_data='back')]]
        
        message = f"✅ *{org[f'name_{lang}']}*\n\n📋 Services at MESOB:\n{services_text}"
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    return 'SERVICES'

async def search_orgs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_term = update.message.text.lower()
    lang = context.user_data.get('lang', 'en')
    data = load_data()
    
    results = []
    for org in data['organizations']:
        for lang_code in ['or', 'am', 'en']:
            if search_term in org.get(f'name_{lang_code}', '').lower():
                results.append(org)
                break
    
    keyboard = []
    for org in results[:8]:
        name = org[f'name_{lang}']
        keyboard.append([InlineKeyboardButton(name, callback_data=f'org_{org["id"]}')])
    
    back_text = "🔙 Deebi'i" if lang == 'or' else "🔙 ተመለስ" if lang == 'am' else "🔙 Back"
    keyboard.append([InlineKeyboardButton(back_text, callback_data='back')])
    
    if results:
        text = f"Found {len(results)} organizations:"
    else:
        text = "No organizations found."
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return 'ORGANIZATION'

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    data = load_data()
    orgs = data['organizations']
    
    keyboard = []
    for org in orgs:
        name = org[f'name_{lang}']
        keyboard.append([InlineKeyboardButton(name, callback_data=f'org_{org["id"]}')])
    
    keyboard.append([InlineKeyboardButton("🔍 Search", callback_data='search')])
    
    if lang == 'or':
        text = "🏢 Dhaabbilee MESOB:\n\nMaqaa filadhu:"
    elif lang == 'am':
        text = "🏢 በMESOB ያሉ ድርጅቶች:\n\nስም ይምረጡ:"
    else:
        text = "🏢 MESOB Organizations:\n\nSelect name:"
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return 'ORGANIZATION'

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "MESOB Service Bot\n"
        "Commands:\n"
        "/start - Start bot\n"
        "/help - Show this message"
    )

def main():
    if not TOKEN:
        print("ERROR: No BOT_TOKEN found!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'LANGUAGE': [CallbackQueryHandler(language_selection, pattern='^lang_')],
            'ORGANIZATION': [
                CallbackQueryHandler(organization_selection, pattern='^org_'),
                CallbackQueryHandler(organization_selection, pattern='^search$'),
                CallbackQueryHandler(back_to_main, pattern='^back$')
            ],
            'SERVICES': [CallbackQueryHandler(back_to_main, pattern='^back$')],
            'SEARCH': [MessageHandler(filters.TEXT & ~filters.COMMAND, search_orgs)]
        },
        fallbacks=[CommandHandler('help', help_command)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('help', help_command))
    
    print("MESOB Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
