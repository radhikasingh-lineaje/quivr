import logging
import os

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from quivr_core.rag.entities.config import (
    DefaultModelSuppliers,
    LLMEndpointConfig,
    get_ollama_base_url,
)
from quivr_core.llm import LLMEndpoint

logger = logging.getLogger("quivr_core")

DEFAULT_OLLAMA_CHAT_MODEL = "llama3.2"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"


async def build_default_vectordb(
    docs: list[Document], embedder: Embeddings
) -> VectorStore:
    try:
        from langchain_community.vectorstores import FAISS

        logger.debug("Using Faiss-CPU as vector store.")
        # TODO(@aminediro) : embedding call is usually not concurrent for all documents but waits
        if len(docs) > 0:
            vector_db = await FAISS.afrom_documents(documents=docs, embedding=embedder)
            return vector_db
        else:
            raise ValueError("can't initialize brain without documents")

    except ImportError as e:
        raise ImportError(
            "Please provide a valid vector store or install quivr-core['base'] package for using the default one."
        ) from e


def using_ollama() -> bool:
    return bool(os.getenv("OLLAMA_CHAT_MODEL") or os.getenv("OLLAMA_EMBED_MODEL"))


def default_embedder() -> Embeddings:
    if using_ollama():
        try:
            from langchain_ollama import OllamaEmbeddings

            model = os.getenv("OLLAMA_EMBED_MODEL") or DEFAULT_OLLAMA_EMBED_MODEL
            logger.debug("Loaded OllamaEmbeddings as default embedder for brain")
            kwargs: dict = {"model": model}
            base_url = get_ollama_base_url()
            if base_url:
                kwargs["base_url"] = base_url
            return OllamaEmbeddings(**kwargs)
        except ImportError as e:
            raise ImportError(
                "Please install langchain-ollama to use Ollama embeddings."
            ) from e

    try:
        from langchain_openai import OpenAIEmbeddings

        logger.debug("Loaded OpenAIEmbeddings as default LLM for brain")
        embedder = OpenAIEmbeddings()
        return embedder
    except ImportError as e:
        raise ImportError(
            "Please provide a valid Embedder or install quivr-core['base'] package for using the defaultone."
        ) from e


def default_llm() -> LLMEndpoint:
    try:
        if using_ollama():
            model = os.getenv("OLLAMA_CHAT_MODEL") or DEFAULT_OLLAMA_CHAT_MODEL
            logger.debug("Loaded ChatOllama as default LLM for brain")
            return LLMEndpoint.from_config(
                LLMEndpointConfig(
                    supplier=DefaultModelSuppliers.OLLAMA,
                    model=model,
                    llm_base_url=get_ollama_base_url(),
                )
            )

        logger.debug("Loaded ChatOpenAI as default LLM for brain")
        llm = LLMEndpoint.from_config(
            LLMEndpointConfig(supplier=DefaultModelSuppliers.OPENAI, model="gpt-4o")
        )
        return llm

    except ImportError as e:
        raise ImportError(
            "Please provide a valid BaseLLM or install quivr-core['base'] package"
        ) from e
