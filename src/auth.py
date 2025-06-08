import os
import json
import uuid
import hashlib
import datetime
from typing import Dict, Any, Optional, Tuple


# 用户数据文件路径
USER_DB_PATH = os.path.join("db", "users.json")

# 确保目录存在
os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)

# 系统配置文件路径
SYSTEM_CONFIG_PATH = os.path.join("db", "system_config.json")

def _load_users() -> Dict[str, Any]:
    """加载用户数据"""
    if not os.path.exists(USER_DB_PATH):
        # 创建空的用户数据文件
        with open(USER_DB_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    
    with open(USER_DB_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # 如果文件格式错误，返回空字典
            return {}
        
def _save_users(users_data: Dict[str, Any]) -> None:
    """保存用户数据"""
    with open(USER_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

def _hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str, email: Optional[str] = None) -> Tuple[bool, str]:
    """
    注册新用户

    参数：
        username: 用户名
        password: 密码
        email: 可选的邮箱

    返回：
        (成功状态，消息)
    """
    # 检查是否允许注册
    if not get_system_config("allow_registration"):
        return False, "系统当前不允许新用户注册"
    
    # 加载用户数据
    users = _load_users()

    # 检查用户名是否已存在
    for user_id, user_data in users.items():
        if user_data["username"] == username:
            return False, "用户名已存在"
        
    # 创建新用户
    user_id = str(uuid.uuid4())
    users[user_id] = {
        "username": username,
        "password": _hash_password(password),
        "email": email,
        "role": "user",  # 默认为普通用户
        "created_at": datetime.datetime.now().isoformat(),
        "is_active": True,
    }

    # 保存用户数据
    _save_users(users)

    # 创建用户数据目录
    for dir_type in ["data", "output", "storage"]:
        user_dir = os.path.join(dir_type, user_id)
        os.makedirs(user_dir, exist_ok=True)

    return True, user_id

def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    验证用户凭据

    参数：
        username: 用户名
        password: 密码
    返回：
        (成功状态，用户ID或None)
    """
    # 加载用户数据
    users = _load_users()

    # 查找用户
    for user_id, user_data in users.items():
        if user_data.get("username") == username:
            # 检查用户是否被禁用
            if not user_data.get("is_active", True):
                return False, None
            
            # 验证密码
            if user_data.get("password") == _hash_password(password):
                return True, user_id
            else:
                return False, None
        
    return False, None

def create_user_session(user_id: str) -> Dict[str, Any]:
    """
    创建用户会话数据

    参数：
        user_id: 用户ID

    返回：
        会话数据字典
    """
    # 加载用户数量
    users = _load_users()

    if user_id not in users:
        raise ValueError("用户不存在")
    
    user_data = users[user_id]

    # 创建会话数据
    session_data = {
        "user_id": user_id,
        "username": user_data.get("username"),
        "role": user_data.get("role", "user"),
        "login_time": datetime.datetime.now().isoformat(),
    }

    return session_data

def get_user_data_path(user_id: str, data_type: str) -> str:
    """
    获取用户特定的数据路径

    参数：
        user_id: 用户ID
        date_type: 数据类型 ("data", "output", "storage")

    返回：
        数据路径字符串
    """
    base_paths = {
        "data": "data",
        "output": "output",
        "storage": "storage",
    }

    if data_type not in base_paths:
        raise ValueError(f"不支持的数据类型: {data_type}")
    
    path = os.path.join(base_paths[data_type], user_id)
    os.makedirs(path, exist_ok=True)
    return path

def check_user_role(user_id: str) -> str:
    """
    检查用户角色

    参数：
        user_id: 用户ID

    返回：
        用户角色 ("admin" 或 "user")
    """
    users = _load_users()

    if user_id not in users:
        raise ValueError("用户不存在")

    return users[user_id].get("role", "user")

def is_admin(user_id: str) -> bool:
    """
    检查用户是否为管理员
    
    参数：
        user_id: 用户ID

    返回：
        True 如果用户是管理员，False 否则
    """
    return check_user_role(user_id) == "admin"

def _load_system_config() -> Dict[str, Any]:
    """加载系统配置"""
    if not os.path.exists(SYSTEM_CONFIG_PATH):
        # 创建默认配置
        default_config = {
            "allow_registration": True,
            "max_documents_per_user": 10,
            "max_document_size_mb": 50,
            "max_concurrent_tasks": 3,
        }
        with open(SYSTEM_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config

    with open(SYSTEM_CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # 如果文件格式错误，返回默认配置
            return {
                "allow_registration": True,
                "max_documents_per_user": 10,
                "max_document_size_mb": 50,
                "max_concurrent_tasks": 3,
            }
        
def _save_system_config(config: Dict[str, Any]) -> None:
    """保存系统配置"""
    with open(SYSTEM_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_system_config(setting_name: str) -> Any:
    """
    获取系统配置设置

    参数：
        setting_name: 设置名称

    返回：
        设置值
    """
    config = _load_system_config()
    return config.get(setting_name)

# 初始化管理员用户（如果不存在）
def initialize_admin_user():
    """初始化管理员用户（如果不存在）"""
    users = _load_users()

    # 检查是否存在管理员用户
    admin_exists = False
    for user_data in users.values():
        if user_data.get("role") == "admin":
            admin_exists = True
            break

    if not admin_exists:
        # 创建默认管理员用户
        admin_id = str(uuid.uuid4())
        users[admin_id] = {
            "username": "admin",
            "password": _hash_password("admin123"),  # 默认密码
            "email": "admin@example.com",
            "role": "admin",
            "create_at": datetime.datetime.now().isoformat(),
            "is_active": True,
        }
        _save_users(users)

        # 创建管理员数据目录
        for dir_type in ["data", "output", "storage"]:
            admin_dir = os.path.join(dir_type, admin_id)
            os.makedirs(admin_dir, exist_ok=True)

        print("已创建默认管理员用户: admin")

# 初始化默认管理员用户
initialize_admin_user()
