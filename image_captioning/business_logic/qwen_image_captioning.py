import torch
from PIL import Image
from accelerate.utils import bnb
from transformers import Qwen2_5_VLForConditionalGeneration, AutoModelForCausalLM
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor
import torch

class ImageCaption:

    def __init__(self):
        self.model_id = "Qwen/Qwen2.5-VL-7B-Instruct"
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(self.model_id, torch_dtype=torch.bfloat16, device_map="auto")
        self.processor= AutoProcessor.from_pretrained(self.model_id)





    def get_caption(self,image_path):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image":f"{image_path}",
                    },
                    {"type": "text", "text": """Generate a factual caption for this image for use in a multimodal retrieval system.
                                                Describe:

                                                - Main objects and subjects
                                                - Actions or interactions
                                                - Scene context (academic, professional, or everyday life)
                                                - Any visible text, charts, or tools if present

                                                Write 1–3 concise sentences using clear, neutral language.
                                                Do not speculate beyond what is visible."""},
                ],
            }
        ]
        #
        #
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs,_ = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to("cuda" if torch.cuda.is_available() else "cpu")

        # Inference: Generation of the output
        generated_ids = self.model.generate(**inputs, max_new_tokens=256)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        return output_text[0]

