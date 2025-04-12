import torch
import logging
import asyncio
from config import settings
from flask import Flask, request, jsonify
from models.model import CodeProcessor
from schemas.code_schemas import CodeInput
from concurrent.futures import ThreadPoolExecutor

# Initialize Flask app and processor
app = Flask(__name__)
processor = CodeProcessor()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

@app.route('/process-code', methods=['POST'])
def process_code():
    """
    Endpoint to process code and generate comments.
    Note: Flask doesn't natively support async routes, so we wrap it.
    """
    try:
        # Validate input
        data = request.get_json()
        if not data or 'code' not in data:
            raise ValueError("Missing required 'code' field")
        
        input = CodeInput(**data)
        
        # Run async task in executor
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            processor.generate_comments(input)
        )
        loop.close()
        
        return jsonify({
            "commented_code": result.commented_code,
            "language": result.language
        })
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
        
    except torch.cuda.OutOfMemoryError:
        logger.error("GPU memory exhausted")
        return jsonify({
            "error": "Server overloaded - try a smaller code snippet",
            "code": "gpu_oom"
        }), 503
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "code": "server_error"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model": settings.model_name,
        "device": processor.device
    })

if __name__ == '__main__':
    app.run(
        host=settings.host,
        port=settings.port,
        threaded=True  # Required for concurrent requests
    )
