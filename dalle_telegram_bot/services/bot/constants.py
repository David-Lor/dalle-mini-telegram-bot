BASIC_COMMAND_REPLIES = {
    "/start": """👋 Hello there!\n\nThis bot returns 9 AI-generated images from any prompt you give, using <a href="https://github.com/borisdayma/dalle-mini">DALL·E mini</a>.\n\n<b>Example:</b> Send a message like <pre>/generate a cat eating a hamburger</pre> to generate a set of images.\n\nCheck /help and /about for more info.""",
    "/help": "Send a message like <pre>/generate a cat eating a hamburger</pre> to generate a set of images.",
    "/about": """<b><a href="https://github.com/David-Lor/dalle-mini-telegram-bot">DALL·E mini Telegram bot</a></b> is a bot that returns 9 AI-generated images from any prompt you give, using <a href="https://github.com/borisdayma/dalle-mini">DALL·E mini</a>.\n\n<b>How does it work?</b>\nThe provided text prompt is passed to <a href="https://github.com/borisdayma/dalle-mini">DALL·E mini</a>, the same way it's done on the official webpage. The returned pictures are forwarded to Telegram via the bot and sent to you.\n\nBuilt with ♥️ using Python and pyTelegramBotAPI.\n<b>Source code:</b> https://github.com/David-Lor/dalle-mini-telegram-bot""",
}

BASIC_COMMAND_DISABLE_LINK_PREVIEWS = {"/start", "/help", "/about"}

COMMAND_GENERATE = "/generate"

COMMAND_GENERATE_REPLY_GENERATING = "The image is being generated. Please wait a few minutes for it..."

COMMAND_GENERATE_REPLY_RATELIMIT_EXCEEDED = "You have other images being generated. " \
                                            "Please wait until those are sent to you before asking for more."

COMMAND_GENERATE_PROMPT_TOO_SHORT = "Your prompt message is too short, try with something longer " \
                                    "(at least {characters} characters)."

COMMAND_GENERATE_PROMPT_TOO_LONG = "Your prompt message is too long, try with something shorter " \
                                   "(at most {characters} characters)."

COMMAND_GENERATE_REPLY_TEMPORARILY_UNAVAILABLE = "Your image could not be generated. Please try again later."

UNKNOWN_ERROR_REPLY = "Unknown error. Please try again later."

COMMANDS_HELP = {
    "/generate": "Generate a set of pictures from a given prompt. The prompt must be given after the /generate command",
    "/help": "Help about the bot usage",
    "/about": "About the bot",
}
