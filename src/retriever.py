import os
from dotenv import load_dotenv
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import Settings
from llama_index.llms.dashscope import DashScope
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.llms.openai import OpenAI
from typing import Tuple, Any

from src.build_index import get_index_storage_path
from src.utils import is_document_indexed


load_dotenv()


def setup_models():
    """初始化语言模型和嵌入模型"""
    # 使用OpenAILike接入第三方中转API
    # Settings.llm = OpenAILike(
    #     model="deepseek-v3",
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     api_base=os.getenv("OPENAI_API_BASE"),
    #     is_chat_model=True,  # 指定是否为聊天模型
    #     is_function_calling_model=True,  # 指定是否支持函数调用
    #     # 可以根据模型实际情况设置上下文窗口大小
    #     context_window=16000,
    # )

    # Settings.llm = DashScope(
    #     model="deepseek-v3",
    #     api_key=os.getenv("ALI_API_KEY"),
    #     api_base=os.getenv("ALI_API_BASE"),
    # )

    Settings.llm = OpenAI(
        model="gpt-4.1-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        api_base=os.getenv("OPENAI_API_BASE"),
    )

    Settings.embed_model = DashScopeEmbedding(
        model="text-embedding-v3",
        api_key=os.getenv("ALI_API_KEY"),
        api_base=os.getenv("ALI_API_BASE"),
    )

# 设置默认消息，用于初始化聊天历史
first_answer = "这是一个基于论文的问答系统。"
DEFAULT_MESSAGES = [
    ChatMessage(role=MessageRole.USER, content="这个系统是什么？"),
    ChatMessage(role=MessageRole.ASSISTANT, content=first_answer)
]

def load_index_for_document(user_id: str, doc_id: str) -> Tuple[bool, Any]:
    """
    加载特定用户的特定文档索引

    参数：
        user_id: 用户ID
        doc_id: 文档ID

    返回：
        (是否成功, 索引对象或错误消息)
    """
    try:
        # 检查文档是否已索引
        if not is_document_indexed(user_id, doc_id):
            return False, "文档尚未索引，无法加载"
        
        # 获取索引存储路径
        full_text_dir, source_dir = get_index_storage_path(user_id, doc_id)

        # 初始化模型
        setup_models()

        # 加载全文索引
        try:
            full_text_storage_context = StorageContext.from_defaults(persist_dir=full_text_dir)
            full_text_index = load_index_from_storage(full_text_storage_context)

            # 加载源文本索引
            source_storage_context = StorageContext.from_defaults(persist_dir=source_dir)
            source_index = load_index_from_storage(source_storage_context)

            return True, (full_text_index, source_index)
        
        except Exception as e:
            return False, f"加载索引失败: {str(e)}"
    
    except Exception as e:
        return False, f"加载索引时发生错误: {str(e)}"
    
def get_chat_engine_for_document(user_id: str, doc_id: str) -> Tuple[bool, Any]:
    """
    获取文档专用回答引擎

    参数：
        user_id: 用户ID
        doc_id: 文档ID

    返回：
        (是否成功, 聊天引擎对象或错误消息)
    """
    try:
        # 加载索引
        success, result = load_index_for_document(user_id, doc_id)

        if not success:
            return False, result
        
        full_text_index, _ = result

        # 创建聊天引擎
        chat_engine = full_text_index.as_chat_engine(
            chat_mode="context",
            system_prompt="""你是基于检索增强生成的AI助手，回答用户问题时基于提供的文档内容。
        如果问题与上下文文档无关，请明确指出："提供的文档中没有关于这个问题的信息。""",
            verbose=True,
            chat_history=DEFAULT_MESSAGES,
            streaming=True,
        )

        return True, chat_engine
    
    except Exception as e:
        return False, f"获取聊天引擎失败: {str(e)}"
    
def get_document_source(user_id: str, doc_id: str):
    pass
