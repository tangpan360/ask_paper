import os
import shutil
import subprocess
import datetime
import time
import streamlit as st
from typing import Dict, Any, Optional, Tuple

from src.utils import update_document_status, save_document_metadata
from src.auth import get_user_data_path

def save_pdf(user_id: str, uploaded_file: Any, doc_id: str) -> Tuple[bool, str]:
    """
    保存上传的PDF文件到用户特定目录

    参数：
        user_id: 用户ID
        uploaded_file: Streamlit上传的文件对象
        doc_id: 文档ID

    返回：
        （成功状态，文件路径或错误消息）
    """
    try:
        # 获取用户数据目录
        user_data_dir = get_user_data_path(user_id, "data")

        # 创建文档目录
        doc_dir = os.path.join(user_data_dir, doc_id)
        os.makedirs(doc_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(doc_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            # getbuffer() 方法返回上传文件的二进制内存视图(memoryview)对象，
            # 此方法可以高效地获取文件内容而无需创建额外的内存副本
            f.write(uploaded_file.getbuffer())

        # 更新文档状态和元数据
        metadata = {
            "filename": uploaded_file.name,
            "original_name": uploaded_file.name,
            "file_size": uploaded_file.size,
            "upload_time": datetime.datetime.now().isoformat(),
            "status": "已上传",
            "indexed": False,
        }
        save_document_metadata(user_id, doc_id, metadata)

        return True, file_path
    
    except Exception as e:
        return False, str(e)
    
def process_pdf_with_magic(user_id: str, pdf_path: str, doc_id: str) -> Tuple[bool, str]:
    """
    使用magid-pdf处理PDF文件

    参数：
        user_id: 用户ID
        pdf_path: PDF文件路径
        doc_id: 文档ID

    返回：
        （成功状态，处理结果或错误消息）
    """
    try:
        # 更新文档状态为处理中
        update_document_status(user_id, doc_id, "处理中")

        # 获取用户输出目录
        user_output_dir = get_user_data_path(user_id, "output")
        doc_output_dir = os.path.join(user_output_dir, doc_id)
        os.makedirs(doc_output_dir, exist_ok=True)

        # 文件名（不含路径）
        pdf_filename = os.path.basename(pdf_path)

        # 组装命令
        cmd = [
            "conda", "run", "-n", "mineru",
            "magic-pdf",
            "-p", pdf_path,
            "-o", doc_output_dir,
            "-m", "auto",
        ]

        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,  # 5分钟超时
        )

        # 检查命令是否成功
        if result.returncode != 0:
            update_document_status(user_id, doc_id, "处理失败")
            return False, f"处理失败: {result.stderr}"
        
        # 更新文档状态为处理完成
        update_document_status(user_id, doc_id, "处理完成")

        # 确定处理结果路径
        # 根据magic-pdf的输出结构，结果在 {output_dir}/{pdf_name}/auto/ 目录下
        pdf_name_without_ext = os.path.splitext(pdf_filename)[0]
        result_dir = os.path.join(doc_output_dir, pdf_name_without_ext, "auto")

        return True, result_dir
    
    except Exception as e:
        # 更新文档状态为处理失败
        update_document_status(user_id, doc_id, "处理失败")
        return False, str(e)
    
def get_markdown_content(user_id: str, doc_id: str) -> Tuple[bool, str]:
    """
    获取处理后的markdown内容
    
    参数：
        user_id: 用户ID
        doc_id: 文档ID

    返回：
        （成功状态，markdown内容或错误消息）
    """
    try:
        # 获取文档元数据
        from src.utils import get_document_metadata
        metadata = get_document_metadata(user_id, doc_id)

        if not metadata:
            return False, "文档元数据不存在"
        
        # 检查文档是否处理完成
        if metadata.get("status") != "处理完成":
            return False, f"文档尚未处理完成，当前状态: {metadata.get('status', '未知')}"
        
        # 获取PDF文件名
        pdf_filename = metadata.get("filename")
        if not pdf_filename:
            return False, "文件名未记录"
        
        # 确定markdown文件路径
        pdf_name_without_ext = os.path.splitext(pdf_filename)[0]
        user_output_dir = get_user_data_path(user_id, "output")
        markdown_path = os.path.join(
            user_output_dir,
            doc_id,
            pdf_name_without_ext,
            "auto",
            f"{pdf_name_without_ext}.md"
        )

        # 检查文件是否存在
        if not os.path.exists(markdown_path):
            return False, f"Markdown文件不存在: {markdown_path}"
        
        # 读取markdown内容
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return True, content
    
    except Exception as e:
        return False, str(e)       
