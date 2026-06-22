# Implementation Plan: Mobile Bookkeeping App

## Overview

按分层顺序实现：项目脚手架 → 数据库模型与迁移 → 认证模块 → 审计日志基础与通用 API 校验 → 账本与 Subject 管理 → 默认分类/商品建议与偏好引擎 → 交易核心流程 → 预算模块 → 图片附件后端预留 → 定期交易调度 → 导出与统计 → 管理员后台 → 安全加固 → 前端 Vue 3 SPA → 共享/个人信息/通知前端完善 → 集成收尾。

技术栈：FastAPI + SQLAlchemy + Alembic + PostgreSQL（后端），Vue 3 + Pinia + vue-i18n + axios（前端），pytest + Hypothesis（测试），Vitest（前端测试），Docker Compose（环境）。

---

## Tasks

- [x] 1. 项目结构与开发环境搭建
  - 按设计文档 monorepo 结构创建目录骨架：`backend/`、`frontend/`、`nginx/`、`.devcontainer/`
  - 编写 `backend/Dockerfile`（多阶段：base / dev / prod）
  - 编写 `frontend/Dockerfile`（多阶段：builder / prod / dev）
  - 编写 `docker-compose.dev.yml`（backend、frontend、db、mailpit 服务）
  - 编写 `docker-compose.prod.yml`（backend、frontend、db、nginx、cloudflared、objstore）
  - 编写 `.devcontainer/devcontainer.json`
  - 编写 `nginx/nginx.conf`（反向代理 `/api/` → backend，`/` → frontend）
  - 创建 `.env.example` 包含所有环境变量占位符（DATABASE_URL、SECRET_KEY、SMTP_HOST 等）
  - 初始化 `backend/requirements.txt`（fastapi、uvicorn、sqlalchemy、alembic、psycopg2-binary、asyncpg、python-jose、passlib[bcrypt]、slowapi、apscheduler、hypothesis、pytest、httpx、python-multipart、boto3）
  - 初始化 `frontend/package.json`（vue 3、pinia、vue-i18n、axios、vitest、@vue/test-utils）
  - 编写 `backend/app/main.py`：FastAPI app 实例、lifespan 事件（运行 alembic upgrade head）、挂载路由占位
  - _Requirements: 15.1, 18.3_

- [x] 2. 数据库模型与 Alembic 迁移
  - [x] 2.1 实现所有 SQLAlchemy ORM 模型
    - 创建 `backend/app/models/` 目录，分文件实现：`user.py`、`ledger.py`、`transaction.py`、`preference.py`、`budget.py`、`recurring.py`、`audit_log.py`
    - 所有金额字段使用 `BigInteger`，UUID 主键使用 `uuid.uuid4`
    - 配置 SQLAlchemy cascade `"all, delete-orphan"` 和数据库 `ON DELETE CASCADE` 外键
    - `AuditLog` 模型不设 `updated_at`，应用层防止 UPDATE/DELETE
    - _Requirements: 15.1, 15.3, 15.4, 19.1, 25.7, 25.8, 25.9_

  - [x] 2.2 编写属性测试：金额字段精度（Property 12）
    - **Property 12: 非数字金额被拒绝**
    - **Validates: Requirements 8.3**

  - [x] 2.3 生成初始 Alembic 迁移脚本
    - 初始化 Alembic（`alembic init alembic/`），配置 `env.py` 读取 `DATABASE_URL` 环境变量
    - 生成包含所有表的 `upgrade()` / `downgrade()` 的初始迁移文件
    - _Requirements: 18.1, 18.2, 18.4, 18.5, 18.6_

- [x] 3. 认证模块（Auth Service）
  - [x] 3.1 实现用户注册与登录 API
    - 创建 `backend/app/routers/auth.py`
    - `POST /auth/register`：bcrypt 密码 hash（work factor ≥ 12），重复邮箱返回 409
    - `POST /auth/login`：验证成功返回 JWT（exp = 7 天），失败时邮箱/密码错误返回相同消息
    - JWT 使用 `python-jose`，密钥从 `SECRET_KEY` 环境变量读取
    - `GET /auth/me` 依赖项：解码 JWT，校验用户 `is_active`，否则返回 403
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 16.2_

  - [x] 3.2 编写属性测试：注册邮箱唯一性（Property 1）
    - **Property 1: 注册邮箱唯一性**
    - **Validates: Requirements 1.1, 1.2**

  - [x] 3.3 编写属性测试：JWT 令牌有效期（Property 2）
    - **Property 2: JWT 令牌有效期**
    - **Validates: Requirements 1.3**

  - [x] 3.4 编写属性测试：登录认证错误不泄露字段信息（Property 3）
    - **Property 3: 登录认证错误不泄露字段信息**
    - **Validates: Requirements 1.4**

  - [x] 3.5 实现密码找回流程
    - `POST /auth/password-reset/request`：生成 `PASSWORD_RESET_TOKEN`（30分钟过期），通过 SMTP 发送邮件；不存在的邮箱返回与真实邮箱相同的 200 响应
    - `POST /auth/password-reset/confirm`：验证 token 未过期未使用，更新密码，标记 token `used=True`，使该用户所有已签发 JWT 失效（在 User 表增加 `password_changed_at` 字段，JWT 验证时比对）
    - _Requirements: 1b.1, 1b.2, 1b.3, 1b.4, 1b.5, 1b.6, 1b.7_

  - [x] 3.6 编写属性测试：密码重置令牌单次有效（Property 4）
    - **Property 4: 密码重置令牌单次有效**
    - **Validates: Requirements 1b.5, 1b.6**

  - [x] 3.7 编写属性测试：密码重置后旧 JWT 失效（Property 5）
    - **Property 5: 密码重置后旧 JWT 失效**
    - **Validates: Requirements 1b.7**

  - [x] 3.8 实现账号注销
    - `DELETE /auth/account`：要求请求体携带当前密码，验证通过后级联删除用户数据（User、Ledger、Transaction、ShareRequest、Preference、AuditLog），立即使所有 JWT 失效
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5, 26.6_

  - [x] 3.9 编写属性测试：账号注销级联清理（Property 28）
    - **Property 28: 账号注销级联清理**
    - **Validates: Requirements 26.3**

  - [x] 3.10 实现限流中间件
    - 使用 `slowapi` 配置：登录 10次失败/IP/15分钟、密码重置 5次/邮箱/小时、注册 10次/IP/小时
    - 超限响应包含 `Retry-After` 头，返回 429
    - _Requirements: 25.1, 25.2, 25.3_

- [x] 4. Checkpoint — 确保认证相关测试全部通过
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4.1 审计日志基础服务
  - 将 `backend/app/services/audit.py` 作为跨模块基础设施稳定下来，统一事件类型、字段格式和调用约定
  - 新增 `Notification` ORM 模型和 Alembic 迁移，用于共享申请与审批结果的应用内状态提示
  - 在 Auth 已有日志基础上，明确后续 Ledger Share、Admin 操作必须调用同一服务
  - 数据库层继续保持 `AuditLog` 无 `updated_at`；应用层不暴露 UPDATE/DELETE 路径
  - _Requirements: 25.7, 25.8, 25.9_

- [x] 4.2 后端通用 API 校验基础
  - 建立所有后端路由的 Pydantic Schema 约定：字符串字段必须显式设置 `min_length` / `max_length`
  - 建立 Content-Type 校验中间件或依赖：对带请求体的 JSON 端点拒绝意外 `Content-Type`
  - 明确所有数据库访问必须通过 SQLAlchemy ORM / 参数化查询
  - _Requirements: 17.1, 17.2, 17.5, 17.7, 25.5_

- [x] 5. 账本管理（Ledger Service）
  - [x] 5.1 实现账本 CRUD API
    - 创建 `backend/app/routers/ledgers.py`
    - `POST /ledgers`：校验名称 1–50 字符，记录 Entry_Mode、subject_enabled、subject_step_mode、necessity_step_mode、default_currency_code（ISO 4217）、timezone；用户账本数 ≥ 10 时拒绝
    - `GET /ledgers`、`GET /ledgers/{id}`、`PATCH /ledgers/{id}`、`DELETE /ledgers/{id}`（级联删除所有关联数据）
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8, 15.4_

  - [x] 5.2 编写属性测试：账本名称长度约束（Property 6）
    - **Property 6: 账本名称长度约束**
    - **Validates: Requirements 2.1**

  - [x] 5.3 编写属性测试：账本数量上限（Property 7）
    - **Property 7: 账本数量上限**
    - **Validates: Requirements 2.7**

  - [x] 5.4 编写属性测试：账本删除级联清理（Property 19）
    - **Property 19: 账本删除级联清理**
    - **Validates: Requirements 15.4**

  - [x] 5.5 实现 Subject 管理 API
    - `GET /ledgers/{id}/subjects`（排序后列表）、`POST /ledgers/{id}/subjects`（自定义，上限 20）、`DELETE /ledgers/{id}/subjects/{sub_id}`（仅自定义可删）
    - 账本创建时预置 10 个预设 Subject（自己、爸爸、妈妈、孩子、爷爷、奶奶、老公、老婆、兄弟、姐妹），`is_preset=True`
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 5.6 编写属性测试：Subject 数量上限（Property 8）
    - **Property 8: 花费对象数量上限**
    - **Validates: Requirements 3.2**

  - [x] 5.7 编写属性测试：预设 Subject 不可删除（Property 9）
    - **Property 9: 预设 Subject 不可删除**
    - **Validates: Requirements 3.3**

  - [x] 5.8 实现账本共享 API
    - `GET /ledgers/{id}/share-code`、`POST /ledgers/{id}/share-requests`、`GET /ledgers/{id}/share-requests`
    - `POST /ledgers/{id}/share-requests/{req_id}/approve`（最多 10 个共享成员，超限拒绝）
    - `POST /ledgers/{id}/share-requests/{req_id}/reject`
    - `GET /ledgers/{id}/members`、`DELETE /ledgers/{id}/members/{user_id}`
    - 共享申请、批准、拒绝、移除成员需更新应用内可见状态；SMTP 已配置时发送邮件通知
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

  - [x] 5.9 编写属性测试：账本共享人数上限（Property 14）
    - **Property 14: 账本共享人数上限**
    - **Validates: Requirements 9.7**

  - [x] 5.10 实现账本成员权限判定基础
    - 提供 `can_read_ledger`、`can_write_ledger` / 等价依赖项，区分 owner、read-write 成员、read-only 成员
    - Ledger 查询、Subject 管理、共享管理均使用统一权限检查
    - 真正的“只读共享用户无法创建交易”API 属性测试放到 Transaction Service 阶段执行
    - _Requirements: 9.3, 9.6, 9.8_

  - [x] 5.11 实现自定义 Category 管理 API
    - 新增 `Category` ORM 模型和 Alembic 迁移；交易明细保存 `category_id` 与 `category_name_snapshot`
    - `GET /ledgers/{id}/categories` 返回系统固定分类，按 display_order 排序
    - `POST /ledgers/{id}/categories`、`PATCH`、`DELETE` 保留为 Legacy/Internal 自定义分类 API，当前产品 UI 不暴露入口
    - 系统默认分类不可删除；分类名称需设置长度约束并参与 i18n 映射策略
    - _Requirements: 4.1, 4.4, 4.5, 14.6, 17.5_

- [x] 6. 偏好引擎（Preference Engine）
  - [x] 6.1 实现默认 Category / Item Suggestion Catalog
    - 定义默认 Category：食品饮料、外食餐饮、日用品、服饰鞋包、居住、水电燃气、通信网络、交通出行、汽车用车、医疗健康、保险、教育学习、育儿子女、宠物、娱乐休闲、旅行住宿、数码家电、订阅会员、社交礼金、美容护理、税费手续费、其他
    - 每个 Category 至少预置 5 个常用 Item name suggestions
    - 默认 Category 初始化到账本分类表，默认顺序作为 Preference Engine 在 selection_count 相同情况下的 tie-breaker
    - 所有默认 Category / Item 名称需可被 i18n 翻译层映射
    - _Requirements: 4.1, 4.2, 4.3, 4.9, 10.3, 14.6_

  - [x] 6.2 实现偏好计数与排序逻辑
    - 创建 `backend/app/services/preference.py`
    - `increment_count(ledger_id, user_id, tag_type, tag_value, category=None)`：写入 PREFERENCE 表
    - `get_sorted_subjects(ledger_id, user_id)`、`get_sorted_categories(ledger_id, user_id)`、`get_sorted_items(ledger_id, user_id, category)`：按 selection_count DESC、默认顺序 ASC 排序
    - 对外暴露 `GET /ledgers/{id}/preferences/subjects`、`/categories`、`/items?category=`
    - _Requirements: 3.4, 3.5, 4.8, 4.9, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 6.3 编写属性测试：偏好引擎计数与排序（Property 10）
    - **Property 10: 偏好引擎计数与排序**
    - **Validates: Requirements 3.4, 3.5, 4.8, 4.9, 10.1, 10.2, 10.3**

- [x] 7. 交易核心流程（Transaction Service）
  - [x] 7.1 实现交易 CRUD API
    - 创建 `backend/app/routers/transactions.py`
    - `POST /ledgers/{id}/transactions`：校验金额为正整数、currency_code ISO 4217、necessity 枚举；Entry_Mode=receipt 时无需 Item name，但需要保存所选 Category 到交易明细；necessity_step_mode=disabled 时强制 necessity="essential"；保存后调用偏好引擎更新计数
    - `GET /ledgers/{id}/transactions`（分页 50/页，按 transaction_date DESC）
    - `GET /ledgers/{id}/transactions/{txn_id}`、`PATCH /ledgers/{id}/transactions/{txn_id}`、`DELETE /ledgers/{id}/transactions/{txn_id}`（级联删除图片）
    - 只读共享用户执行写操作返回 403
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 12.1, 12.2, 12.3, 12.4, 5.13, 9.3, 15.1, 15.2, 15.3_

  - [x] 7.2 编写属性测试：交易列表按日期倒序（Property 15）
    - **Property 15: 交易列表按日期倒序排列**
    - **Validates: Requirements 12.1**

  - [x] 7.3 编写属性测试：分页每页不超过 50 条（Property 16）
    - **Property 16: 分页每页不超过 50 条**
    - **Validates: Requirements 12.4**

  - [x] 7.4 编写属性测试：禁用必要性步骤后自动记录为"刚需"（Property 11）
    - **Property 11: 禁用必要性步骤后自动记录为"刚需"**
    - **Validates: Requirements 5.13**

  - [x] 7.5 编写属性测试：只读共享用户无法创建交易（Property 13）
    - **Property 13: 只读共享用户无法创建交易**
    - 使用 Transaction API 验证 read-only 共享用户创建、更新、删除交易均返回 403
    - **Validates: Requirements 9.3**

  - [x] 7.6 实现交易统计汇总与 CSV 导出
    - `GET /ledgers/{id}/summary`：接受 time_range 参数（本周/本月/本年/自定义区间），按 Category、Subject、Necessity 分组汇总，按 currency_code 分组不混用
    - `GET /ledgers/{id}/export`：生成 CSV，列：date、amount、currency_code、category、item_name、subject、necessity、note、recorded_by；设置 `Content-Disposition: attachment` 头
    - 导出服务按查询层与 formatter 层分离，MVP 只实现 CSV，但保留 OFX formatter 扩展点
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 21.6, 24.1, 24.2, 24.3, 24.4, 24.5_

  - [x] 7.7 编写属性测试：分类汇总金额正确性（Property 17）
    - **Property 17: 分类汇总金额正确性**
    - **Validates: Requirements 13.1, 21.6**

  - [x] 7.8 编写属性测试：CSV 导出数据完整性（Property 26）
    - **Property 26: CSV 导出数据完整性**
    - **Validates: Requirements 24.1, 24.2**

- [x] 8. Checkpoint — 确保交易与偏好相关测试全部通过
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. 预算模块（Budget Service）
  - [x] 9.1 实现预算 CRUD API
    - 创建 `backend/app/routers/budget.py`
    - `POST /ledgers/{id}/budget`：存储月度总预算、可选年度总预算、可选 Category 细分；年度预算默认 = 月度 × 12；Category 细分默认 = `floor(monthly_total / category_count)`
    - `GET /ledgers/{id}/budget`：返回预算配置及当月支出进度
    - `DELETE /ledgers/{id}/budget`：禁用预算
    - _Requirements: 19.1, 19.2, 19.4, 19.5, 19.6, 19.7, 19.8, 20.1, 20.2, 20.5, 20.6_

  - [x] 9.2 实现预算进度阈值告警
    - 在 Transaction Service 的 `POST /transactions` 保存后，计算当月支出占月度预算百分比
    - 达到 80% 时响应体加入 `budget_warning: "soft"` 标志
    - 超过 100% 时加入 `budget_warning: "over"` 标志
    - _Requirements: 20.3, 20.4_

  - [x] 9.3 编写属性测试：默认分类预算均等分配（Property 22）
    - **Property 22: 默认分类预算均等分配**
    - **Validates: Requirements 19.4**

  - [x] 9.4 编写属性测试：预算进度阈值提示（Property 23）
    - **Property 23: 预算进度阈值提示**
    - **Validates: Requirements 20.3, 20.4**

- [x] 10. 图片附件后端预留（Image Attachment Backend Reserve）
  - [x] 10.1 实现图片上传与删除 API（首个可用版本不要求前端入口）
    - `POST /transactions/{txn_id}/images`：multipart/form-data，每笔交易最多 3 张；校验 magic bytes 确认 JPEG/PNG；单文件 ≤ 5MB（流式读取时提前拒绝）；存储路径写入 `TRANSACTION_IMAGE` 表
    - `DELETE /transactions/{txn_id}/images/{img_id}`：删除数据库记录及对象存储文件
    - 根据 `STORAGE_BACKEND` 环境变量选择本地文件系统 volume 或 S3/MinIO 存储
    - 交易删除时级联调用存储层删除所有关联图片文件
    - _Requirements: 22.2, 22.3_

  - [x] 10.2 编写属性测试：图片附件约束（Property 24）
    - **Property 24: 图片附件后端预留约束**
    - **Validates: Requirements 22.2, 22.3**

  - [x] 10.3 编写属性测试：交易删除级联清理图片（Property 25）
    - **Property 25: 图片后端级联清理**
    - **Validates: Requirements 22.3**

- [x] 11. 定期交易调度（Recurring Transaction Service）
  - [x] 11.1 实现定期交易模板 CRUD API
    - `POST /ledgers/{id}/recurring`、`GET /ledgers/{id}/recurring`、`PATCH /ledgers/{id}/recurring/{id}`、`DELETE /ledgers/{id}/recurring/{id}`
    - 模板 `template_data` JSONB 存储与 Transaction 相同结构的快照
    - 删除模板不影响已生成的历史交易记录
    - _Requirements: 23.1, 23.4, 23.5, 23.6_

  - [x] 11.2 实现 APScheduler 定期交易生成逻辑
    - 配置 `AsyncIOScheduler`，每天 00:00 UTC 触发
    - 查询所有 `is_active=True` 且 `next_run_date <= today` 的模板
    - 按 Ledger `timezone` 换算日期，复制 `template_data` 创建新 Transaction
    - 更新 `next_run_date`，异常捕获并写日志不影响主进程
    - _Requirements: 23.2, 23.3_

- [x] 12. 审计日志（Audit Log）
  - [x] 12.1 完成跨模块审计日志接入
    - 确认 Auth、Ledger share approval/rejection、shared user removal、Admin 操作均写入 `AuditLog`
    - 每条日志包含 event_type、user_id、UTC timestamp、source_ip 和必要 metadata
    - 数据库层通过应用代码确保 AuditLog 表无 UPDATE/DELETE 路径（不暴露修改/删除接口）
    - _Requirements: 25.7, 25.8, 25.9_

  - [x] 12.2 编写属性测试：审计日志不可删除（Property 27）
    - **Property 27: 审计日志不可删除**
    - **Validates: Requirements 25.7, 25.9**

- [x] 13. 管理员后台（Admin Service）
  - [x] 13.1 实现管理员 API
    - 创建 `backend/app/routers/admin.py`，所有路由通过 `require_admin_role` 依赖项守卫（非 admin 返回 403）
    - `GET /admin/users`：列出所有用户（email、注册日期、状态）
    - `PATCH /admin/users/{id}/status`：启用/禁用账号；禁用后该用户 JWT 返回 403
    - `DELETE /admin/users/{id}`：删除用户及所有关联数据
    - `GET /admin/stats`：返回总用户数、账本数、交易数
    - _Requirements: 16.1, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8_

  - [x] 13.2 编写属性测试：禁用用户 / 非管理员权限控制（Property 20）
    - **Property 20: 禁用用户 / 非管理员权限控制**
    - **Validates: Requirements 16.5, 16.8**

- [x] 14. 安全加固中间件
  - [x] 14.1 实现安全 HTTP 头与输入验证
    - 在 FastAPI 中间件中添加 `Content-Security-Policy`、`Strict-Transport-Security`（max-age ≥ 31536000）、`X-Content-Type-Options` 响应头
    - 复核所有路由 Pydantic Schema 已设置 `max_length` 约束（ledger name ≤ 50、note ≤ 500 等），超出返回 422
    - 复核 JSON 请求 Content-Type 校验和 ORM/参数化查询约定已覆盖所有 API
    - 在生产部署文档中明确 Cloudflare “Always Use HTTPS” 或 Redirect Rules 负责公网 HTTP → HTTPS 301；Docker 内网保持 HTTP
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 25.4, 25.5, 25.6_

  - [x] 14.2 编写属性测试：输入字段最大长度校验（Property 21）
    - **Property 21: 输入字段最大长度校验**
    - **Validates: Requirements 17.5**

  - [x] 14.3 编写属性测试：语言偏好持久化（Property 18）
    - **Property 18: 语言偏好持久化**
    - **Validates: Requirements 14.4, 14.5**

- [x] 15. Checkpoint — 后端全量测试
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. 前端：项目初始化与基础设施
  - [x] 16.1 初始化 Vue 3 项目结构
    - 配置 Vite + TypeScript，创建 `src/` 目录结构：`router/`、`stores/`、`components/`、`views/`、`api/`、`i18n/`
    - 创建 `src/api/index.ts`：axios 实例，统一注入 `Authorization: Bearer <token>` 头，处理 401/403 响应
    - 创建 `src/stores/auth.ts`（Pinia）：存储 token、user 信息，提供 login/logout/register actions
    - 配置 `vue-router`：定义路由守卫（未登录重定向到登录页）
    - _Requirements: 1.5, 1.6_

  - [x] 16.2 实现 i18n 国际化服务
    - 创建 `src/i18n/`，包含 `zh-CN.ts`、`en.ts`、`ja.ts` 三个语言文件，涵盖所有 UI 文本、错误消息、预设 Subject 和 Category 名称
    - 配置 `vue-i18n`，根据 `navigator.language` 或用户存储偏好自动选择语言
    - 语言切换在 300ms 内生效，不刷新页面
    - 用户选择语言后调用后端 API 持久化偏好
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [x] 17. 前端：认证页面
  - [x] 17.1 实现注册/登录/密码重置页面
    - 创建 `src/views/AuthPages.vue`：注册表单（email、password ≥ 8 位、可选 nickname）、登录表单、密码重置请求/确认表单
    - 原生数字输入场景使用 `inputmode="numeric"`；交易金额主流程由 Wizard 自制数字键盘承担
    - 所有交互按钮 tap target ≥ 44×44 CSS px
    - _Requirements: 1.1, 1b.1, 8.1, 8.2, 11.1_

- [x] 18. 前端：账本列表与设置
  - [x] 18.1 实现账本列表页与账本创建向导
    - 创建 `src/views/LedgerList.vue`：展示用户账本列表，提供新建账本入口
    - 账本创建向导：分屏收集名称、Entry_Mode（toggle）、Subject tracking（toggle）、Subject_Step_Mode、Necessity 开关、默认货币（ISO 4217）、是否启用预算
    - 若启用预算则跳转到 `BudgetWizard.vue`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 11.3_

  - [x] 18.2 实现账本设置页
    - 创建 `src/views/Settings.vue`：修改账本名称、Subject_Step_Mode（支持重新启用）、Necessity_Step_Mode、预算配置入口、共享码与共享成员管理
    - _Requirements: 2.8, 5.9, 9.8_

- [x] 19. 前端：Wizard Flow（记账向导）
  - [x] 19.1 实现 WizardFlow 状态机容器
    - 创建 `src/components/WizardFlow.vue`：维护步骤顺序数组；receipt 模式为 Amount → Category → Necessity → Subject，item 模式为 Amount → Category → Item → Necessity → Subject，根据账本配置动态启/禁步骤
    - 步骤完成后自动跳转下一步（无需点击 Next），支持返回上一步
    - 步骤切换和完成页显示时重置滚动位置到顶部
    - Entry_Mode=item 时进入 Category→Item→Necessity 步骤并保存单个消费名称；Entry_Mode=receipt 时选择 Category 后跳过 Item
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

  - [x] 19.2 实现各 Wizard 步骤组件
    - `WizardStepAmount.vue`：应用内自制数字键盘，顶部计算器式金额显示，OK 后进入下一步（一账本一货币，使用 Ledger 默认货币）
    - `WizardStepCategory.vue`：分类 chip 列表（偏好排序），tap 即选中
    - `WizardStepItem.vue`：消费名称 chip 列表（偏好排序）+ `+ 自定义` chip 触发手动输入文本框；仅在 Entry_Mode=item 时出现
    - `WizardStepNecessity.vue`：刚需/非刚需两选项，不默认选择、不超时自动保存，提供与普通选项同等级的大块"关闭此步骤"按钮
    - `WizardStepSubject.vue`：Subject chip 列表（偏好排序），Subject_Step_Mode=optional 时提供"以后不再问"选项
    - _Requirements: 5.1, 5.7, 5.8, 5.10, 5.11, 5.12, 7.2, 7.3, 8.1, 8.2, 11.1, 11.2, 11.4, 11.5, 21.2, 21.3_

  - [x] 19.3 实现完成提示与继续操作
    - 交易保存成功后 300ms 内显示完成提示：提供"再记一笔"和"完成，回到主页"两个选项
    - "再记一笔"重置 Wizard 从 Amount 步骤重新开始
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 19.4 编写 Vitest 测试：WizardFlow 步骤状态机
    - 验证步骤顺序与条件渲染（Subject disabled/enabled、Necessity enabled/disabled）
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 19.5 编写 Vitest 测试：Amount 自制数字键盘
    - 验证 Amount 步骤不依赖原生数字输入框，渲染应用内数字键盘并通过 OK 进入下一步
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 20. 前端：账本详情与交易列表
  - [x] 20.1 实现账本详情页
    - 创建 `src/views/LedgerDetail.vue`：按月展示消费记录（按日期倒序），每条记录尽量压缩为一行并显示日期/金额/消费名称/备注/Subject（若启用）
    - 在账本名称右侧以 plus icon 显示记一笔入口，以 gear icon 显示设置入口
    - 若预算已启用，显示月度预算进度条（80% 软警告样式、100% 超额样式）
    - _Requirements: 7.1, 12.1, 12.2, 12.3, 12.4, 12.5, 20.1, 20.2, 20.6, 11.6_

- [x] 21. 前端：预算向导与统计汇总
  - [x] 21.1 实现预算向导
    - 创建 `src/views/BudgetWizard.vue`：四步分屏向导（月度预算 → 年度预算 → 是否细分 → 逐 Category 金额），每步提供"跳过，使用默认设置"选项
    - 数字输入字段使用 `inputmode="numeric"`
    - Category 细分金额之和超出月度预算时显示警告，但允许保存
    - _Requirements: 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 11.1_

  - [x] 21.2 实现统计汇总页
    - 创建 `src/views/SummaryView.vue`：时间范围选择（本周/本月/本年/自定义），按 Category / Subject / Necessity 分组展示汇总金额
    - 按 currency_code 分组显示，不混用多货币
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 21.6_

- [x] 22. 前端：管理员后台
  - [x] 22.1 实现管理员面板
    - 创建 `src/views/AdminPanel.vue`：用户列表（email、注册日期、状态）、启用/禁用按钮、删除用户按钮、系统统计展示
    - 路由守卫：非 admin 用户访问重定向
    - _Requirements: 16.3, 16.4, 16.6, 16.7_

- [x] 23. 编写 Vitest 测试：i18n 语言切换与组件渲染
  - 验证语言切换后 i18n 消息键正确替换
  - 验证预算进度条在 80%/100% 时显示正确样式类
  - _Requirements: 14.3, 20.3, 20.4_

- [x] 24. 集成测试与端到端验收
  - [x] 24.1 编写后端集成测试（pytest + httpx TestClient）
    - 认证流程：注册 → 重复邮箱 409 → 登录 → `/auth/me` → 密码重置 → 旧 JWT 失效 → 账号注销
    - 完整记账流程：注册 → 登录 → 创建账本 → 记账 → 查看列表
    - 账本共享：申请 → 批准 → 只读用户尝试写入（返回 403）
    - 账本删除：验证交易和 share_requests 均已删除
    - 账号注销：验证所有相关数据清除
    - CSV 导出：验证行数与数据库记录一致
    - 定期交易：手动触发调度逻辑，验证生成交易字段与模板一致
    - 每个测试用例在事务内运行并在结束时回滚（`TEST_DATABASE_URL` 环境变量）
    - _Requirements: 15.1, 15.2, 15.4, 22.5, 23.2, 26.3_

- [x] 25. Final Checkpoint — 全量测试通过
  - Ensure all tests pass, ask the user if questions arise.

- [x] 26. 近期移动端记账 UX 修正
  - [x] 26.1 账本详情页记录入口压缩
    - 将账本主页的"记一笔"按钮替换为账本名称右侧 plus icon，将"设置"替换为 gear icon，并保持足够间距防误触
    - 记账过程中隐藏账本主页操作、预算和消费记录列表，只显示当前 Wizard 步骤
    - 交易保存后回到账本主页时不显示额外绿色"记录成功"状态文字，成功反馈仅保留在完成页
    - _Requirements: 5.14, 7.1, 11.1_

  - [x] 26.2 Wizard Flow 标题栏与返回行为统一
    - 为 Amount、Category、Item、Necessity、Subject、完成页统一顶部标题栏
    - Amount 页标题显示"输入金额"，左侧返回回到账本主页；后续步骤左侧返回上一屏；完成页不提供返回动作
    - 移除底部"上一步"按钮，避免重复导航
    - _Requirements: 5.4, 5.4a, 6.5, 8.1_

  - [x] 26.3 消费名称与必要性选择触控优化
    - 将"商品名称"显示文案改为"消费名称"
    - 自定义消费名称输入框的 OK 按钮固定在输入框右侧
    - 将 Item、Necessity、Subject、完成页操作统一为大块 tile 风格
    - _Requirements: 4.7, 5.10, 5.11, 11.8_

  - [x] 26.4 消费记录按月查看
    - 后端交易列表支持 `start_date` / `end_date` 日期范围过滤
    - 前端账本详情显示"消费记录"和"本月合计"，使用上一月/下一月按钮切换月份，不显示页码
    - 消费记录列表尽量一行显示，窄屏时动态隐藏次要字段
    - _Requirements: 12.4, 12.5, 12.6_

  - [x] 26.5 顶部菜单语言切换与账本列表入口调整
    - 在已登录右上角菜单中提供语言切换入口，并调用用户偏好持久化接口
    - 将账本列表页"新建账本"按钮移动到账本列表下方
    - _Requirements: 14.2, 14.4_

- [x] 27. 用户建议与公开支持功能
  - [x] 27.1 后端数据模型与迁移
    - 新增 `Suggestion` ORM 模型：author_id、title、body、is_public、status、created_at、updated_at
    - 新增 `SuggestionVote` ORM 模型：suggestion_id、user_id、vote_type，并建立 `(suggestion_id, user_id)` 唯一约束
    - 生成 Alembic 迁移脚本，支持 downgrade
    - _Requirements: 27.1, 27.2, 27.7_

  - [x] 27.2 实现 Suggestion Service API
    - `POST /suggestions`：提交建议，校验 title/body 长度和公开状态
    - `GET /suggestions/mine`：用户查看自己的建议
    - `GET /suggestions/public`：用户查看公开建议及支持/反对计数
    - `POST /suggestions/{id}/vote`：支持/反对公开建议，重复投票更新现有立场，作者不可投自己的建议
    - _Requirements: 27.1, 27.2, 27.4, 27.5, 27.6, 27.7, 27.8, 27.9, 27.12_

  - [x] 27.3 实现 Admin 建议管理 API
    - `GET /admin/suggestions`：管理员查看所有建议，包括私有建议、作者邮箱、公开状态、票数、创建时间、状态
    - `PATCH /admin/suggestions/{id}/status`：管理员更新建议状态为 new/reviewing/planned/completed/declined
    - 非 Admin 访问返回 403
    - _Requirements: 27.10, 27.11, 27.12_

  - [x] 27.4 实现前端 SuggestionsView
    - 在右上角菜单加入"提出建议"入口并跳转到建议页面
    - 建议页面提供提交表单、公开开关、"我的建议" tab、"公开建议" tab
    - 公开建议列表显示支持/反对计数，并允许当前用户支持或反对
    - _Requirements: 27.3, 27.4, 27.5, 27.6, 27.9_

  - [x] 27.5 扩展 AdminPanel 建议页面
    - 管理员后台增加建议管理视图或 tab
    - 显示所有建议的作者、内容摘要、公开状态、票数和处理状态
    - 支持管理员更新建议处理状态
    - _Requirements: 27.10, 27.11_

  - [x] 27.6 测试建议功能
    - 后端属性测试：公开建议投票唯一性（Property 29）
    - 后端集成测试：私有建议权限、作者不可自投、Admin 可查看所有建议并更新状态
    - 前端 Vitest：建议提交、我的建议/公开建议 tab、支持/反对按钮、Admin 建议管理
    - _Requirements: 27.1 - 27.12_

- [x] 28. 账本共享、个人信息与通知中心完善
  - [x] 28.1 扩展用户资料模型与认证 API
    - User 增加 `nickname` 字段，注册时可选输入 nickname
    - `GET /auth/me` 返回 nickname 与 display_name
    - `PATCH /auth/me/profile` 支持创建、更新、清空 nickname，并继续支持语言偏好持久化
    - `POST /auth/me/change-password` 支持登录用户输入当前密码后修改密码，并使旧 JWT 失效
    - _Requirements: 1.1a, 1c.1, 1c.2, 1c.3, 1c.4, 1c.5, 1c.6, 14.4_

  - [x] 28.2 完善共享 API 响应与成员权限变更
    - Share_Request、LedgerMember 响应包含用户 email、nickname、display_name
    - 新增或补齐 `PATCH /ledgers/{id}/members/{user_id}`，Owner 可修改成员 role
    - 移除/停止共享时生成 Notification，并保持只读/可写权限立即生效
    - _Requirements: 9.3, 9.5, 9.6, 9.12, 9.13, 9.14, 9.15, 9.16_

  - [x] 28.3 实现通知 API
    - `GET /notifications`、`GET /notifications/unread-count`
    - `POST /notifications/{id}/read`、`POST /notifications/read-all`
    - 共享申请、批准、拒绝、权限变更、移除成员均生成通知
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6, 28.7, 28.8, 28.9_

  - [x] 28.4 实现前端个人信息页面
    - 右上角汉堡菜单新增“个人信息”入口
    - `ProfileView.vue` 显示 email，编辑 nickname，修改密码
    - 将账号注销入口放在危险操作区域
    - _Requirements: 1c.1, 1c.2, 1c.3, 1c.5, 1c.7_

  - [x] 28.5 实现前端通知铃铛与通知列表
    - 汉堡菜单左侧显示 bell icon
    - 未读通知显示红点
    - 点击进入通知列表或抽屉，可标记单条/全部已读
    - 通知文案使用 i18n，用户名显示 nickname fallback email
    - _Requirements: 28.1 - 28.9_

  - [x] 28.6 完善前端账本共享流程
    - 设置页分享码显示框右侧增加 copy icon，并使用顶栏下方居中 toast 提示复制结果
    - 右上角菜单新增“加入共享账本”入口，输入分享码提交申请
    - 设置页 Owner 可查看待审批申请，批准/拒绝，并选择 read-only / read-write
    - 成员列表显示 nickname fallback email；点击成员进入详情页，可修改权限或停止共享
    - _Requirements: 9.1 - 9.16_

  - [x] 28.7 增加共享/通知/个人信息测试
    - 后端属性测试：通知未读计数一致性（Property 30）、共享成员权限变更生效（Property 31）
    - 后端集成测试：申请加入 → Owner 收通知 → 批准/拒绝 → 申请人收通知 → 标记已读
    - 前端 Vitest：ProfileView、NotificationBell、NotificationsView、ShareJoinView、ShareMemberView、Settings 共享区
    - _Requirements: 1c, 9, 28_

---

## Notes

- 当前任务列表未标记可选项；默认所有未完成任务都属于验收范围
- 每个任务均引用具体需求条款以确保可追溯性
- 属性测试使用 `@settings(max_examples=100)`，每个测试文件头部注释格式：`# Feature: mobile-bookkeeping-app, Property N: <property_text>`
- 早期属性测试可以先落在 service/schema 层，但 Final Checkpoint 前必须由 API + 数据库级集成测试覆盖关键业务链路
- 所有金额字段在 API 与数据库层均使用整数（货币最小单位），显示层按 locale 格式化
- 集成测试使用独立 `TEST_DATABASE_URL` 数据库，每个测试在事务中隔离
