"""Prototype LlamaIndex RetrieverAgent integration."""

from llama_index.agent import RetrieverAgent
from llama_index import VectorStoreIndex

PERSONAL = VectorStoreIndex.from_weaviate("Personal")
PAY = VectorStoreIndex.from_weaviate("PayReady")
RX = VectorStoreIndex.from_weaviate("ParagonRX")

agent = RetrieverAgent(indices=[PERSONAL, PAY, RX], llm="gpt-4o")


def query(payload: dict) -> dict:
    return agent.chat(payload["query"])
