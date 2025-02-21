from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# In-memory log storage (optional: can be replaced with a DB later)
logs = []

@app.route("/", methods=["GET"])
def home():
    return "GMass Webhook is Running!"

@app.route("/gmass-webhook", methods=["POST"])
def gmass_webhook():
    try:
        data = request.json  # Receive JSON payload
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Extract fields (if missing, default to 'N/A')
        email = data.get("EmailAddress", "N/A")
        user_agent = data.get("UserAgent", "N/A")
        timestamp = data.get("TimeStamp", datetime.datetime.now().isoformat())
        event_type = data.get("TYPE", "N/A")  # GMass event type (open, click, reply, unsubscribe)
        clicked_link = data.get("ClickedLink", "N/A")
        reply_text = data.get("ReplyText", "N/A")
        unsubscribe_timestamp = data.get("UnsubscribeTimestamp", "N/A")

        # Create a log entry
        log_entry = {
            "email": email,
            "user_agent": user_agent,
            "timestamp": timestamp,
            "event_type": event_type,
            "clicked_link": clicked_link,
            "reply_text": reply_text,
            "unsubscribe_timestamp": unsubscribe_timestamp
        }

        # Store log in memory (this can be replaced with a DB or log file)
        logs.append(log_entry)

        # Print log to console for debugging
        print(f"Received Event: {log_entry}")

        return jsonify({"message": "Webhook received successfully!", "data": log_entry}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/logs", methods=["GET"])
def get_logs():
    """Endpoint to view all stored logs"""
    return jsonify(logs), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
