import torch
import asyncio
from config import settings
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, StoppingCriteria, StoppingCriteriaList
from schemas.code_schemas import CodeInput, CodeOutput
from cachetools import TTLCache


model_name = "bigcode/starcoder"

class StopGenerationCriteria(StoppingCriteria):
    """Stop generation when encountering certain sequences (e.g., triple newlines)."""
    def __init__(self, stop_sequences):
        self.stop_sequences = stop_sequences

    def __call__(self, input_ids, scores, **kwargs):
        for stop_seq in self.stop_sequences:
            if torch.all(input_ids[:, -len(stop_seq):] == stop_seq).item():
                return True
        return False


class CodeProcessor:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=settings.cache_ttl)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(
            settings.model_name,
            padding_side="left",
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            settings.model_name,
            device_map="auto",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            load_in_4bit=settings.quantize,
            trust_remote_code=True
        )
        self.stop_criteria = StopGenerationCriteria(
            stop_sequences=[self.tokenizer.encode("\n\n\n", return_tensors="pt").to(self.device)]
        )

    async def generate_comments(self, input: CodeInput) -> CodeOutput:
        cache_key = f"{abs(hash(input.code))}:{input.language or 'none'}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._generate_with_fim(input, cache_key)
        )
        return result
    

    def generate_with_fim(self, input: CodeInput, cache_key: str) -> CodeOutput:
        # Structured prompt for better semantic analysis
        prompt = f"""Analyze this {input.language} code and add detailed comments:
        1. Purpose of functions/classes.
        2. Key logic steps (avoid trivial comments like "loop starts here").
        3. Important variables/data structures.

        Code:
        {input.code}

        Commented Code:
        """
        # Encode with FIM (Fill-in-the-Middle) tokens for better insertion
        inputs = self.tokenizer.encode(
            f"<fim_prefix>{prompt}<fim_suffix><fim_middle>",
            return_tensors="pt"
        ).to(self.device)

        # Generate with constrained decoding
        outputs = self.model.generate(
            inputs,
            max_new_tokens=min(512, len(input.code.splitlines()) * 10),  # Dynamic length
            temperature=0.3,  # Lower for deterministic comments
            top_p=0.9,
            num_beams=3,
            stopping_criteria=StoppingCriteriaList([self.stop_criteria]),
            pad_token_id=self.tokenizer.eos_token_id,
        )

        # Decode and post-process
        commented_code = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        ).split("Commented Code:")[-1].strip()

        # Basic validation (e.g., ensure comments reference actual code)
        self._validate_comments(commented_code, input.code)

        output = CodeOutput(
            commented_code=commented_code,
            language=input.language or "plaintext"
        )
        self.cache[cache_key] = output
        return output
    

    def validate_comments(self, commented_code: str, original_code: str):
        """Basic checks to ensure comments align with code."""
        # Example: Verify at least 50% of functions/variables are mentioned
        import re
        code_entities = set(re.findall(r'\b(def|class|var)\s+(\w+)', original_code))
        mentioned_entities = set(re.findall(r'#.*?(\w+).*?\n', commented_code))
        
        if len(code_entities) > 0 and len(mentioned_entities) / len(code_entities) < 0.5:
            raise ValueError("Generated comments may not cover key code elements.")
