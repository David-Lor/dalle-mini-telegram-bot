# DALL·E mini Telegram bot

[![@dalle_mini_bot](https://img.shields.io/badge/Telegram%20Bot-@dalle_mini_bot-blue?logo=telegram&style=plastic)](https://telegram.me/dalle_mini_bot)

A Telegram bot interface for [DALL·E mini](https://github.com/borisdayma/dalle-mini).
Request 9 AI-generated images from any prompt you give, directly from Telegram.

![Bot logo, generated by DALL·E mini with the prompt "a cat playing with a paper plane"](docs/bot-logo.jpg)

[![Telegram Bot screenshot](docs/Telegram-DalleMiniBot-screenshot.png)](https://telegram.me/dalle_mini_bot)

## Features

- Request from Telegram, return the 9 pictures result as an album
- Status report while the images are being generated (the bot sends a 'typing-like' status to the user, until all its requests are completed)
- If the server is too busy, keep retrying until success (or timeout)

The bot is deployed here: [https://telegram.me/dalle_mini_bot](https://telegram.me/dalle_mini_bot)

## Changelog

- v..
  - **(Breaking)** Redis is now required
  - Use Redis for RateLimiter counters (this allows sharing counters between bot instances)
  - Add MQTT integration for sending logs to MQTT topic
  - Close Redis connection on teardown
  - Set Redis password as pydantic.SecretStr on settings model
- v0.2.2
  - Support Redis authentication
  - Fixed exceptions not being included on "Request failed" log records
  - Fixed loguru incompatibility with ApiTelegramException
  - Ignore errors when pushing logs to Redis
- v0.2.1
  - Graceful shutdown (configurable; wait until pending requests are completed, while not accepting new requests)
  - Retry Telegram Bot API requests on 'Too Many Requests' error; usage of requests.Session
  - Set bot commands via API on startup, for Telegram hinting
  - Limit prompt text length on Generate command (configurable min/max limits via settings)
  - Add Redis integration for sending logs to Redis queue
  - Improvements in log records
- v0.1.1
  - Send message to users while the image is being generated, informing that it may take a while; the message is deleted on success or controlled error
  - Add `/about` command
  - Timeout chat 'typing-like' action & stop it when bot blocked by user
  - Remove chats with count of 0 from Counters
  - Setting for deleting Telegram bot Webhook on startup
- v0.0.2
  - Add pysocks requirement
  - Detect when bot blocked by user on middleware
- v0.0.1
  - Initial release
    - Generate images from `/generate` command, return as album
    - `/generate` command rate limited at chat level (concurrent requests limit)
    - `/generate` command sends a 'typing-like' status to the user, while the prompt/s requested are being generated
