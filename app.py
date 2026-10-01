import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import CHATBOT_TITLE, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__, template_folder="templates")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not configured in the environment.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.1-flash-lite"


@app.get("/")
def index():
    return render_template("index.html", chatbot_title=CHATBOT_TITLE)


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Please enter a study-related question."}), 400

    contents = []
    for message in messages[-20:]:
        role = message.get("role")
        text = str(message.get("content", "")).strip()

        if not text or role not in {"user", "model"}:
            continue

        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
        )

    if not contents:
        return jsonify({"error": "Please enter a study-related question."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            return jsonify({"error": "I couldn't generate a response. Please try again."}), 502

        return jsonify({"answer": answer})

    except Exception:
        return jsonify(
            {"error": "Something went wrong while contacting Gemini. Please try again."}
        ), 500


if __name__ == "__main__":
    app.run()
