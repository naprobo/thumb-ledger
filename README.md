# Thumb Ledger

生产环境 Cloudflare Tunnel 使用 token 方式，不使用 `cloudflared/config.yml` 或 `credentials.json`。

服务器上不要执行：

```bash
sudo cloudflared service install <token>
```

先清理旧 systemd 版 cloudflared：

```bash
sudo cloudflared service uninstall || true
sudo systemctl disable --now cloudflared || true
sudo systemctl daemon-reload
sudo systemctl status cloudflared || true
```

在 `.env.prod` 中填写：

```env
TUNNEL_TOKEN=<Cloudflare 给你的完整 token>
```

Cloudflare Zero Trust 控制台里的 Public Hostname：

```text
Hostname: ledger.neuronspark.studio
Service: http://nginx:80
```

## Release 分支发布方式

`release` 分支提交已经编译好的 `frontend/dist`。OCI 服务器不编译前端，只读取 `git pull` 后的静态文件并用 nginx 提供服务。

本地或 CI 更新前端后，在提交 release 分支前执行：

```bash
cd frontend
npm ci
npm run build
cd ..
git add frontend/dist
```

如果本地 Node/npm 的可选依赖在 Windows 上异常，可以用 Docker 在本机生成同样的 `dist`：

```bash
docker run --rm -v "$PWD:/app" -w /app/frontend node:22-alpine sh -lc "npm ci && npm run build"
git add frontend/dist
```

服务器部署：

```bash
git pull --ff-only
./deploy-app.sh
```

`deploy-app.sh` 只构建 `backend` 镜像，并重新应用 `backend` 与 `frontend` 容器；`frontend` 容器直接挂载 `./frontend/dist`，不会执行 `npm ci` 或 `npm run build`。脚本随后会显式重启外层 `nginx`，因为 `frontend` 容器重建后 Docker 内部 IP 可能变化。

首次启动：

```bash
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f cloudflared
```
