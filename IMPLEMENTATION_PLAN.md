## 📂 Phase 1: Configuration & Structure

### 1. File Structure
We will add a centralized `.env` file and a dedicated Nginx configuration folder.
```text
/fullstack-app
├── .env                 # Central secrets (DB creds, API URLs)
├── docker-compose.yml
├── /backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── database.py
│   └── models.py
└── /frontend
    ├── Dockerfile
    ├── nginx/
    │   └── default.conf # Nginx config for React
    ├── package.json
    └── src/
```

### 2. The `.env` File
This file will be passed to Docker Compose.
*   **Content:**
    *   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
    *   `DATABASE_URL` (Constructed for the backend to use internally)
    *   `VITE_API_URL` (Used by React at **build time** to know where the backend is, e.g., `http://localhost:8000`)

---

## 🛠 Phase 2: Backend (FastAPI + Psycopg v3)

### 1. Dependencies (`requirements.txt`)
*   Switching driver to the modern **Psycopg 3**.
*   Libraries: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg[binary]`, `pydantic-settings` (for clean .env loading).

### 2. Database Connection (`database.py`)
*   **Driver:** Use the SQLAlchemy async dialect: `postgresql+psycopg://user:pass@db:5432/dbname`.
*   **Engine:** `create_async_engine` with `pool_pre_ping=True` (handles connection drops).
*   **Startup:** Define a lifecycle manager (`@asynccontextmanager`) in `main.py` to await `conn.run_sync(Base.metadata.create_all)` ensures tables exist before the app accepts requests.

### 3. Models (`models.py`)
*   **Table:** `submissions`
*   **Columns:**
    *   `id`: Integer, Primary Key, Autoincrement.
    *   `data`: `JSONB` type (Specific to Postgres).

### 4. API & CORS (`main.py`)
*   **Middleware:** Add `CORSMiddleware`.
    *   `allow_origins=["*"]` (As per your request).
    *   `allow_methods=["*"]`, `allow_headers=["*"]`.
*   **Endpoints:**
    *   `GET /form`: Returns the hardcoded schema.
    *   `POST /form`: Accepts `pydantic.Json` or `Dict`.
        *   **Validation:** Check if keys `name` and `email` exist in the payload.
        *   **Storage:** Save the entire dictionary into the `data` (JSONB) column.

---

## 🎨 Phase 3: Frontend (React + Nginx)

### 1. Build Logic
*   The React app needs to know the Backend URL. Since Nginx serves static files, we cannot inject environment variables at runtime easily.
*   **Strategy:** We will pass `VITE_API_URL` as a **build argument** in the Dockerfile so it gets baked into the static JS bundle.

### 2. Nginx Configuration (`frontend/nginx/default.conf`)
*   **Root:** `/usr/share/nginx/html`.
*   **SPA Routing:** Essential for React.
    *   `location / { try_files $uri $uri/ /index.html; }`
    *   This ensures that refreshing a page like `localhost/form` doesn't return a 404 from Nginx, but serves `index.html` so React Router can handle it.

### 3. Dockerfile (Multi-stage)
*   **Stage 1 (Builder):** Node image.
    *   `ARG VITE_API_URL`
    *   `ENV VITE_API_URL=$VITE_API_URL`
    *   `RUN npm run build`
*   **Stage 2 (Runner):** Nginx image.
    *   Copy build output from Stage 1.
    *   Copy `default.conf` to `/etc/nginx/conf.d/default.conf`.

---

## 🐳 Phase 4: Orchestration (Docker Compose)

### 1. Services
*   **db:** `postgres:15`.
    *   `env_file`: `.env` (Auto-configures user/pass).
    *   `volumes`: Persistent data mapping.
*   **backend:**
    *   `env_file`: `.env`.
    *   `depends_on`: `db`.
    *   `ports`: `8000:8000` (Exposed so the browser/React can hit it).
*   **frontend:**
    *   `build`:
        *   `context`: ./frontend
        *   `args`:
            *   `VITE_API_URL: "http://localhost:8000"` (Or read from .env).
    *   `ports`: `80:80`.

### 2. Networking
*   All services on a shared `bridge` network to allow container-to-container communication (Backend talking to DB).

---

## 📋 Execution Steps

1.  **Create `.env`** with your credentials.
2.  **Setup Backend:** Create `models.py` with JSONB and `main.py` with CORS/Async logic.
3.  **Setup Frontend:** Scafffold Vite app, add `axios`/`fetch` calls pointing to `import.meta.env.VITE_API_URL`.
4.  **Create Nginx Config:** Ensure `try_files` is set.
5.  **Docker Compose Up:** Run the stack.