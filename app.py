import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

# Configure file handlers
os.makedirs("logs", exist_ok=True)
activity_handler = logging.FileHandler("logs/bot_activity.log")
activity_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
activity_logger.addHandler(activity_handler)
activity_logger.propagate = False

error_handler = logging.FileHandler("logs/bot_errors.log")
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_logger.addHandler(error_handler)
error_logger.propagate = False

# Initialize Flask app
app = Flask(__name__)

# Import components (after Flask app is created)
from modules.vpn_manager import VPNManager
from modules.captcha_solver import CaptchaSolver
from modules.browser_manager import BrowserManager
from modules.traffic_bot import TrafficBot
from modules.traffic_scheduler import TrafficScheduler

# Initialize components
vpn_manager = VPNManager()
captcha_solver = CaptchaSolver(os.getenv("ANTICAPTCHA_KEY", ""))
browser_manager = BrowserManager(vpn_manager, captcha_solver)
traffic_scheduler = TrafficScheduler()
traffic_bot = TrafficBot(vpn_manager, browser_manager, traffic_scheduler)

# Import API routes
from api.bot_api import *
from api.vpn_api import *
from api.logs_api import *

@app.route('/')
def index():
    """Render the main web interface."""
    return render_template('index.html')

if __name__ == "__main__":
    # Load proxies if the file exists
    if os.path.exists("proxies.txt"):
        vpn_manager.load_proxies("proxies.txt")
    
    # Load VPN regions
    vpn_manager.load_vpn_regions('pia')
    vpn_manager.load_vpn_regions('nordvpn')
    vpn_manager.load_vpn_regions('expressvpn')
    
    # Start the web application
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 5000))
    app.run(host=host, port=port)