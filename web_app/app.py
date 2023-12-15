"""
This is a web-app ... 
"""
import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from flask_cors import CORS
import requests
from flask_session import Session
from requests.exceptions import RequestException
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")
CORS(app)
logging.basicConfig(level=logging.INFO)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Connect to MongoDB
client = MongoClient("database", 27017)
db = client["database"]

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Render index page.
    """
    if "messages" not in session:
        session["messages"] = []

    if "user_id" not in session:
        return render_template("login.html")
    
    else:
        if request.method == "POST":
            user_input = request.form.get("user_input")
            user_id = session.get("user_id")
            session["messages"].append({"type": "User", "content": user_input})
            return render_template("index.html", messages=session["messages"], user_id=user_id)
        user_id = session.get("user_id")
        return render_template("index.html", messages=session["messages"], user_id=user_id)


@app.route("/get_response", methods=["POST"])
def get_response():
    """
    Get response for user input.
    """
    user_input = request.form.get("user_input")
    personality = request.form.get("personality", "helpful")
    user_id = session["user_id"]
    try:
        response = requests.post(
            "http://client:5002/get_response", json={"prompt": user_input, "personality": personality, "user_id": user_id}, timeout=60
        )
        # response = requests.post(
        #     "http://client:5002/reset_conversation", json={"prompt": user_input, "personality": personality, "user_id": user_id}, timeout=60
        # )
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




# Login, Sign Up Functionality
@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Renders the signup page"""
    # If there is a user_id in session, it redirects them back to the home page
    if "user_id" in session:
        return redirect(url_for("index"))

    # If there is no account, then we allow the user to creat one.
    if request.method == "POST":
        # We allow the user to create their username, password, confirm password, email
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email = request.form["email"]
        errors = []

        # This checks if there is already a user that has this exact username
        if db.users.find_one({"username": username}):
            errors.append("Username already exists!")

        # This checks if there is already a user that has this exact email
        if db.users.find_one({"email": email}):
            errors.append("Email already used, try another or try logging in!")

        # This checks if the password is in between 8-20 characters
        if not 8 <= len(password) <= 20:
            errors.append("Password must be between 8 and 20 characters long!")

        # This checks if the password does not have any numbers
        if not any(char.isdigit() for char in password):
            errors.append("Password should have at least one number!")

        # This checks if the password does not have any alphabets
        if not any(char.isalpha() for char in password):
            errors.append("Password should have at least one alphabet!")

        # This checks if the password and the confirm password do not match
        if not confirm_password == password:
            errors.append("Passwords do not match!")

        # If any errors, it will re-render the signup.html page and allow the user to try again
        if errors:
            return render_template("signup.html", errors=errors)

        # If user managed to create a proper account, it will generate a hash for their password
        password_hash = generate_password_hash(password)

        # Here we insert their account details to the database
        user_collection = db["users"]
        user_collection.insert_one(
            {
                "username": username,
                "password": password_hash,
                "email": email,
                "midi_files": [],
            }
        )

        # This redirects the user to the login page where they must login to access the webpage.
        return redirect(url_for("login"))

    # Renders the signup.html page
    return render_template("signup.html")


# Rendering either the login template if they haven't logged in, otherwise, the home page
@app.route("/login", methods=["GET"])
def login():
    """Renders the login page"""
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


#This function is the backend of the login functionality from the login.html file
@app.route("/login_auth", methods=["POST"])
def login_auth():
    """Route for login authentication"""
    # If a user is already logged in, redirect them to the home page
    if "user_id" in session:
        return redirect(url_for("index"))

    # Else, ask them to login by inputting a username and password
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        session["username"] = username

        errors = []

        # Once inputted their username and password, check the database for existing users
        user = db.users.find_one({"username": username})

        # We provide the _id attribute of the user to the user_id in the session
        if user and check_password_hash(user["password"], password):
            # User sessions to keep track of who's logged in
            session["user_id"] = str(user["_id"])
            return redirect(url_for("index"))

        # If the username or password does not match we render the login.html template once more
        errors.append("Invalid username or password!")
        return render_template("login.html", errors=errors)
    return None

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Renders the forgot password page"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email = request.form["email"]
        errors = []
        user = db.users.find_one({"email": email, "username": username})

        if not user:
            errors.append("Invalid username or email!")

        if not 8 <= len(password) <= 20:
            errors.append("Password must be between 8 and 20 characters long!")

        if not any(char.isdigit() for char in password):
            errors.append("Password should have at least one number!")

        if not any(char.isalpha() for char in password):
            errors.append("Password should have at least one alphabet!")

        if not confirm_password == password:
            errors.append("Passwords do not match!")

        if errors:
            return render_template("forgot_password.html", errors=errors)
    return None


# Here we have another route, if the user decides to logout,
# it will pop their user_id from the session and redirect them to the login page
@app.route("/logout")
def logout():
    """route for logout"""
    session.pop("user_id", None)
    clear_session()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
