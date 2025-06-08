import os
import sys
import shutil
import datetime
import argparse
import re
import streamlit as st

from typing import List, Dict, Any, Tuple
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Document,
    ListIndex,
    Settings,
    )
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from dotenv import load_dotenv

from src.utils import (
    get_document_metadata,
    update_document_status,
    update_document_index_status,
    is_document_processed,
    )
from src.auth import get_user_data_path

load_dotenv("../.env")


Settings.embed_model = DashScopeEmbedding(
    model="text-embedding-v3",
    api_key=os.getenv("ALI_API_KEY"),
    api_base=os.getenv("ALI_API_BASE"),
)

def get_index_storage_path(user_id: str, doc_id: str) -> Tuple[str, str]:
    """
    获取索引存储路径

    参数：
        user_id: 用户ID
        doc_id: 文档ID

    返回：
        (全文索引路径, 源文本索引路径)
    """
    # 获取用户存储目录
    user_storage_dir = get_user_data_path(user_id, "storage")

    # 创建文档存储目录
    doc_storage_dir = os.path.join(user_storage_dir, doc_id)
    os.makedirs(doc_storage_dir, exist_ok=True)

    # 创建全文索引和源文本索引目录
    full_text_dir = os.path.join(doc_storage_dir, "full_text")
    source_dir = os.path.join(doc_storage_dir, "source")

    os.makedirs(full_text_dir, exist_ok=True)
    os.makedirs(source_dir, exist_ok=True)

    return full_text_dir, source_dir

# def build_index_from_directory(directory_path: str, full_text_persist_dir: str, source_persist_dir: str):
#     """从目录中构建索引，创建全文索引和源文本索引"""

#     os.makedirs(full_text_persist_dir, exist_ok=True)
#     os.makedirs(source_persist_dir, exist_ok=True)

#     # 加载单篇文章
#     print(f"从目录 {directory_path} 中加载文章...")
#     documents = SimpleDirectoryReader(directory_path).load_data()
#     print(f"加载 {len(documents)} 个文档")

#     # 创建全文索引（不分割，用于传递给大模型进行问答）
#     full_text_parser = SentenceSplitter(chunk_size=1000000, chunk_overlap=50)

#     # 获取完整文章内容的单个节点
#     full_text_nodes = full_text_parser.get_nodes_from_documents(documents)

#     # 创建全文索引
#     full_text_index = ListIndex(full_text_nodes)

#     # 保存全文索引
#     full_text_index.storage_context.persist(persist_dir=full_text_persist_dir)

#     print(f"全文索引已保存到 {full_text_persist_dir}")

#     # 创建源文本索引（分割成小块，用于匹配答案来源）
#     source_parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)
#     source_nodes = source_parser.get_nodes_from_documents(documents)

#     # 创建源文本索引
#     source_index = ListIndex(source_nodes)

#     # 保存源文本索引
#     source_index.storage_context.persist(persist_dir=source_persist_dir)

#     print(f"源文本索引已保存到 {source_persist_dir}")

#     return full_text_index, source_index

def build_index_for_document(user_id: str, doc_id: str, progress_callback=None) -> Tuple[bool, str]:
    """
    为特定用户的特定文档构建索引

    参数：
        user_id: 用户ID
        doc_id: 文档ID
        progress_callback: 进程回调函数

    返回：
        (是否成功, 结果消息)
    """
    try:
        # 检查文档是否已处理
        if not is_document_processed(user_id, doc_id):
            return False, "文档尚未处理完成，无法构建索引"

        # 获取文档元数据
        metadata = get_document_metadata(user_id, doc_id)
        if not metadata:
            return False, "无法获取文档元数据" 
        
        # 获取markdown文件路径
        from src.pdf_processor import get_markdown_content
        success, markdown_content = get_markdown_content(user_id, doc_id)

        if not success:
            return False, f"获取文档内容失败: {markdown_content}"
        
        # 更新文档状态为索引构建中
        update_document_status(user_id, doc_id, "索引构建中")
        
        # 创建临时文件保存markdown内容
        if progress_callback:
            progress_callback("准备文档内容...", 10)

        # 获取索引存储路径
        full_text_dir, source_dir = get_index_storage_path(user_id, doc_id)

        # 创建临时目录存放markdown文件
        import tempfile
        temp_dir = tempfile.mkdtemp()
        try:
            # 将markdown内容写入临时文件
            temp_file_path = os.path.join(temp_dir, f"{doc_id}.md")
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            if progress_callback:
                progress_callback("加载文档...", 30)

            # 加载文档
            documents = SimpleDirectoryReader(temp_dir).load_data()

            if not documents:
                return False, "无法加载文档内容"
            
            # 创建全文索引（不分割，用于传递给大模型进行问答）
            if progress_callback:
                progress_callback("构建全文索引...", 50)

            full_text_parser = SentenceSplitter(chunk_size=1000000, chunk_overlap=50)
            full_text_nodes = full_text_parser.get_nodes_from_documents(documents)
            full_text_index = ListIndex(full_text_nodes)

            # 保存全文索引
            full_text_index.storage_context.persist(persist_dir=full_text_dir)

            if progress_callback:
                progress_callback("构建源文本索引...", 70)

            # 创建源文本索引（分割成小块，用于匹配答案来源）
            source_parser = SentenceSplitter(chunk_size=512, chunk_overlap=100)
            source_nodes = source_parser.get_nodes_from_documents(documents)
            source_index = ListIndex(source_nodes)

            # 保存源文本索引
            source_index.storage_context.persist(persist_dir=source_dir)

            if progress_callback:
                progress_callback("完成索引构建", 100)

            # 更新文档状态为索引完成
            update_document_status(user_id, doc_id, "处理完成")
            update_document_index_status(user_id, doc_id, True)

            return True, "索引构建成功"
        
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)

    except Exception as e:
        # 更新文档状态为索引构建失败
        update_document_status(user_id, doc_id, "索引构建失败")
        update_document_index_status(user_id, doc_id, False)

        return False, f"索引构建失败: {str(e)}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建文档索引")
    parser.add_argument("--dir", type=str, default="../data_2", help="文档目录路径")
    parser.add_argument("--full_text_persist_dir", type=str, default="../storage/full_text", help="全文索引存储路径")
    parser.add_argument("--source_persist_dir", type=str, default="../storage/source", help="源文本索引存储路径")

    args = parser.parse_args()

    build_index_from_directory(args.dir, args.full_text_persist_dir, args.source_persist_dir)
