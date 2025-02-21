import os
import csv
import requests
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load .env file (Only for local development)
if os.getenv("KOYEB_ENV") is None:
    load_dotenv()

# Retrieve environment variables
api_keys = os.getenv("API_KEYS", "").split(",")  # Convert CSV string to list
campaign_ids = os.getenv("CAMPAIGN_IDS", "").split(",")
webhook_url = os.getenv("WEBHOOK_URL", "").strip()

# Flask app for Gunicorn
app = Flask(__name__)

# CSV File Path
CSV_FILE = "gmass_events.csv"

# Configure logging
logging.basicConfig(
    filename="gmass_webhook.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Events to track
events = ["Opens", "Clicks", "Replies", "Bounces", "Unsubscribes", "Sends", "Blocks"]

# Ensure CSV file exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "event", "campaign_id", "email", "extra_data"])

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "running", "message": "GMass Webhook API is live!"}), 200

@app.route("/gmass-webhook", methods=["POST"])
def receive_gmass_event():
    """
    Receives incoming GMass event data and saves it to CSV.
    """
    data = request.get_json()
    logging.info(f"Received GMass webhook data: {data}")

    # Extract relevant data
    timestamp = data.get("TimeStamp", "N/A")
    event = data.get("platformSource", "Unknown")
    campaign_id = data.get("CampaignID", "N/A")
    email = data.get("EmailAddress", "N/A")

    # Store additional details in case of different event types
    extra_data = ""
    if "UserAgent" in data:
        extra_data = data["UserAgent"]
    elif "BounceMessage" in data:
        extra_data = data["BounceMessage"]
    elif "URL" in data:
        extra_data = data["URL"]

    # Save to CSV
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, event, campaign_id, email, extra_data])

    return jsonify({"status": "success", "message": "Event received and stored"}), 200

def create_webhooks():
    """
    Creates GMass webhooks for tracking events.
    """
    # Ensure required environment variables are set
    if not api_keys or not campaign_ids or not webhook_url:
        logging.error("Missing required environment variables. Check API_KEYS, CAMPAIGN_IDS, and WEBHOOK_URL.")
        return
    
    # Use first API key
    api_key = api_keys[0]

    logging.info("Starting GMass Webhook Setup")
    logging.info(f"Using API Key: {api_key[:5]}**** (hidden for security)")
    logging.info(f"Webhook URL: {webhook_url}")
    logging.info(f"Tracking events: {', '.join(events)}")

    for campaign_id in campaign_ids:
        logging.info(f"Processing campaign ID: {campaign_id}")

        for event in events:
            payload = {
                "platformSource": event,
                "eventType": event,
                "Url": webhook_url,  # Your webhook URL that GMass will call
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
                    logging.info(f"✅ Webhook created for '{event}' on campaign '{campaign_id}'. Response: {response_data}")
                    print(f"✅ Webhook created for '{event}' on campaign '{campaign_id}'.")
                else:
                    logging.error(f"❌ Failed webhook '{event}' on '{campaign_id}'. Status: {response.status_code}, Error: {response_data}")
                    print(f"❌ Failed webhook '{event}' on '{campaign_id}'. Check logs for details.")

            except requests.exceptions.RequestException as e:
                logging.error(f"⚠️ API request error '{event}' on '{campaign_id}': {e}")
                print(f"⚠️ API request error '{event}' on '{campaign_id}'. Check logs for details.")

if __name__ == "__main__":
    create_webhooks()
    app.run(host="0.0.0.0", port=8000)
