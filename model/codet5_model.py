import torch
from transformers import RobertaTokenizer, T5ForConditionalGeneration
from flask_caching import Cache
import logging 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "Salesforce/codet5-small"
tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)

# Initialize Flask caching
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})


def generate_comments(code, comment_style="brief"):
    """
    Generates commented code using CodeT5.

    Args:
        code (str): The input code to be commented.
        comment_style (str): Either "brief" or "detailed" for comment verbosity.

    Returns:
        str: Commented code or error message.
    """
    if not code.strip():
        return "Error: Empty code input."

    if comment_style not in ["brief", "detailed"]:
        return "Error: Invalid comment_style. Use 'brief' or 'detailed'."

    max_length = 512
    prompt = f"Generate {'detailed' if comment_style == 'detailed' else 'brief'} comments for the following code:\n{code}"

    try:
        inputs = tokenizer(prompt, return_tensors="pt", max_length=max_length, truncation=True)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_length=max_length,
                num_return_sequences=1,
                num_beams=3
            )
        commented_code = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return commented_code
    
    except torch.cuda.OutOfMemoryError as e:
        logger.error(f"CUDA Out-of-Memory error during model inference: {e}")
        return "Error: CUDA Out-of-Memory. Please try with smaller code snippets"

    except Exception as e:
        logger.error(f"Error generating comments: {str(e)}")
        return f"Error generating comments: {str(e)}"
