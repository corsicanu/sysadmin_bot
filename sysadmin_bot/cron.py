# sysadmin_bot/cron.py

import schedule
import time
import threading
import logging, psutil, platform, requests
import subprocess
from telegram import Update, ParseMode, Bot
import datetime
from .config_loader import get_telegram_bot_token, get_owner_id, get_machine_password

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_current_time():
    return datetime.datetime.now().strftime("%H:%M:%S")

def get_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days} days, {hours} hours, {minutes} minutes"

def get_ip():
    try:
        res = requests.get("http://ipinfo.io/ip")
        return res.text.strip()
    except Exception as e:
        logger.error(f"Failed to get IP address: {str(e)}")
        return "N/A"

def get_free_space(path):
    partition = psutil.disk_usage(path)
    return partition.free / (1024 ** 3)

def get_memory_info():
    ram = psutil.virtual_memory()
    return ram.used / (1024 ** 2), ram.total / (1024 ** 2)  # Convert to MB

def get_swap_info():
    swap = psutil.swap_memory()
    return swap.used / (1024 ** 2), swap.total / (1024 ** 2)  # Convert to MB

def check_updates():
    try:
        command = "echo {} | sudo -S apt update".format(get_machine_password())
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        
        output_lines = result.stdout.splitlines()
        
        if output_lines:
            last_line = output_lines[-1]
        else:
            last_line = "No output returned"
        
        return last_line
    
    except subprocess.CalledProcessError as e:
        return 'No updates available'

def get_temp():
    try:
        temperature = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        temperature = "N/A"
    return temperature

def neofetch():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    logger.info(f"Running neofetch at {current_time}")
    neofetch_output = subprocess.check_output(["neofetch", "--stdout"], text=True)
    return neofetch_output

def send_message(message):
    OWNER_ID = get_owner_id()
    token = get_telegram_bot_token()
    bot = Bot(token=token)
    try:
        bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Failed to send message to user ID {OWNER_ID}: {str(e)}")

def daily():
    uptime = get_uptime()
    current_time = get_current_time()
    free_space_gb = get_free_space('/home')
    ip = get_ip()
    send_message(ip)
    
    ram_usage, ram_total = get_memory_info()
    swap_usage, total_swap = get_swap_info()
    temp=get_temp()
    
    response = (
        f"<b>System status:</b> OK\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Hostname:</b> {platform.node()}\n"
        f"<b>Temperature:</b> {temp}\n"
        f"<b>Disk Free Space:</b> {free_space_gb:.2f} GB\n"
        f"<b>Memory:</b> {ram_usage:.2f} MB / {ram_total:.2f} MB\n"
        f"<b>Swap:</b> {swap_usage:.2f} MB / {total_swap:.2f} MB\n"
        f"<b>Uptime:</b> {uptime}\n"
        f"<b>Current Time:</b> {current_time}\n"
        f"<b>{check_updates()}</b>\n"
    )

    send_message(response)

def schedule_jobs():
    # schedule.every().day.at("06:00").do()
    # schedule.every().monday.at("20:00").do()
    schedule.every(5).seconds.do(daily)

    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_jobs)
    scheduler_thread.start()

if __name__ == "__main__":
    logger.info("Starting cron...")
    start_scheduler()
    logger.info("Cron succesfully started")
