# Thumb Ledger

手机端快速记账网页应用。后端 FastAPI + PostgreSQL，前端 Vue 3，通过 Docker Compose 管理开发与生产环境。

## 技术栈

- **后端**: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **前端**: Vue 3, Pinia, vue-i18n, Vite
- **环境**: Docker Compose, VS Code Dev Container
- **生产**: nginx + Cloudflare Zero Trust Tunnel

---

## 开发环境启动

### 前提条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [VS Code](https://code.visualstudio.com/) + [Dev Containers 扩展](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### 步骤

**1. 复制环境变量文件**

```bash
cp .env.example .env
```

`.env` 中的默认值适用于本地开发，无需修改即可启动。

**2. 用 VS Code 打开 Dev Container**

按 `F1` → `Dev Containers: Reopen in Container`

VS Code 会自动构建并启动所有服务（backend、frontend、db、mailpit）。

**3. 访问服务**

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 邮件查看（Mailpit） | http://localhost:8025 |
| 数据库 | localhost:5432 |

### 不使用 Dev Container 直接启动

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

---

## 数据库迁移

```bash
# 生成新迁移文件
alembic revision --autogenerate -m "描述变更内容"

# 应用迁移
alembic upgrade head

# 回滚一个版本
alembic downgrade -1
```

---

## 运行测试

```bash
# 后端（在 backend/ 目录或 Dev Container 内）
pytest

# 前端
cd frontend
npm run test
```

---

## 生产环境部署

**1. 在 Cloudflare Zero Trust 创建 Tunnel**

使用 Cloudflare 推荐的 token 方式。Tunnel 创建后，在 Public Hostname 中配置：

```text
Hostname: ledger.neuronspark.studio
Service: http://nginx:80
```

这里的 `nginx` 是 Docker Compose 内部服务名，不是服务器的 `localhost`。

如果服务器上曾经安装过 systemd 版 cloudflared，先清理旧服务：

```bash
sudo cloudflared service uninstall || true
sudo systemctl disable --now cloudflared || true
sudo systemctl daemon-reload
```

本项目由 Docker Compose 启动 `cloudflared` 容器，不需要执行 `sudo cloudflared service install <token>`。

**2. 创建生产环境变量文件**

```bash
cp .env.example .env.prod
# 编辑 .env.prod，填入强密码、生产配置和 Cloudflare Tunnel token
```

至少需要设置：

```env
APP_ENV=production
SECRET_KEY=<openssl rand -hex 32 生成的密钥>
ALLOWED_ORIGINS=https://ledger.neuronspark.studio
TUNNEL_TOKEN=<Cloudflare 提供的完整 tunnel token>
```

不要提交 `.env.prod`，其中包含生产密钥。

**3. 构建并启动**

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f cloudflared
```

生产环境下 cloudflared 会自动建立 Tunnel，外部流量通过 Cloudflare → nginx → backend/frontend，数据库不对外暴露。

---

## 项目结构

```
/
├── backend/          # FastAPI 后端
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # Vue 3 前端
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── nginx/            # 生产 nginx 配置
├── .devcontainer/    # VS Code Dev Container 配置
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── .env.example
```
