from agency_swarm.tools import BaseTool
from pydantic import Field
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import json
import os
import traceback
from datetime import datetime, timedelta
from utils.logging_utils import logging_manager
from dotenv import load_dotenv
from scraper_agent.tools.UyumsoftLogin import UyumsoftLogin

load_dotenv()  # Load environment variables

# Global constants
CHROME_DRIVER_PATH = "scraper_agent/drivers/chromedriver"
BASE_URL = "https://edonusum.uyum.com.tr"
LOGIN_ENDPOINT = f"{BASE_URL}/login"
INVOICES_ENDPOINT = f"{BASE_URL}/Gelen"
MAX_RETRIES = 3
username = os.getenv("UYUMSOFT_USERNAME")
password = os.getenv("UYUMSOFT_PASSWORD")
WAIT_TIMEOUT = 10  # seconds
BATCH_SIZE = 10  # Number of invoices to process in one batch


class InvoiceDataScraper(BaseTool):
    """
    Tool for scraping invoice data from the Uyumsoft Portal's Incoming Invoices section.
    Extracts data from the dynamic table in a top-to-bottom manner with pagination support.
    Uses shared_state to check for already processed invoice IDs.
    """
    class ToolConfig:
        one_call_at_a_time = True
        strict = True

    headless: bool = Field(
        ..., 
        description="Whether to run browser in headless mode"
    )
    
    max_pages: int = Field(
        ...,
        description="Maximum number of pages to scrape"
    )

    def run(self):
        """
        Scrapes invoice data from the portal using Selenium with top-to-bottom approach and pagination.
        Uses shared_state to check for already processed invoice IDs.
        """
        # Get logger from centralized logging manager
        logger = logging_manager.get_logger('invoice_scraper')
        logger.info("=== Starting invoice scraping process ===")
        
        driver = None
        try:
            # Access processed invoice IDs from shared state
            processed_ids = []
            if hasattr(self.__class__, '_shared_state') and self.__class__._shared_state:
                processed_ids = self.__class__._shared_state.get("processed_invoice_ids", [])
                logger.info(f"Found {len(processed_ids)} previously processed invoice IDs in shared state")
            else:
                logger.info("No processed invoice IDs found in shared state")
            
            # Use UyumsoftLogin tool to get a logged-in driver
            logger.info("Using UyumsoftLogin tool to authenticate")
            login_tool = UyumsoftLogin(
                username=username,
                password=password,
                headless=self.headless
            )
            login_result = login_tool.run()
            
            if login_result["status"] != "success":
                logger.error(f"Login failed: {login_result['message']}")
                return {
                    "status": "error",
                    "message": f"Login failed: {login_result['message']}",
                    "data": []
                }
            
            # Get the driver from the login tool
            driver = login_result["driver"]
            logger.info("Successfully obtained authenticated driver from UyumsoftLogin")
            
            try:
                # Navigate to the Incoming Invoices section
                logger.info("Navigating to Incoming Invoices section")
                driver.get("https://edonusum.uyum.com.tr/Gelen")
                
                # Wait for page to load with multiple strategies
                logger.info("Waiting for invoice page to load")
                try:
                    # First try waiting for the specific table ID
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.ID, "inboxList"))
                    )
                    logger.info("Found table with ID 'inboxList'")
                except TimeoutException:
                    logger.warning("Could not find table with ID 'inboxList', trying alternative approaches")
                    
                    # Try waiting for the dataTable class
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "dataTable"))
                        )
                        logger.info("Found a table with class 'dataTable'")
                    except TimeoutException:
                        logger.error("Could not find any table on the page")
                        
                # Add a sleep to ensure JavaScript has fully loaded the table
                logger.info("Waiting for JavaScript to fully load the table")
                time.sleep(5)
                
                # Find the invoice table
                logger.info("Finding invoice table")
                try:
                    invoice_table = driver.find_element(By.ID, "inboxList")
                    logger.info("Found invoice table by ID")
                except NoSuchElementException:
                    logger.warning("Could not find table by ID, trying by class")
                    try:
                        invoice_table = driver.find_element(By.CLASS_NAME, "dataTable")
                        logger.info("Found invoice table by class")
                    except NoSuchElementException:
                        logger.warning("Could not find table by class, trying to find any table")
                        tables = driver.find_elements(By.TAG_NAME, "table")
                        if tables:
                            invoice_table = tables[0]
                            logger.info(f"Found {len(tables)} tables, using the first one")
                        else:
                            raise Exception("No tables found on the page")
                
                # Process the table rows
                all_invoice_data = []
                new_invoices = []
                new_invoice_ids = []
                current_page = 1
                
                while current_page <= self.max_pages:
                    logger.info(f"Processing page {current_page}")
                    
                    # Find all rows in the table
                    try:
                        # Wait for rows to be present
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#inboxList tbody tr"))
                        )
                        rows = invoice_table.find_elements(By.TAG_NAME, "tr")
                        logger.info(f"Found {len(rows)} rows in the table")
                        
                        # Skip header row
                        for i, row in enumerate(rows[1:]):  # Skip header row
                            try:
                                # Check if this is a valid invoice row (has cells)
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) < 5:  # Not enough cells for a valid row
                                    continue
                                
                                # Extract invoice ID from the row
                                try:
                                    invoice_id_input = row.find_element(By.CLASS_NAME, "invoiceId")
                                    invoice_id = invoice_id_input.get_attribute("value")
                                    
                                    # Skip if already processed - use shared_state
                                    if invoice_id in processed_ids:
                                        logger.debug(f"Skipping already processed invoice: {invoice_id}")
                                        continue
                                    
                                    # Track new invoice ID for reporting back to Manager Agent
                                    new_invoice_ids.append(invoice_id)
                                except NoSuchElementException:
                                    logger.warning(f"Could not find invoice ID in row {i+1}")
                                    continue
                                
                                # Initialize invoice data dictionary
                                invoice_data = {
                                    "Invoice ID": invoice_id,
                                    "Scrape Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                # Extract invoice number and ETTN
                                try:
                                    # Invoice number is in the second cell
                                    number_cell = cells[1]
                                    number_spans = number_cell.find_elements(By.TAG_NAME, "span")
                                    
                                    if len(number_spans) >= 1:
                                        invoice_data["Invoice No"] = number_spans[0].text.strip()
                                    
                                    if len(number_spans) >= 2:
                                        invoice_data["ETTN"] = number_spans[1].text.strip()
                                except:
                                    logger.warning(f"Could not extract Invoice No from row {i+1}")
                                
                                # Extract invoice date
                                try:
                                    # Invoice date is in the third cell
                                    date_cell = cells[2]
                                    invoice_data["Invoice Date"] = date_cell.text.strip()
                                except:
                                    logger.warning(f"Could not extract Invoice Date from row {i+1}")
                                
                                # Extract creation date
                                try:
                                    # Creation date is in the fourth cell
                                    creation_cell = cells[3]
                                    invoice_data["Creation Date"] = creation_cell.text.strip()
                                except:
                                    logger.warning(f"Could not extract Creation Date from row {i+1}")
                                
                                # Extract supplier info
                                try:
                                    # Supplier info is in the fifth cell
                                    supplier_cell = cells[4]
                                    supplier_spans = supplier_cell.find_elements(By.TAG_NAME, "span")
                                    
                                    if len(supplier_spans) >= 1:
                                        invoice_data["Supplier VKN"] = supplier_spans[0].text.strip()
                                    
                                    if len(supplier_spans) >= 2:
                                        invoice_data["Supplier Name"] = supplier_spans[1].text.strip()
                                    
                                    if len(supplier_spans) >= 3:
                                        invoice_data["Supplier PK"] = supplier_spans[2].text.strip()
                                except:
                                    logger.warning(f"Could not extract Supplier info from row {i+1}")
                                
                                # Extract amount info
                                try:
                                    # Amount info is in the sixth cell
                                    amount_cell = cells[5]
                                    amount_spans = amount_cell.find_elements(By.TAG_NAME, "span")
                                    
                                    if len(amount_spans) >= 1:
                                        amount_text = amount_spans[0].text.strip()
                                        # Remove currency and convert to float
                                        amount_text = amount_text.replace("TL", "").replace(".", "").replace(",", ".").strip()
                                        invoice_data["Total Amount"] = float(amount_text)
                                    
                                    if len(amount_spans) >= 2:
                                        tax_excl_text = amount_spans[1].text.strip()
                                        # Extract the number part
                                        tax_excl_text = tax_excl_text.split(":")[1].replace("TL", "").replace(".", "").replace(",", ".").strip()
                                        invoice_data["Tax Exclusive Amount"] = float(tax_excl_text)
                                except:
                                    logger.warning(f"Could not extract Amount info from row {i+1}")
                                
                                # Extract tax info
                                try:
                                    # Tax info is in the seventh cell
                                    tax_cell = cells[6]
                                    tax_spans = tax_cell.find_elements(By.TAG_NAME, "span")
                                    
                                    # Last span should be the total
                                    if tax_spans:
                                        total_tax_span = tax_spans[-1]
                                        total_tax_text = total_tax_span.text.strip()
                                        # Extract the number part
                                        if "=" in total_tax_text:
                                            total_tax_text = total_tax_text.split("=")[1].strip()
                                        invoice_data["Tax Amount"] = float(total_tax_text.replace(".", "").replace(",", "."))
                                    
                                    # Calculate tax rate if possible
                                    if "Tax Exclusive Amount" in invoice_data and invoice_data["Tax Exclusive Amount"] > 0:
                                        invoice_data["Tax Rate"] = invoice_data["Tax Amount"] / invoice_data["Tax Exclusive Amount"]
                                except:
                                    logger.warning(f"Could not extract Tax info from row {i+1}")
                                
                                # Extract invoice type and direction
                                try:
                                    # Invoice type is in the eighth cell
                                    type_cell = cells[7]
                                    type_spans = type_cell.find_elements(By.TAG_NAME, "span")
                                    
                                    if len(type_spans) >= 1:
                                        invoice_data["Invoice Type"] = type_spans[0].text.strip()
                                    
                                    if len(type_spans) >= 2:
                                        invoice_data["Invoice Direction"] = type_spans[1].text.strip()
                                except:
                                    logger.warning(f"Could not extract Type info from row {i+1}")
                                
                                # Extract approval status
                                try:
                                    # Approval status is in the ninth cell
                                    status_cell = cells[8]
                                    status_spans = status_cell.find_elements(By.TAG_NAME, "span")
                                    
                                    if status_spans:
                                        invoice_data["Approval Status"] = status_spans[0].text.strip()
                                except:
                                    logger.warning(f"Could not extract Status info from row {i+1}")
                                
                                # Add to our list of invoices
                                all_invoice_data.append(invoice_data)
                                new_invoices.append(invoice_data)
                                logger.info(f"Processed invoice: {invoice_data.get('Invoice No', 'Unknown')} ({invoice_data.get('Supplier Name', 'Unknown')})")
                                
                            except Exception as row_error:
                                logger.error(f"Error processing row {i+1} on page {current_page}: {str(row_error)}")
                                logger.error(traceback.format_exc())
                                continue
                    
                    except Exception as table_error:
                        logger.error(f"Error processing table on page {current_page}: {str(table_error)}")
                        logger.error(traceback.format_exc())
                        break
                    
                    # Check if there are more pages
                    try:
                        # Find pagination
                        pagination = driver.find_element(By.CLASS_NAME, "pagination")
                        next_button = pagination.find_element(By.XPATH, ".//li[contains(@class, 'next')]/a")
                        
                        # Check if next button is disabled
                        if "disabled" in next_button.get_attribute("class"):
                            logger.info("Reached last page")
                            break
                        
                        # Click next page
                        next_button.click()
                        logger.info(f"Navigating to page {current_page + 1}")
                        
                        # Wait for table to reload
                        time.sleep(3)
                        
                        # Increment page counter
                        current_page += 1
                        
                    except Exception as page_error:
                        logger.warning(f"Error navigating to next page: {str(page_error)}")
                        break
                
                # Close the browser
                driver.quit()
                logger.info("Browser closed")
                
                # Log results
                logger.info(f"Scraped {len(all_invoice_data)} total invoices ({len(new_invoices)} new)")
                logger.info("=== Invoice scraping process completed ===")
                
                # After scraping all invoices, update shared state with the newly found invoices
                if hasattr(self.__class__, '_shared_state') and self.__class__._shared_state:
                    self.__class__._shared_state.set("new_invoice_data", new_invoices)
                    self.__class__._shared_state.set("new_invoice_ids", new_invoice_ids)
                    logger.info(f"Added {len(new_invoices)} new invoices to shared state")
                    logger.info(f"Added {len(new_invoice_ids)} new invoice IDs to shared state")
                
                return {
                    "status": "success",
                    "message": f"Successfully scraped {len(new_invoices)} new invoices",
                    "data": new_invoices
                }
                
            except Exception as e:
                logger.error(f"Error during scraping: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Ensure browser is closed in case of error
                if driver:
                    try:
                        driver.quit()
                        logger.info("Browser closed after error")
                    except Exception as close_error:
                        logger.error(f"Error closing browser: {str(close_error)}")
                
                logger.info("=== Scraping process failed ===")
                return {
                    "status": "error",
                    "message": f"Scraping error: {str(e)}",
                    "data": []
                }
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Ensure browser is closed in case of error
            if driver:
                try:
                    driver.quit()
                    logger.info("Browser closed after error")
                except Exception as close_error:
                    logger.error(f"Error closing browser: {str(close_error)}")
            
            logger.info("=== Scraping process failed ===")
            return {
                "status": "error",
                "message": f"Scraping error: {str(e)}",
                "data": []
            }
        finally:
            # Log end of scraping process
            logging_manager.log_end_process(logger, "invoice scraping process")

if __name__ == "__main__":
    # Test the tool
    tool = InvoiceDataScraper(
        username=os.getenv("UYUMSOFT_USERNAME"),
        password=os.getenv("UYUMSOFT_PASSWORD"),
        headless=False,
        max_pages=3  # Limit to 3 pages for testing
    )
    result = tool.run()
    print(json.dumps(result, indent=2)) 