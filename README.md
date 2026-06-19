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

启动：

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f cloudflared
```
