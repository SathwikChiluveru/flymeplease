from telegram import BotCommand
from telegram.ext import CommandHandler, ConversationHandler

from handlers.start import start
from handlers.search import search
# from handlers.subscribe import subscribe  # New conversation handler
# from handlers.my_routes import my_routes  # New conversation handler
from handlers.cancel import cancel
# from handlers.help import help

def setup_dispatcher(app):
    # Set commands for the bot
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("search", "Search for flight alerts"),
        BotCommand("subscribe", "Subscribe to route alerts"),
        BotCommand("my_routes", "Manage your subscribed routes"),
        BotCommand("help", "Show help information"),
        BotCommand("cancel", "Cancel the current operation")
    ]
    
    async def set_commands(application):
        await application.bot.set_my_commands(commands)
    
    app.post_init = set_commands

    # Simple Command Handlers 
    app.add_handler(CommandHandler("start", start))
    # app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("cancel", cancel))

    # Conversation Handlers 
    app.add_handler(search())
    # app.add_handler(subscribe())    
    # app.add_handler(my_routes()) 
