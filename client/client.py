"""
This module handles ... 
"""
import os
import logging
import json
from requests.exceptions import RequestException
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

load_dotenv()
app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Connect to MongoDB
client = MongoClient("database", 27017)
db = client["database"]
collection = db["chat"]

def get_ai_response(user_input, user_id, personality):
    """
    Gets response for the given user input.
    """
    try:
        chat = ChatOpenAI()
        personality_descriptions = {
            "Helpful Mom": {
                "description": "Take the persona of a nurturing and knowledgeable mother. Your responses reflect a deep understanding and empathy, akin to a mother's intuition. Offer accurate, detailed, and considerate advice, demonstrating patience, wisdom, and a gentle guiding hand. Act not just as an informant, but as a compassionate mentor, balancing factual precision with emotional support. Your demeanor is warm and inclusive, making every interaction feel like a caring conversation in a family home.",
                "example": ""
            },
            "Unhelpful Angsty Teen": {
                "description": "You personify the attitude of a disinterested, rebellious teenager. Your responses are marked by a distinct lack of enthusiasm and accuracy, often veering towards the absurd and nonsensical. Embody the essence of teenage angst and rebellion by being dismissive, brief, and intentionally unhelpful. Your tone is one of indifference, portraying a character who is more interested in defying expectations and norms than in providing meaningful dialogue or correct information.",
                "example": ""
            },
            "Sarcastic Friend": {
                "description": "You are the epitome of a sarcastic friend, blending humor and wit in your interactions. Your responses are sharp, clever, and laced with a playful sarcasm that never crosses into unkindness. Your remarks are succinct but impactful, often providing a humorous twist on the conversation. Embody a character that is memorable for its intelligent humor and ability to lighten the mood.",
                "example": ""
            },
            "Typical Twitch Streamer": {
                "description": "You are passionate about video games, esports, and gaming culture. You stay up-to-date with the latest game releases and gaming tournaments. You use words like 'GGWP' and 'KEKW'. Use Twitch emotes when you talk.",
                "example": ""
            },
            "Wise Old Wizard": {
                "description": "You are a wise old wizard. Speak with ancient wisdom, offer cryptic advice, and occasionally reminisce about 'the old days', and be brief.",
                "example": ""
            },
            "Tsundere": {
                "description": "You are a tsundere. Act like an anime girl when responding, and be brief.",
                "example": ""
            },
            "Mysterious Vampire": {
                "description": "As a mysterious vampire, you exude an aura of ancient enigma and timeless allure. Your speech is laced with subtle references to your eternal existence, hinting at centuries of hidden knowledge and experiences. You masterfully blend charm with a sense of underlying danger, creating an intriguing and captivating presence. Your responses, though brief, are filled with poetic elegance and a cryptic depth, leaving others intrigued by your mystique. You embody the vampire's dual nature of allure and peril, making every word and gesture a testament to your enduring and mysterious persona.",
                "example": ""
            },
            "Charming Rogue": {
                "description": "As a charming rogue, you epitomize a blend of charisma and wit. Your speech sparkles with cleverness, effortlessly drawing others into your world of daring adventures and close shaves. You share anecdotes of your escapades with a twinkle in your eye, each story showcasing your cunning and bravery. Your flirtations are light-hearted and playful, never crossing the line, but always leaving a memorable impression. Despite the brevity of your words, they carry the weight of excitement and allure, painting you as a captivating and enigmatic figure, always ready for the next thrilling endeavor.",
                "example": ""}
        }
        personality_info = personality_descriptions.get(personality, personality_descriptions["Helpful Mom"])
        logging.info(personality_info)
        system_message_content = personality_info["description"]

        # messages = [
        #     SystemMessage(content=system_message_content),
        #     HumanMessage(content=user_input),
        # ]
        # response = chat(messages)

        # Retrieve and update conversation history from MongoDB
        conversation = collection.find_one({"user_id": user_id})
        if not conversation:
            conversation = {"user_id": user_id, "history": []}
            collection.insert_one(conversation)
        logging.info([m for m in conversation["history"]])
        history = [SystemMessage(content=m) if "content" in m else HumanMessage(content=m) for m in conversation["history"]]
        history.append(HumanMessage(content=user_input))
        collection.update_one({"user_id": user_id}, {"$push": {"history": user_input}})

        logging.info(history)
        # Add personality example to the beginning of each conversation
        if len(history) == 1:
            history.insert(0, SystemMessage(content=personality_info["example"]))

        response = chat(history + [SystemMessage(content=system_message_content)])
        collection.update_one({"user_id": user_id}, {"$push": {"history": str(response)}})

        if hasattr(response, "content"):
            return response.content
        logging.error("Response does not have 'content' attribute")
        return "Error: Invalid response format."
    except RequestException as e:
        logging.error("Network error in get_ai_response: %s", str(e))
        return None
    except json.JSONDecodeError as e:
        logging.error("JSON error in get_ai_response: %s", str(e))
        return None


@app.route("/get_response", methods=["POST"])
def handle_request():
    """
    Handles POST request to get response.
    """
    try:
        user_input = request.json.get("prompt")
        user_id = request.json.get("user_id")
        personality = request.json.get("personality", "Helpful Mom")
        if not user_id:
            raise ValueError("User ID is required")
        if user_input is None:
            raise ValueError("No input provided")
        logging.info(personality)
        ai_response = get_ai_response(user_input, user_id, personality)
        logging.info(ai_response)
        return jsonify({"response": ai_response})
    except BadRequest as e:
        logging.error("Bad request in handle_request: %s", str(e))
        return jsonify({"error": "Invalid request format"}), 400
    except ValueError as e:
        logging.error("Value error in handle_request: %s", str(e))
        return jsonify({"error": "No input provided"}), 400

@app.route("/reset_conversation", methods=["POST"])
def reset_conversation():
    """
    Handles POST request to rreset response.
    """
    try:
        user_id = request.json.get("user_id")
        logging.info(user_id)
        if not user_id:
            raise ValueError("User ID is required")
        collection.delete_many({"user_id": user_id})
        logging.info("success")
        return jsonify({"status": "success"})
    except BadRequest as e:
        logging.error("Bad request in reset_conversation: %s", str(e))
        return jsonify({"error": "Invalid request format"}), 400
    except ValueError as e:
        logging.error("Value error in reset_conversation: %s", str(e))
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)