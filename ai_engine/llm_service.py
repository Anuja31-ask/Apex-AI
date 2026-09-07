# ai_engine/llm_service.py
from langchain_ollama import ChatOllama

def get_local_llm():
    """
    Returns an instance of ChatOllama pointing to the local Qwen2.5-VL model.
    Guarantees local execution with zero cloud egress.
    """
    return ChatOllama(
        model="qwen2.5vl:7b",
        base_url="http://localhost:11434",
        temperature=0.1
    )

if __name__ == "__main__":
    # Test script to verify local LLM connection
    print("Testing connection to local Ollama server...")
    llm = get_local_llm()
    response = llm.invoke("Confirm system operational status in 1 sentence.")
    print("\nLocal LLM Response:", response.content)