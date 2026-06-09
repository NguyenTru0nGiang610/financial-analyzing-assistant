import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging


class LocalLLMGenerator:

    def __init__(self):

        model_name = "Qwen/Qwen2.5-3B-Instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=self.device,
            torch_dtype="auto",
        )
        self.model.eval()

    def generate(self, prompt):
        messages = [
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant in financial analysis "
            "and your mission is to answer any question based on the provided context with the most relevant information and financial analysis."},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(**model_inputs, max_new_tokens=512)
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids, strict=False)
        ]
        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]