import streamlit as st
import os
import sys
import time
import pandas as pd
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import get_user_documents, is_document_indexed, is_document_processed
from src.build_index import build_index_for_document

# 设置页面
st.set_page_config(
    page_title="构建索引",
    page_icon="🔍",
    layout="wide"
)

# 检查登录状态
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.error("请先登录")
    st.stop()

# 获取用户ID
user_id = st.session_state.user_id

# 页面标题
st.title("🔍 构建文档索引")
st.write(f"欢迎，{st.session_state.username}！您现在可以在此处为已处理的文档构建索引，以便进行问答。")

# 添加自动构建索引的说明信息
st.info("""
### 系统会自动构建索引！
    
现在当您在**上传文档**页面完成"处理文档"后，系统将**自动构建索引**，无需再手动操作。

您仅在以下情况下需要使用此页面：
1. 需要**重新构建**文档索引（如果索引出现问题或需要更新）
2. 为**旧文档**手动构建索引（处理文档前未启用自动索引功能的文档）
3. 自动构建索引**失败**时进行手动构建
""")

# 获取用户文档列表
user_docs = get_user_documents(user_id)

# 过滤已处理但未索引的文档
processed_docs = [doc for doc in user_docs if is_document_processed(user_id, doc["doc_id"])]

if not processed_docs:
    st.info("您还没有处理完成的文档，请先上传并处理文档")
else:
    # 创建表格展示文档
    doc_data = []
    for doc in processed_docs:
        indexed = is_document_indexed(user_id, doc["doc_id"])
        doc_data.append({
            "文档ID": doc.get("doc_id", "未知"),
            "文件名": doc.get("filename", "未知文件"),
            "上传时间": doc.get("upload_time", "未知时间"),
            "状态": doc.get("status", "未知状态"),
            "索引状态": "已建索引" if indexed else "未建索引"
        })

    # 显示文档表格
    st.subheader("可索引文档")
    st.dataframe(doc_data)

    # 选择文档进行构建索引
    doc_options = {f"{doc.get('filename', '未知文件')} ({doc.get('doc_id', '未知')})": doc.get("doc_id") for doc in processed_docs}

    if doc_options:
        selected_doc_display = st.selectbox("选择要构建索引的文档", list(doc_options.keys()))
        selected_doc_id = doc_options[selected_doc_display]

        # 判断所选文档是否已索引
        already_indexed = next((doc for doc in processed_docs if doc["doc_id"] == selected_doc_id), {}).get("indexed", False)

        # 构建索引按钮
        if already_indexed:
            if st.button("重新构建索引", help="文档已索引，但您可以重新构建"):
                st.warning("正在重新构建索引...")
                start_indexing = True
            else:
                start_indexing = False
        else:
            if st.button("构建索引", help="构建文档的索引，以便进行问答"):
                start_indexing = True
            else:
                start_indexing = False

        # 构建索引
        if start_indexing:
            # 创建进度条
            progress_text = st.empty()
            progress_bar = st.progress(0)

            # 进度条回调函数
            def update_progress(message, percent):
                progress_text.text(message)
                progress_bar.progress(percent / 100)

            # 开始构建索引
            with st.spinner("正在构建索引..."):
                success, result = build_index_for_document(user_id, selected_doc_id, update_progress)

                if success:
                    st.success(result)
                    # 等待1秒显示成功消息
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result)

# 显示已索引文档
indexed_docs = [doc for doc in user_docs if is_document_indexed(user_id, doc["doc_id"])]

if indexed_docs:
    st.subheader("已索引文档")

    # 创建表格展示已索引文档
    indexed_data = []
    for doc in indexed_docs:
        indexed_data.append({
            "文档ID": doc.get("doc_id", "未知"),
            "文件名": doc.get("filename", "未知文件"),
            "上传时间": doc.get("upload_time", "未知时间"),
            "索引时间": doc.get("index_time", "未知时间")
        })
    # 显示已索引文档表格
    st.dataframe(indexed_data)

    # 提示可以进行回答
    st.info("您可以前往'论文回答'页面，基于已索引的文章进行智能问答")

    # 跳转到问答页面的按钮
    if st.button("前往问答页面"):
        # 使用st.session_state保存状态以供其他页面使用
        st.session_state.last_indexed_doc_id = indexed_docs[0]["doc_id"]
        # 重定向到问答页面
        st.switch_page("pages/03_论文问答.py")
else:
    st.info("您还没有已索引的文档，请先构建索引")
