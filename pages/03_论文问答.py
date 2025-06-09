import streamlit as st
import os
import sys
import time
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入模块
from src.utils import get_user_documents, is_document_indexed, get_document_metadata
from src.retriever import get_chat_engine_for_document

# 设置页面
st.set_page_config(
    page_title="论文问答",
    page_icon="💬",
    layout="wide"
)

# 检查登录状态
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.error("请先登录")
    st.stop()

# 获取用户ID
user_id = st.session_state.user_id

# 页面标题
st.title("💬 论文问答")
st.write(f"欢迎，{st.session_state.username}！您可以在此基于已索引的文档进行智能问答。")

# 初始化聊天历史
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}

# 初始化当前选择的文档
if "selected_doc_id" not in st.session_state:
    st.session_state.selected_doc_id = None

# 初始化聊天引擎
if "chat_engines" not in st.session_state:
    st.session_state.chat_engines = {}

# 检查是否从索引页面跳转过来
if "last_indexed_doc_id" in st.session_state:
    st.session_state.selected_doc_id = st.session_state.last_indexed_doc_id
    # 清除跳转状态
    del st.session_state.last_indexed_doc_id

# 获取用户已索引的文档
user_docs = get_user_documents(user_id)
indexed_docs = [doc for doc in user_docs if is_document_indexed(user_id, doc["doc_id"])]

# 侧边栏：选择文档
with st.sidebar:
    st.header("选择文档")
    
    if not indexed_docs:
        st.warning("您还没有已索引的文档，请先构建索引")
        if st.button("前往构建索引"):
            st.switch_page("pages/02_构建索引.py")
        st.stop()
    
    # 文档选择器
    doc_options = {f"{doc.get('filename', '未知文件')}": doc.get("doc_id") for doc in indexed_docs}
    selected_doc_name = st.selectbox(
        "选择要问答的文档", 
        list(doc_options.keys()),
        index=0 if st.session_state.selected_doc_id is None else 
              list(doc_options.values()).index(st.session_state.selected_doc_id) 
              if st.session_state.selected_doc_id in doc_options.values() else 0
    )
    
    selected_doc_id = doc_options[selected_doc_name]
    
    # 如果选择了新文档，更新状态
    if st.session_state.selected_doc_id != selected_doc_id:

        # 更新当前选择
        st.session_state.selected_doc_id = selected_doc_id
        
        # 确保当前文档有聊天历史
        if selected_doc_id not in st.session_state.chat_histories:
            st.session_state.chat_histories[selected_doc_id] = []

        # 加载新文档的聊天引擎
        with st.spinner("正在加载文档索引..."):
            # 创建新文档的聊天引擎
            success, result = get_chat_engine_for_document(
                user_id,
                selected_doc_id,
            )

            if success:
                # 存储当前文档的聊天引擎
                st.session_state.chat_engines[selected_doc_id] = result
                st.success("文档加载成功！")
            else:
                st.error(f"加载文档失败：{result}")

    # 显示文档信息
    selected_doc_metadata = get_document_metadata(user_id, selected_doc_id)
    if selected_doc_metadata:
        st.subheader("文档信息")
        st.write(f"文件名: {selected_doc_metadata.get('filename', '未知')}")
        st.write(f"上传时间: {selected_doc_metadata.get('upload_time', '未知')}")
        st.write(f"索引时间: {selected_doc_metadata.get('index_time', '未知')}")
    
    # 清除聊天按钮
    if st.button("清除聊天历史"):
        st.session_state.chat_histories[selected_doc_id] = []

        # 重新创建聊天引擎
        success, result = get_chat_engine_for_document(
            user_id,
            selected_doc_id,
        )

        if success:
            st.session_state.chat_engines[selected_doc_id] = result
        st.rerun()

# 主区域：聊天界面
if st.session_state.selected_doc_id is None:
    st.info("请从侧边栏选择一个文档进行问答")
    st.stop()

# 确保选定文档的聊天引擎已加载
if (st.session_state.selected_doc_id not in st.session_state.chat_engines or 
    st.session_state.chat_engines[st.session_state.selected_doc_id] is None):
    st.error("聊天引擎未成功加载，请重新选择文档")
    st.stop()

# 获取当前文档的聊天引擎
current_chat_engine = st.session_state.chat_engines[st.session_state.selected_doc_id]

# 获取当前文档的聊天历史
current_chat_history = st.session_state.chat_histories[st.session_state.selected_doc_id]

# 显示聊天历史
for message in current_chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("请输入您的问题"):
    # 添加用户消息到历史
    current_chat_history.append({"role": "user", "content": prompt})

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    # 显示助手消息（流式输出）
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # 使用流式模式获取回答
            streaming_response = current_chat_engine.stream_chat(prompt)
            
            # 流式处理响应
            for token in streaming_response.response_gen:
                full_response += token
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)

            # 显示最终完整回答（去掉光标）
            message_placeholder.markdown(full_response)

            # 添加助手消息到历史
            current_chat_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_message = f"处理您的问题时出错：{str(e)}"
            message_placeholder.markdown(error_message)