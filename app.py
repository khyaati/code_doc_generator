from flask import Flask, request, jsonify
from models.model import CodeProcessor
from schemas.code_schemas import CodeInput
import asyncio
import logging
import torch

app = Flask(__name__)
processor = CodeProcessor()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/process-code', methods=['POST'])
async def process_code():
    try:
        input = CodeInput(**request.get_json())
        result = await processor.generate_comments(input)
        return jsonify(result.model_dump())
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except torch.cuda.OutOfMemoryError:
        logger.error("GPU memory exhausted")
        return jsonify({"error": "Server overloaded"}), 503
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
