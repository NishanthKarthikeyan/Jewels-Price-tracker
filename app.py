from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
import os

# Load API keys from .env file
load_dotenv()
GOLD_API_KEY = os.getenv("GOLD_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)

# Function to fetch metal prices from GoldAPI
def get_price(metal_code):
    url = f"https://www.goldapi.io/api/{metal_code}/INR"
    headers = {"x-access-token": GOLD_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price_per_gram = round(data["price"] / 31.1035, 2)
            return {
                "per_gram": price_per_gram,
                "per_8gram": round(price_per_gram * 8, 2),
                "per_kg": round(price_per_gram * 1000, 2),
            }
    except Exception as e:
        print(f"Error fetching price for {metal_code}: {e}")
    return {"per_gram": 0, "per_8gram": 0, "per_kg": 0}

@app.route("/")
def home():
    metal_codes = {
        "Gold": "XAU",
        "Silver": "XAG",
        "Platinum": "XPT",
        "Palladium": "XPD",
    }
    all_prices = {metal: get_price(code) for metal, code in metal_codes.items()}
    return render_template("index.html", all_prices=all_prices)

@app.route("/api/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = { "Content-Type": "application/json" }
    payload = { "contents": [{"parts": [{"text": user_input}]}] }
    params = { "key": GEMINI_API_KEY }

    try:
        r = requests.post(gemini_url, headers=headers, params=params, json=payload, timeout=10)
        r.raise_for_status() # This raises an exception for bad status codes
        
        data = r.json()
        reply = data['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"response": reply})
        
    except requests.exceptions.RequestException as e:
        # Catch and handle specific HTTP errors
        print(f"Chatbot error: {e}")
        return jsonify({"response": f"Error communicating with the chatbot: {e}"}), 500
    except (KeyError, IndexError):
        # Handle cases where the API response structure is unexpected
        return jsonify({"response": "Sorry, I couldn't understand the response from the API. Please try again later."}), 500

if __name__ == "__main__":
    app.run(debug=True)