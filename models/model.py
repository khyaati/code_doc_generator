import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Define model name
MODEL_NAME = "E:/Desktop/models/santacoder"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Load model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32 if DEVICE == "cpu" else torch.float16,
    device_map="auto"
)

def generate_code_comments(code, language="auto"):
    """Generates comments for the given code snippet."""
    prompt = f"### Code in {language}:\n{code}\n### Add helpful comments:\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=512, do_sample=True, temperature=0.7, top_k=50)

    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract the meaningful response
    comment_start = generated_text.find("### Add helpful comments:")
    final_output = generated_text[comment_start + len("### Add helpful comments:"):].strip()

    return final_output
