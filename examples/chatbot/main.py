import os
import tempfile
from uuid import uuid4

import chainlit as cl
from quivr_core import Brain, register_processor
from quivr_core.files.file import FileExtension
from quivr_core.llm import LLMEndpoint
from quivr_core.processor.implementations.simple_txt_processor import SimpleTxtProcessor
from quivr_core.rag.entities.config import LLMEndpointConfig, RetrievalConfig

# MegaParse is registered first for .txt but needs a NATS server. This example
# only accepts plain text, so use the local processor instead.
register_processor(FileExtension.txt, SimpleTxtProcessor, override=True)


def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"


def using_ollama() -> bool:
    return bool(os.getenv("OLLAMA_CHAT_MODEL") or os.getenv("OLLAMA_EMBED_MODEL"))


def build_ollama_llm_and_embedder():
    try:
        from langchain_ollama import ChatOllama, OllamaEmbeddings
    except ImportError:
        from langchain_community.chat_models import ChatOllama
        from langchain_community.embeddings import OllamaEmbeddings

    chat_model = os.getenv("OLLAMA_CHAT_MODEL") or "llama3.2"
    embed_model = os.getenv("OLLAMA_EMBED_MODEL") or "nomic-embed-text"
    base_url = _ollama_base_url()

    llm_config = LLMEndpointConfig(
        model=chat_model,
        llm_base_url=base_url,
        llm_api_key=os.getenv("OLLAMA_API_KEY") or "ollama",
    )
    chat = ChatOllama(
        model=chat_model,
        base_url=base_url,
        temperature=llm_config.temperature,
    )
    llm = LLMEndpoint(llm=chat, llm_config=llm_config)
    llm._supports_func_calling = False
    embedder = OllamaEmbeddings(model=embed_model, base_url=base_url)
    return llm, embedder


@cl.on_chat_start
async def on_chat_start():
    files = None

    # Wait for the user to upload a file
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload a text .txt file to begin!",
            accept=["text/plain"],
            max_size_mb=20,
            timeout=180,
        ).send()

    file = files[0]

    backend = "Ollama" if using_ollama() else "OpenAI"
    msg = cl.Message(content=f"Processing `{file.name}` with {backend}...")
    await msg.send()

    with open(file.path, "r", encoding="utf-8") as f:
        text = f.read()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=file.name, delete=False
    ) as temp_file:
        temp_file.write(text)
        temp_file.flush()
        temp_file_path = temp_file.name

    brain_kwargs = {
        "name": "user_brain",
        "file_paths": [temp_file_path],
    }
    if using_ollama():
        llm, embedder = build_ollama_llm_and_embedder()
        brain_kwargs["llm"] = llm
        brain_kwargs["embedder"] = embedder

    brain = Brain.from_files(**brain_kwargs)

    # Store the file path in the session
    cl.user_session.set("file_path", temp_file_path)

    # Let the user know that the system is ready
    msg.content = f"Processing `{file.name}` done. You can now ask questions!"
    await msg.update()

    cl.user_session.set("brain", brain)


@cl.on_message
async def main(message: cl.Message):
    brain = cl.user_session.get("brain")  # type: Brain
    if brain is None:
        await cl.Message(content="Please upload a file first.").send()
        return

    path_config = "basic_rag_workflow.yaml"
    retrieval_config = RetrievalConfig.from_yaml(path_config)
    # Keep the brain's LLM (Ollama or OpenAI) instead of the YAML OpenAI default
    retrieval_config.llm_config = brain.llm.get_config()

    # Prepare the message for streaming
    msg = cl.Message(content="", elements=[])
    await msg.send()

    saved_sources = set()
    saved_sources_complete = []
    elements = []

    # Use the ask_stream method for streaming responses
    async for chunk in brain.ask_streaming(
        message.content,
        run_id=uuid4(),
        retrieval_config=retrieval_config,
    ):
        await msg.stream_token(chunk.answer)
        for source in chunk.metadata.sources:
            if source.page_content not in saved_sources:
                saved_sources.add(source.page_content)
                saved_sources_complete.append(source)
                print(source)
                elements.append(cl.Text(name=source.metadata["original_file_name"], content=source.page_content, display="side"))

    
    await msg.send()
    sources = ""
    for source in saved_sources_complete:
        sources += f"- {source.metadata['original_file_name']}\n"
    msg.elements = elements
    msg.content = msg.content + f"\n\nSources:\n{sources}"
    await msg.update()
