import base64
import json
import os
import ollama

from db_operations.business_logic.db import Session
from db_operations.business_logic.image_files_storage import ImageRepository
from vector_database.business_logic.vector_database_operations import VectorDb

class SemanticAnswer:
    def __init__(self,collection_name:str,model:str):
        self.collection_name = collection_name
        self.model=model
        base_url = os.getenv("OLLAMA_BASE_URL")
        # Docker: belirli host ile Client; Lokal: module-level fonksiyon
        self._ollama = ollama.Client(host=base_url) if base_url else ollama



    def _get_semantic_result(self,query:str):
        result=VectorDb(self.collection_name).similarity_search(query=query)
        semantic_result=[{"chunk":item.page_content,
                          "doc_name":item.metadata["document_name"],
                          "page_num":item.metadata["page_number"],
                          "has_image":item.metadata["has_image"]}
                         for item in result]

        return semantic_result


    def _get_images(self,images):
        images_desc=ImageRepository(Session).get_images_to_db(images)
        return images_desc


    def _get_rag_result(self, query):

        semantic_results = self._get_semantic_result(query)

        chunks=[]
        images=[]
        encoded_images=[]
        for semantic_result in semantic_results:

            if semantic_result["chunk"]:
                chunks.append(semantic_result["chunk"])

            if semantic_result["has_image"]:
                images.append(str(semantic_result["doc_name"])+"_p"+str(semantic_result["page_num"])+"_")

        if images:
            images_res=self._get_images(images)
            image_list=[item["image"] for item in images_res]

            encoded_images=[
                {"data":base64.b64encode(img).decode(), "mime":"image/png"} for img in image_list
            ]
            print(len(images))
            if len(images_res) > 1:
                image_info = "Additionally, the images below illustrate this: " + str([item["context"] for item in images_res])
                chunks.append(image_info)
            elif len(images_res) == 1:
                image_info = "Additionally, the image below illustrates this: " + str(images_res[0]["context"])
                chunks.append(image_info)

        docs={item["doc_name"] for item in semantic_results}
        return chunks,encoded_images,docs

    def rag_llm_results(self,query):


        if not self.collection_name:
            response = self._ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": query}])

            return {"llm_response": response["message"]["content"],
                    "images": ""}

        chunks, image_list,docs = self._get_rag_result(query)

        with open("prompts.json", 'r', encoding="utf-8") as f:
            prompts = json.load(f)

        SYSTEM_PROMPT = prompts["SYSTEM_PROMPT"]
        USER_PROMPT = prompts["USER_PROMPT"]
        USER_PROMPT = USER_PROMPT.replace("{query}", str(query)).replace("{chunks}", str(chunks))

        print(USER_PROMPT)

        response = self._ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={
                "temperature": 0.25,
                "top_p": 0.9,
                "repeat_penalty": 1.15,
                "num_ctx": 8192,
                "num_predict": 768,
            }
        )
        return {"llm_response": response["message"]["content"],
                "images": image_list,
                "docs":docs}
