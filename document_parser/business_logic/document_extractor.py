import base64
import json
import os
import requests  # URL'den resim indirmek için gerekli
from pathlib import Path
from typing import List, Dict, Optional
from io import BytesIO  # six.BytesIO yerine standart io kullanmak daha modern

import torch
from PIL import Image
from docx2pdf import convert

# Docling Imports
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat


class PageBasedExtractor:
    def __init__(self,UPLOAD_DIR):
        self.SAVE_DIR = Path(rf"{UPLOAD_DIR}/results")
        self.IMAGE_DIR = self.SAVE_DIR / "images"
        self.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = True
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.images_scale = 2.0
        self.pipeline_options.generate_picture_images = True
        self.pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        self.device = AcceleratorDevice.CUDA if torch.cuda.is_available() else AcceleratorDevice.CPU
        self.pipeline_options.accelerator_options = AcceleratorOptions(num_threads=8, device=self.device)
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.PPTX
            ],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options),
            }
        )

    def _save_image(self, picture_item, page_no, base_name, img_index):

        filename = f"{base_name}_p{page_no}_img{img_index}.png"
        save_path = self.IMAGE_DIR / filename
        real_image = None
        if hasattr(picture_item, "image") and picture_item.image is not None:
            if hasattr(picture_item.image, "pil_image") and picture_item.image.pil_image is not None:
                real_image = picture_item.image.pil_image

        if real_image:
            try:
                real_image.save(save_path)
                return str(save_path)
            except Exception as e:
                print(f"PIL Image (.pil_image) kaydetme hatası: {e}")

        uri = None
        if hasattr(picture_item, "image") and picture_item.image and hasattr(picture_item.image, "uri"):
            uri = picture_item.image.uri
        elif hasattr(picture_item, "uri"):
            uri = picture_item.uri

        if not uri:
            return None

        uri_str = str(uri)

        try:

            if "base64," in uri_str:
                image_bytes = base64.b64decode(uri_str.split("base64,")[1])
                real_image = Image.open(BytesIO(image_bytes))

            elif uri_str.startswith("http"):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(uri_str, headers=headers, timeout=10)
                if response.status_code == 200:
                    real_image = Image.open(BytesIO(response.content))
                else:
                    print(f"Resim indirilemedi (Status {response.status_code}): {uri_str}")
                    return None

            if real_image:
                real_image.save(save_path)
                return str(save_path)

        except Exception as e:
            print(f"Resim işleme hatası ({uri_str[:30]}...): {e}")
            return None

        return None

    def process_document(self, file_paths: List):

        docs=[]
        for file_path in file_paths:
            is_url = file_path.startswith("http")

            if is_url:
                base_name = file_path.split("/")[-1]
                if not base_name: base_name = "web_page"
                base_name = "".join([c for c in base_name if c.isalnum() or c in ('-', '_')])
            else:
                file_path = str(file_path)
                base_name = os.path.splitext(os.path.basename(file_path))[0]

                if file_path.lower().endswith(".docx"):
                    convert(file_path)
                    file_path = file_path.replace(".docx", ".pdf")

            print(f"İşleniyor: {base_name}")

            result = self.converter.convert(file_path)
            doc = result.document

            pages_data = {}

            if hasattr(doc, "pictures"):
                for i, pic in enumerate(doc.pictures):
                    page_no = 1
                    if hasattr(pic, "prov") and pic.prov:
                        page_no = pic.prov[0].page_no

                    if page_no not in pages_data:
                        pages_data[page_no] = {"texts": [], "images": []}

                    img_path = self._save_image(pic, page_no, base_name, i)
                    if img_path:
                        pages_data[page_no]["images"].append(img_path)

            last_page = 1
            for item, level in doc.iterate_items():
                if not hasattr(item, "text") or not item.text.strip():
                    continue

                if hasattr(item, "prov") and item.prov:
                    page_no = item.prov[0].page_no
                    last_page = page_no
                else:
                    page_no = last_page

                if page_no not in pages_data:
                    pages_data[page_no] = {"texts": [], "images": []}

                pages_data[page_no]["texts"].append(item.text.strip())

            pages_output = []
            all_page_texts = []

            for p_no in sorted(pages_data.keys()):
                p_content = pages_data[p_no]
                combined_text = "\n".join(p_content["texts"])

                all_page_texts.append(combined_text)

                page_obj = {
                    "page_number": p_no,
                    "content": combined_text,
                    "image_paths": p_content["images"],
                    "token_count_approx": len(combined_text.split())
                }
                pages_output.append(page_obj)

            full_text = "\n\n".join(all_page_texts)

            final_output = {
                "document_name": base_name,
                "full_text": full_text,
                "total_pages": len(pages_output),
                "pages": pages_output
            }

            docs.append(final_output)

        # # JSON Kaydet
        # out_path = self.SAVE_DIR / f"{base_name}_rag_ready.json"
        # with open(out_path, "w", encoding="utf-8") as f:
        #     json.dump(final_output, f, ensure_ascii=False, indent=2)
        #
        # print(f"Bitti! RAG JSON şurada: {out_path}")
        return docs
