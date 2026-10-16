# AI HR 智能招聘平台

内部 AI 简历初筛系统（MVP）。领域术语见 `CONTEXT.md`，方案见 `docs/specs/`，决策见 `docs/adr/`。

## 快速开始

1. 启动基础设施（PostgreSQL/pgvector、Redis、MinIO）：

   ```
   docker compose up -d
   ```

2. 后端（在 `backend/` 下）：

   ```
   python -m venv .venv
   .venv/Scripts/pip install -r requirements.txt    # Windows
   .venv/Scripts/uvicorn app.main:app --reload
   ```

3. 前端（在 `frontend/` 下）：

   ```
   npm install
   npm run dev
   ```

4. 访问 http://localhost:5173

## 测试

```
cd backend
.venv/Scripts/pytest
```
