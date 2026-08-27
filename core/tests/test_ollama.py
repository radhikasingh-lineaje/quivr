from langchain_ollama import ChatOllama, OllamaEmbeddings

from quivr_core.brain.brain_defaults import default_embedder, default_llm, using_ollama
from quivr_core.rag.entities.config import DefaultModelSuppliers


def test_using_ollama_false_by_default(monkeypatch):
    monkeypatch.delenv("OLLAMA_CHAT_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_EMBED_MODEL", raising=False)
    assert using_ollama() is False


def test_default_llm_uses_ollama_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_CHAT_MODEL", "llama3")
    monkeypatch.delenv("OLLAMA_EMBED_MODEL", raising=False)
    llm = default_llm()
    assert isinstance(llm._llm, ChatOllama)
    assert llm.get_config().supplier == DefaultModelSuppliers.OLLAMA
    assert llm.get_config().model == "llama3"


def test_default_embedder_uses_ollama_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    monkeypatch.delenv("OLLAMA_CHAT_MODEL", raising=False)
    embedder = default_embedder()
    assert isinstance(embedder, OllamaEmbeddings)
    assert embedder.model == "nomic-embed-text"


def test_default_llm_falls_back_to_llama32_when_only_embed_set(monkeypatch):
    monkeypatch.setenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    monkeypatch.delenv("OLLAMA_CHAT_MODEL", raising=False)
    llm = default_llm()
    assert llm.get_config().model == "llama3.2"
    assert llm.get_config().supplier == DefaultModelSuppliers.OLLAMA
