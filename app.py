from flask import Flask, render_template, request
import requests
import time

app = Flask(__name__)

# IBM IAM Token URL
TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
API_KEY = "G75K2zUTU93680aujv91-HUn2_gxG8qYEtvJFjfzxaMm"

# URLs
URL_STAGING = "https://api.8798-f464fa20.eu-de.ri.apiconnect.cloud.ibm.com/analytics/ibm-managed-analytics-service-v2/catalogs/tmfb/dev-catalog/events"
URL_PRODUCTION = "https://api.8798-f464fa20.eu-de.ri.apiconnect.cloud.ibm.com/analytics/ibm-managed-analytics-service-v2/catalogs/tmfb/gateway/events"

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
    "30d": "last30days"
}

def get_token():
    global cached_token, token_expiry

    if cached_token and time.time() < token_expiry:
        return cached_token

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": API_KEY
    }
    res = requests.post(TOKEN_URL, headers=headers, data=data)
    res.raise_for_status()
    token_data = res.json()

    cached_token = token_data["access_token"]
    token_expiry = time.time() + token_data.get("expires_in", 3600) - 60

    return cached_token


@app.route("/analytics", methods=["GET", "POST"])
def analytics():

    # Determine environment
    env = request.args.get("env") or request.form.get("environment") or "staging"

    ANALYTICS_URL = URL_STAGING if env == "staging" else URL_PRODUCTION

    response_data = None

    if request.method == "POST":
        params = {}

        # Timeframe
        timeframe = request.form.get("timeframe")
        if timeframe in TIMEFRAME_MAP:
            params["timeframe"] = TIMEFRAME_MAP[timeframe]

        # App Name
        if request.form.get("app_name"):
            params["app_name"] = f"contains:{request.form.get('app_name')}"

        # API Name
        if request.form.get("use_api_name"):
            api_name = request.form.get("api_name")
            if api_name:
                params["api_name"] = f"equals:{api_name}"

        # Global Transaction ID
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
            request_body = request.form.get("request_body")
            if request_body:
                params["request_body"] = f"contains:{request_body}"

        # Response Body
        if request.form.get("use_response_body"):
            response_body = request.form.get("response_body")
            if response_body:
                params["response_body"] = f"contains:{response_body}"

        # Required fields
        params["fields"] = (
            "api_name,app_name,global_transaction_id,api_resource_id,"
            "request_body,response_body,timeframe,time_to_serve_request"
        )

        # Fetch token
        try:
            token = get_token()
        except Exception as e:
            return render_template("analytics.html", response={"error": str(e)}, environment=env)

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        try:
            res = requests.get(ANALYTICS_URL, headers=headers, params=params)
            res.raise_for_status()
            response_data = res.json()
        except Exception as e:
            response_data = {"error": str(e)}

    return render_template("analytics.html", response=response_data, environment=env)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
