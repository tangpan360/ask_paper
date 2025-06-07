# ask_paper: 论文问答系统

这个系统能够上传PDF论文并处理成markdown格式，构建索引并进行智能问答。

## 项目结构

```
/
├── app.py                  # 主入口文件
├── pages/                  # Streamlit多页面
│   ├── 00_登录注册.py      # 用户登录注册页面
│   ├── 01_上传文档.py      # PDF上传和处理页面
│   ├── 02_构建索引.py      # 查看文档和构建索引页面  
│   ├── 03_论文问答.py      # 问答页面
│   └── 04_管理中心.py      # 管理员管理中心页面
├── src/                    # 核心代码
│   ├── pdf_processor.py    # PDF处理相关功能
│   ├── build_index.py      # 索引构建功能
│   ├── retriever.py        # 检索和问答功能
│   ├── auth.py             # 用户认证和管理
│   ├── admin.py            # 管理员功能
│   └── utils.py            # 工具函数
├── data/                   # 存储上传的PDF文件
│   └── {user_id}/          # 按用户ID隔离数据
├── output/                 # 存储处理后的PDF输出
│   └── {user_id}/          # 按用户ID隔离输出
├── storage/                # 存储索引文件
│   └── {user_id}/          # 按用户ID隔离存储
│       └── {document_id}/  # 每个文档的索引存储在单独目录
│           ├── full_text/  # 全文索引
│           └── source/     # 源文本索引
├── db/                     # 数据库文件
│   ├── users.json          # 用户信息数据库
│   ├── admin.json          # 管理员设置数据库
│   └── system_config.json  # 系统配置数据库
└── config/                 # 系统配置目录
    └── config.yaml         # 系统配置文件
```

## 功能概述

1. **用户认证管理**：用户注册、登录和权限管理
2. **PDF上传与处理**：上传PDF文件，使用magic-pdf工具处理成markdown格式
3. **索引构建**：为处理后的文档构建知识索引，为问答做准备
4. **论文问答**：基于已索引的文档进行智能问答
5. **系统管理**：管理员可进行用户管理和系统设置

## 实施计划

### 阶段一：项目基础结构搭建

- [x] 创建README.md和项目规划
- [x] 创建项目目录结构
  - [x] 创建主目录和子目录
  - [x] 设置目录权限
- [x] 设置环境依赖
  - [x] 创建requirements.txt
  - [x] 确认conda环境"mineru"可用

### 阶段二：用户认证系统开发

#### 1. 认证模块 (src/auth.py)

- [ ] 实现用户注册功能
  ```python
  def register_user(username, password, email=None):
      # 用户注册并保存到数据库
  ```
- [ ] 实现用户登录验证
  ```python
  def authenticate_user(username, password):
      # 验证用户身份
  ```
- [ ] 实现用户会话管理
  ```python
  def create_user_session(user_id):
      # 创建用户会话
  ```
- [ ] 实现数据隔离机制
  ```python
  def get_user_data_path(user_id, data_type):
      # 获取用户特定的数据路径
  ```
- [ ] 实现角色和权限管理
  ```python
  def check_user_role(user_id):
      # 检查用户角色（普通用户/管理员）
  ```
- [ ] 实现系统设置控制
  ```python
  def get_system_config(setting_name):
      # 获取系统配置设置
  ```

#### 2. 管理员模块 (src/admin.py)

- [ ] 实现用户管理功能
  ```python
  def list_all_users():
      # 列出所有用户信息
  ```
  ```python
  def disable_user(user_id):
      # 禁用用户账户
  ```
  ```python
  def delete_user(user_id):
      # 删除用户账户及其所有数据
  ```
  ```python
  def change_user_role(user_id, new_role):
      # 更改用户角色
  ```
- [ ] 实现系统设置管理
  ```python
  def update_system_config(setting_name, value):
      # 更新系统配置
  ```
  ```python
  def toggle_registration(enabled):
      # 启用/禁用用户注册功能
  ```
- [ ] 实现使用统计和监控
  ```python
  def get_usage_statistics():
      # 获取系统使用统计信息
  ```

#### 3. 登录注册页面 (pages/00_登录注册.py)

- [ ] 实现登录界面
  ```python
  # 登录表单
  with st.form("login_form"):
      # 登录表单内容
  ```
- [ ] 实现注册界面
  ```python
  # 注册表单
  with st.form("register_form"):
      # 注册表单内容
  ```
- [ ] 实现会话状态管理
  ```python
  # 检查用户登录状态
  if "user_id" not in st.session_state:
      # 显示登录界面
  ```
- [ ] 检查注册功能是否启用
  ```python
  # 检查是否允许注册
  if get_system_config("allow_registration"):
      # 显示注册选项
  ```

#### 4. 管理中心页面 (pages/04_管理中心.py)

- [ ] 实现管理员身份验证
  ```python
  # 检查是否为管理员
  if not is_admin(st.session_state.user_id):
      st.error("您没有访问此页面的权限")
      st.stop()
  ```
- [ ] 实现用户管理界面
  ```python
  # 用户管理部分
  with st.expander("用户管理"):
      # 显示所有用户
      users = list_all_users()
      # 用户操作按钮
  ```
- [ ] 实现系统设置界面
  ```python
  # 系统设置部分
  with st.expander("系统设置"):
      # 各种系统设置选项
  ```
- [ ] 实现使用统计界面
  ```python
  # 使用统计部分
  with st.expander("使用统计"):
      # 显示系统使用统计信息
  ```

### 阶段三：核心功能模块开发

#### 1. 文档管理模块 (src/utils.py)

- [ ] 实现文档ID生成和管理函数
  ```python
  def generate_document_id():
      # 生成唯一文档ID
  ```
- [ ] 实现文档状态跟踪和更新
  ```python
  def update_document_status(user_id, doc_id, status):
      # 更新文档状态
  ```
- [ ] 实现文档元数据存储
  ```python
  def save_document_metadata(user_id, doc_id, metadata):
      # 保存文档元数据
  ```

#### 2. PDF处理模块 (src/pdf_processor.py)

- [ ] 实现PDF文件保存功能
  ```python
  def save_pdf(user_id, uploaded_file, doc_id):
      # 保存上传的PDF文件到用户特定目录
  ```
- [ ] 实现调用conda环境的函数
  ```python
  def process_pdf_with_magic(user_id, pdf_path, doc_id):
      # 调用magic-pdf处理PDF
  ```
- [ ] 实现markdown提取和读取
  ```python
  def get_markdown_content(user_id, doc_id):
      # 获取处理后的markdown内容
  ```

#### 3. 索引构建模块 (src/build_index.py)

- [ ] 调整为针对单个文档构建索引
  ```python
  def build_index_for_document(user_id, doc_id):
      # 为特定用户的特定文档构建索引
  ```
- [ ] 实现按用户和文档ID管理索引存储
  ```python
  def get_index_storage_path(user_id, doc_id):
      # 获取索引存储路径
  ```

#### 4. 检索模块 (src/retriever.py)

- [ ] 调整为按用户和文档ID加载特定索引
  ```python
  def load_index_for_document(user_id, doc_id):
      # 加载特定用户的特定文档索引
  ```
- [ ] 实现针对特定文档的问答功能
  ```python
  def get_chat_engine_for_document(user_id, doc_id):
      # 获取文档专用问答引擎
  ```

### 阶段四：用户界面开发

#### 1. 主入口页面 (app.py)

- [ ] 设置应用标题、图标
- [ ] 实现用户认证检查
- [ ] 实现简单的导航和应用介绍
- [ ] 显示当前用户的文档处理状态概览
- [ ] 根据用户角色显示不同的导航选项

#### 2. 上传页面 (pages/01_上传文档.py)

- [ ] 实现用户认证检查
- [ ] 实现拖拽和点击上传功能
  ```python
  # 文件上传部分
  uploaded_file = st.file_uploader("上传PDF论文", type="pdf", ...)
  ```
- [ ] 实现上传后的处理流程
  ```python
  # 处理流程
  if uploaded_file is not None:
      # 处理文件
  ```
- [ ] 显示处理状态和进度
- [ ] 完成后显示markdown内容

#### 3. 索引页面 (pages/02_构建索引.py)

- [ ] 实现用户认证检查
- [ ] 显示当前用户的已处理文档列表
- [ ] 实现"构建索引"按钮和逻辑
- [ ] 显示索引构建状态和进度

#### 4. 问答页面 (pages/03_论文问答.py)

- [ ] 实现用户认证检查
- [ ] 实现当前用户的文档选择功能
- [ ] 实现聊天界面
- [ ] 集成检索模块进行问答

### 阶段五：系统集成和调试

- [ ] 完整工作流程测试
  - [ ] 登录→上传→处理→索引→问答流程测试
  - [ ] 管理员功能测试
- [ ] 边界情况处理
  - [ ] 认证失败处理
  - [ ] 文件上传失败处理
  - [ ] PDF处理失败处理
  - [ ] 索引构建失败处理
- [ ] 用户体验优化
  - [ ] 添加加载指示器和进度条
  - [ ] 优化页面布局
  - [ ] 添加错误提示和用户指导
- [ ] 多用户并发测试
  - [ ] 确保数据隔离有效
  - [ ] 测试多用户同时使用的性能

## 开发注意事项

1. **用户角色与权限**：
   - 系统支持两种角色：普通用户和管理员
   - 管理员可以管理用户、配置系统设置
   - 普通用户只能管理自己的文档和数据

2. **用户数据隔离**：
   - 所有数据按用户ID进行隔离存储
   - 确保用户只能访问自己的文档和数据
   - 管理员可以查看所有用户数据统计，但不直接访问内容

3. **文件存储命名规则**：
   - PDF文件：`data/{user_id}/{doc_id}/{filename}.pdf`
   - 处理结果：`output/{user_id}/{doc_id}/auto/{filename}.md`
   - 索引文件：`storage/{user_id}/{doc_id}/full_text/` 和 `storage/{user_id}/{doc_id}/source/`

4. **状态管理**：
   - 使用Streamlit的`session_state`管理用户会话和文档状态
   - 状态包括：已上传、处理中、处理完成、索引构建中、索引构建完成

5. **环境调用**：
   - 使用`subprocess`模块调用conda环境中的命令
   - 命令格式：`conda run -n mineru magic-pdf -p "input_name.pdf" -o output -m auto`

6. **安全性考虑**：
   - 密码加密存储
   - 防止路径遍历攻击
   - 限制用户文件大小和数量
   - 管理员操作日志记录

7. **系统配置选项**：
   - 是否允许新用户注册
   - 单用户最大文档数量限制
   - 单文档最大大小限制
   - 并发处理任务数限制

## 开发流程

1. 先完成用户认证和管理系统
2. 修改基础结构和工具函数以支持多用户
3. 实现PDF上传和处理功能，并测试
4. 实现索引构建功能，并测试
5. 实现问答功能，并测试
6. 实现管理员功能，并测试
7. 整合所有功能，完成最终调试
8. 进行多用户并发测试

## 完成情况追踪

以下是各功能模块的完成情况：

### 基础结构
- [x] 创建项目规划和README.md
- [x] 创建目录结构
- [x] 设置环境依赖

### 用户认证系统
- [ ] 认证模块 (src/auth.py)
- [ ] 管理员模块 (src/admin.py)
- [ ] 登录注册页面
- [ ] 管理中心页面

### 核心功能模块
- [ ] 文档管理模块
- [ ] PDF处理模块
- [ ] 索引构建模块
- [ ] 检索模块

### 用户界面
- [ ] 主入口页面
- [ ] 上传页面
- [ ] 索引页面
- [ ] 问答页面

### 系统集成和调试
- [ ] 完整工作流程测试
- [ ] 边界情况处理
- [ ] 用户体验优化
- [ ] 多用户并发测试

## 依赖库

```
streamlit
streamlit-authenticator
llama-index
python-dotenv
subprocess
uuid
bcrypt
pyyaml
```