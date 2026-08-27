# Copyright (c) Lineaje, Inc. All rights reserved.
# Lineaje UnifAI guardrail  version=2.0.0-alpha
def _lineaje_load_gr_client():
    """Lineaje-added: load gr_stub_client.py without a pip dependency."""
    import sys as _s, importlib.util as _ilu
    from pathlib import Path as _P
    n = "_lineaje_gr_stub_client"
    if n in _s.modules: return _s.modules[n]
    h = _P(__file__).resolve().parent
    _cand = next((d / "gr_stub_client.py" for d in [h, *h.parents][:8] if (d / "gr_stub_client.py").is_file()), h / "gr_stub_client.py")
    _spec = _ilu.spec_from_file_location(n, _cand)
    _s.modules[n] = _m = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_m); return _m

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
            _lineaje_payload = "Loaded ChatOllama as default LLM for brain"
            # LINEAJE: enforce() `_lineaje_payload` at agent->log log_emit — scan flagged AI_DAT_SEC_029 (Enforce decision logging, audit trail, and forensic readiness for AI-driven actions.); AI_DAT_SEC_030 (Enforce minimum six-month log retention for high-risk AI systems). Mask/block; do not remove without review. site_id='site:sha256:6ea458ce1e0c2c5557d594f9e5800922fd0ec39eabfc26602b0edf70d5b178e8'
            _gr_client = _lineaje_load_gr_client()
            _gr_site = _gr_client.SiteDescriptor(site_id='site:sha256:6ea458ce1e0c2c5557d594f9e5800922fd0ec39eabfc26602b0edf70d5b178e8', phase='log_emit', boundary={'source': 'log', 'sink': 'log'}, candidate_policies=[{'policy_id': 'AI_DAT_SEC_010', 'guardrail_id': 'Mask PII in Logs', 'policy_version': '2026.08.1'}], fail_mode='BLOCK', source_type='agent', destination_type='log')
            _lineaje_payload = _gr_client.enforce(_gr_site, _lineaje_payload, content_type='application/json')
            logger.debug(_lineaje_payload)
            return LLMEndpoint.from_config(
                LLMEndpointConfig(
                    supplier=DefaultModelSuppliers.OLLAMA,
                    model=model,
                    llm_base_url=get_ollama_base_url(),
                )
            )

        _lineaje_payload = "Loaded ChatOpenAI as default LLM for brain"
        # LINEAJE: enforce() `_lineaje_payload` at agent->log log_emit — scan flagged AI_DAT_SEC_029 (Enforce decision logging, audit trail, and forensic readiness for AI-driven actions.); AI_DAT_SEC_030 (Enforce minimum six-month log retention for high-risk AI systems). Mask/block; do not remove without review. site_id='site:sha256:0706edc29bc1b6d5e09aef2fffcf68a2be091b47ee3f310ed19290d6f7d5c393'
        _gr_client = _lineaje_load_gr_client()
        _gr_site = _gr_client.SiteDescriptor(site_id='site:sha256:0706edc29bc1b6d5e09aef2fffcf68a2be091b47ee3f310ed19290d6f7d5c393', phase='log_emit', boundary={'source': 'log', 'sink': 'log'}, candidate_policies=[{'policy_id': 'AI_DAT_SEC_010', 'guardrail_id': 'Mask PII in Logs', 'policy_version': '2026.08.1'}], fail_mode='BLOCK', source_type='agent', destination_type='log')
        _lineaje_payload = _gr_client.enforce(_gr_site, _lineaje_payload, content_type='application/json')
        logger.debug(_lineaje_payload)
        llm = LLMEndpoint.from_config(
            LLMEndpointConfig(supplier=DefaultModelSuppliers.OPENAI, model="gpt-4o")
        )
        return llm

    except ImportError as e:
        raise ImportError(
            "Please provide a valid BaseLLM or install quivr-core['base'] package"
        ) from e
