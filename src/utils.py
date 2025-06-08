import os
import uuid
import json
import datetime
import streamlit as st
from typing import Dict, Any, Optional, List


# 文档 ID 生成
def generate_document_id() -> str:
    """生成唯一的文档ID"""
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
    
    参数:
        user_id: 用户ID
        doc_id: 文档ID
        status: 新状态 (上传中、处理中、处理完成、索引构建中、索引完成)
    """
    # 获取现有元数据（如果存在）
    metadata = get_document_metadata(user_id, doc_id) or {}
    
    # 更新状态和时间戳
    metadata["status"] = status
    metadata["updated_at"] = datetime.datetime.now().isoformat()
    
    # 更新会话状态
    if "documents" not in st.session_state:
        st.session_state.documents = {}
    
    if user_id not in st.session_state.documents:
        st.session_state.documents[user_id] = {}
    
    st.session_state.documents[user_id][doc_id] = metadata
    
    # 保存更新后的完整元数据
    save_document_metadata(user_id, doc_id, metadata)

# 保存文档元数据
def save_document_metadata(user_id: str, doc_id: str, metadata: Dict[str, Any]) -> None:
    """
    保存文档元数据到文件
    
    参数:
        user_id: 用户ID
        doc_id: 文档ID
        metadata: 元数据字典 (包含filename, status, upload_time等)
    """
    # 确保目录存在
    metadata_dir = os.path.join("data", user_id, doc_id)
    os.makedirs(metadata_dir, exist_ok=True)
    # 添加最后更新时间
    if "updated_at" not in metadata:
        metadata["updated_at"] = datetime.datetime.now().isoformat()
    
    # 保存元数据
    metadata_path = os.path.join(metadata_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

# 获取文档元数据
def get_document_metadata(user_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    获取文档元数据
    
    参数:
        user_id: 用户ID
        doc_id: 文档ID
        
    返回:
        元数据字典或None（如果不存在）
    """
    metadata_path = os.path.join("data", user_id, doc_id, "metadata.json")
    
    if not os.path.exists(metadata_path):
        return None
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

# 获取用户所有文档
def get_user_documents(user_id: str) -> List[Dict[str, Any]]:
    """
    获取用户的所有文档
    
    参数:
        user_id: 用户ID
        
    返回:
        文档元数据列表
    """
    user_dir = os.path.join("data", user_id)
    
    if not os.path.exists(user_dir):
        return []
    
    documents = []
    
    # 遍历用户目录下的所有子目录（每个子目录代表一个文档）
    for doc_id in os.listdir(user_dir):
        doc_dir = os.path.join(user_dir, doc_id)
        
        if os.path.isdir(doc_dir):
            # 获取文档元数据
            metadata = get_document_metadata(user_id, doc_id)
            
            if metadata:
                metadata["doc_id"] = doc_id
                documents.append(metadata)
            else:
                # 如果元数据不存在，创建基本信息
                basic_info = {
                    "doc_id": doc_id,
                    "filename": "未知文件名",
                    "status": "未知状态",
                    "upload_time": "未知"
                }
                documents.append(basic_info)
    
    # 按上传时间排序（最新的在前）
    documents.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
    
    return documents

# 检查文档是否已处理
def is_document_processed(user_id: str, doc_id: str) -> bool:
    """
    检查文档是否已处理完成
    
    参数:
        user_id: 用户ID
        doc_id: 文档ID
        
    返回:
        是否已处理
    """
    metadata = get_document_metadata(user_id, doc_id)
    
    if not metadata:
        return False
    
    return metadata.get("status") == "处理完成"

# 检查文档是否已建索引
def is_document_indexed(user_id: str, doc_id: str) -> bool:
    """
    检查文档是否已建索引
    
    参数:
        user_id: 用户ID
        doc_id: 文档ID
        
    返回:
        是否已建索引
    """
    metadata = get_document_metadata(user_id, doc_id)
    
    if not metadata:
        return False
    
    return metadata.get("indexed", False)

# 更新文档索引状态
def update_document_index_status(user_id: str, doc_id: str, indexed: bool) -> None:
    """
    更新文档索引状态
    
    参数:
        user_id: 用户ID
        doc_id: 文档ID
        indexed: 是否已建索引
    """
    metadata = get_document_metadata(user_id, doc_id)
    
    if not metadata:
        metadata = {}
    
    metadata["indexed"] = indexed
    
    if indexed:
        metadata["index_time"] = datetime.datetime.now().isoformat()
    
    save_document_metadata(user_id, doc_id, metadata)
