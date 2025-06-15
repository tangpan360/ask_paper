import streamlit as st
import os
import sys
import time
import re
import base64
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入模块
from src.utils import generate_document_id, get_document_metadata, delete_document
from src.pdf_processor import save_pdf, process_pdf_with_magic, get_markdown_content
from src.auth import get_user_data_path, get_system_config
# 导入构建索引功能
from src.build_index import build_index_for_document

# 处理markdown中的图片，转换为base64编码
def process_markdown_images(markdown_content: str, base_dir: str) -> str:
    """
    处理markdown内容中的图片链接，将图片转换为base64编码

    参数：
        markdown_content: markdown内容
        base_dir: 图片所在的基础目录

    返回：
        处理后的markdown内容
    """
    try:
        # 查找markdown中的所有图片链接
        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        
        def replace_image(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(image_path):
                image_path = os.path.join(base_dir, image_path)
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                return f"![{alt_text}]({image_path}) (图片不存在)"
            
            # 读取图片并转换为base64
            try:
                with open(image_path, "rb") as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode()
                    
                    # 获取文件扩展名
                    ext = os.path.splitext(image_path)[1].lower().lstrip('.')
                    if ext in ['jpg', 'jpeg']:
                        mime_type = 'image/jpeg'
                    elif ext == 'png':
                        mime_type = 'image/png'
                    elif ext == 'gif':
                        mime_type = 'image/gif'
                    elif ext == 'svg':
                        mime_type = 'image/svg+xml'
                    else:
                        mime_type = 'image/jpeg'  # 默认为JPEG
                    
                    # 创建base64 URL
                    base64_url = f"data:{mime_type};base64,{img_base64}"
                    return f"![{alt_text}]({base64_url})"
            except Exception as e:
                return f"![{alt_text}]({image_path}) (图片加载失败: {str(e)})"
        
        # 替换所有图片链接
        processed_content = re.sub(image_pattern, replace_image, markdown_content)
        return processed_content
    
    except Exception as e:
        st.error(f"处理markdown图片时出错: {str(e)}")
        return markdown_content

# 设置页面
st.set_page_config(
    page_title="上传文档",
    page_icon="📄",
    layout="wide"
)

# 检查登录状态
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.error("请先登录")
    st.stop()

# 获取用户ID
user_id = st.session_state.user_id

# 页面标题
st.title("📄 上传论文")
st.write(f"欢迎，{st.session_state.username}！您可以在此上传PDF论文，系统将自动处理并提取内容。")

# 上传区域
with st.expander("上传新文档", expanded=True):
    uploaded_file = st.file_uploader("选择PDF文件", type="pdf", key="pdf_uploader")

    if uploaded_file is not None:
        # 获取系统配置的文件大小限制
        max_doc_size_mb = get_system_config("max_document_size_mb") or 50  # 默认50MB

        # 将字节转换为MB
        file_size_mb = uploaded_file.size / (1024 * 1024)

        # 验证文件大小
        if file_size_mb > max_doc_size_mb:
            st.error(f"文件大小 ({file_size_mb:.2f}MB) 超过系统限制 ({max_doc_size_mb}MB)")
            st.info("请联系管理员调整文件大小限制，或上传更小的文件")
        else:
            # 显示文件信息
            file_details = {
                "文件名": uploaded_file.name,
                "文件大小": f"{uploaded_file.size / 1024:.2f} KB",
                "文件类型": uploaded_file.type,
            }
            st.write(file_details)

            # 处理按钮和前往问答按钮放在同一行
            col1, col2 = st.columns(2)
            
            with col1:
                # 处理按钮
                if st.button("处理文档"):
                    with st.spinner("正在处理文档..."):
                        # 生成文档ID
                        doc_id = generate_document_id()

                        # 保存PDF文件
                        st.write("保存文件...")
                        success, result = save_pdf(user_id, uploaded_file, doc_id)
                        
                        if not success:
                            st.error(f"保存文件失败: {result}")
                            st.stop()
                        
                        pdf_path = result
                        st.write(f"文件已保存：{pdf_path}")

                        # 处理PDF
                        st.write("使用magic-pdf处理文件...")
                        success, result = process_pdf_with_magic(user_id, pdf_path, doc_id)

                        if not success:
                            st.error(f"处理文件失败: {result}")
                            st.stop()

                        result_dir = result
                        st.success(f"文件处理完成！结果保存在：{result_dir}")

                        # 获取markdown内容
                        success, content = get_markdown_content(user_id, doc_id)

                        if success:
                            # 自动构建索引
                            st.write("开始自动构建索引...")
                            
                            # 定义进度回调函数
                            def update_progress(message, percent):
                                st.write(f"{message} - {percent}%")
                            
                            # 构建索引
                            index_success, index_result = build_index_for_document(user_id, doc_id, update_progress)
                            
                            if index_success:
                                st.success(f"索引构建成功: {index_result}")
                            else:
                                st.warning(f"索引构建失败: {index_result}")
                            
                            st.session_state.current_doc_id = doc_id
                            st.session_state.current_content = content
                            st.rerun()
            
            with col2:
                # 添加前往问答页面的按钮
                from src.utils import is_document_indexed, get_user_documents
                
                # 获取用户已索引的文档
                user_docs = get_user_documents(user_id)
                indexed_docs = [doc for doc in user_docs if doc.get("indexed", False)]
                
                if indexed_docs:
                    if st.button("直接前往问答页面", help="使用已索引的文档开始问答"):
                        st.session_state.last_indexed_doc_id = indexed_docs[0]["doc_id"]
                        st.switch_page("pages/03_论文问答.py")

# 显示用户已有文档
st.subheader("我的文档")

# 获取用户文档列表
from src.utils import get_user_documents
user_docs = get_user_documents(user_id)

if not user_docs:
    st.info("您还没有上传任何文档")
else:
    # 创建表格展示文档
    doc_data = []
    for doc in user_docs:
        doc_data.append({
            "文档ID": doc.get("doc_id", "未知"),
            "文件名": doc.get("filename", "未知文件"),
            "上传时间": doc.get("upload_time", "未知时间"),
            "状态": doc.get("status", "未知状态"),
            "索引状态": "已建索引" if doc.get("indexed", False) else "未建索引",
        })

    # 显示文档表格
    st.table(doc_data)
    
    # 选择文档以查看或删除
    doc_ids = {f"{doc.get('filename', '未知文件')} ({doc.get('doc_id', '未知')})": doc.get("doc_id") for doc in user_docs}
    
    if doc_ids:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("查看文档")
            view_doc_ids = {f"{doc.get('filename', '未知文件')} ({doc.get('doc_id', '未知')})": doc.get("doc_id") 
                           for doc in user_docs if doc.get("status") == "处理完成"}
            
            if view_doc_ids:
                selected_doc_display = st.selectbox("选择文档查看", list(view_doc_ids.keys()))
                selected_doc_id = view_doc_ids[selected_doc_display]

                if st.button("查看文档"):
                    success, content = get_markdown_content(user_id, selected_doc_id)

                    if success:
                        st.session_state.current_doc_id = selected_doc_id
                        st.session_state.current_content = content
                        st.rerun()
                    else:
                        st.error(f"获取文档内容失败: {content}")
            else:
                st.info("没有可查看的已处理文档")
                
        with col2:
            st.subheader("删除文档")
            delete_doc_display = st.selectbox("选择要删除的文档", list(doc_ids.keys()))
            delete_doc_id = doc_ids[delete_doc_display]
            
            # 添加确认删除的功能
            if st.button("删除文档", type="primary", help="此操作不可恢复，请谨慎操作"):
                if "confirm_delete" not in st.session_state:
                    st.session_state.confirm_delete = delete_doc_id
                    st.session_state.confirm_delete_name = delete_doc_display
                    st.rerun()
            
            # 处理确认删除
            if "confirm_delete" in st.session_state:
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("✅ 确认删除"):
                        success, message = delete_document(user_id, st.session_state.confirm_delete)
                        if success:
                            st.success(message)
                            # 清除确认状态
                            del st.session_state.confirm_delete
                            del st.session_state.confirm_delete_name
                            # 如果正在查看该文档，清除查看状态
                            if "current_doc_id" in st.session_state and st.session_state.current_doc_id == delete_doc_id:
                                if "current_content" in st.session_state:
                                    del st.session_state.current_content
                                del st.session_state.current_doc_id
                            # 刷新页面
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                
                with confirm_col2:
                    if st.button("❌ 取消"):
                        # 清除确认状态
                        del st.session_state.confirm_delete
                        del st.session_state.confirm_delete_name
                        st.rerun()

# 显示处理结果
if "current_doc_id" in st.session_state and "current_content" in st.session_state:
    doc_id = st.session_state.current_doc_id
    content = st.session_state.current_content

    # 获取文档元数据
    metadata = get_document_metadata(user_id, doc_id)
    filename = metadata.get("filename", "未知文件") if metadata else "未知文件"

    # 获取markdown文件所在目录，用于处理图片路径
    pdf_name_without_ext = os.path.splitext(filename)[0]
    user_output_dir = get_user_data_path(user_id, "output")
    markdown_dir = os.path.join(
        user_output_dir,
        doc_id,
        pdf_name_without_ext,
        "auto"
    )

    # 显示文档信息
    st.subheader(f"处理结果：{filename}")
    
    # 添加操作按钮区域（移到上方）
    col1, col2 = st.columns(2)
    
    with col1:
        # 清除当前显示
        if st.button("清除预览内容"):
            del st.session_state.current_doc_id
            del st.session_state.current_content
            st.rerun()
    
    with col2:
        # 添加直接前往问答页面的按钮
        from src.utils import is_document_indexed
        
        if is_document_indexed(user_id, doc_id):
            if st.button("前往问答页面", type="primary"):
                st.session_state.last_indexed_doc_id = doc_id
                st.switch_page("pages/03_论文问答.py")

    # 创建选项卡
    tab1, tab2 = st.tabs(["内容预览", "原始Markdown"])

    # 内容预览选项卡
    with tab1:
        # 处理markdown中的图片，转换为base64编码
        processed_content = process_markdown_images(content, markdown_dir)
        st.markdown(processed_content)

    # 原始Markdown选项卡
    with tab2:
        st.text_area("Markdown源码", content, height=500)




