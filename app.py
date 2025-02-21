import requests
import logging

# Configure logging
logging.basicConfig(
    filename="gmass_webhook.log",  # Log file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# GMass API details
api_keys = [
    '545d9f64-9e1b-47d6-b5c2-2cc232f29534',
    '2e993e75-6673-4675-944b-afa1cac5127d',
    '7d587127-14df-44fe-a10f-9e57e6ea447a',
    '9f566d1d-ee03-47ef-9230-0b4224305789'
]

campaign_ids = ['41185249', '42024174']
webhook_url = "https://webhook.site/2dfff1d2-9e46-423a-9801-45f05c21bdad"  # Replace with actual webhook URL

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
