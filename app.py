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
LOG_FILE = "gmass_webhook.log"

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Ensure log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("GMass Webhook Log Started\n")

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


@app.route("/logs", methods=["GET"])
def get_logs():
    """
    Serves the gmass_webhook.log file content
    """
    try:
        with open(LOG_FILE, "r") as f:
            return f"<pre>{f.read()}</pre>", 200  # Display logs in a readable format
    except FileNotFoundError:
        return "Log file not found", 404


def get_gmass_report(campaign_id, report_type):
    """
    Fetches GMass report for a given campaign ID and report type.
    Available types: opens, clicks, unsubscribes, bounces, blocks, replies.
    """

    # Find an API key that matches the campaign ID
    api_key = None
    for key in api_keys:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        check_url = f"https://api.gmass.co/api/campaigns/{campaign_id}"

        response = requests.get(check_url, headers=headers)

        if response.status_code == 200:
            api_key = key
            break

    if api_key is None:
        logging.error(f"❌ No valid API key found for campaign ID {campaign_id}")
        return jsonify({"error": "No valid API key found for this campaign"}), 403

    # Now, fetch the actual report
    url = f"https://api.gmass.co/api/reports/{campaign_id}/{report_type}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        logging.info(f"✅ Successfully retrieved {report_type} report for campaign {campaign_id}")
        return jsonify(data), 200
    else:
        logging.error(f"❌ Failed to retrieve {report_type} report for campaign {campaign_id}: {response.text}")
        return jsonify({"error": "Failed to retrieve report", "status_code": response.status_code}), response.status_code



@app.route("/reports/<campaign_id>/opens", methods=["GET"])
def get_opens_report(campaign_id):
    """Fetches recipients who opened the email campaign."""
    return get_gmass_report(campaign_id, "opens")


@app.route("/reports/<campaign_id>/clicks", methods=["GET"])
def get_clicks_report(campaign_id):
    """Fetches recipients who clicked a URL in the email campaign."""
    return get_gmass_report(campaign_id, "clicks")


@app.route("/reports/<campaign_id>/unsubscribes", methods=["GET"])
def get_unsubscribes_report(campaign_id):
    """Fetches recipients who unsubscribed from the email campaign."""
    return get_gmass_report(campaign_id, "unsubscribes")


@app.route("/reports/<campaign_id>/bounces", methods=["GET"])
def get_bounces_report(campaign_id):
    """Fetches recipients whose email bounced."""
    return get_gmass_report(campaign_id, "bounces")


@app.route("/reports/<campaign_id>/blocks", methods=["GET"])
def get_blocks_report(campaign_id):
    """Fetches recipients who blocked the emails."""
    return get_gmass_report(campaign_id, "blocks")


@app.route("/reports/<campaign_id>/replies", methods=["GET"])
def get_replies_report(campaign_id):
    """Fetches recipients who replied to the email campaign."""
    return get_gmass_report(campaign_id, "replies")

@app.route("/csv", methods=["GET"])
def get_csv():
    """Serves the gmass_events.csv file content."""
    try:
        with open(CSV_FILE, "r") as f:
            return f"<pre>{f.read()}</pre>", 200  # Display CSV content in a readable format
    except FileNotFoundError:
        return "CSV file not found", 404


def create_webhooks():
    """
    Creates GMass webhooks for tracking events using multiple API keys.
    """
    if not api_keys or not campaign_ids or not webhook_url:
        logging.error("Missing required environment variables. Check API_KEYS, CAMPAIGN_IDS, and WEBHOOK_URL.")
        return

    logging.info("Starting GMass Webhook Setup")
    logging.info(f"Webhook URL: {webhook_url}")
    logging.info(f"Tracking events: {', '.join(events)}")

    for index, campaign_id in enumerate(campaign_ids):
        api_key = api_keys[index % len(api_keys)]  # Cycle through API keys

        logging.info(f"Processing campaign ID: {campaign_id} using API Key: {api_key[:5]}****")

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
