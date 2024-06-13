# sysadmin_bot/modules/tools.py

import os
import psutil
import html

import requests
import subprocess
import glob, time, datetime, speedtest
from ..config_loader import get_owner_id
from telegram import Update, ParseMode
from telegram.ext import run_async, CommandHandler

OWNER_ID = get_owner_id()

def is_owner(update: Update) -> bool:
    return update.message.from_user.id == int(OWNER_ID)

def status(update, context):
    if not is_owner(update):
        update.message.reply_text('GTFO haha')
        logger.info(f'Ignoring command from non-owner user {update.effective_user.id}')
        return
        
    # Get free space on the drive that holds DOWNLOAD_DIR in GB
    free_space_gb = get_free_space('/home')
    
    # Get memory and swap usage
    ram_usage, ram_total = get_memory_info()
    swap_usage, total_swap = get_swap_info()
    
    # Get system uptime and current time
    uptime = get_uptime()
    current_time = get_current_time()
    
    # Compose the response message in HTML format
    response = (
        f"<b>System Information</b>\n"
        f"<b>Disk Free Space:</b> {free_space_gb:.2f} GB\n"
        f"<b>Memory:</b> {ram_usage:.2f} MB / {ram_total:.2f} MB\n"
        f"<b>Swap:</b> {swap_usage:.2f} MB / {total_swap:.2f} MB\n"
        f"<b>Uptime:</b> {uptime}\n"
        f"<b>Current Time:</b> {current_time}\n"
    )

    # Send the response to the user
    update.message.reply_text(response, parse_mode=ParseMode.HTML)

def get_directory_size(path):
    total_size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(path, '**', '*.*'), recursive=True))
    return total_size / (1024 ** 3)

def get_free_space(path):
    partition = psutil.disk_usage(path)
    return partition.free / (1024 ** 3)

def get_memory_info():
    ram = psutil.virtual_memory()
    return ram.used / (1024 ** 2), ram.total / (1024 ** 2)  # Convert to MB

def get_swap_info():
    swap = psutil.swap_memory()
    return swap.used / (1024 ** 2), swap.total / (1024 ** 2)  # Convert to MB

def get_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days} days, {hours} hours, {minutes} minutes"

def get_current_time():
    return datetime.datetime.now().strftime("%H:%M:%S")
    
def neofetch(update, context):
    # Run the neofetch command and capture its output
    neofetch_output = subprocess.check_output(["neofetch", "--stdout"], text=True)

    # Send the neofetch output to the user
    update.message.reply_text(neofetch_output, parse_mode=ParseMode.HTML)

def run_shell_command(update, context):
    if not is_owner(update):
        update.message.reply_text('GTFO haha')
        logger.info(f'Ignoring command from non-owner user {update.effective_user.id}')
        return

    args = context.args
    if not args:
        update.message.reply_text("Usage: /sh <command>")
        return

    # Join the command arguments into a single string
    command = " ".join(args)

    try:
        # Execute the shell command
        result = subprocess.check_output(command, shell=True, text=True)
        update.message.reply_text(f"Command Output:\n\n`{result}`", disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)
    except subprocess.CalledProcessError as e:
        update.message.reply_text(f"Command failed with error:\n\n`{e}`", parse_mode=ParseMode.MARKDOWN)

def get_bot_ip(update, context):
    if not is_owner(update):
        update.message.reply_text('GTFO haha')
        logger.info(f'Ignoring command from non-owner user {update.effective_user.id}')
        return
    bot = context.bot
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)

def speedtest_command(update, context):
    if not is_owner(update):
        update.message.reply_text('GTFO haha')
        logger.info(f'Ignoring command from non-owner user {update.effective_user.id}')
        return
    # Send a "Running speed test, please wait..." message with web preview disabled
    message = update.message.reply_text("Running speed test, please wait...", disable_web_page_preview=True)

    try:
        # Create a SpeedtestClient
        st = speedtest.Speedtest()

        # Get the closest server based on ping
        st.get_best_server()

        # Perform the speed test
        st.download()
        st.upload()

        # Get the results
        download_speed = st.results.download / 1_000_000  # Convert to Mbps
        upload_speed = st.results.upload / 1_000_000  # Convert to Mbps
        ping = st.results.ping  # in ms
        jitter = st.results.ping
        isp = st.results.client["isp"]
        server_name = st.results.server["name"]

        # Get the current date and time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate a clickable link to the Speedtest image
        speedtest_url = st.results.share()

        # Compose the response message
        response = (
            f"*Speedtest Results*\n"
            f"Date and Time: {current_time}\n"
            f"Download Speed: {download_speed:.2f} Mbps\n"
            f"Upload Speed: {upload_speed:.2f} Mbps\n"
            f"Test Server: {server_name}\n"
            f"Ping: {ping} ms\n"
            f"ISP: {isp}\n"
            f"{speedtest_url}"
        )

        # Edit the original message with the speedtest results and disable web preview
        message.edit_text(response, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception as e:
        # Handle errors and report them
        message.edit_text(f"Speedtest failed with error:\n\n`{e}`", parse_mode=ParseMode.MARKDOWN)

SHELLCMD_HANDLER = CommandHandler("sh", run_shell_command, pass_args=True, run_async=True)
STATUS_HANDLER = CommandHandler("status", status, run_async=True)
NEOFETCH_HANDLER = CommandHandler("neofetch", neofetch, run_async=True)
SPEEDTEST_HANDLER = CommandHandler("speedtest", speedtest_command, run_async=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, run_async=True)

def register_handlers(dp):
    dp.add_handler(STATUS_HANDLER)
    dp.add_handler(NEOFETCH_HANDLER)
    dp.add_handler(SHELLCMD_HANDLER)
    dp.add_handler(IP_HANDLER)
    dp.add_handler(SPEEDTEST_HANDLER)
