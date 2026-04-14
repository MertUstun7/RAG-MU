import os
import ollama
from config import logger

class ModelCollection:

    @staticmethod
    def get_local_models():
        try:
            base_url = os.getenv("OLLAMA_BASE_URL")
            if base_url:
                # Docker: bağlantı URL'si ile Client kullan
                response = ollama.Client(host=base_url).list()
            else:
                # Lokal: module-level fonksiyon (eski davranış)
                response = ollama.list()

            model_names = [model.model for model in response.models]
            return {"models": model_names}

        except Exception as e:
            logger.error("Ollama couldn't connect the ollama module", e)
            return {"models": []}
