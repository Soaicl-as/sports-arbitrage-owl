
import time
import logging
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from config import BET365_URL, BETMGM_URL, STAKE_URL, HEADLESS, TIMEOUT, REGION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BettingScraper:
    def __init__(self):
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Selenium WebDriver"""
        try:
            chrome_options = Options()
            if HEADLESS:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Set up user agent to avoid detection
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            # Disable automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(TIMEOUT)
            
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            raise
    
    def close_driver(self):
        """Close the WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def scrape_bet365(self):
        """Scrape odds from Bet365"""
        try:
            logger.info("Scraping Bet365...")
            self.driver.get(BET365_URL)
            
            # Wait for page to load
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.event-list"))
            )
            
            # Add random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))
            
            # Extract sports categories
            sports = self.driver.find_elements(By.CSS_SELECTOR, "div.sport-category")
            
            all_events = []
            
            for sport in sports:
                sport_name = sport.find_element(By.CSS_SELECTOR, "div.sport-name").text
                
                # Extract events
                events = sport.find_elements(By.CSS_SELECTOR, "div.event-row")
                
                for event in events:
                    try:
                        event_name = event.find_element(By.CSS_SELECTOR, "div.event-name").text
                        event_time = event.find_element(By.CSS_SELECTOR, "div.event-time").text
                        
                        # Extract markets
                        markets = event.find_elements(By.CSS_SELECTOR, "div.market")
                        
                        for market in markets:
                            market_name = market.find_element(By.CSS_SELECTOR, "div.market-name").text
                            selections = market.find_elements(By.CSS_SELECTOR, "div.selection")
                            
                            for selection in selections:
                                selection_name = selection.find_element(By.CSS_SELECTOR, "div.selection-name").text
                                odds = selection.find_element(By.CSS_SELECTOR, "div.odds").text
                                
                                all_events.append({
                                    'bookmaker': 'Bet365',
                                    'sport': sport_name,
                                    'event': event_name,
                                    'datetime': event_time,
                                    'market': market_name,
                                    'selection': selection_name,
                                    'odds': self.convert_odds_to_decimal(odds)
                                })
                    except NoSuchElementException:
                        continue
            
            logger.info(f"Scraped {len(all_events)} odds from Bet365")
            return pd.DataFrame(all_events)
        
        except TimeoutException:
            logger.error("Timeout while loading Bet365")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error scraping Bet365: {str(e)}")
            return pd.DataFrame()
    
    def scrape_betmgm(self):
        """Scrape odds from BetMGM"""
        try:
            logger.info("Scraping BetMGM...")
            self.driver.get(BETMGM_URL)
            
            # Wait for page to load
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.sports-list"))
            )
            
            # Add random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))
            
            # Extract sports categories
            sports = self.driver.find_elements(By.CSS_SELECTOR, "div.sport-category")
            
            all_events = []
            
            for sport in sports:
                sport_name = sport.find_element(By.CSS_SELECTOR, "div.sport-name").text
                
                # Extract events
                events = sport.find_elements(By.CSS_SELECTOR, "div.event-row")
                
                for event in events:
                    try:
                        event_name = event.find_element(By.CSS_SELECTOR, "div.event-name").text
                        event_time = event.find_element(By.CSS_SELECTOR, "div.event-time").text
                        
                        # Extract markets
                        markets = event.find_elements(By.CSS_SELECTOR, "div.market")
                        
                        for market in markets:
                            market_name = market.find_element(By.CSS_SELECTOR, "div.market-name").text
                            selections = market.find_elements(By.CSS_SELECTOR, "div.selection")
                            
                            for selection in selections:
                                selection_name = selection.find_element(By.CSS_SELECTOR, "div.selection-name").text
                                odds = selection.find_element(By.CSS_SELECTOR, "div.odds").text
                                
                                all_events.append({
                                    'bookmaker': 'BetMGM',
                                    'sport': sport_name,
                                    'event': event_name,
                                    'datetime': event_time,
                                    'market': market_name,
                                    'selection': selection_name,
                                    'odds': self.convert_odds_to_decimal(odds)
                                })
                    except NoSuchElementException:
                        continue
            
            logger.info(f"Scraped {len(all_events)} odds from BetMGM")
            return pd.DataFrame(all_events)
        
        except TimeoutException:
            logger.error("Timeout while loading BetMGM")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error scraping BetMGM: {str(e)}")
            return pd.DataFrame()
    
    def scrape_stake(self):
        """Scrape odds from Stake"""
        try:
            logger.info("Scraping Stake...")
            self.driver.get(STAKE_URL)
            
            # Wait for page to load
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.sports-list"))
            )
            
            # Add random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))
            
            # Extract sports categories
            sports = self.driver.find_elements(By.CSS_SELECTOR, "div.sport-category")
            
            all_events = []
            
            for sport in sports:
                sport_name = sport.find_element(By.CSS_SELECTOR, "div.sport-name").text
                
                # Extract events
                events = sport.find_elements(By.CSS_SELECTOR, "div.event-row")
                
                for event in events:
                    try:
                        event_name = event.find_element(By.CSS_SELECTOR, "div.event-name").text
                        event_time = event.find_element(By.CSS_SELECTOR, "div.event-time").text
                        
                        # Extract markets
                        markets = event.find_elements(By.CSS_SELECTOR, "div.market")
                        
                        for market in markets:
                            market_name = market.find_element(By.CSS_SELECTOR, "div.market-name").text
                            selections = market.find_elements(By.CSS_SELECTOR, "div.selection")
                            
                            for selection in selections:
                                selection_name = selection.find_element(By.CSS_SELECTOR, "div.selection-name").text
                                odds = selection.find_element(By.CSS_SELECTOR, "div.odds").text
                                
                                all_events.append({
                                    'bookmaker': 'Stake',
                                    'sport': sport_name,
                                    'event': event_name,
                                    'datetime': event_time,
                                    'market': market_name,
                                    'selection': selection_name,
                                    'odds': self.convert_odds_to_decimal(odds)
                                })
                    except NoSuchElementException:
                        continue
            
            logger.info(f"Scraped {len(all_events)} odds from Stake")
            return pd.DataFrame(all_events)
        
        except TimeoutException:
            logger.error("Timeout while loading Stake")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error scraping Stake: {str(e)}")
            return pd.DataFrame()
    
    def scrape_all_sites(self):
        """Scrape all betting sites and combine the data"""
        try:
            bet365_df = self.scrape_bet365()
            betmgm_df = self.scrape_betmgm()
            stake_df = self.scrape_stake()
            
            # Combine all dataframes
            combined_df = pd.concat([bet365_df, betmgm_df, stake_df])
            
            logger.info(f"Total scraped odds: {len(combined_df)}")
            return combined_df
        except Exception as e:
            logger.error(f"Error scraping sites: {str(e)}")
            return pd.DataFrame()
    
    def convert_odds_to_decimal(self, odds_str):
        """Convert different odds formats to decimal"""
        try:
            # Check if odds are already in decimal format
            if '.' in odds_str:
                return float(odds_str)
            
            # Convert American odds to decimal
            if '+' in odds_str:
                american = int(odds_str.replace('+', ''))
                return round(american / 100 + 1, 2)
            elif '-' in odds_str:
                american = int(odds_str.replace('-', ''))
                return round(100 / american + 1, 2)
            
            # Convert fractional odds (e.g., "5/1") to decimal
            if '/' in odds_str:
                numerator, denominator = map(int, odds_str.split('/'))
                return round(numerator / denominator + 1, 2)
            
            # Default case
            return float(odds_str)
        except Exception as e:
            logger.warning(f"Could not convert odds '{odds_str}': {str(e)}")
            return 0.0
