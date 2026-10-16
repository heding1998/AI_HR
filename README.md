# AI HR 智能招聘平台

内部 AI 简历初筛系统（MVP）。领域术语见 `CONTEXT.md`，方案见 `docs/specs/`，决策见 `docs/adr/`。

## 快速开始

1. 启动基础设施（PostgreSQL/pgvector、Redis、MinIO）：

   ```
   docker compose up -d
   ```

   > 注：为避免与本机 PostgreSQL 服务（占用 5432）冲突，本项目 Docker 的 PG 映射到宿主机 5433 端口。

2. 后端（在 `backend/` 下）：

   ```
   python -m venv .venv
   .venv/Scripts/pip install -r requirements.txt    # Windows
   .venv/Scripts/alembic upgrade head                # 建表
   .venv/Scripts/python -m app.seed                  # 预置默认管理员
   .venv/Scripts/uvicorn app.main:app --reload
   ```

3. 前端（在 `frontend/` 下）：

   ```
   npm install
   npm run dev
   ```

4. 访问 http://localhost:5173

## 默认管理员

- 用户名：`admin`
- 密码：`admin123`

可通过 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 环境变量覆盖（见 `.env.example`）。

## 测试

后端测试依赖 Docker PostgreSQL（`docker compose up -d postgres`）。测试库 `aihr_test` 会在测试会话中自动创建与清理。

```
cd backend
.venv/Scripts/pytest
```
