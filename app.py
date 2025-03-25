import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import io
import chardet
from datetime import datetime
from models.model import detect_language, comment_code, LANGUAGES

app = Flask(__name__)

# Setup logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1MB upload limit

@app.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html', languages=LANGUAGES.keys())

@app.route('/process', methods=['POST'])
def process_code():
    try:
        logger.info("Received /process request")
        code = request.form.get('code', '')
        selected_lang = request.form.get('language', '').lower()
        file = request.files.get('file')

        if file and file.filename:
            filename = secure_filename(file.filename)
            file_bytes = file.read()
            encoding = chardet.detect(file_bytes)['encoding']
            code = file_bytes.decode(encoding)
            logger.info(f"Uploaded file: {filename}, detected encoding: {encoding}")
        elif not code:
            logger.warning("No code provided")
            return jsonify({"error": "No code provided"}), 400

        language = selected_lang if selected_lang in LANGUAGES else detect_language(code)
        if language == "unknown":
            logger.warning("Unknown language detected")
            return jsonify({"error": "Could not detect language, please select manually"}), 400

        commented_code = comment_code(code, language)
        logger.info(f"Commented code generated")
        return jsonify({"commented_code": commented_code, "language": language})
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route('/download', methods=['POST'])
def download_code():
    try:
        code = request.form.get('code', '')
        language = request.form.get('language', '')
        if not code or language not in LANGUAGES:
            logger.warning("Invalid download request")
            return jsonify({"error": "Invalid code or language"}), 400
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"commented_code_{timestamp}.{LANGUAGES[language]}"
        file_stream = io.BytesIO(code.encode('utf-8'))
        logger.info(f"Generating download: {filename}")
        return send_file(file_stream, download_name=filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    logger.info("Starting Flask app")
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
