from transformers import pipeline
from schemas.code_schemas import CodeInput, CodeOutput
from cachetools import TTLCache
import torch
from config import settings
import asyncio

class CodeProcessor:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=settings.cache_ttl)
        self.generator = pipeline(
            "text-generation",
            model=settings.model_name,
            device="cuda" if torch.cuda.is_available() else "cpu",
            torch_dtype=torch.float16,
            model_kwargs={
                "load_in_4bit": settings.quantize,
                "use_cache": True
            }
        )

    async def generate_comments(self, input: CodeInput) -> CodeOutput:
        cache_key = f"{abs(hash(input.code))}:{input.language or 'none'}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._sync_generate(input, cache_key)
        )
        return result

    def _sync_generate(self, input: CodeInput, cache_key: str) -> CodeOutput:
        prompt = f"""Add meaningful comments to this {input.language} code:
        
        {input.code}

        Commented Code:
        """
        
        result = self.generator(
            prompt,
            max_new_tokens=500,
            temperature=0.7,
            do_sample=True,
            pad_token_id=self.generator.tokenizer.eos_token_id,
            stop_sequence=["\n\n\n"]
        )[0]["generated_text"]
        
        output = CodeOutput(
            commented_code=result.split("Commented Code:")[-1].strip(),
            language=input.language or "plaintext"
        )
        
        self.cache[cache_key] = output
        return output
