from flask import Flask, render_template, request, jsonify
from model.codet5_model import generate_comments
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound
from flask_caching import Cache
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Enable caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})


def detect_language(code):
    """
    Detects the programming language of the input code.

    Args:
        code (str): The input code.

    Returns:
        str: Detected language or "unknown".
    """
    try:
        lexer = guess_lexer(code)
        return lexer.name.lower() if lexer else "unknown"
    except ClassNotFound:
        return "unknown"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect_language", methods=["POST"])
def detect_language_route():
    data = request.get_json()
    code = data.get("code", "").strip()
    language = detect_language(code) if code else "unknown"
    return jsonify({"language": language})

@app.route("/upload", methods=["POST"])
@cache.cached(timeout=300)
def process_code():
    data = request.get_json()
    code = data.get("code", "").strip()
    comment_style = data.get("comment_style", "brief")

    if not code:
        return jsonify({"error": "No code provided"}), 400

    try:
        commented_code = generate_comments(code, comment_style)
        return jsonify({"commented_code": commented_code})
    except Exception as e:
        app.logger.error(f"Error processing code: {str(e)}")
        return jsonify({"error": f"Error processing code: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
