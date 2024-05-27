# M3U8 Video Converter Bot

This project contains a Telegram bot designed to convert M3U8 video streams into a single MP4 file and send it to the user. It utilizes the `python-telegram-bot` library for interacting with the Telegram API, `aiohttp` for asynchronous HTTP requests, and `ffmpeg` for merging video segments.

## Features

- Download M3U8 file and extract video segments.
- Download video segments concurrently for faster processing.
- Merge video segments into a single MP4 file.
- Send the converted video file directly to the user on Telegram.
- Utilizes Pyrogram for sending large video files.

## Requirements

- Python 3.6+
- `python-telegram-bot`
- `aiohttp`
- `ffmpeg` installed on the system and accessible from the command line.
- A Telegram bot token, and API ID and Hash from [my.telegram.org](https://my.telegram.org).

## Installation

1. Clone this repository or download the source code.
2. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

3. Make sure `ffmpeg` is installed on your system and is accessible from the command line.

4. Create a `config.json` file in the project root with the following structure:

    ```json
    {
      "API_ID": "your_api_id",
      "API_HASH": "your_api_hash",
      "BOT_TOKEN": "your_bot_token"
    }
    ```

    Replace `your_api_id`, `your_api_hash`, and `your_bot_token` with your actual Telegram API ID, API Hash, and bot token.

## Usage

1. Start the bot by running:

    ```bash
    python main.py
    ```

2. Interact with your bot on Telegram. Use the `/convert <M3U8 URL>` command to start converting a video.

## How It Works

- The bot accepts an M3U8 URL via the `/convert` command.
- It downloads the M3U8 file and extracts the URLs of the video segments.
- Video segments are downloaded concurrently to speed up the process.
- Downloaded segments are merged into a single MP4 file using `ffmpeg`.
- The final video file is sent to the user on Telegram.

## Limitations

- The bot is designed to work with publicly accessible M3U8 URLs. It may not work with URLs that require authentication or are behind a paywall.
- The size of the final video file is limited by Telegram's maximum file size for bots, which is 50 MB for documents and 2 GB for videos sent using Pyrogram.

## Disclaimer

This project is for educational purposes only. Use it at your own risk. The author is not responsible for any misuse or damage caused by this program.
