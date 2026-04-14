import logging
from typing import Optional
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
from db_operations.business_logic.db import Session
from db_operations.business_logic.image_files_storage import ImageRepository

logger=logging.getLogger(__name__)

class VectorDb:
    EMBEDDING_MODEL = "BAAI/bge-m3"
    RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
    PERSIST_DIR = "./chroma_db"
    DEFAULT_HYBRID_WEIGHTS = [0.3, 0.7]
    DEFAULT_INITIAL_K = 20
    DEFAULT_FINAL_K = 5
    BATCH_SIZE = 500
    def __init__(self,collection_name:str,
                 embedding_model:str=EMBEDDING_MODEL,
                 reranker_model:str=RERANKER_MODEL,
                 persist_dir:str=PERSIST_DIR):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device":"cuda" if torch.cuda.is_available() else "cpu"},
            encode_kwargs={"normalize_embeddings":True}
            )


        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_dir
        )
        self.reranker=CrossEncoder(reranker_model)

        self._bm25_documents:list[Document]=[]
        self._bm25_retriever:Optional[BM25Retriever]=None

        self._load_existing_bm25_docs()

    def similarity_search(self,
                          query:str,
                          initial_k:int=DEFAULT_INITIAL_K,
                          final_k:int=DEFAULT_FINAL_K)->list[Document]:

        candidates=self._hybrid_retrieve(query, k=initial_k)
        if not candidates:
            return []

        reranked=self._rerank(query, candidates, top_k=final_k)
        return reranked

    def _hybrid_retrieve(self, query:str, k:int)->list[Document]:

        dense_results=self.vectorstore.similarity_search(query=query, k=k)

        if self._bm25_retriever is None:
            return dense_results

        try:
            self._bm25_retriever.k=k
            bm25_results=self._bm25_retriever.invoke(query)
        except Exception as e:
            logger.warning("BM25 retrieval failed.",e)
            return dense_results

        seen_contents:set[str]=set()
        merged:list[Document]=[]

        for doc in dense_results + bm25_results:
            content_hash=doc.page_content[:200]
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                merged.append(doc)

        return merged


    def _rerank(self, query:str, documents:list[Document], top_k:int)->list[Document]:

        if not documents:
            return []

        pairs=[(query,doc.page_content) for doc in documents]
        scores=self.reranker.predict(pairs)

        ranked=sorted(zip(documents,scores),key=lambda x:x[1],reverse=True)

        return [doc for doc, _score in ranked[:top_k]]


    def add_documents(self,documents:list[dict])->dict:
        # chunker = SemanticChunker(
        #     self.embeddings,
        #     breakpoint_threshold_type="percentile",
        #     breakpoint_threshold_amount=75
        # )

        chunker = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=100
        )

        chroma_docs:list[Document]=[]
        all_image_paths:list[str]=[]

        for document in documents:
            document_name = document["document_name"]

            for page in document["pages"]:
                logger.info("Processing page %d / %d", page["page_number"])
                page_number = page["page_number"]
                content = page["content"]

                if not content or not content.strip():
                    continue

                try:
                    chunks = chunker.split_text(content)
                    print(len(chunks))
                    #chunks=chunker.create_documents([content])
                except Exception as e:
                    logger.warning("Semantic chunking failed for %s p.%s, skipping:%s", document_name,page_number,e)
                    continue


                for idx, chunk in enumerate(chunks):
                    print(chunk)
                    enriched_content=(
                        #f"Document: {document_name} | Page: {page_number}\n"
                        f"{chunk}"
                    )
                    image_paths=page.get("image_paths",[])
                    has_image=bool(image_paths)

                    chroma_docs.append(Document(
                        page_content=enriched_content,
                        metadata={
                            "document_name": document_name,
                            "page_number": page_number,
                            "chunk_id": idx,
                            "has_image":has_image,
                            "image_paths":str(image_paths) if image_paths else ""
                        },
                    )
                    )

                if page.get("image_paths"):
                    all_image_paths.extend(page["image_paths"])

        if all_image_paths:
            try:
                ImageRepository(Session).add_image_to_db(all_image_paths)

            except Exception as e:
                logger.error("Image DB insert failed: %s",e,exc_info=True)

        if chroma_docs:
            self._batch_add_to_chroma(chroma_docs)
            self._update_bm25_index(chroma_docs)

        return {
            "status":"success",
            "chunks_added": len(chroma_docs),
            "images_added": len(all_image_paths),
        }

    def _batch_add_to_chroma(self, documents:list[Document])->None:

        for i in range(0, len(documents), self.BATCH_SIZE):
            batch=documents[i:i+self.BATCH_SIZE]
            self.vectorstore.add_documents(batch)
            logger.info("Indexed batch %d-%d / %d",i,i+len(batch),len(documents))

    def _update_bm25_index(self, new_docs:list[Document])->None:

        self._bm25_documents.extend(new_docs)

        if self._bm25_documents:
            self._bm25_retriever=BM25Retriever.from_documents(self._bm25_documents)


    def _load_existing_bm25_docs(self)->None:

        try:
            collection=self.vectorstore._collection
            existing=collection.get(limit=10000,include=["documents","metadatas"])

            if existing and existing["documents"]:
                for content,metadata in zip(existing["documents"],existing["metadatas"]):
                    if content:
                        self._bm25_documents.append(Document(
                            page_content=content,
                            metadata=metadata or {}
                        ))

                if self._bm25_documents:
                    self._bm25_retriever=BM25Retriever.from_documents(self._bm25_documents)
                    logger.info("Loaded %d existing doc into BM25 index",len(self._bm25_documents))

        except Exception as e:
            logger.warning("Could not load existing BM25 index: %s",e)


