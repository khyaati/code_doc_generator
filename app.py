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
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})


def detect_language(code, selected_language="auto"):
    """
    Detects the programming language of the input code.

    Args:
        code (str): The input code.
        selected_language (str): The language selected by the user.

    Returns:
        str: Detected language or "unknown".
    """
    if selected_language != "auto":
        return selected_language 
    
    try:
        lexer = guess_lexer(code)
        detected_language = lexer.name.lower() if lexer else "unknown"
        app.logger.info(f"Detected Language: {detected_language}")
        return lexer.name.lower() if lexer else "unknown"
    except ClassNotFound:
        app.logger.warning("Language detection failed")
        return "unknown"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect_language", methods=["POST"])
def detect_language_route():
    data = request.get_json()
    code = data.get("code", "").strip()
    selected_language = data.get("language", "auto")
    language = detect_language(code, selected_language) if code else "unknown"
    return jsonify({"language": language})

@app.route("/upload", methods=["POST"])
@cache.cached(timeout=300, key_prefix='process_code')
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
    app.run(debug=False)
