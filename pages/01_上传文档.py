import streamlit as st
import os
import sys
import time
import re
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入模块
from src.utils import generate_document_id, get_document_metadata
from src.pdf_processor import save_pdf, process_pdf_with_magic, get_markdown_content
from src.auth import get_user_data_path, get_system_config


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
                        st.session_state.current_doc_id = doc_id
                        st.session_state.current_content = content
                        st.rerun()

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
    
    # 选择文档以查看
    doc_ids = {f"{doc.get('filename', '未知文件')} ({doc.get('doc_id', '未知')})": doc.get("doc_id") for doc in user_docs if doc.get("status") == "处理完成"}
    
    if doc_ids:
        selected_doc_display = st.selectbox("选择文档查看", list(doc_ids.keys()))
        selected_doc_id = doc_ids[selected_doc_display]

        if st.button("查看文档"):
            success, content = get_markdown_content(user_id, selected_doc_id)

            if success:
                st.session_state.current_doc_id = selected_doc_id
                st.session_state.current_content = content
                st.rerun()
            else:
                st.error(f"获取文档内容失败: {content}")

# 显示处理结果
if "current_doc_id" in st.session_state and "current_content" in st.session_state:
    doc_id = st.session_state.current_doc_id
    content = st.session_state.current_content

    # 获取文档元数据
    metadata = get_document_metadata(user_id, doc_id)
    filename = metadata.get("filename", "未知文件") if metadata else "未知文件"

    # 显示文档信息
    st.subheader(f"处理结果：{filename}")

    # 创建选项卡
    tab1, tab2 = st.tabs(["内容预览", "原始Markdown"])

    # 获取图片目录的URL路径
    pdf_name_without_ext = os.path.splitext(filename)[0]
    user_output_dir = get_user_data_path(user_id, "output")
    images_dir = os.path.join(
        user_output_dir,
        doc_id,
        pdf_name_without_ext,
        "auto",
        "images"
    )
    
    # 检查图片目录是否存在
    if os.path.exists(images_dir):
        # 获取图片文件列表
        image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        # 创建图片URL映射
        image_urls = {}
        for img_file in image_files:
            # 构建图片的完整路径
            img_path = os.path.join(images_dir, img_file)
            # 将相对路径转换为绝对路径
            abs_img_path = os.path.abspath(img_path)
            # 创建一个可访问的URL
            image_urls[img_file] = abs_img_path
        
        # 修改markdown内容中的图片引用
        modified_content = content
        # 查找并替换所有图片引用
        img_pattern = r'!\[(.*?)\]\((images/([^)]+))\)'
        
        def replace_img_path(match):
            alt_text = match.group(1)
            img_filename = match.group(3)
            if img_filename in image_urls:
                # 使用data URI方案直接嵌入图片
                try:
                    with open(image_urls[img_filename], "rb") as img_file:
                        import base64
                        img_data = base64.b64encode(img_file.read()).decode()
                        img_type = img_filename.split('.')[-1].lower()
                        if img_type == 'jpg':
                            img_type = 'jpeg'
                        return f'![{alt_text}](data:image/{img_type};base64,{img_data})'
                except Exception as e:
                    st.error(f"加载图片失败: {e}")
                    return f'![{alt_text}](无法加载图片)'
            return match.group(0)
        
        modified_content = re.sub(img_pattern, replace_img_path, content)
    else:
        modified_content = content
        st.warning("未找到图片目录，图片可能无法正常显示")

    # 内容预览选项卡
    with tab1:
        st.markdown(modified_content)

    # 原始Markdown选项卡
    with tab2:
        st.text_area("Markdown源码", content, height=500)
    
    # 清除当前显示
    if st.button("清除预览内容"):
        del st.session_state.current_doc_id
        del st.session_state.current_content
        st.rerun()




