import streamlit as st
import os
import sys
import time
import uuid
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入模块
from src.utils import get_user_documents, is_document_indexed, get_document_metadata
from src.retriever import (
    find_source_references,
    get_source_nodes_from_index,
    match_source_references,
    load_document_engines
)

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

# 初始化源文本查询引擎
if "source_query_engines" not in st.session_state:
    st.session_state.source_query_engines = {}

# 初始化源文本索引
if "source_indices" not in st.session_state:
    st.session_state.source_indices = {}

# 初始化引用功能开关
if "enable_reference" not in st.session_state:
    st.session_state.enable_reference = True

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
    
    # 引用功能开关
    enable_reference = st.toggle("启用原文引用功能", value=st.session_state.enable_reference)
    if enable_reference != st.session_state.enable_reference:
        st.session_state.enable_reference = enable_reference
        # 如果切换了引用功能，需要重新加载当前文档
        if st.session_state.selected_doc_id:
            st.rerun()

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

        # 加载新文档的聊天引擎和源文本查询引擎
        with st.spinner("正在加载文档索引..."):
            # 加载索引和引擎，传递引用功能开关状态
            success, result = load_document_engines(user_id, selected_doc_id, st.session_state.enable_reference)
            
            if success:
                # 存储索引和引擎
                st.session_state.chat_engines[selected_doc_id] = result["chat_engine"]
                
                # 如果启用了引用功能，存储源文本索引和查询引擎
                if st.session_state.enable_reference and "source_index" in result:
                    st.session_state.source_indices[selected_doc_id] = result["source_index"]
                    st.session_state.source_query_engines[selected_doc_id] = result["source_query_engine"]
                
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

        # 重新加载索引和引擎，传递引用功能开关状态
        success, result = load_document_engines(user_id, selected_doc_id, st.session_state.enable_reference)
        
        if success:
            # 更新索引和引擎
            st.session_state.chat_engines[selected_doc_id] = result["chat_engine"]
            
            # 如果启用了引用功能，更新源文本索引和查询引擎
            if st.session_state.enable_reference and "source_index" in result:
                st.session_state.source_indices[selected_doc_id] = result["source_index"]
                st.session_state.source_query_engines[selected_doc_id] = result["source_query_engine"]
        
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

# 获取当前文档的聊天引擎和源文本查询引擎
current_doc_id = st.session_state.selected_doc_id
current_chat_engine = st.session_state.chat_engines[current_doc_id]
current_source_query_engine = st.session_state.source_query_engines.get(current_doc_id)
current_source_index = st.session_state.source_indices.get(current_doc_id)

# 获取当前文档的聊天历史
current_chat_history = st.session_state.chat_histories[current_doc_id]

# 显示聊天历史
for message in current_chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # 如果是助手消息且有源文本参考，且引用功能已启用，显示参考
        if message["role"] == "assistant" and "references" in message and st.session_state.enable_reference:
            if message["references"]:
                with st.expander("查看原文参考"):
                    for i, ref in enumerate(message["references"]):
                        st.markdown(f"**<span style='color:red;'>参考 {i+1}</span>**:", unsafe_allow_html=True)
                        st.markdown(f"\n{ref['node_text']}\n")
            else:
                with st.expander("查看原文参考"):
                    st.info("未找到与回答直接相关的原文参考。")

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
            
            # 查找源文本参考
            references = []
            if st.session_state.enable_reference and current_source_query_engine and current_source_index:
                with st.spinner("正在查找原文参考..."):
                    # 查找源文本参考片段
                    source_list = find_source_references(current_source_query_engine, full_response)
                    
                    # 获取源文本节点
                    source_nodes = get_source_nodes_from_index(current_source_index)
                    
                    # 匹配源文本参考
                    references = match_source_references(source_list, source_nodes)
                    
                    # 显示源文本参考
                    if references:
                        with st.expander("查看原文参考"):
                            for i, ref in enumerate(references):
                                st.markdown(f"**<span style='color:red;'>参考 {i+1}</span>**:", unsafe_allow_html=True)
                                st.markdown(f"\n{ref['node_text']}\n")
                    else:
                        with st.expander("查看原文参考"):
                            st.info("未找到与回答直接相关的原文参考。")

            # 添加助手消息到历史（包含源文本参考）
            current_chat_history.append({
                "role": "assistant", 
                "content": full_response,
                "references": references
            })
            
        except Exception as e:
            error_message = f"处理您的问题时出错：{str(e)}"
            message_placeholder.markdown(error_message)
            
            # 添加错误消息到历史
            current_chat_history.append({
                "role": "assistant", 
                "content": error_message,
                "references": []
            })