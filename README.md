# 青禾 · AI 校园社区

> 让每一次校园连接，都被 AI 温柔接住。

传智杯「AI Web 网页开发挑战赛」参赛作品 · 智慧校园方向。

一个面向高校学生的 AI 校园社区：把「校园事务问答、发帖写作助手、搭子匹配」三种 AI 能力
嵌进真实的社区场景，并配备私信与后台管理。

技术栈：**FastAPI + SQLAlchemy + MySQL 8.0 + Vue 3 + Vite + TailwindCSS**

---

## 一、赛题理解与设计思路

### 1. 这个赛道考什么

| 层次 | 考察内容 | 本项目的回应 |
|---|---|---|
| 界面工程 | 结构清晰、交互合理、视觉统一 | Vue 3 组件化 + Tailwind 设计系统 + 暗色模式 + 响应式 |
| AI 集成 | 调用大模型，处理流式 / 加载 / 错误 / 重试 | SSE 流式问答 + 来源引用 + 置信度 + 失败重试 |
| 场景设计 | Prompt、对话流程、AI 出错如何引导 | 三种能力嵌进真实动线；AI 只建议，不代替用户行动 |

### 2. 为什么做「AI 校园社区」

校园信息是碎的：通知在教务系统、问路在班级群、二手在朋友圈、找搭子在群公告。
同学真正缺的不是又一个论坛，而是：

1. **能立刻回答问题的人** → 校园问答（RAG）
2. **把话说清楚的工具** → 发帖写作助手
3. **遇到同频同学的机会** → 搭子匹配

---

## 二、功能清单

### 社区
- 注册 / 登录（scrypt 加盐哈希 + HMAC 签名 Token）
- 个人资料与兴趣标签（专业、年级、简介、最多 8 个标签）
- 帖子发布 / 浏览 / 搜索 / 分类筛选 / 最新与最热排序
- 5 大分类：学习互助、社团活动、二手闲置、失物招领、校园生活
- 点赞、评论、浏览量、热度算法
- **私信**：会话列表、历史消息、WebSocket 实时推送与在线状态
- **后台管理**：数据概览、帖子删除、用户权限管理
- 暗色模式、响应式布局

### AI 能力
| 能力 | 入口 | 说明 |
|---|---|---|
| 校园事务问答 | AI 助手页 / 悬浮球 | 26 类校园知识，TF-IDF 检索 + 来源引用 + 置信度，SSE 流式输出 |
| 发帖写作助手 | 发帖弹窗「AI 帮我润色」 | 标题建议、润色正文、分类推荐、标签抽取、摘要、违规检测 |
| 搭子匹配 | 个人主页「AI 搭子匹配」 | 兴趣标签 Jaccard + 简介文本相似度，输出匹配度与可解释理由 |

> 所有 AI 输出标注「仅供参考」；**AI 不会自动发帖、评论或私信**。

---

## 三、技术架构

```
浏览器
  └─ Vue 3 + Vue Router + TailwindCSS（Vite 构建）
       ├─ /api  →  代理到 FastAPI
       └─ /ws   →  代理到 FastAPI WebSocket

FastAPI（Python 3.10+）
  ├─ 认证：scrypt 哈希 + HMAC Token（无第三方 JWT 依赖）
  ├─ ORM：SQLAlchemy 2.0（MySQL 8.0 / SQLite 双支持）
  ├─ AI ：本地引擎（TF-IDF + 规则） ⇄ DeepSeek 云端（自动降级）
  ├─ 实时：WebSocket 私信推送
  └─ 文档：Swagger UI  /docs
```

### 目录结构

```
E:\小肥鱼
├─ 启动.cmd                 # 一键启动前后端并打开浏览器
├─ 一键安装.cmd             # 安装依赖 + 初始化数据库
├─ backend/
│  ├─ requirements.txt
│  ├─ .env.example          # 环境变量模板（复制为 .env）
│  ├─ sql/schema.sql        # MySQL 建表脚本（评审/手动导入用）
│  ├─ scripts/init_db.py    # 建库 + 建表 + 演示数据
│  └─ app/
│     ├─ main.py            # FastAPI 入口
│     ├─ config.py          # 只从环境变量读取密钥
│     ├─ db.py models.py schemas.py security.py deps.py serializers.py
│     ├─ seed.py            # 演示数据（8 用户 / 14 帖子 / 12 评论）
│     ├─ ws.py              # WebSocket 连接管理
│     ├─ ai/
│     │  ├─ engine.py       # 本地 AI 引擎
│     │  ├─ knowledge.py    # 26 条校园知识库
│     │  └─ service.py      # DeepSeek 编排 + 降级
│     └─ routers/           # auth users posts ai messages admin meta
└─ frontend/
   ├─ package.json vite.config.ts tailwind.config.js
   └─ src/
      ├─ main.ts App.vue style.css
      ├─ router/  api/  stores/
      ├─ components/  NavBar PostCard Composer AiPanel ToastHost
      └─ views/       Home Post Ai Profile Login Messages Admin
```

---

## 四、快速开始

### 方式一：双击脚本（推荐）

1. 双击 **`一键安装.cmd`**（创建虚拟环境、装依赖、建库建表、写演示数据）
2. 双击 **`启动.cmd`**（启动后端 8000 与前端 5173，并自动打开浏览器）

### 方式二：手动

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\init_db.py
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

# 前端（另开一个终端）
cd frontend
npm install
npm run dev
```

- 前端：<http://127.0.0.1:5173>
- 接口文档：<http://127.0.0.1:8000/docs>

### 数据库配置

`backend/.env` 中二选一：

```ini
# 方式一：完整 URL
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/campus_ai_community?charset=utf8mb4

# 方式二：由 MYSQL_* 自动拼装（DATABASE_URL 留空时生效）
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=campus_ai_community
```

未配置 MySQL 密码时会自动降级到 SQLite（`backend/data/campus.db`），保证开箱即跑。

### 演示账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| `linxiaoman` | `123456` | 管理员 |

其余 7 个账号密码相同：`zhouyihang`、`suwanqing`、`chenmo`、`guxingye`、`heyinuo`、`shenzhiyao`、`jiangyuan`。

### 接入 DeepSeek（可选）

在 `backend/.env` 填入：

```ini
DEEPSEEK_API_KEY=sk-xxxx
DEEPSEEK_MODEL=deepseek-chat
```

不配置时 AI 自动使用本地引擎，完全离线可用。

---

## 五、5 分钟演示脚本

1. **首页**：信息流、分类筛选、热度；切换深色模式。
2. **AI 助手**：点「图书馆几点关门？」→ 流式输出、来源引用、置信度。
3. **发帖 + AI 写作助手**：输入口语化文字 → AI 返回标题/正文/分类/标签 → 强调必须点「应用到正文」才生效。
4. **搭子匹配**：个人主页 →「开始匹配」→ 匹配度与理由。
5. **私信**：两个浏览器窗口分别登录不同账号，发消息实时到达。
6. **后台**：管理员进入 `/admin`，查看数据、删除帖子、调整权限。

---

## 六、接口一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/meta` | 应用信息、分类、AI 模式、统计 |
| POST | `/api/auth/register` `/api/auth/login` | 注册 / 登录 |
| GET | `/api/auth/me` | 当前用户 |
| PUT | `/api/users/me` | 更新资料与标签 |
| GET | `/api/users/{id}` | 用户主页 + TA 的帖子 |
| GET | `/api/posts` | 列表（category / q / sort / limit） |
| POST | `/api/posts` | 发帖 |
| GET | `/api/posts/{id}` | 详情 + 评论 + 相关推荐 |
| POST | `/api/posts/{id}/like` | 点赞 / 取消 |
| GET/POST | `/api/posts/{id}/comments` | 评论列表 / 发表 |
| POST | `/api/ai/write` | AI 写作助手 |
| POST | `/api/ai/match` | AI 搭子匹配 |
| POST | `/api/ai/chat` | AI 问答（SSE 流式） |
| GET | `/api/messages/conversations` | 会话列表 |
| GET/POST | `/api/messages/{peer_id}` | 历史消息 / 发送 |
| WS | `/ws?token=...` | 私信实时推送 |
| GET | `/api/admin/overview` `/api/admin/users` | 后台数据 |
| DELETE | `/api/admin/posts/{id}` | 删除帖子 |

完整的交互式文档见 <http://127.0.0.1:8000/docs>。

---

## 七、AI 双引擎说明

```
请求 → 是否配置 DEEPSEEK_API_KEY？
        ├─ 是 → 调用 DeepSeek（超时 20s）
        │        └─ 失败/超时 → 自动降级
        └─ 否 → 本地引擎
                  ├─ 问答：TF-IDF 向量 + 余弦相似度检索知识库
                  ├─ 写作：分词 + 分类规则 + 标签抽取 + 摘要 + 敏感词
                  └─ 匹配：Jaccard 标签相似度 + 文本向量相似度
```

本地问答的可解释性：返回答案的同时给出**来源**（如「校图书馆官网」）与**置信度**；
低于阈值时不硬答，而是引导用户换说法或去社区求助。

---

## 八、边界与合规

- AI 不代替用户行动：不自动发帖、不自动评论、不自动私信
- AI 写作建议需用户点击「应用到正文」后才会进入表单
- 所有 AI 输出统一标注「AI 生成内容仅供参考」
- 密钥只从环境变量读取，`.env` 已在 `.gitignore` 中
- 密码 scrypt 加盐哈希 + 定长比较；Token 带过期时间
- 内置敏感词检测，违规内容会提示修改

---

## 九、评分点对照

| 评分维度 | 本项目对应 |
|---|---|
| 完成度 | 社区 + AI 三能力 + 私信 + 后台，全部可运行 |
| 技术难度 | 自研检索/分词算法、SSE 流式、WebSocket、双引擎降级 |
| 代码质量 | 前后端分层、路由/服务/序列化分离、函数注释完整 |
| 创新性 | AI 嵌入「问答 → 发帖 → 匹配」完整动线 |
| 用户体验 | 暗色模式、响应式、加载/空/错误态、微动效 |
| 工程规范 | 一键安装、一键启动、环境变量隔离、SQL 脚本、接口文档 |
| 答辩表现 | README 赛题分析 + 5 分钟演示脚本 |

---

## 十、常见问题

**Q：端口被占用？**
修改 `backend/.env` 的 `PORT` 或启动命令中的 `--port`，并同步修改 `frontend/vite.config.ts` 的代理目标。

**Q：MySQL 连接失败？**
先确认服务已启动（`Get-Service MySQL80`），再核对 `backend/.env` 中的密码；
或清空 `DATABASE_URL` 让它退回 SQLite。

**Q：想重置演示数据？**
删除 MySQL 中的 `campus_ai_community` 库，重新运行 `backend/scripts/init_db.py`；
SQLite 模式则删除 `backend/data/campus.db`。

**Q：前端改端口后 WebSocket 不工作？**
`vite.config.ts` 中 `/ws` 代理需保留 `ws: true`。
