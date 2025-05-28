import os
import argparse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv


load_dotenv()


def build_index_from_directory(directory_path: str, persist_dir: str):
    """从目录中构建索引"""

    os.makedirs(persist_dir, exist_ok=True)

    # 加载文档
    print(f"从目录 {directory_path} 中加载文档...")
    documents = SimpleDirectoryReader(directory_path).load_data()
    print(f"加载 {len(documents)} 个文档")

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=100)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"文档被分割成 {len(nodes)} 个节点")

    print("开始构建索引...")
    index = VectorStoreIndex(nodes, show_progress=True)

    print(f"将索引保存到 {persist_dir} 目录...")
    index.storage_context.persist(persist_dir=persist_dir)

    print("索引构建完成")

    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建文档索引")
    parser.add_argument("--dir", type=str, default="../data", help="文档目录路径")
    parser.add_argument("--persist_dir", type=str, default="../storage", help="索引存储路径")

    args = parser.parse_args()

    build_index_from_directory(args.dir, args.persist_dir)