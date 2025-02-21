from flask import Flask, request, jsonify, redirect, url_for
import datetime

app = Flask(__name__)

# In-memory log storage (optional: can be replaced with a DB later)
logs = []

@app.route("/", methods=["GET"])
def home():
    return "GMass Webhook is Running!"

@app.route("/gmass-webhook", methods=["POST"])
def gmass_webhook():
    """Handles GMass Webhook and Redirects to /user1"""
    try:
        data = request.json  # Receive JSON payload
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Store payload temporarily before redirection
        request.environ["gmass_payload"] = data

        return redirect(url_for("user1"))  # Redirect to /user1

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/user1", methods=["GET", "POST"])
def user1():
    """Prints the payload from GMass webhook"""
    data = request.environ.get("gmass_payload", {})

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
    print(f"Received Event at /user1: {log_entry}")

    return jsonify({"message": "Redirected and received!", "data": log_entry}), 200

@app.route("/logs", methods=["GET"])
def get_logs():
    """Endpoint to view all stored logs"""
    return jsonify(logs), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
