import logging
from flask import Flask, render_template, request, jsonify
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
from models.model import generate_code_comments

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="app.log", filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate_comments", methods=["POST"])
def generate_comments():
    try:
        data = request.json
        code = data.get("code", "")
        language = data.get("language", "auto")

        if not code.strip():
            return jsonify({"error": "No code provided!"})

        # Auto-detect language if "auto" is selected
        if language == "auto":
            try:
                lexer = guess_lexer(code)
                language = lexer.name
            except ClassNotFound:
                language = "Unknown"

        logging.info(f"Processing code in language: {language}")

        # Generate commented code using the model
        commented_code = generate_code_comments(code, language)

        return jsonify({"commented_code": commented_code, "language": language})

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(debug=True)
