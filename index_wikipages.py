from llama_index.readers.wikipedia import WikipediaReader
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

def create_index(topic: str):
    reader = WikipediaReader()
    docs = reader.load_data([topic])
    parser = SentenceSplitter()
    nodes = parser.get_nodes_from_documents(docs)
    index = VectorStoreIndex(nodes)
    return index