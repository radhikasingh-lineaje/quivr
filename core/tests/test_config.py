from quivr_core.rag.entities.config import (
    DefaultModelSuppliers,
    LLMEndpointConfig,
    LLMModelConfig,
    RetrievalConfig,
)


def test_default_llm_config():
    config = LLMEndpointConfig()

    assert (
        config.model_dump()
        == LLMEndpointConfig(
            model="gpt-4o",
            llm_base_url=None,
            llm_api_key=None,
            max_context_tokens=2000,
            max_output_tokens=2000,
            temperature=0.7,
            streaming=True,
        ).model_dump()
    )


def test_default_retrievalconfig():
    config = RetrievalConfig()

    assert config.max_files == 20
    assert config.prompt is None
    print("\n\n", config.llm_config, "\n\n")
    print("\n\n", LLMEndpointConfig(), "\n\n")
    assert config.llm_config == LLMEndpointConfig()


def test_ollama_supplier_from_model_name():
    assert (
        LLMModelConfig.get_supplier_by_model_name("llama3")
        == DefaultModelSuppliers.OLLAMA
    )
    assert (
        LLMModelConfig.get_supplier_by_model_name("llama3.2")
        == DefaultModelSuppliers.OLLAMA
    )
    assert (
        LLMModelConfig.get_supplier_by_model_name("llama3.2:3b")
        == DefaultModelSuppliers.OLLAMA
    )


def test_retrieval_config_uses_ollama_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OLLAMA_CHAT_MODEL", "llama3")
    yaml_path = tmp_path / "rag.yaml"
    yaml_path.write_text(
        "max_history: 10\n"
        "llm_config:\n"
        "  max_output_tokens: 4096\n"
        "  temperature: 0.7\n"
    )
    config = RetrievalConfig.from_yaml(yaml_path)
    assert config.llm_config.supplier == DefaultModelSuppliers.OLLAMA
    assert config.llm_config.model == "llama3"
