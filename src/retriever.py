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
from typing import Tuple, Any, Dict
import json

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
    
def load_document_engines(user_id: str, doc_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    加载特定用户的特定文档索引，并创建聊天引擎和源文本查询引擎

    参数：
        user_id: 用户ID
        doc_id: 文档ID

    返回：
        (是否成功, 包含索引和引擎的字典或错误消息)
    """
    try:
        # 加载索引
        success, result = load_index_for_document(user_id, doc_id)

        if not success:
            return False, result
        
        full_text_index, source_index = result
        
        # 创建聊天引擎
        chat_engine = full_text_index.as_chat_engine(
            chat_mode="context",
            system_prompt="""你是基于检索增强生成的AI助手，回答用户问题时基于提供的文档内容。
        如果问题与上下文文档无关，请明确指出："提供的文档中没有关于这个问题的信息。""",
            verbose=True,
            streaming=True,
        )
        
        # 创建源文本查询引擎
        source_query_engine = source_index.as_query_engine()
        
        return True, {
            "full_text_index": full_text_index,
            "source_index": source_index,
            "chat_engine": chat_engine,
            "source_query_engine": source_query_engine
        }
    
    except Exception as e:
        return False, f"加载文档引擎失败: {str(e)}"

def find_source_references(source_query_engine, response_text: str) -> list:
    """
    根据回复内容查找源文本参考

    参数：
        source_query_engine: 源文本查询引擎
        response_text: 回复内容

    返回：
        源文本参考列表
    """
    try:
        # 构建查询提示词
        query_prompt = f"""作为一个智能文档助手，请帮我分析用户陈述的内容在原文中是否有相关依据。请找出原文中支持或反驳这些陈述的段落，并按照JSON格式返回结果（只需要给出该段落的前10个单词），格式为：{{"片段1":"相关内容...", "片段2":"相关内容..."}}。如果找不到相关内容，请返回空JSON对象 {{}}。

用户陈述：

{response_text}
"""
        
        # 查询源文本
        source_response = source_query_engine.query(query_prompt)
        
        # 尝试解析JSON响应
        try:
            # 提取响应中的JSON部分
            response_text = source_response.response
            # 查找第一个 { 和最后一个 } 的位置
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                source_json = json.loads(json_str)
                source_list = list(source_json.values())
                return source_list
            else:
                return []
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试使用正则表达式提取
            import re
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response_text, re.DOTALL)
            if match:
                try:
                    source_json = json.loads(match.group(0))
                    source_list = list(source_json.values())
                    return source_list
                except:
                    return []
            return []
    
    except Exception as e:
        print(f"查找源文本参考失败: {str(e)}")
        return []

def get_source_nodes_from_index(source_index):
    """
    从源文本索引中获取所有节点

    参数：
        source_index: 源文本索引

    返回：
        源文本节点列表
    """
    try:
        # 获取索引中的所有节点
        return source_index.docstore.docs.values()
    except Exception as e:
        print(f"获取源文本节点失败: {str(e)}")
        return []

def match_source_references(source_list: list, source_nodes: list) -> list:
    """
    匹配源列表中的项目与节点文本
    
    参数：
        source_list: 包含要匹配文本片段的列表
        source_nodes: 包含节点对象的列表
        
    返回：
        包含匹配结果的列表，每个结果是一个字典，包含source_item和node_text
    """
    # 创建一个列表存储匹配结果
    matching_results = []
    # 用于去重的集合，存储已经添加的node_text
    added_texts = set()
    
    # 遍历 source_list 中的每一项
    for item in source_list:
        if not item:
            continue
            
        # 对于每个 item，检查它是否存在于任何 source_nodes 的文本中
        for node in source_nodes:
            if hasattr(node, 'text') and item in node.text:
                # 如果该文本还未添加过，则添加到结果中
                if node.text not in added_texts:
                    matching_results.append({
                        "source_item": item,
                        "node_text": node.text
                    })
                    # 将文本添加到已添加集合中
                    added_texts.add(node.text)
    
    return matching_results
