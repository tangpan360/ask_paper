import os
import json
import shutil
import datetime
from typing import Dict, Any, List, Optional, Tuple
from src.auth import _load_users, _save_users, _load_system_config, _save_system_config


def list_all_users() -> List[Dict[str, Any]]:
    """
    列出所有用户信息

    返回：
        用户信息列表
    """
    users = _load_users()

    # 格式化用户数据以返回
    user_list = []
    for user_id, user_data in users.items():
        # 排除敏感信息
        user_info = {
            "user_id": user_id,
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "role": user_data.get("role", "user"),
            "created_at": user_data.get("created_at"),
            "is_active": user_data.get("is_active", True),
        }
        user_list.append(user_info)

    return user_list

def disable_user(user_id: str) -> Tuple[bool, str]:
    """
    禁用用户账户

    参数：
        user_id: 用户ID

    返回：
        (成功状态，消息)
    """
    users = _load_users()
    
    if user_id not in users:
        return False, "用户不存在"
    
    # 检查是否为最后一个管理员
    if users[user_id].get("role") == "admin":
        admin_count = sum(1 for u in users.values() if u.get("role") == "admin" and u.get("is_active", True))
        if admin_count <= 1:
            return False, "不能禁用最后一个活跃的管理员账户，至少需要一个管理员账户"
        
    users[user_id]["is_active"] = False
    _save_users(users)

    return True, "用户已禁用"

def enable_user(user_id: str) -> Tuple[bool, str]:
    """
    启用用户账户

    参数：
        user_id: 用户ID

    返回：
        (成功状态，消息)
    """
    users = _load_users()

    if user_id not in users:
        return False, "用户不存在"
    
    users[user_id]["is_active"] = True
    _save_users(users)

    return True, "用户已启用"

def delete_user(user_id: str) -> Tuple[bool, str]:
    """
    删除用户账户及其所有数据

    参数：
        user_id: 用户ID

    返回：
        (成功状态，消息)
    """
    users = _load_users()

    if user_id not in users:
        return False, "用户不存在"
    
    # 检查是否为最后一个管理员
    if users[user_id].get("role") == "admin":
        admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
        if admin_count <= 1:
            return False, "不能删除最后一个活跃的管理员账户，至少需要一个管理员账户"
        
    # 删除用户数据目录
    for dir_type in ["data", "output", "storage"]:
        user_dir = os.path.join(dir_type, user_id)
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)

    # 从用户数据库中删除
    del users[user_id]
    _save_users(users)

    return True, "用户及其数据已删除"

def change_user_role(user_id: str, new_role: str) -> Tuple[bool, str]:
    """
    更改用户角色

    参数：
        user_id: 用户ID
        new_role: 新角色（"admin" 或 "user"）

    返回：
        (成功状态，消息)
    """
    if new_role not in ["admin", "user"]:
        return False, "无效的角色"
    
    users = _load_users()

    if user_id not in users:
        return False, "用户不存在"
    
    # 检查是否降级最后一个管理员
    if users[user_id].get("role") == "admin" and new_role == "user":
        admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
        if admin_count <= 1:
            return False, "不能降级最后一个活跃的管理员账户，至少需要一个管理员账户"
        
    users[user_id]["role"] == new_role
    _save_users(users)

    return True, f"用户角色已更改为 {new_role}"

def update_system_config(setting_name: str, value: Any) -> Tuple[bool, str]:
    """
    更新系统配置

    参数：
        setting_name: 设置名称
        value: 新值
    
    返回：
        (成功状态，消息)
    """
    config = _load_system_config()

    # 验证设置是否存在
    if setting_name not in config:
        return False, f"无效的设置名称: {setting_name}"
    
    # 验证数据类型
    expected_type = type(config[setting_name])
    if not isinstance(value, expected_type):
        return False, f"设置 {setting_name} 的值类型不正确，期望 {expected_type.__name__}"
    
    # 更新设置
    config[setting_name] = value
    _save_system_config(config)

    return True, "系统配置已更新"

def toggle_registration(enable: bool) -> Tuple[bool, str]:
    """
    启用/禁用用户注册功能

    参数：
        enable: 是否启用注册

    返回：
        (成功状态，消息)
    """
    return update_system_config("allow_registration", enable)

def get_usage_statistics() -> Dict[str, Any]:
    """
    获取系统使用统计信息

    返回：
        统计信息字典
    """
    users = _load_users()

    # 统计用户数量
    total_users = len(users)
    active_users = sum(1 for u in users.values() if u.get("is_active", True))
    admin_users = sum(1 for u in users.values() if u.get("role") == "admin")

    # 统计文档数量
    total_documents = 0
    total_indexed_documents = 0
    for user_id in users:
        user_data_dir = os.path.join("data", user_id)
        if os.path.exists(user_data_dir):
            # 统计文档数量
            for item in os.listdir(user_data_dir):
                doc_dir = os.path.join(user_data_dir, item)
                if os.path.isdir(doc_dir):
                    total_documents += 1

                    # 检查是否已索引
                    index_dir = os.path.join("storage", user_id, item)
                    if os.path.exists(index_dir):
                        total_indexed_documents += 1

    # 统计存储使用情况
    storage_usage = {
        "data": _get_directory_size("data"),
        "output": _get_directory_size("output"),
        "storage": _get_directory_size("storage"),
    }

    # 返回统计信息
    return {
        "user": {
            "total": total_users,
            "active": active_users,
            "admin": admin_users,
        },
        "documents": {
            "total": total_documents,
            "indexed": total_indexed_documents,
        },
        "storage": storage_usage,
        "timestamp": datetime.datetime.now().isoformat(),
    }

def _get_directory_size(path: str) -> int:
    """
    获取目录大小（字节）

    参数：
        path: 目录路径

    返回：
        目录大小（字节）
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)

    return total_size
