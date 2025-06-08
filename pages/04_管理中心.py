import streamlit as st
import sys
import os
import pandas as pd
import humanize
import datetime

# 添加项目根目录到python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.admin import (
    list_all_users, disable_user, enable_user, delete_user, change_user_role,
    update_system_config, toggle_registration, get_usage_statistics
)
from src.auth import is_admin, get_system_config

# 设置页面标题
st.set_page_config(
    page_title="管理中心",
    page_icon="⚙️",
    layout="wide",
)

# 检查登录状态
if "user_id" not in st.session_state or not st.session_state.user_id:
    st.error("请先登录")
    st.stop()

# 检查管理员权限
if not is_admin(st.session_state.user_id):
    st.error("您没有访问此页面的权限")
    st.stop()

# 显示管理员欢迎信息
st.title("⚙️ 系统管理中心")
st.write(f"欢迎， 管理员 {st.session_state.username}")

# 创建侧边栏菜单
st.sidebar.title("管理功能")
menu = st.sidebar.radio(
    "选择功能",
    ["用户管理", "系统设置", "使用统计"]
)

# 用户管理功能
if menu == "用户管理":
    st.header("用户管理")

    # 获取用户列表
    users = list_all_users()

    # 转换为数据框
    if users:
        df = pd.DataFrame(users)

        # 格式化日期
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")

        # 格式化活跃状态
        if "is_active" in df.columns:
            df["is_active"] = df["is_active"].map({True: "✅ 活跃", False: "❌ 禁用"})

        # 显示用户表格
        st.dataframe(df.set_index("user_id"))

        # 用户操作
        with st.expander("用户操作"):
            # 下拉选择用户
            user_ids = {f"{user['username']} ({user['user_id']})": user["user_id"] for user in users}
            selected_user_display = st.selectbox("选择用户", list(user_ids.keys()))
            selected_user_id = user_ids[selected_user_display]

            # 获取当前用户信息
            selected_user = next((user for user in users if user["user_id"] == selected_user_id), None)

            if selected_user:
                # 显示当前状态
                st.write(f"当前状态: {'活跃' if selected_user['is_active'] else '禁用'}")
                st.write(f"当前角色: {'管理员' if selected_user['role'] == 'admin' else '普通用户'}")

                # 操作按钮容器
                col1, col2, col3 = st.columns(3)

                # 启用/禁用按钮
                with col1:
                    if selected_user["is_active"]:
                        if st.button("禁用用户"):
                            success, message = disable_user(selected_user_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        if st.button("启用用户"):
                            success, message = enable_user(selected_user_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

                # 角色更改按钮
                with col2:
                    new_role = "user" if selected_user["role"] == "admin" else "admin"
                    role_text = "降为普通用户" if selected_user["role"] == "admin" else "提升为管理员"

                    if st.button(role_text):
                        success, message = change_user_role(selected_user_id, new_role)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

                # 删除用户按钮
                with col3:
                    if st.button("删除用户", type="primary", help="此操作将删除用户及其所有数据"):
                        # 二次确认
                        st.warning("此操作将永久删除用户及其所有数据！")
                        confirm = st.checkbox("我已了解风险并确认删除")

                        if confirm and st.button("确认删除"):
                            success, message = delete_user(selected_user_id)
                            if success:
                                st.success(message)
                                st.rerun()

                            else:
                                st.error(message)
    else:
        st.info("没有找到用户")

# 系统设置功能
elif menu == "系统设置":
    st.header("系统设置")

    # 用户注册设置
    with st.expander("注册设置"):
        # 获取当前设置
        allow_registration = get_system_config("allow_registration")

        # 当前注册状态
        st.write(f"当前状态：{'允许注册' if allow_registration else '禁止注册'}")

        # 切换注册设置
        if allow_registration:
            if st.button("禁止新用户注册"):
                success, message = toggle_registration(False)
                if success:
                    st.success("已禁止新用户注册")
                    st.error(message)
                else:
                    st.error(message)
        else:
            if st.button("允许新用户注册"):
                success, message = toggle_registration(True)
                if success:
                    st.success("允许新用户注册")
                    st.rerun()
                else:
                    st.error(message)

    # 文档限制设置
    with st.expander("文档限制设置"):
        # 获取当前设置
        max_documents = get_system_config("max_documents_per_user")
        max_size = get_system_config("max_document_size_mb")
        max_tasks = get_system_config("max_concurrent_tasks")

        # 显示和修改设置
        new_max_documents = st.number_input("每个用户最大文档数量", min_value=1, value=max_documents)
        new_max_size = st.number_input("每个文档最大大小 (MB)", min_value=1, value=max_size)
        new_max_tasks = st.number_input("最大并发处理任务数", min_value=1, value=max_tasks)

        # 更新按钮
        if st.button("更新设置"):
            # 更新文档数量限制
            if new_max_documents != max_documents:
                success, message = update_system_config("max_documents_per_user", new_max_documents)
                if not success:
                    st.error(f"更新文档数量限制失败：{message}")
            
            # 更新文档大小限制
            if new_max_size != max_size:
                success, message = update_system_config("max_document_size_mb", new_max_size)
                if not success:
                    st.error(f"更新文档大小限制失败：{message}")
            
            # 更新并发任务限制
            if new_max_tasks != max_tasks:
                success, message = update_system_config("max_concurrent_tasks", new_max_tasks)
                if not success:
                    st.error(f"更新并发任务限制失败：{message}")

            st.success("设置已更新")
            st.rerun()

# 使用功能统计
elif menu == "使用统计":
    st.header("系统使用统计")

    # 获取使用统计
    stats = get_usage_statistics()

    # 格式化时间戳
    timestamp = datetime.datetime.fromisoformat(stats["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"统计时间：{timestamp}")

    # 创建多列布局
    col1, col2 = st.columns(2)

    # 用户统计
    with col1:
        st.subheader("用户统计")
        st.write(f"总用户数: {stats['users']['total']}")
        st.write(f"总文档数：{stats['documents']['indexed']}")
        st.wtire(f"索引率: {stats['documents']['indexed'] / max(1, stats['documents']['total']) *100:.1f}%")

        # 创建文档状态图
        doc_data = {
            "状态": ["已索引", "未索引"],
            "数量": [
                stats['documents']['indexed'],
                stats['documents']['total'] - stats['documents']['indexed']
            ]
        }
        doc_df = pd.DataFrame(doc_data)
        st.bar_chart(doc_df.set_index("状态"))

    # 存储使用情况
    st.subheader("存储使用情况")

    # 格式化存储大小
    storage_data = {
        "目录": ["数据文件", "处理输出", "索引文件"],
        "大小 (MB)": [
            stats['storage']['data'] / (1024 * 1024),
            stats['storage']['output'] / (1024 * 1024),
            stats['storage']['storage'] / (1024 * 1024)
        ],
        "人类可读大小": [
            humanize.naturalsize(stats['storage']['data']),
            humanize.naturalsize(stats['storage']['output']),
            humanize.naturalsize(stats['storage']['storage'])
        ]
    }
    storage_df = pd.DataFrame(storage_data)

    # 显示存储表格
    st.dataframe(storage_df.set_index("目录"))

    # 显示存储图表
    st.bar_chart(storage_df[["目录", "大小 (MB)"]].set_index("目录"))

    # 刷新按钮
    if st.button("刷新统计数据"):
        st.rerun()
