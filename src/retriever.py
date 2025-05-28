import os
from dotenv import load_dotenv
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import Settings
from llama_index.llms.dashscope import DashScope
from llama_index.embeddings.dashscope import DashScopeEmbedding


load_dotenv()

Settings.llm = DashScope(
    model="deepseek-v3",
    api_key=os.getenv("ALI_API_KEY"),
    api_base=os.getenv("ALI_API_BASE"),
    streaming=True,
)

Settings.embed_model = DashScopeEmbedding(
    model="text-embedding-v3",
    api_key=os.getenv("ALI_API_KEY"),
    api_base=os.getenv("ALI_API_BASE"),
)

first_answer = "这是一个基于 Llamaindex 和自定义向量库的问答系统。"
DEFAULT_MESSAGES = [
    ChatMessage(role=MessageRole.USER, content="这个系统是什么？"),
    ChatMessage(role=MessageRole.ASSISTANT, content=first_answer)
]

PERSIST_DIR = "../storage"
os.makedirs(PERSIST_DIR, exist_ok=True)

try:
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)
    print("加载索引成功")
except:
    print("未找到现有索引，需要先创建索引")
    index = None

def get_chat_engine():
    if index is None:
        raise ValueError("索引未初始化，请先创建索引")

    chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context",
        similarity_top_k=3,
        system_prompt="""你是基于检索增强生成的AI助手，回答用户问题时基于提供的文档内容。
        如果问题与上下文文档无关，请明确指出："提供的文档中没有关于这个问题的信息。""",
        verbose=True,
        chat_history=DEFAULT_MESSAGES,
        streaming=True,
    )

    return chat_engine
