from flask import Flask, render_template, request
import requests
import time
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)


TOKEN_URL = os.getenv("TOKEN_URL")
API_KEY = os.getenv("API_KEY")
URL_STAGING = os.getenv("URL_STAGING")
URL_PRODUCTION = os.getenv("URL_PRODUCTION")

# Token cache
cached_token = None
token_expiry = 0

# Timeframe mapping
TIMEFRAME_MAP = {
    "1m": "last1minute",
    "5m": "last5minutes",
    "15m": "last15minutes",
    "1h": "last1hour",
    "4h": "last4hours",
    "12h": "last12hours",
    "24h": "last24hours",
    "7d": "last7days",
    "30d": "last30days",
    "all-event": "all"
}

def get_token():
    global cached_token, token_expiry

    if cached_token and time.time() < token_expiry:
        return cached_token

    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    data = {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": API_KEY}

    res = requests.post(TOKEN_URL, headers=headers, data=data)
    res.raise_for_status()
    token_data = res.json()

    cached_token = token_data["access_token"]
    token_expiry = time.time() + token_data.get("expires_in", 3600) - 60

    return cached_token


@app.route("/analytics", methods=["GET", "POST"])
def analytics():
    # Determine environment
    env = request.args.get("env") or request.form.get("environment") or "production"
    ANALYTICS_URL = URL_STAGING if env == "staging" else URL_PRODUCTION

    response_data = None

    if request.method == "POST":
        params = {}

        # Timeframe
        timeframe = request.form.get("timeframe")
        params["timeframe"] = TIMEFRAME_MAP.get(timeframe, "last24hours")

        # App Name
        if request.form.get("app_name"):
            params["app_name"] = f"contains:{request.form.get('app_name')}"

        # API Name
        if request.form.get("use_api_name"):
            api_name = request.form.get("api_name")
            if api_name:
                params["api_name"] = f"equals:{api_name}"

        # Global Txn ID
        if request.form.get("use_global_transaction_id"):
            gtid = request.form.get("global_transaction_id")
            if gtid:
                params["global_transaction_id"] = f"equals:{gtid}"

        # API Resource ID
        if request.form.get("use_api_resource_id"):
            api_resource = request.form.get("api_resource_id")
            if api_resource:
                params["api_resource_id"] = f"contains:{api_resource}"

        # Request Body
        if request.form.get("use_request_body"):
            req_body = request.form.get("request_body")
            if req_body:
                params["request_body"] = f"contains:{req_body}"

        # Response Body
        if request.form.get("use_response_body"):
            res_body = request.form.get("response_body")
            if res_body:
                params["response_body"] = f"contains:{res_body}"

        # Fields to fetch
        params["fields"] = (
            "api_name,api_resource_id,app_name,request_http_headers,datetime,"
            "global_transaction_id,request_body,response_body,status_code,"
            "time_to_serve_request"
        )

        try:
            token = get_token()
        except Exception as e:
            return render_template("analytics.html", response={"error": str(e)}, environment=env)

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        try:
            res = requests.get(ANALYTICS_URL, headers=headers, params=params)
            res.raise_for_status()

            raw = res.json()
            events = raw.get("events", [])

            reordered_events = []

            for ev in events:
                # Extract X-Channel
                x_channel = None
                for header in ev.get("request_http_headers", []):
                    for key, value in header.items():
                        if key.lower() == "x-channel":
                            x_channel = value
                            break
                    if x_channel:
                             break
                # Convert UTC datetime → Pakistan time + AM/PM
                original_dt = ev.get("datetime")
                formatted_dt = None

                if original_dt:
                    try:
                        utc_dt = datetime.fromisoformat(original_dt.replace("Z", "+00:00"))
                        pk_dt = utc_dt.astimezone(timezone(timedelta(hours=5)))
                        formatted_dt = pk_dt.strftime("%Y-%m-%d %I:%M:%S %p")
                    except:
                        formatted_dt = original_dt

                ordered = OrderedDict()
                ordered["api_name"] = ev.get("api_name")
                ordered["api_resource_id"] = ev.get("api_resource_id")
                ordered["app_name"] = ev.get("app_name")
                ordered["X-Channel"] = x_channel
                ordered["datetime"] = formatted_dt
                ordered["global_transaction_id"] = ev.get("global_transaction_id")
                ordered["request_body"] = ev.get("request_body")
                ordered["response_body"] = ev.get("response_body")
                ordered["status_code"] = ev.get("status_code")
                ordered["time_to_serve_request"] = ev.get("time_to_serve_request")

                reordered_events.append(ordered)

            response_data = {"events": reordered_events}

        except Exception as e:
            response_data = {"error": str(e)}

    return render_template("analytics.html", response=response_data, environment=env)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)