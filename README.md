# AI Policy Platform (MVP) / AI 策略管理平台（最小可行版本）

> Inspired by **Microsoft Entra Conditional Access (CA)** and **Identity 
Protection**, this project is an experimental platform combining AI + 
policy automation.  
> 本项目受 **微软 Entra 条件访问 (Conditional Access, CA)** 和 **身份保护 
(Identity Protection)** 启发，旨在探索 **AI + 策略自动化** 的结合。

---

## 🌟 Features / 功能亮点

- **AI Drafting (Stub for now)**  
  Generate initial policy drafts from natural language prompts. (LLM 
integration planned with OpenAI/Claude)  
  **AI 策略草案（目前为模拟，未来接入 LLM）**  
  通过自然语言生成策略草案（例如：“只允许员工在工作时间从加州访问 CRM”）。

- **Policy CRUD with SQLite**  
  Create, view, update, and enable/disable access policies.  
  **策略增删改查 (SQLite 存储)**  
  支持新建、查看、修改、启用/禁用策略。

- **Policy Evaluation Engine**  
  Evaluate simulated login requests against policies, with explanations.  
  **策略评估引擎**  
  
可输入模拟的登录请求（用户、地点、时间、设备、风险等级），系统给出决策及解释。

- **Conflict Resolution Logic**  
  - Block > Allow  
  - Stricter requirements win (e.g., MFA enforced if any policy requires 
it)  
  **冲突决策逻辑**  
  - 阻止优先于允许  
  - 多策略冲突时取更严格要求（如任一策略要求 MFA → 整体要求 MFA）

- **Swagger API Docs**  
  Available at `/docs` for testing and exploration.  
  **自带 Swagger API 文档**  
  访问 `/docs` 即可交互测试。

---

## 🎯 Scenarios / 应用场景

This project simulates how enterprises manage secure access:  
- Employees accessing business apps (CRM, ERP, Email)  
- Conditional rules: location, device compliance, time of day, risk level  
- Automating tedious manual policy changes with AI-driven workflows  

本项目模拟了企业如何管理安全访问：  
- 员工访问企业应用（CRM、ERP、邮件）  
- 条件规则：地理位置、设备合规性、时间窗口、风险等级  
- 通过 AI 自动化减少管理员手动配置的繁琐工作

---

## 🚀 Quickstart / 快速开始

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

