
import logging
import time
import os
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import BettingScraper
from arbitrage_finder import ArbitrageFinder
from email_service import send_test_email, send_opportunity_email, send_error_email
from config import SCRAPE_INTERVAL, HEARTBEAT_INTERVAL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Flags to track initial run and errors
first_run = True
consecutive_errors = 0

def run_arbitrage_check():
    """Main function to check for arbitrage opportunities"""
    global first_run, consecutive_errors
    
    logger.info("Starting arbitrage check...")
    
    try:
        # Initialize scraper and finder
        scraper = BettingScraper()
        finder = ArbitrageFinder()
        
        # First run test email
        if first_run:
            logger.info("First run - sending test email")
            send_test_email()
            first_run = False
        
        # Scrape data
        odds_data = scraper.scrape_all_sites()
        
        # Find opportunities
        opportunities = finder.find_arbitrage_opportunities(odds_data)
        
        # Send emails for each opportunity
        for opportunity in opportunities:
            logger.info(f"Found opportunity: {opportunity['event']} - {opportunity['profit_percentage']:.2f}%")
            send_opportunity_email(opportunity)
        
        # Reset error counter on successful run
        consecutive_errors = 0
        
        # Close the web driver
        scraper.close_driver()
        
        logger.info("Arbitrage check completed successfully")
        return True
    
    except Exception as e:
        consecutive_errors += 1
        error_message = f"Error in arbitrage check: {str(e)}"
        logger.error(error_message)
        
        # Send error email after 3 consecutive errors
        if consecutive_errors >= 3:
            send_error_email(error_message)
            consecutive_errors = 0
        
        return False
    finally:
        # Ensure the driver is closed even if there's an error
        if 'scraper' in locals() and hasattr(scraper, 'close_driver'):
            scraper.close_driver()

def heartbeat():
    """Simple heartbeat function to keep the service active"""
    logger.info("Heartbeat ping")
    return True

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_arbitrage_check, 'interval', seconds=SCRAPE_INTERVAL, id='arbitrage_check')
scheduler.add_job(heartbeat, 'interval', seconds=HEARTBEAT_INTERVAL, id='heartbeat')

# Flask routes
@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "message": "Sports Arbitrage Bot is running",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "uptime": time.time() - start_time
    })

@app.route('/run-now')
def run_now():
    """Endpoint to manually trigger an arbitrage check"""
    result = run_arbitrage_check()
    return jsonify({
        "status": "success" if result else "error",
        "message": "Arbitrage check completed" if result else "Arbitrage check failed"
    })

if __name__ == '__main__':
    # Start time tracking
    start_time = time.time()
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    # Get port for Render compatibility
    port = int(os.environ.get("PORT", 8080))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port)
