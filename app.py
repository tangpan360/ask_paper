import streamlit as st
import os
import sys


sys.path.append(os.path.abspath(os.path.dirname(__file__)))

for dir_path in ["data", "output", "storage", "db", "config"]:
    os.makedirs(dir_path, exist_ok=True)

st.set_page_config(
    page_title="论文问答系统",
    page_icon="📚",
    layout="wide",
)

if "documents" not in st.session_state:
    st.session_state.documents = {}

st.title("📚 论文问答系统")
st.markdown("""
            
### 欢迎使用论文问答系统

这个系统够可以帮助您：
-  上传论文并解析成网页格式方便翻译
-  为论文构建知识索引为问答做准备
-  基于论文内容进行问答

请使用左侧导航菜单开始使用不同的功能
""")

if st.session_state.documents:
    st.subheader("已处理文档概览")

    data = []
    for doc_id, doc_info in st.session_state.documents.items():
        data.append({
            "文档ID": doc_id,
            "文件名": doc_info.get("filename", "未知"),
            "上传时间": doc_info.get("upload_time", "未知"),
            "处理状态": doc_info.get("status", "未知"),
            "索引状态": "已建索引" if doc_info.get("index", False) else "未建索引"
        })

    if data:
        st.table(data)
else:
    st.info("还没有上传和处理文档，请前往上传文档页面上传您的第一个PDF文件")
