import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from huggingface_hub import login

HF_TOKEN = ""  # add your HF token here
login(token=HF_TOKEN)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

MODEL_NAME = 'microsoft/Phi-4-mini-instruct'

MAX_NEW_TOKENS = 512
TEMPERATURE = 0.3
TOP_K = 50
TOP_P = 0.95
REPETITION_PENALTY = 1.1

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
    quantization_config=quantization_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True
)

supported_langs = ['python', 'c', 'cpp', 'java', 'javascript']


@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route("/comment", methods=["POST"])
def comment_code():
    data = request.json
    code = data.get("code", "")
    language = data.get("language", "").strip().lower()

    if not code:
        return jsonify({"error": "No code provided"}), 400

    if not language or language not in supported_langs:
        return jsonify({
            "error": f"Valid language must be provided. Supported languages: {', '.join(supported_langs)}"
        }), 400

    try:
        prompt = f"""<|system|>
You are a helpful AI assistant specialized in code analysis.
Your task is to analyze code and add clear, concise comments to it.

<|user|>
Analyze the following {language} code and add meaningful inline comments to explain what each part does.
Make sure the output includes only the commented version of the code — no extra text before or after.

<CODE>
{code}
</CODE>

Commented Code:
"""

        inputs = tokenizer(
            prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=2048
        )

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=TEMPERATURE,
                do_sample=True,
                top_k=TOP_K,
                top_p=TOP_P,
                repetition_penalty=REPETITION_PENALTY,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

    
        try:
            comment = full_output.split("Commented Code:\n", 1)[1].strip()
        except IndexError:
            comment = "Failed to generate."

        
        return jsonify({"commented code": comment})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False)
