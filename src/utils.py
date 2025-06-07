import os
import uuid
import json
import datetime
import streamlit as st
from typing import Dict, Any, Optional


# 文档 ID 生成
def generate_document_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())

# 用户数据路径获取
def get_user_data_path(user_id: str, data_type: str) -> str:
    """
    获取用户特定的数据路径

    参数:
        user_id: 用户ID
        data_type: 数据类型 ("data", "output", "storage")

    返回：
        数据路径字符串
    """
    base_paths = {
        "data": "data",
        "output": "output",
        "storage": "storage",
    }

    if data_type not in base_paths:
        raise ValueError(f"无效的数据类型：{data_type}")
    
    path = os.path.join(base_paths[data_type], user_id)
    os.makedirs(path, exist_ok=True)
    return path

# 文档状态更新
def update_document_status(user_id: str, doc_id: str, status: str) -> None:
    """
    更新文档状态

    参数：
        user_id: 用户ID
        doc_id: 文档ID
        status: 新状态
    """
    # 初始化用户文档数据
    if "documents" not in st.session_state:
        st.session_state.documents = {}

    if user_id not in st.session_state.documents:
        st.session_state.documents[user_id] = {}

    if doc_id not in st.session_state.documents[user_id]:
        st.session_state.documents[user_id][doc_id] = {}

    # 更新状态
    st.session_state.documents[user_id][doc_id]["status"] = status

    # 保存到本地以持久化
    save_document_metadata(user_id, doc_id, st.session_state.documents[user_id][doc_id])

# 保存文档元数据
def save_document_metadata(user_id: str, doc_id: str, metadata: Dict[str, Any]) -> None:
    """
    保存文档元数据到文件

    参数：
        user_id: 用户ID
        doc_id: 文档ID
        metadata: 元数据字典
    """
    # 确保目录存在
    metadata_dir = os.path.join("data", user_id, doc_id)
    os.makedirs(metadata_dir, exist_ok=True)

    # 添加时间戳
    metadata["last_updated"] = datetime.datetime.now().isoformat()

    # 保存元数据
    metadata_path = os.path.join(metadata_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
