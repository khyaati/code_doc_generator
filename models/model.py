import os
import logging
import requests
from pygments import lexers
from pygments.util import ClassNotFound
from dotenv import load_dotenv

# Load API token from .env
load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/CodeLlama-7b-hf"

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Supported languages
LANGUAGES = {
    "python": "py", "javascript": "js", "cpp": "cpp", "java": "java", "c": "c",
    "ruby": "rb", "go": "go", "php": "php", "typescript": "ts"
}

def detect_language(code):
    """Detect programming language using Pygments."""
    try:
        lexer = lexers.guess_lexer(code)
        lang = lexer.name.split()[0].lower()
        for key in LANGUAGES:
            if key == lang or key in lang:
                logger.info(f"Detected language: {key}")
                return key
        logger.warning(f"Ambiguous language detected: {lang}")
        return "unknown"
    except ClassNotFound:
        logger.warning("Language detection failed")
        return "unknown"

def comment_code(code, language):
    """Call Code Llama API to add comments to the code."""
    if len(code) > 5000:
        return "Error: Code input is too large. Please limit input to 5000 characters."

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    prompt = (
        f"Add detailed comments to the following {language} code, explaining the logic block-by-block:\n\n"
        f"``` {language}\n{code}\n```"
    )
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 500, "temperature": 0.7, "truncation": True}
    }

    try:
        logger.info(f"Sending code to Code Llama API (language: {language})")
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        response_data = response.json()
        if isinstance(response_data, list) and response_data and "generated_text" in response_data[0]:
            result = response_data[0]["generated_text"]
            try:
                commented_code = result.split(f"``` {language}\n", 1)[1].split("```")[0]
                logger.info("Successfully parsed commented code")
                return commented_code
            except IndexError:
                logger.error("API response missing expected code block")
                return "Error: API returned invalid format"
        else:
            logger.error(f"Unexpected API response: {response_data}")
            return "Error: Unexpected API response format"
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return f"Error: API failure - {str(e)}"
