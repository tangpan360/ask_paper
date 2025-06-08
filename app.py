import streamlit as st
import os
import sys
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 导入工具函数
from src.utils import get_user_documents
from src.auth import is_admin

# 创建必要的目录
for dir_path in ["data", "output", "storage", "db", "config"]:
    os.makedirs(dir_path, exist_ok=True)

# 设置页面配置
st.set_page_config(
    page_title="论文问答系统",
    page_icon="📚",
    layout="wide",
)

# 标题和介绍
st.title("📚 论文问答系统")

# 检查用户登录状态
if "user_id" not in st.session_state or not st.session_state.user_id:
    # 未登录显示欢迎信息
    st.markdown("""
    ### 欢迎使用论文问答系统

    这个系统可以帮助您:
    - 上传PDF论文并提取内容
    - 为论文构建知识索引
    - 基于论文内容进行智能问答

    请先登录或注册账号以使用系统功能。
    """)
    
    st.info("请点击左侧边栏的 '登录/注册' 选项进行登录")
else:
    # 已登录显示用户信息
    user_role = "管理员" if is_admin(st.session_state.user_id) else "普通用户"
    st.markdown(f"### 欢迎回来，{st.session_state.username}！({user_role})")
    
    st.markdown("""
    这个系统可以帮助您:
    - 上传PDF论文并提取内容
    - 为论文构建知识索引
    - 基于论文内容进行智能问答

    请使用左侧导航菜单开始使用不同功能。
    """)
    
    # 显示用户文档状态概览
    st.subheader("我的文档概览")
    
    # 获取用户文档列表
    user_docs = get_user_documents(st.session_state.user_id)
    
    if not user_docs:
        st.info("您还没有上传任何文档。请前往'上传文档'页面上传您的第一个PDF文件。")
    else:
        # 创建文档状态统计
        total_docs = len(user_docs)
        processed_docs = sum(1 for doc in user_docs if doc.get("status") == "处理完成")
        indexed_docs = sum(1 for doc in user_docs if doc.get("indexed", False))
        
        # 显示统计数据
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总文档数", total_docs)
        with col2:
            st.metric("已处理文档", processed_docs)
        with col3:
            st.metric("已索引文档", indexed_docs)
        
        # 创建文档列表表格
        doc_data = []
        for doc in user_docs:
            doc_data.append({
                "文件名": doc.get("filename", "未知文件"),
                "上传时间": doc.get("upload_time", "未知时间"),
                "状态": doc.get("status", "未知状态"),
                "索引状态": "已建索引" if doc.get("indexed", False) else "未建索引"
            })
        
        # 显示文档表格
        st.dataframe(doc_data)
        
        # 快速导航按钮
        st.subheader("快速操作")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("上传新文档"):
                st.switch_page("pages/01_上传文档.py")
        with col2:
            if st.button("构建索引"):
                st.switch_page("pages/02_构建索引.py")
        with col3:
            if indexed_docs > 0:
                if st.button("开始问答"):
                    st.switch_page("pages/03_论文问答.py")
    
    # 如果是管理员，显示系统概览
    if is_admin(st.session_state.user_id):
        st.subheader("系统管理")
        if st.button("进入管理中心"):
            st.switch_page("pages/04_管理中心.py")
