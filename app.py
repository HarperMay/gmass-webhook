import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
api_keys = os.getenv("API_KEYS").split(",")  # Convert CSV string to list
campaign_ids = os.getenv("CAMPAIGN_IDS").split(",")
webhook_url = os.getenv("WEBHOOK_URL")

# Configure logging
logging.basicConfig(
    filename="gmass_webhook.log",  
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Events to track
events = ["Opens", "Clicks", "Replies", "Bounces", "Unsubscribes", "Sends", "Blocks"]

# Using the first API key for authentication
api_key = api_keys[0]

logging.info("Starting GMass Webhook Setup")
logging.info(f"Using API Key: {api_key[:5]}**** (hidden for security)")
logging.info(f"Webhook URL: {webhook_url}")
logging.info(f"Tracking events: {', '.join(events)}")

# Loop through each campaign and create webhooks for each event
for campaign_id in campaign_ids:
    logging.info(f"Processing campaign ID: {campaign_id}")

    for event in events:
        payload = {
            "platformSource": event,
            "eventType": event,
            "Url": webhook_url,
            "dataFormat": "json",
            "enabled": True
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post("https://api.gmass.co/api/webhook", json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                logging.info(f"Webhook created successfully for event '{event}' on campaign '{campaign_id}'. Response: {response_data}")
                print(f"✅ Webhook created for event '{event}' on campaign '{campaign_id}'.")
            else:
                logging.error(f"❌ Failed to create webhook for '{event}' on campaign '{campaign_id}'. Status Code: {response.status_code}. Error: {response_data}")
                print(f"❌ Failed to create webhook for '{event}' on campaign '{campaign_id}'. Check logs for details.")

        except requests.exceptions.RequestException as e:
            logging.error(f"⚠️ API request error for '{event}' on campaign '{campaign_id}': {e}")
            print(f"⚠️ API request error for '{event}' on campaign '{campaign_id}'. Check logs for details.")

logging.info("GMass Webhook Setup Completed")
print("✅ GMass Webhook Setup Completed! Check gmass_webhook.log for details.")
