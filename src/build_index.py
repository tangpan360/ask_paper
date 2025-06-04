import os
import argparse
import re
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document, ListIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from dotenv import load_dotenv


load_dotenv()


def build_index_from_directory(directory_path: str, full_text_persist_dir: str, source_persist_dir: str):
    """从目录中构建索引，创建全文索引和源文本索引"""

    os.makedirs(full_text_persist_dir, exist_ok=True)
    os.makedirs(source_persist_dir, exist_ok=True)

    # 加载单篇文章
    print(f"从目录 {directory_path} 中加载文章...")
    documents = SimpleDirectoryReader(directory_path).load_data()
    print(f"加载 {len(documents)} 个文档")

    # 创建全文索引（不分割，用于传递给大模型进行问答）
    full_text_parser = SentenceSplitter(chunk_size=1000000, chunk_overlap=50)

    # 获取完整文章内容的单个节点
    full_text_nodes = full_text_parser.get_nodes_from_documents(documents)

    # 创建全文索引
    full_text_index = ListIndex(full_text_nodes)

    # 保存全文索引
    full_text_index.storage_context.persist(persist_dir=full_text_persist_dir)

    print(f"全文索引已保存到 {full_text_persist_dir}")

    # 创建源文本索引（分割成小块，用于匹配答案来源）
    source_parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)
    source_nodes = source_parser.get_nodes_from_documents(documents)

    # 创建源文本索引
    source_index = ListIndex(source_nodes)

    # 保存源文本索引
    source_index.storage_context.persist(persist_dir=source_persist_dir)

    print(f"源文本索引已保存到 {source_persist_dir}")

    return full_text_index, source_index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建文档索引")
    parser.add_argument("--dir", type=str, default="../data_2", help="文档目录路径")
    parser.add_argument("--full_text_persist_dir", type=str, default="../storage/full_text", help="全文索引存储路径")
    parser.add_argument("--source_persist_dir", type=str, default="../storage/source", help="源文本索引存储路径")

    args = parser.parse_args()

    build_index_from_directory(args.dir, args.full_text_persist_dir, args.source_persist_dir)
