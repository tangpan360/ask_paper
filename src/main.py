import uuid
import time
import streamlit as st
from dotenv import load_dotenv
from retriever import get_chat_engine
import sys
import os


# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

st.set_page_config(
    page_title="论文问答系统",
    page_icon="📚"
)

st.write("## 论文问答系统")

with st.sidebar:
    st.markdown("## 关于")
    st.markdown("这是一个针对论文的问答系统")
    
# 初始化会话状态
if "chat_engine" not in st.session_state:
    try:
        st.session_state.chat_engine = get_chat_engine()
    except ValueError as e:
        st.error(f"错误：{str(e)}")
        st.info("请先运行 build_index.py 创建索引")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("请输入您的问题"):
    # 添加用户消息到历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 显示助手消息（流式输出）
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 使用流式模式获取回答
            streaming_response = st.session_state.chat_engine.stream_chat(prompt)
            
            # 流式处理响应
            for token in streaming_response.response_gen:
                full_response += token
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)  # 控制显示速度
                
            # 显示最终完整回答（去掉光标）
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"处理您的问题时出错：{str(e)}"
            message_placeholder.markdown(full_response)
        
        # 添加助手消息到历史
        st.session_state.messages.append({"role": "assistant", "content": full_response})

