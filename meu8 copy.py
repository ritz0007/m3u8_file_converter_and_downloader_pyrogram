import requests
import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
import aiohttp
import subprocess
import uuid
import logging
import json
from datetime import datetime
from pyrogram import Client

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configurations
with open('config.json', 'r') as f:
    config = json.load(f)
api_id = config.get('API_ID')  # Your API ID
api_hash = config.get('API_HASH')  # Your API Hash
bot_token = config.get('BOT_TOKEN')  # Your Bot Token

pyro_client = Client("my_bot_session", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

async def send_large_video(chat_id, video_path):
        await pyro_client.send_video(chat_id=chat_id, video=video_path)

async def convert_and_send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    m3u8_url = ' '.join(context.args)  # Assuming the M3U8 URL is passed as a command argument

    if not m3u8_url:
        await context.bot.send_message(chat_id=chat_id, text="Please provide an M3U8 URL.")
        return

    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Cookie': 'csrfToken=GjmLm2ef0PXV7E7Om7sQ14dw; browserid=4IDM1uXiu8OR9zyqdPRdOWb9hlpuEdXE_ljyg9BZPC0P-ZVg7JwjWDMpVC0=; lang=en; TSID=ZhvPYdhs492b9mXESdk4fXXoNFEs7aFm; __bid_n=18faea486c0385893e4207; ndut_fmt=B5E57700A6E9911F495F7360C8AA567A79624741DECF6ADB7F5B850FFFB9E9F2; ab_sr=1.0.1_MjUzZDU5NmI1NjQzZDE2ZWMzNDhjNjZhNmIyZDBmMTMzYmI3YjdiY2E3ZTI1MWMyNThjNjQ2YmIxODVjNDQ0YjkxMDFiODRiYTQxYWQ1ZjIyODg2ZjdiMGQ1ZmIzODRhNTZhNDJhNDM5Njg2MjBjMWZiMDk5MjE5MzIxYjc3ZWYyNmYxZGRlNDI1Y2U3MjVkNzNiYTE4NWU3ODM0YWU3MA==; _ga_06ZNKL8C2E=GS1.1.1716621973.1.1.1716622752.17.0.0; _ga=GA1.1.515141628.1716621973; ndus=Y2G_NeyteHuiKaVLHQB80MDytI3rs4MzrNJzPtjV; ab_ymg_result={"data":"a130b873d3834b33ac12249ef2e05128b5847af44e7cbf8fbd012928a6bb27b09503a853fe5eb4da3a25489dd47f7b0910dcbad19ee865691e3bc8adc1de1ab74eb79be1ef5f50412d69d754923d9da2cbc5e0f984e150841b52c9f2dbede174f63f765154be620d6e843675918cf1dc99d4e308f144d25df1c29fcfd1a5e9fc","key_id":"66","sign":"90cb60ab"}'
        }

    # Step 1: Download the M3U8 file
    response = requests.get(m3u8_url, headers=headers)
    if response.status_code != 200:
        await context.bot.send_message(chat_id=chat_id, text="Failed to download the M3U8 file.")
        return

    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    m3u8_file_path = os.path.join(output_dir, "playlist.m3u8")
    with open(m3u8_file_path, 'wb') as file:
        file.write(response.content)

    await context.bot.send_message(chat_id=chat_id, text="M3U8 file downloaded. Extracting links...")
        # Parse the M3U8 file to find the highest quality stream
    highest_quality_url = None
    highest_bandwidth = 0
    with open(m3u8_file_path, 'r') as file:
        for line in file:
            if 'BANDWIDTH' in line:
                bandwidth = int(line.split('BANDWIDTH=')[1].split(',')[0])
                if bandwidth > highest_bandwidth:
                    highest_bandwidth = bandwidth
                    # The next line after the BANDWIDTH line contains the URL of the stream
                    highest_quality_url = next(file).strip()

    if highest_quality_url:
        # Update the m3u8_url to the highest quality stream URL
        m3u8_url = highest_quality_url
        await context.bot.send_message(chat_id=chat_id, text=f"Selected highest quality stream with bandwidth: {highest_bandwidth}")
            # Delete the previously downloaded master M3U8 file
        os.remove(m3u8_file_path)
        
        # Download the M3U8 file for the highest quality stream
        response = requests.get(m3u8_url, headers=headers)
        if response.status_code == 200:
            with open(m3u8_file_path, 'wb') as file:
                file.write(response.content)
            await context.bot.send_message(chat_id=chat_id, text="Seeding the file...")
        else:
            await context.bot.send_message(chat_id=chat_id, text="Failed to download the file for the selected quality stream.")
            return
    else:
        await context.bot.send_message(chat_id=chat_id, text="No multiple quality options found, proceeding with the default stream.")

    def extract_links(m3u8_txt_path, output_dir):
        links_file_path = os.path.join(output_dir, "links.txt")
        with open(m3u8_txt_path, 'r') as m3u8_file, open(links_file_path, 'w') as links_file:
            for line in m3u8_file:
                if line.startswith("http://") or line.startswith("https://"):
                    links_file.write(line)
                if not m3u8_url.startswith(('http://', 'https://')):
                    m3u8_url = 'https://' + m3u8_url
        return links_file_path

    links_file_path = extract_links(m3u8_file_path, output_dir)
    await context.bot.send_message(chat_id=chat_id, text="Links extracted. Downloading segments...")

    # Step 3 & 4: Download the segments
    download_start_time = datetime.now()
    segment_files = await download_segments(links_file_path, output_dir, context, chat_id)  # This should be an async version of your download_segments function
    download_end_time = datetime.now()
    await context.bot.send_message(chat_id=chat_id, text="Segments downloaded. Merging into a single video...")

    # Step 5: Merge all the segments
    ffmpeg_path = 'ffmpeg'
        # Corrected call to merge_segments with the right parameters
    merge_start_time = datetime.now()
    full_output_path = merge_segments(segment_files, output_dir, ffmpeg_path)  # This function now correctly returns the path to the merged video file
    merge_end_time = datetime.now()
    merged_file_size = os.path.getsize(full_output_path)
    merged_file_size_mb = merged_file_size / (1024 * 1024)
    await context.bot.send_message(chat_id=chat_id, text="Video merged successfully. Sending the video...")
    try:
        # Ensure full_output_path contains the path to the video you want to send
        upload_start_time = datetime.now()
        await send_large_video(chat_id, full_output_path)
        upload_end_time = datetime.now()
        
        download_duration = (download_end_time - download_start_time).total_seconds()
        merge_duration = (merge_end_time - merge_start_time).total_seconds()
        upload_duration = (upload_end_time - upload_start_time).total_seconds()

        download_speed = merged_file_size_mb / download_duration if download_duration > 0 else 0
        upload_speed = merged_file_size_mb / upload_duration if upload_duration > 0 else 0

        success_message = f"Video merged and sent successfully.\nDownload Speed: {download_speed:.2f} MB/s\nMerge Duration: {merge_duration:.2f} seconds\nUpload Speed: {upload_speed:.2f} MB/s"
        await context.bot.send_message(chat_id=chat_id, text=success_message)
    except Exception as e:
        logging.error(f"Failed to send video: {e}")
        await context.bot.send_message(chat_id=chat_id, text=success_message)
    # cleanup
    try:
        # The call to send_large_video has been removed from here to avoid duplication
        await cleanup_files(output_dir, segment_files, full_output_path)
    except Exception as e:
        logging.error(f"Failed during cleanup: {e}")

async def download_segment(session, segment_url, output_dir, context, chat_id):
    segment_filename = f"segment_{uuid.uuid4()}.ts"
    segment_file_path = os.path.join(output_dir, segment_filename)
    try:
        async with session.get(segment_url) as response:
            if response.status == 200:
                content = await response.read()
                with open(segment_file_path, 'wb') as segment_file:
                    segment_file.write(content)
                return segment_file_path
            else:
                logging.error(f"Failed to download segment {segment_url} with status: {response.status}")
    except Exception as e:
        logging.error(f"Exception occurred while downloading segment {segment_url}: {e}")

async def download_segments(links_file_path, output_dir, context, chat_id):
    segment_files = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Cookie': 'csrfToken=GjmLm2ef0PXV7E7Om7sQ14dw; browserid=4IDM1uXiu8OR9zyqdPRdOWb9hlpuEdXE_ljyg9BZPC0P-ZVg7JwjWDMpVC0=; lang=en; TSID=ZhvPYdhs492b9mXESdk4fXXoNFEs7aFm; __bid_n=18faea486c0385893e4207; ndut_fmt=B5E57700A6E9911F495F7360C8AA567A79624741DECF6ADB7F5B850FFFB9E9F2; ab_sr=1.0.1_MjUzZDU5NmI1NjQzZDE2ZWMzNDhjNjZhNmIyZDBmMTMzYmI3YjdiY2E3ZTI1MWMyNThjNjQ2YmIxODVjNDQ0YjkxMDFiODRiYTQxYWQ1ZjIyODg2ZjdiMGQ1ZmIzODRhNTZhNDJhNDM5Njg2MjBjMWZiMDk5MjE5MzIxYjc3ZWYyNmYxZGRlNDI1Y2U3MjVkNzNiYTE4NWU3ODM0YWU3MA==; _ga_06ZNKL8C2E=GS1.1.1716621973.1.1.1716622752.17.0.0; _ga=GA1.1.515141628.1716621973; ndus=Y2G_NeyteHuiKaVLHQB80MDytI3rs4MzrNJzPtjV; ab_ymg_result={"data":"a130b873d3834b33ac12249ef2e05128b5847af44e7cbf8fbd012928a6bb27b09503a853fe5eb4da3a25489dd47f7b0910dcbad19ee865691e3bc8adc1de1ab74eb79be1ef5f50412d69d754923d9da2cbc5e0f984e150841b52c9f2dbede174f63f765154be620d6e843675918cf1dc99d4e308f144d25df1c29fcfd1a5e9fc","key_id":"66","sign":"90cb60ab"}'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        with open(links_file_path, 'r') as links_file:
            tasks = [download_segment(session, line.strip(), output_dir, context, chat_id) for line in links_file]
            segment_files = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out None values and exceptions
            segment_files = [segment_file for segment_file in segment_files if segment_file and not isinstance(segment_file, Exception)]
    return segment_files

def extract_links(m3u8_txt_path, output_dir):
    links_file_path = os.path.join(output_dir, "links.txt")
    with open(m3u8_txt_path, 'r') as m3u8_file, open(links_file_path, 'w') as links_file:
        for line in m3u8_file:
            if line.startswith("http://") or line.startswith("https://"):
                links_file.write(line)
    return links_file_path

def merge_segments(segment_files, output_dir, ffmpeg_path):
    # Ensure output_dir is an absolute path
    output_dir = os.path.abspath(output_dir)
    list_file_path = os.path.join(output_dir, "filelist.txt")
    with open(list_file_path, 'w') as list_file:
        for segment_file in segment_files:
            # Write the absolute path of each segment file
            list_file.write(f"file '{os.path.abspath(segment_file)}'\n")

    # Define the output file name here, not outside this function
    output_file_name = "output_video.mp4"
    full_output_path = os.path.join(output_dir, output_file_name)
    ffmpeg_command = [
        ffmpeg_path, '-y', '-loglevel', 'error',
        '-f', 'concat', '-safe', '0', '-i', list_file_path,
        '-c', 'copy', full_output_path
    ]

    subprocess.run(ffmpeg_command, check=True)
    return full_output_path

async def cleanup_files(output_dir, segment_files, output_file):
    for segment_file in segment_files:
        os.remove(os.path.join(output_dir, segment_file))
    os.remove(output_file)  # Delete the final merged file
    os.remove(os.path.join(output_dir, 'filelist.txt'))  # Delete the filelist

def main():
    pyro_client.start()
    application = Application.builder().token(bot_token).build()

    # Command handler for the /convert command
    convert_handler = CommandHandler('convert', convert_and_send_video)
    application.add_handler(convert_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()