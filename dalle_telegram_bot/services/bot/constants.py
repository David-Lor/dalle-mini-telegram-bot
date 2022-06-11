BASIC_COMMAND_REPLIES = {
    "/start": """👋 Hello there!\n\nThis bot returns 9 AI-generated images from any prompt you give, using <a href="https://github.com/borisdayma/dalle-mini">DALL·E mini</a>.\n\n<b>Example:</b> Send a message like <pre>/generate a cat eating a hamburger</pre> to generate a set of images.""",
    "/help": "Send a message like <pre>/generate a cat eating a hamburger</pre> to generate a set of images.",
}

BASIC_COMMAND_DISABLE_LINK_PREVIEWS = {"/start"}

COMMAND_GENERATE = "/generate"

COMMAND_GENERATE_REPLY_RATELIMIT_EXCEEDED = "You have other images being generated. " \
                                            "Please wait until those are sent to you before asking for more."

COMMAND_GENERATE_PROMPT_TOO_SHORT = "Your prompt message is too short, try with something longer."

COMMAND_GENERATE_REPLY_TEMPORARILY_UNAVAILABLE = "Your image could not be generated. Please try again later."

UNKNOWN_ERROR_REPLY = "Unknown error. Please try again later."
