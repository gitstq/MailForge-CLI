<p align="center">
  <h1>📧 MailForge-CLI</h1>
  <p><strong>Lightweight Terminal Email Marketing Intelligent Engine</strong></p>
  <p>轻量级终端邮件营销智能引擎</p>
</p>

<p align="center">
  <a href="#-项目介绍--project-introduction">简体中文</a> ·
  <a href="#-專案介紹--project-introduction-1">繁體中文</a> ·
  <a href="#-project-introduction">English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Zero_Dependencies-Core-success.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Tests-101%20Passed-brightgreen.svg" alt="Tests">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange.svg" alt="Version">
</p>

---

## 🎉 项目介绍 | Project Introduction

**MailForge-CLI** 是一款零核心依赖的轻量级终端邮件营销智能引擎，专为开发者和中小团队打造。它将 SMTP/IMAP 协议操作、邮件模板引擎、联系人管理、营销活动编排、发送分析统计、TUI 可视化仪表盘等能力整合到一个简洁的 CLI 工具中，让你在终端中即可完成从邮件编写到批量发送的全链路操作。

### 💡 灵感来源

受 GitHub Trending 热门项目 **BillionMail**（开源自托管邮件服务器）启发，我们发现很多开发者只需要**邮件营销自动化**能力，而不需要搭建完整的邮件服务器。MailForge-CLI 专注于这一细分场景，以 CLI 工具的形式提供更轻量、更灵活的解决方案。

### ✨ 自研差异化亮点

- 🚫 **零核心依赖** — 核心功能仅使用 Python 标准库，无需安装任何第三方包即可运行
- 📝 **纯 Python 模板引擎** — 自研实现变量替换、条件渲染、循环、17 种内置过滤器、模板继承，无需 Jinja2
- 🎯 **智能联系人管理** — CSV/JSON 自动导入、字段智能映射、分组管理、邮箱去重、批量操作
- 📊 **TUI 可视化仪表盘** — 实时发送统计、活动状态监控、联系人概览（可选 rich 依赖增强）
- 🔒 **AES-256-GCM 加密** — SMTP 密码安全存储，支持环境变量覆盖
- ⚡ **发送速率控制** — 滑动窗口频率限制器，防止触发邮件服务商限制
- 🛡️ **内容安全检查** — 内置垃圾邮件关键词检测，发送前自动预警

---

## ✨ 核心特性 | Core Features

### 📤 SMTP 发送引擎
- **多协议支持** — SMTP / SMTPS / STARTTLS 全覆盖
- **连接池管理** — 高效复用连接，批量发送性能优异
- **Multipart 邮件** — 同时支持 HTML + 纯文本，兼容所有邮件客户端
- **附件支持** — 多文件、大文件分块发送
- **智能重试** — 指数退避自动重试机制，应对临时网络故障
- **队列化发送** — 异步批量发送，支持暂停/恢复

### 📥 IMAP 接收引擎
- **邮件搜索** — 按日期、发件人、主题、未读状态等多维度搜索
- **邮件解析** — 提取正文、附件、邮件头信息
- **退信检测** — 自动识别并标记退信邮件
- **邮件管理** — 自动标记/移动/删除

### 📝 模板引擎（零依赖）
- `{{variable}}` — 变量替换，支持个性化邮件
- `{%if condition%}...{%endif%}` — 条件渲染
- `{%for item in list%}...{%endfor%}` — 循环渲染
- **17 种内置过滤器** — upper, lower, date, default, truncate, nl2br, strip_tags 等
- **模板继承** — extends/block 机制，复用布局
- **模板预览** — 终端内实时预览渲染效果

### 👥 联系人管理
- **多格式导入** — CSV / JSON 自动导入，智能识别字段映射
- **分组管理** — 按标签分组，精准定向发送
- **自动去重** — 基于邮箱地址自动去重
- **批量操作** — 添加、删除、更新、导出

### 📊 营销活动管理
- **活动编排** — 创建、调度、状态跟踪（draft/sending/paused/completed/failed）
- **进度监控** — 实时查看发送进度和成功率
- **活动报告** — 自动生成 JSON/CSV/Markdown 格式报告

### 📈 发送分析
- **成功率统计** — 总体发送成功率、退信率
- **时间段分析** — 按小时/天/周分析发送趋势
- **分组对比** — 不同联系人组的表现对比
- **多格式导出** — JSON / CSV / Markdown

### 🖥️ TUI 仪表盘
- **发送概览** — 总发送量、成功率、退信数
- **实时进度** — 当前活动发送进度条
- **联系人统计** — 分组人数、活跃度
- **快捷键导航** — 键盘操作，高效浏览

---

## 🚀 快速开始 | Quick Start

### 📋 环境要求

| 项目 | 最低要求 |
|------|---------|
| Python | 3.9+ |
| 操作系统 | Windows / macOS / Linux |
| 依赖 | 无（核心功能零依赖） |
| 可选依赖 | rich>=13.0（TUI 增强）、textual>=3.0（高级 TUI） |

### 📦 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/MailForge-CLI.git
cd MailForge-CLI

# 安装（开发模式）
pip install -e .

# 或仅安装可选依赖（TUI 增强）
pip install -r requirements.txt
```

### ⚙️ 初始化配置

```bash
# 交互式初始化
mailforge init

# 或手动设置 SMTP 配置
mailforge config set smtp.host smtp.gmail.com
mailforge config set smtp.port 587
mailforge config set smtp.username your@email.com
mailforge config set smtp.password your_app_password
mailforge config set smtp.tls true
mailforge config set smtp.from_name "Your Name"
mailforge config set smtp.from_email your@email.com
```

### 📧 快速发送第一封邮件

```bash
# 快速发送
mailforge send \
  --to recipient@example.com \
  --subject "Hello from MailForge" \
  --body "This is a test email sent via MailForge-CLI!"

# 使用模板批量发送
mailforge send \
  --template welcome \
  --group subscribers
```

### 🎯 典型工作流

```bash
# 1. 导入联系人
mailforge contact import subscribers.csv

# 2. 创建邮件模板
mailforge template create newsletter

# 3. 创建营销活动
mailforge campaign create "Weekly Newsletter" \
  --template newsletter \
  --group subscribers

# 4. 启动活动
mailforge campaign start 1

# 5. 查看报告
mailforge campaign report 1

# 6. 打开仪表盘
mailforge dashboard
```

---

## 📖 详细使用指南 | Detailed Guide

### 🔧 配置管理

```bash
# 初始化配置文件（~/.mailforge/config.json）
mailforge init

# 查看所有配置
mailforge config list

# 设置配置项
mailforge config set smtp.host smtp.qq.com
mailforge config set smtp.port 465
mailforge config set smtp.username user@qq.com
mailforge config set smtp.password auth_code
mailforge config set smtp.ssl true

# 也支持环境变量覆盖
export MAILFORGE_SMTP_HOST=smtp.gmail.com
export MAILFORGE_SMTP_PORT=587
export MAILFORGE_SMTP_USERNAME=your@email.com
export MAILFORGE_SMTP_PASSWORD=your_password
```

**多账户配置示例** (`~/.mailforge/config.json`)：

```json
{
  "accounts": {
    "primary": {
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "user@gmail.com",
      "password": "encrypted_password",
      "tls": true,
      "from_name": "Team",
      "from_email": "user@gmail.com"
    },
    "backup": {
      "smtp_host": "smtp.qq.com",
      "smtp_port": 465,
      "username": "user@qq.com",
      "password": "encrypted_password",
      "ssl": true,
      "from_name": "Backup",
      "from_email": "user@qq.com"
    }
  },
  "defaults": {
    "rate_limit_per_minute": 30,
    "retry_max_attempts": 3,
    "retry_backoff_factor": 2
  }
}
```

### 👥 联系人管理

```bash
# 从 CSV 导入（自动识别 name/email 列）
mailforge contact import subscribers.csv

# 从 JSON 导入
mailforge contact import contacts.json

# 列出所有联系人
mailforge contact list

# 按组筛选
mailforge contact list --group subscribers

# 查看分组
mailforge contact groups

# 导出联系人
mailforge contact export --format json --output my_contacts.json
```

**CSV 格式示例**：

```csv
name,email,group
Alice,alice@example.com,subscribers
Bob,bob@example.com,subscribers
Charlie,charlie@example.com,vip
```

### 📝 模板管理

```bash
# 列出模板
mailforge template list

# 创建模板
mailforge template create newsletter

# 预览模板渲染效果
mailforge template preview newsletter --data '{"name": "Alice"}'
```

**模板语法示例**：

```html
<h1>你好，{{name}}！</h1>

<p>感谢你订阅我们的{{newsletter_type}}。</p>

{%if is_premium%}
<p>🌟 你是我们的高级会员，享受专属权益。</p>
{%else%}
<p>升级高级会员，解锁更多功能！</p>
{%endif%}

<ul>
{%for item in updates%}
<li>{{item.title}} - {{item.date|date:"Y-m-d"}}</li>
{%endfor%}
</ul>

<p>发送时间：{{send_date|date:"Y年m月d日"}}</p>
```

### 📊 营销活动

```bash
# 创建活动
mailforge campaign create "Black Friday Sale" \
  --template promo \
  --group subscribers \
  --schedule "2025-06-01 09:00"

# 列出所有活动
mailforge campaign list

# 启动活动
mailforge campaign start 1

# 暂停活动
mailforge campaign pause 1

# 查看活动报告
mailforge campaign report 1
```

### 📈 发送统计

```bash
# 查看总体统计
mailforge analytics

# 按时间段筛选
mailforge analytics --period 7d

# 导出报告
mailforge analytics --export markdown --output report.md
```

### 📥 收件箱管理

```bash
# 查看收件箱
mailforge inbox

# 搜索邮件
mailforge inbox search --from sender@example.com
mailforge inbox search --subject "newsletter"
mailforge inbox search --unread

# 检测退信
mailforge inbox --bounce-only
```

### 🖥️ TUI 仪表盘

```bash
# 打开仪表盘（需要 rich 依赖）
mailforge dashboard
```

> 💡 **提示**：如果未安装 rich，仪表盘会自动降级为纯文本模式输出。

### 🔐 密码加密存储

```bash
# 初始化时会自动提示加密 SMTP 密码
# 也可手动加密
mailforge config set smtp.password --encrypt
```

密码使用 **AES-256-GCM** 加密算法存储，密钥派生自机器唯一标识，确保密码文件即使泄露也无法在其他机器上解密。

---

## 💡 设计思路与迭代规划 | Design & Roadmap

### 🎯 设计理念

1. **零依赖优先** — 核心功能只用 Python 标准库，降低安装门槛，避免依赖冲突
2. **渐进增强** — 有 rich/textual 则启用 TUI，无则降级为纯文本，确保任何环境都能运行
3. **安全内建** — 密码加密存储、内容安全检查、频率限制，从设计层面防止滥用
4. **开发者友好** — CLI 设计遵循 Unix 哲学，每个命令做好一件事，支持管道和脚本集成

### 🔧 技术选型原因

| 技术 | 原因 |
|------|------|
| Python 标准库 | 零依赖、跨平台、生态丰富 |
| argparse | 标准库内置，无额外依赖 |
| smtplib/imaplib | Python 内置邮件协议支持 |
| json/csv | 标准库数据格式处理 |
| logging | 标准库日志系统 |
| rich（可选） | 终端美化，社区最活跃的 Python TUI 库 |

### 🗺️ 后续迭代计划

- [ ] **v1.1** — Webhook 回调集成（发送成功/失败通知）
- [ ] **v1.2** — AI 邮件内容优化建议（接入 LLM API）
- [ ] **v1.3** — 邮件打开追踪（嵌入追踪像素）
- [ ] **v1.4** — A/B 测试支持（多模板对比发送）
- [ ] **v1.5** — 数据库后端存储（SQLite 替代 JSON 文件）
- [ ] **v2.0** — Web 管理界面（Flask/FastAPI）

### 🤝 社区贡献方向

- 更多邮件服务商的预置配置模板
- 国际化支持（更多语言的模板示例）
- 插件系统（自定义过滤器、发送后钩子）
- Docker 一键部署方案

---

## 📦 安装与部署指南 | Installation & Deployment

### 🔧 从源码安装

```bash
git clone https://github.com/gitstq/MailForge-CLI.git
cd MailForge-CLI
pip install -e .
```

### 🐍 使用 pip 安装（未来支持）

```bash
pip install mailforge-cli
```

### 🐳 Docker 部署（规划中）

```bash
# 未来版本将支持
docker run -it -v ~/.mailforge:/root/.mailforge mailforge-cli dashboard
```

### 🖥️ 系统兼容性

| 平台 | 支持状态 |
|------|---------|
| Linux (x86_64) | ✅ 完全支持 |
| macOS (x86_64/ARM64) | ✅ 完全支持 |
| Windows (x86_64) | ✅ 完全支持 |
| Python 3.9 | ✅ 支持 |
| Python 3.10+ | ✅ 推荐 |

---

## 🤝 贡献指南 | Contributing

我们欢迎所有形式的贡献！无论是提交 Bug 报告、改进文档，还是提交代码 PR。

### 📋 提交 PR 规范

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交代码：`git commit -m "feat: add your feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 📝 提交信息规范（Angular Convention）

| 前缀 | 用途 |
|------|------|
| `feat:` | 新增功能 |
| `fix:` | 修复问题 |
| `docs:` | 文档更新 |
| `refactor:` | 代码重构 |
| `test:` | 测试相关 |
| `chore:` | 构建/工具链更新 |

### 🐛 反馈问题

- 通过 [GitHub Issues](https://github.com/gitstq/MailForge-CLI/issues) 提交 Bug 或功能建议
- 请尽量附带复现步骤和运行环境信息

---

## 📄 开源协议 | License

本项目基于 [MIT License](https://opensource.org/licenses/MIT) 开源。

```
MIT License

Copyright (c) 2025 MailForge-CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>

---

## 🎉 專案介紹 | Project Introduction

**MailForge-CLI** 是一款零核心依賴的輕量級終端郵件營銷智能引擎，專為開發者和中小團隊打造。它將 SMTP/IMAP 協議操作、郵件模板引擎、聯繫人管理、營銷活動編排、發送分析統計、TUI 可視化儀表盤等能力整合到一個簡潔的 CLI 工具中，讓你在終端中即可完成從郵件編寫到批量發送的全鏈路操作。

### 💡 靈感來源

受 GitHub Trending 熱門項目 **BillionMail**（開源自託管郵件伺服器）啟發，我們發現很多開發者只需要**郵件營銷自動化**能力，而不需要搭建完整的郵件伺服器。MailForge-CLI 專注於這一細分場景，以 CLI 工具的形式提供更輕量、更靈活的解決方案。

### ✨ 自研差異化亮點

- 🚫 **零核心依賴** — 核心功能僅使用 Python 標準庫，無需安裝任何第三方包即可運行
- 📝 **純 Python 模板引擎** — 自研實現變量替換、條件渲染、循環、17 種內置過濾器、模板繼承，無需 Jinja2
- 🎯 **智能聯繫人管理** — CSV/JSON 自動導入、字段智能映射、分組管理、郵箱去重、批量操作
- 📊 **TUI 可視化儀表盤** — 實時發送統計、活動狀態監控、聯繫人概覽（可選 rich 依賴增強）
- 🔒 **AES-256-GCM 加密** — SMTP 密碼安全存儲，支持環境變量覆蓋
- ⚡ **發送速率控制** — 滑動窗口頻率限制器，防止觸發郵件服務商限制
- 🛡️ **內容安全檢查** — 內置垃圾郵件關鍵詞檢測，發送前自動預警

---

## ✨ 核心特性 | Core Features

### 📤 SMTP 發送引擎
- **多協議支持** — SMTP / SMTPS / STARTTLS 全覆蓋
- **連接池管理** — 高效復用連接，批量發送性能優異
- **Multipart 郵件** — 同時支持 HTML + 純文本，兼容所有郵件客戶端
- **附件支持** — 多文件、大文件分塊發送
- **智能重試** — 指數退避自動重試機制，應對臨時網絡故障
- **隊列化發送** — 異步批量發送，支持暫停/恢復

### 📥 IMAP 接收引擎
- **郵件搜索** — 按日期、發件人、主題、未讀狀態等多維度搜索
- **郵件解析** — 提取正文、附件、郵件頭信息
- **退信檢測** — 自動識別並標記退信郵件
- **郵件管理** — 自動標記/移動/刪除

### 📝 模板引擎（零依賴）
- `{{variable}}` — 變量替換，支持個性化郵件
- `{%if condition%}...{%endif%}` — 條件渲染
- `{%for item in list%}...{%endfor%}` — 循環渲染
- **17 種內置過濾器** — upper, lower, date, default, truncate, nl2br, strip_tags 等
- **模板繼承** — extends/block 機制，復用佈局
- **模板預覽** — 終端內實時預覽渲染效果

### 👥 聯繫人管理
- **多格式導入** — CSV / JSON 自動導入，智能識別字段映射
- **分組管理** — 按標籤分組，精準定向發送
- **自動去重** — 基於郵箱地址自動去重
- **批量操作** — 添加、刪除、更新、導出

### 📊 營銷活動管理
- **活動編排** — 創建、調度、狀態跟蹤（draft/sending/paused/completed/failed）
- **進度監控** — 實時查看發送進度和成功率
- **活動報告** — 自動生成 JSON/CSV/Markdown 格式報告

### 📈 發送分析
- **成功率統計** — 總體發送成功率、退信率
- **時間段分析** — 按小時/天/周分析發送趨勢
- **分組對比** — 不同聯繫人組的表現對比
- **多格式導出** — JSON / CSV / Markdown

### 🖥️ TUI 儀表盤
- **發送概覽** — 總發送量、成功率、退信數
- **實時進度** — 當前活動發送進度條
- **聯繫人統計** — 分組人數、活躍度
- **快捷鍵導航** — 鍵盤操作，高效瀏覽

---

## 🚀 快速開始 | Quick Start

### 📋 環境要求

| 項目 | 最低要求 |
|------|---------|
| Python | 3.9+ |
| 操作系統 | Windows / macOS / Linux |
| 依賴 | 無（核心功能零依賴） |
| 可選依賴 | rich>=13.0（TUI 增強）、textual>=3.0（高級 TUI） |

### 📦 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/MailForge-CLI.git
cd MailForge-CLI

# 安裝（開發模式）
pip install -e .

# 或僅安裝可選依賴（TUI 增強）
pip install -r requirements.txt
```

### ⚙️ 初始化配置

```bash
# 交互式初始化
mailforge init

# 或手動設置 SMTP 配置
mailforge config set smtp.host smtp.gmail.com
mailforge config set smtp.port 587
mailforge config set smtp.username your@email.com
mailforge config set smtp.password your_app_password
mailforge config set smtp.tls true
mailforge config set smtp.from_name "Your Name"
mailforge config set smtp.from_email your@email.com
```

### 📧 快速發送第一封郵件

```bash
# 快速發送
mailforge send \
  --to recipient@example.com \
  --subject "Hello from MailForge" \
  --body "This is a test email sent via MailForge-CLI!"

# 使用模板批量發送
mailforge send \
  --template welcome \
  --group subscribers
```

### 🎯 典型工作流

```bash
# 1. 導入聯繫人
mailforge contact import subscribers.csv

# 2. 創建郵件模板
mailforge template create newsletter

# 3. 創建營銷活動
mailforge campaign create "Weekly Newsletter" \
  --template newsletter \
  --group subscribers

# 4. 啟動活動
mailforge campaign start 1

# 5. 查看報告
mailforge campaign report 1

# 6. 打開儀表盤
mailforge dashboard
```

---

## 📖 詳細使用指南 | Detailed Guide

### 🔧 配置管理

```bash
# 初始化配置文件（~/.mailforge/config.json）
mailforge init

# 查看所有配置
mailforge config list

# 設置配置項
mailforge config set smtp.host smtp.qq.com
mailforge config set smtp.port 465
mailforge config set smtp.username user@qq.com
mailforge config set smtp.password auth_code
mailforge config set smtp.ssl true

# 也支持環境變量覆蓋
export MAILFORGE_SMTP_HOST=smtp.gmail.com
export MAILFORGE_SMTP_PORT=587
export MAILFORGE_SMTP_USERNAME=your@email.com
export MAILFORGE_SMTP_PASSWORD=your_password
```

### 👥 聯繫人管理

```bash
# 從 CSV 導入（自動識別 name/email 列）
mailforge contact import subscribers.csv

# 從 JSON 導入
mailforge contact import contacts.json

# 列出所有聯繫人
mailforge contact list

# 按組篩選
mailforge contact list --group subscribers

# 查看分組
mailforge contact groups

# 導出聯繫人
mailforge contact export --format json --output my_contacts.json
```

### 📝 模板管理

```bash
# 列出模板
mailforge template list

# 創建模板
mailforge template create newsletter

# 預覽模板渲染效果
mailforge template preview newsletter --data '{"name": "Alice"}'
```

**模板語法示例**：

```html
<h1>你好，{{name}}！</h1>

<p>感謝你訂閱我們的{{newsletter_type}}。</p>

{%if is_premium%}
<p>🌟 你是我們的高級會員，享受專屬權益。</p>
{%else%}
<p>升級高級會員，解鎖更多功能！</p>
{%endif%}

<ul>
{%for item in updates%}
<li>{{item.title}} - {{item.date|date:"Y-m-d"}}</li>
{%endfor%}
</ul>
```

### 📊 營銷活動

```bash
# 創建活動
mailforge campaign create "Black Friday Sale" \
  --template promo \
  --group subscribers \
  --schedule "2025-06-01 09:00"

# 列出所有活動
mailforge campaign list

# 啟動活動
mailforge campaign start 1

# 暫停活動
mailforge campaign pause 1

# 查看活動報告
mailforge campaign report 1
```

### 📈 發送統計

```bash
# 查看總體統計
mailforge analytics

# 按時間段篩選
mailforge analytics --period 7d

# 導出報告
mailforge analytics --export markdown --output report.md
```

### 📥 收件箱管理

```bash
# 查看收件箱
mailforge inbox

# 搜索郵件
mailforge inbox search --from sender@example.com
mailforge inbox search --subject "newsletter"
mailforge inbox search --unread

# 檢測退信
mailforge inbox --bounce-only
```

### 🖥️ TUI 儀表盤

```bash
# 打開儀表盤（需要 rich 依賴）
mailforge dashboard
```

> 💡 **提示**：如果未安裝 rich，儀表盤會自動降級為純文本模式輸出。

---

## 💡 設計思路與迭代規劃 | Design & Roadmap

### 🎯 設計理念

1. **零依賴優先** — 核心功能只用 Python 標準庫，降低安裝門檻，避免依賴衝突
2. **漸進增強** — 有 rich/textual 則啟用 TUI，無則降級為純文本，確保任何環境都能運行
3. **安全內建** — 密碼加密存儲、內容安全檢查、頻率限制，從設計層面防止濫用
4. **開發者友好** — CLI 設計遵循 Unix 哲學，每個命令做好一件事，支持管道和腳本集成

### 🗺️ 後續迭代計劃

- [ ] **v1.1** — Webhook 回調集成（發送成功/失敗通知）
- [ ] **v1.2** — AI 郵件內容優化建議（接入 LLM API）
- [ ] **v1.3** — 郵件打開追蹤（嵌入追蹤像素）
- [ ] **v1.4** — A/B 測試支持（多模板對比發送）
- [ ] **v1.5** — 資料庫後端存儲（SQLite 替代 JSON 文件）
- [ ] **v2.0** — Web 管理界面（Flask/FastAPI）

---

## 📦 安裝與部署指南 | Installation & Deployment

### 🔧 從源碼安裝

```bash
git clone https://github.com/gitstq/MailForge-CLI.git
cd MailForge-CLI
pip install -e .
```

### 🐍 使用 pip 安裝（未來支持）

```bash
pip install mailforge-cli
```

### 🖥️ 系統兼容性

| 平台 | 支持狀態 |
|------|---------|
| Linux (x86_64) | ✅ 完全支持 |
| macOS (x86_64/ARM64) | ✅ 完全支持 |
| Windows (x86_64) | ✅ 完全支持 |
| Python 3.9 | ✅ 支持 |
| Python 3.10+ | ✅ 推薦 |

---

## 🤝 貢獻指南 | Contributing

我們歡迎所有形式的貢獻！無論是提交 Bug 報告、改進文檔，還是提交代碼 PR。

### 📋 提交 PR 規範

1. Fork 本倉庫
2. 創建特性分支：`git checkout -b feature/your-feature`
3. 提交代碼：`git commit -m "feat: add your feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 創建 Pull Request

### 📝 提交信息規範（Angular Convention）

| 前綴 | 用途 |
|------|------|
| `feat:` | 新增功能 |
| `fix:` | 修復問題 |
| `docs:` | 文檔更新 |
| `refactor:` | 代碼重構 |
| `test:` | 測試相關 |
| `chore:` | 構建/工具鏈更新 |

### 🐛 反饋問題

- 通過 [GitHub Issues](https://github.com/gitstq/MailForge-CLI/issues) 提交 Bug 或功能建議
- 請盡量附帶復現步驟和運行環境信息

---

## 📄 開源協議 | License

本項目基於 [MIT License](https://opensource.org/licenses/MIT) 開源。

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>

---

## 🎉 Project Introduction

**MailForge-CLI** is a zero-dependency, lightweight terminal email marketing intelligent engine built for developers and small teams. It integrates SMTP/IMAP protocol operations, an email template engine, contact management, campaign orchestration, send analytics, and a TUI visual dashboard into a single CLI tool — empowering you to manage the entire email marketing workflow right from your terminal.

### 💡 Inspiration

Inspired by the trending GitHub project **BillionMail** (an open-source self-hosted mail server), we realized that many developers only need **email marketing automation** capabilities without setting up a full mail server. MailForge-CLI focuses on this specific use case, delivering a lighter and more flexible solution as a CLI tool.

### ✨ Differentiation Highlights

- 🚫 **Zero Core Dependencies** — Core functionality uses only the Python standard library; no third-party packages required
- 📝 **Pure Python Template Engine** — Custom-built variable substitution, conditional rendering, loops, 17 built-in filters, and template inheritance — no Jinja2 needed
- 🎯 **Smart Contact Management** — CSV/JSON auto-import with intelligent field mapping, grouping, deduplication, and batch operations
- 📊 **TUI Visual Dashboard** — Real-time send statistics, campaign status monitoring, contact overview (enhanced with optional rich dependency)
- 🔒 **AES-256-GCM Encryption** — Secure SMTP password storage with environment variable override support
- ⚡ **Send Rate Control** — Sliding window rate limiter to prevent triggering ISP throttling
- 🛡️ **Content Safety Check** — Built-in spam keyword detection with pre-send alerts

---

## ✨ Core Features

### 📤 SMTP Sending Engine
- **Multi-protocol Support** — SMTP / SMTPS / STARTTLS
- **Connection Pooling** — Efficient connection reuse for high-performance bulk sending
- **Multipart Emails** — HTML + plain text support for maximum client compatibility
- **Attachment Support** — Multi-file and chunked large file sending
- **Smart Retry** — Exponential backoff auto-retry for transient network failures
- **Queue-based Sending** — Async bulk sending with pause/resume support

### 📥 IMAP Receiving Engine
- **Email Search** — Multi-dimensional search by date, sender, subject, read status
- **Email Parsing** — Extract body, attachments, and headers
- **Bounce Detection** — Automatic identification and flagging of bounced emails
- **Email Management** — Auto-mark, move, and delete

### 📝 Template Engine (Zero Dependencies)
- `{{variable}}` — Variable substitution for personalized emails
- `{%if condition%}...{%endif%}` — Conditional rendering
- `{%for item in list%}...{%endfor%}` — Loop rendering
- **17 Built-in Filters** — upper, lower, date, default, truncate, nl2br, strip_tags, and more
- **Template Inheritance** — extends/block mechanism for layout reuse
- **Template Preview** — Real-time rendering preview in terminal

### 👥 Contact Management
- **Multi-format Import** — CSV / JSON auto-import with intelligent field mapping
- **Group Management** — Tag-based grouping for targeted sending
- **Auto Deduplication** — Email-based automatic deduplication
- **Batch Operations** — Add, remove, update, and export in bulk

### 📊 Campaign Management
- **Campaign Orchestration** — Create, schedule, and track status (draft/sending/paused/completed/failed)
- **Progress Monitoring** — Real-time send progress and success rate tracking
- **Campaign Reports** — Auto-generate reports in JSON/CSV/Markdown formats

### 📈 Send Analytics
- **Success Rate Statistics** — Overall send success rate and bounce rate
- **Time-series Analysis** — Hourly/daily/weekly send trend analysis
- **Group Comparison** — Performance comparison across contact groups
- **Multi-format Export** — JSON / CSV / Markdown

### 🖥️ TUI Dashboard
- **Send Overview** — Total sends, success rate, bounce count
- **Real-time Progress** — Current campaign send progress bar
- **Contact Statistics** — Group counts and activity levels
- **Keyboard Navigation** — Efficient browsing with keyboard shortcuts

---

## 🚀 Quick Start

### 📋 Requirements

| Item | Minimum |
|------|---------|
| Python | 3.9+ |
| OS | Windows / macOS / Linux |
| Dependencies | None (zero core dependencies) |
| Optional | rich>=13.0 (TUI enhancement), textual>=3.0 (advanced TUI) |

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/MailForge-CLI.git
cd MailForge-CLI

# Install in development mode
pip install -e .

# Or install optional dependencies only (TUI enhancement)
pip install -r requirements.txt
```

### ⚙️ Initial Configuration

```bash
# Interactive initialization
mailforge init

# Or manually configure SMTP settings
mailforge config set smtp.host smtp.gmail.com
mailforge config set smtp.port 587
mailforge config set smtp.username your@email.com
mailforge config set smtp.password your_app_password
mailforge config set smtp.tls true
mailforge config set smtp.from_name "Your Name"
mailforge config set smtp.from_email your@email.com
```

### 📧 Send Your First Email

```bash
# Quick send
mailforge send \
  --to recipient@example.com \
  --subject "Hello from MailForge" \
  --body "This is a test email sent via MailForge-CLI!"

# Bulk send with template
mailforge send \
  --template welcome \
  --group subscribers
```

### 🎯 Typical Workflow

```bash
# 1. Import contacts
mailforge contact import subscribers.csv

# 2. Create email template
mailforge template create newsletter

# 3. Create marketing campaign
mailforge campaign create "Weekly Newsletter" \
  --template newsletter \
  --group subscribers

# 4. Start campaign
mailforge campaign start 1

# 5. View report
mailforge campaign report 1

# 6. Open dashboard
mailforge dashboard
```

---

## 📖 Detailed Usage Guide

### 🔧 Configuration Management

```bash
# Initialize config file (~/.mailforge/config.json)
mailforge init

# List all configurations
mailforge config list

# Set configuration items
mailforge config set smtp.host smtp.gmail.com
mailforge config set smtp.port 587
mailforge config set smtp.username your@email.com
mailforge config set smtp.password your_app_password
mailforge config set smtp.tls true

# Environment variable overrides
export MAILFORGE_SMTP_HOST=smtp.gmail.com
export MAILFORGE_SMTP_PORT=587
export MAILFORGE_SMTP_USERNAME=your@email.com
export MAILFORGE_SMTP_PASSWORD=your_password
```

**Multi-account Configuration Example** (`~/.mailforge/config.json`):

```json
{
  "accounts": {
    "primary": {
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "user@gmail.com",
      "password": "encrypted_password",
      "tls": true,
      "from_name": "Team",
      "from_email": "user@gmail.com"
    },
    "backup": {
      "smtp_host": "smtp.office365.com",
      "smtp_port": 587,
      "username": "user@outlook.com",
      "password": "encrypted_password",
      "tls": true,
      "from_name": "Backup",
      "from_email": "user@outlook.com"
    }
  },
  "defaults": {
    "rate_limit_per_minute": 30,
    "retry_max_attempts": 3,
    "retry_backoff_factor": 2
  }
}
```

### 👥 Contact Management

```bash
# Import from CSV (auto-detects name/email columns)
mailforge contact import subscribers.csv

# Import from JSON
mailforge contact import contacts.json

# List all contacts
mailforge contact list

# Filter by group
mailforge contact list --group subscribers

# View groups
mailforge contact groups

# Export contacts
mailforge contact export --format json --output my_contacts.json
```

**CSV Format Example**:

```csv
name,email,group
Alice,alice@example.com,subscribers
Bob,bob@example.com,subscribers
Charlie,charlie@example.com,vip
```

### 📝 Template Management

```bash
# List templates
mailforge template list

# Create template
mailforge template create newsletter

# Preview rendered template
mailforge template preview newsletter --data '{"name": "Alice"}'
```

**Template Syntax Example**:

```html
<h1>Hello, {{name}}!</h1>

<p>Thank you for subscribing to our {{newsletter_type}}.</p>

{%if is_premium%}
<p>🌟 You're a premium member with exclusive benefits.</p>
{%else%}
<p>Upgrade to premium to unlock more features!</p>
{%endif%}

<ul>
{%for item in updates%}
<li>{{item.title}} - {{item.date|date:"Y-m-d"}}</li>
{%endfor%}
</ul>

<p>Sent on: {{send_date|date:"F j, Y"}}</p>
```

### 📊 Campaign Management

```bash
# Create campaign
mailforge campaign create "Black Friday Sale" \
  --template promo \
  --group subscribers \
  --schedule "2025-06-01 09:00"

# List all campaigns
mailforge campaign list

# Start campaign
mailforge campaign start 1

# Pause campaign
mailforge campaign pause 1

# View campaign report
mailforge campaign report 1
```

### 📈 Send Analytics

```bash
# View overall statistics
mailforge analytics

# Filter by time period
mailforge analytics --period 7d

# Export report
mailforge analytics --export markdown --output report.md
```

### 📥 Inbox Management

```bash
# View inbox
mailforge inbox

# Search emails
mailforge inbox search --from sender@example.com
mailforge inbox search --subject "newsletter"
mailforge inbox search --unread

# Detect bounces
mailforge inbox --bounce-only
```

### 🖥️ TUI Dashboard

```bash
# Open dashboard (requires rich dependency)
mailforge dashboard
```

> 💡 **Tip**: If rich is not installed, the dashboard automatically falls back to plain text mode.

---

## 💡 Design Philosophy & Roadmap

### 🎯 Design Principles

1. **Zero Dependencies First** — Core features use only the Python standard library to minimize installation friction and dependency conflicts
2. **Progressive Enhancement** — TUI activates with rich/textual, degrades gracefully to plain text when unavailable
3. **Security by Design** — Encrypted password storage, content safety checks, and rate limiting built in from the ground up
4. **Developer-Friendly** — CLI follows Unix philosophy: each command does one thing well, supports piping and scripting

### 🔧 Technology Choices

| Technology | Reason |
|-----------|--------|
| Python Standard Library | Zero dependencies, cross-platform, rich ecosystem |
| argparse | Built-in argument parsing, no extra dependencies |
| smtplib/imaplib | Native Python email protocol support |
| json/csv | Standard library data format handling |
| logging | Standard library logging system |
| rich (optional) | Most active Python TUI library in the community |

### 🗺️ Roadmap

- [ ] **v1.1** — Webhook callback integration (send success/failure notifications)
- [ ] **v1.2** — AI email content optimization suggestions (LLM API integration)
- [ ] **v1.3** — Email open tracking (tracking pixel embedding)
- [ ] **v1.4** — A/B testing support (multi-template comparison sends)
- [ ] **v1.5** — Database backend storage (SQLite replacing JSON files)
- [ ] **v2.0** — Web management interface (Flask/FastAPI)

### 🤝 Community Contribution Areas

- Preset configuration templates for more email providers
- Internationalization support (template examples in more languages)
- Plugin system (custom filters, post-send hooks)
- Docker one-click deployment solution

---

## 📦 Installation & Deployment Guide

### 🔧 Install from Source

```bash
git clone https://github.com/gitstq/MailForge-CLI.git
cd MailForge-CLI
pip install -e .
```

### 🐍 Install via pip (Coming Soon)

```bash
pip install mailforge-cli
```

### 🖥️ System Compatibility

| Platform | Status |
|----------|--------|
| Linux (x86_64) | ✅ Fully Supported |
| macOS (x86_64/ARM64) | ✅ Fully Supported |
| Windows (x86_64) | ✅ Fully Supported |
| Python 3.9 | ✅ Supported |
| Python 3.10+ | ✅ Recommended |

---

## 🤝 Contributing

We welcome contributions of all kinds! Whether it's filing bug reports, improving documentation, or submitting code PRs.

### 📋 PR Submission Guidelines

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push the branch: `git push origin feature/your-feature`
5. Create a Pull Request

### 📝 Commit Message Convention (Angular)

| Prefix | Purpose |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation update |
| `refactor:` | Code refactoring |
| `test:` | Test-related |
| `chore:` | Build/tooling update |

### 🐛 Reporting Issues

- Submit bugs or feature requests via [GitHub Issues](https://github.com/gitstq/MailForge-CLI/issues)
- Please include reproduction steps and runtime environment details when possible

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

```
MIT License

Copyright (c) 2025 MailForge-CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
