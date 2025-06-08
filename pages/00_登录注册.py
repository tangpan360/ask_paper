import streamlit as st
import sys
import os


# 添加项目根目录到python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.auth import register_user, authenticate_user, create_user_session, get_system_config


# 设置页面标题和图标
st.set_page_config(page_title="登录/注册", page_icon="🔐")

# 初始化session状态
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.user_name = None
if "role" not in st.session_state:
    st.session_state.role = None

# 用户已登录时显示的内容
def show_logged_in_status():
    st.success(f"已登录为：{st.session_state.username}")

    # 显示用户类型
    role_display = "管理员" if st.session_state.role == "admin" else "普通用户"
    st.info(f"用户类型：{role_display}")
    
    # 登出按钮
    if st.button("登出"):
        for key in ["user_id", "username", "role"]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()

# 用户未登录时显示的内容
def show_login_form():
    st.title("🔐 用户登录")

    # 创建标签页
    tab1, tab2 = st.tabs(["登录", "注册"])

    # 登录标签页
    with tab1:
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submit_button = st.form_submit_button("登录")

            if submit_button:
                if not username or not password:
                    st.error("请输入用户名和密码")
                else:
                    success, user_id = authenticate_user(username, password)
                    if success:
                        # 创建会话
                        session_data = create_user_session(user_id)
                        st.session_state.user_id = session_data["user_id"]
                        st.session_state.username = session_data["username"]
                        st.session_state.role = session_data["role"]
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")

    # 注册标签页
    with tab2:
        # 检查是否允许注册
        if not get_system_config("allow_registration"):
            st.warning("系统不允许新用户注册，请联系管理员")
        else:
            with st.form("register_form"):
                new_username = st.text_input("用户名", placeholder="请输入用户名")
                new_password = st.text_input("密码", type="password", placeholder="请输入密码")
                confirm_password = st.text_input("确认密码", type="password", placeholder="请确认密码")
                email = st.text_input("邮箱（可选）", placeholder="请输入邮箱")
                submit_button = st.form_submit_button("注册")

                if submit_button:
                    if not new_username or not new_password:
                        st.error("请输入用户名和密码")
                    elif new_password != confirm_password:
                        st.error("两次输入的密码不一致")
                    else:
                        success, message = register_user(new_username, new_password, email)
                        if success:
                            st.success(f"注册成功！请使用用户名 {new_username} 登录")
                        else:
                            st.error(f"注册失败：{message}")

# 主程序逻辑
def main():
    # 根据登录状态显示不同内容
    if st.session_state.user_id:
        show_logged_in_status()
    else:
        show_login_form()

if __name__ == "__main__":
    main()
