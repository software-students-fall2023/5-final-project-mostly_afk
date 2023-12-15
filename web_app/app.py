"""
This is a web-app ... 
"""
import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import requests
from flask_session import Session
from requests.exceptions import RequestException

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")
CORS(app)
logging.basicConfig(level=logging.INFO)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Render index page.
    """
    if "messages" not in session:
        session["messages"] = []

    if request.method == "POST":
        user_input = request.form.get("user_input")
        session["messages"].append({"type": "User", "content": user_input})
        return render_template("index.html", messages=session["messages"])

    return render_template("index.html", messages=session["messages"])


@app.route("/get_response", methods=["POST"])
def get_response():
    """
    Get response for user input.
    """
    user_input = request.form.get("user_input")
    personality = request.form.get("personality", "helpful")
    try:
        response = requests.post(
            "http://client:5002/get_response", json={"prompt": user_input, "personality": personality}, timeout=60
        )
        response.raise_for_status()
        ai_response = response.json().get("response")
        session["messages"].append({"type": "Assistant", "content": ai_response})
        return jsonify(ai_response)
    except RequestException as e:
        logging.error("Error making the request to the client: %s", str(e))
        return (
            jsonify(
                {
                    "error": "An error occurred while getting the response from the client"
                }
            ),
            500,
        )


@app.route("/clear_session", methods=["POST"])
def clear_session():
    """
    Route for clearing session.
    """
    try:
        session.clear()
        return jsonify({"message": "Session cleared successfully"})
    except RuntimeError as e:
        logging.error("Error clearing session: %s", str(e))
        return jsonify({"error": "An error occurred while clearing the session"}), 500


if __name__ == "__main__":
    app.run(debug=True)
