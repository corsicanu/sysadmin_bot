# sysadmin_bot/cron.py

import schedule
import time
import threading
import logging, psutil, platform
import subprocess
from telegram import Update, ParseMode, Bot
import datetime
from .config_loader import get_telegram_bot_token, get_owner_id, get_machine_password

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# helpers
def get_current_time():
    return datetime.datetime.now().strftime("%H:%M:%S")

def get_uptime():
    uptime_seconds = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days} days, {hours} hours, {minutes} minutes"

def get_ip():
    res = requests.get("http://ipinfo.io/ip")
    return res;

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
        # Command to update apt
        command = "echo {} | sudo -S apt update".format(get_machine_password())
        
        # Run the command
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        
        # Split the output into lines
        output_lines = result.stdout.splitlines()
        
        # Get the last line
        if output_lines:
            last_line = output_lines[-1]
        else:
            last_line = "No output returned"
        
        # Print the last line
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

# actual cron
def daily():
    uptime = get_uptime()
    current_time = get_current_time()
    free_space_gb = get_free_space('/home')
    
    # Get memory and swap usage
    ram_usage, ram_total = get_memory_info()
    swap_usage, total_swap = get_swap_info()
    temp=get_temp()
    
    # Compose the response message in HTML format
    response = (
        f"<b>System status:</b> OK\n"
        f"<b>Hostname:</b> {platform.node()}\n"
        f"<b>Temperature:</b> {temp}\n"
        f"<b>Disk Free Space:</b> {free_space_gb:.2f} GB\n"
        f"<b>Memory:</b> {ram_usage:.2f} MB / {ram_total:.2f} MB\n"
        f"<b>Swap:</b> {swap_usage:.2f} MB / {total_swap:.2f} MB\n"
        f"<b>Uptime:</b> {uptime}\n"
        f"<b>Current Time:</b> {current_time}\n"
        f"<b>{check_updates()}</b>\n"
    )

    # Send the response to the user
    send_message(response)

# Function to schedule jobs
def schedule_jobs():
    # Schedule a job to run every day at 10:30 AM
    # schedule.every().day.at("11:08").do(neofetch)

    # Schedule a job to run every Monday at 8:00 PM
    # schedule.every().monday.at("20:00").do(job)

    # Example: Schedule a job to run every 30 minutes
    schedule.every(5).seconds.do(daily)

    # Start the scheduler thread
    while True:
        schedule.run_pending()
        time.sleep(1)

# Function to start the scheduler in a separate thread
def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_jobs)
    scheduler_thread.start()

# Call start_scheduler when this file is executed directly
if __name__ == "__main__":
    logger.info("Starting cron...")
    start_scheduler()
    logger.info("Cron succesfully started")
