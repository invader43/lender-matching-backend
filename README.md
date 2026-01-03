# Dynamic Lender Matching System

An AI-powered lender matching system that uses **Gemini** to extract underwriting rules from PDF documents and automatically adapts its data schema as new requirements are discovered.

## 🌟 Key Features

- **Dynamic Schema** - Parameter registry allows adding new fields without database migrations
- **AI-Powered Ingestion** - Gemini processes PDFs and extracts structured rules
- **Flexible Matching** - Rule evaluation engine that works with any parameter combination
- **Transparent Results** - Detailed explanations of why each lender matched or rejected
- **Modern UI** - Responsive React application with TypeScript and dynamic forms

## 🏗️ Architecture

### Backend (FastAPI + PostgreSQL)
- **Dynamic Parameter Registry** - Defines available fields in the system
- **Normalized Database Schema** - Proper relationships between lenders, policies, and rules
- **RESTful API** - 15+ endpoints organized by domain
- **Background Processing** - Async tasks for PDF ingestion and matching
- **Gemini Integration** - Uses `google-genai` client for native PDF processing

### Frontend (React + TypeScript)
- **Type-Safe** - Full TypeScript coverage
- **Dynamic Forms** - Forms that adapt based on backend parameter definitions
- **Rich UI** - Modern design with gradients, animations, and responsive layout
- **Real-time Updates** - Polls for async processing results

## 🚀 Quick Start
The fastest way to get started is to use Docker Compose.
## 🐳 Docker Deployment
Create a `.env` file in the `root` directory.

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lender_db
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/lender_db

# External APIs
GOOGLE_API_KEY=<GEMINI_API_KEY>
```
```bash
# Build and run with Docker Compose
docker-compose up --build

# The application will be available at:
# - Frontend: http://localhost:80
# - Backend: http://localhost:8000
```


### Prerequisites

- PostgreSQL database
- Google Cloud account with Gemini API enabled
- Node.js 18+ and Python 3.9+

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -e .
# or with uv
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and set:
# - DATABASE_URL=postgresql+psycopg://user:pass@localhost/dbname
# - GOOGLE_API_KEY=your_gemini_api_key

# Seed initial parameters
python seed_parameters.py

# Run the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional)
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

The application will be available at `http://localhost:5173`

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**Parameters**
- `GET /parameters` - List all parameter definitions
- `POST /parameters` - Create new parameter

**Lenders**
- `POST /lenders` - Create lender
- `POST /lenders/{id}/ingest-guidelines` - Upload PDF
- `GET /lenders/{id}/policies` - Get lender policies

**Applications**
- `POST /applications` - Submit loan application
- `GET /applications/{id}/matches` - Get match results

## 🧪 Testing

### Test Dynamic Form

1. Open frontend at `http://localhost:5173`
2. Fill out the loan application form
3. Submit and view matching results

### Test PDF Ingestion

```bash
# Create a lender
curl -X POST http://localhost:8000/lenders \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Lender", "description": "Test"}'

# Upload PDF (replace {lender_id})
curl -X POST http://localhost:8000/lenders/{lender_id}/ingest-guidelines \
  -F "file=@policy.pdf"
```

## 📁 Project Structure

```
root/
├── backend/
│   ├── models/              # SQLAlchemy models
│   │   ├── parameter_definitions.py
│   │   ├── lenders.py
│   │   ├── policies.py
│   │   ├── policy_rules.py
│   │   ├── loan_applications.py
│   │   └── match_results.py
│   ├── routers/             # API endpoints
│   │   ├── parameters.py
│   │   ├── lenders.py
│   │   ├── policies.py
│   │   └── applications.py
│   ├── services/            # Business logic
│   │   ├── gemini_service.py
│   │   ├── ingestion_service.py
│   │   └── matching_service.py
│   ├── utils/               # Utilities
│   │   └── validators.py
│   ├── database.py          # Database configuration
│   ├── schemas.py           # Pydantic schemas
│   ├── main.py              # FastAPI application
│   └── seed_parameters.py   # Initial data
├── frontend/
│   └── src/
│       ├── types/           # TypeScript types
│       │   └── models.ts
│       ├── services/        # API client
│       │   └── api.ts
│       ├── components/      # Shared components
│       │   ├── DynamicFieldRenderer.tsx
│       │   ├── MatchCard.tsx
│       │   └── ReasoningList.tsx
│       ├── views/           # Page components
│       │   ├── ApplicationForm.tsx
│       │   └── MatchingResults.tsx
│       ├── App.tsx          # Main app with routing
│       ├── App.css          # Styles
│       └── main.tsx         # Entry point
└── docker-compose.yml       # Docker setup
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory or use the settings in `docker-compose.yml`.

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lender_db
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/lender_db

# External APIs
GOOGLE_API_KEY=<GEMINI_API_KEY>
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory (or use `.env.local` for local dev).

```env
VITE_API_URL=http://localhost:8000
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** - Database with JSONB support
- **google-genai** - Official Gemini SDK
- **Pydantic** - Data validation
- **asyncpg** - Async PostgreSQL driver

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Vite** - Build tool

## 📝 How It Works

### 1. Parameter Registry
The system maintains a registry of all available data fields. This allows the schema to grow dynamically without database migrations.

### 2. PDF Ingestion
When a lender uploads a policy PDF:
1. File is sent to Gemini with context about existing parameters
2. Gemini extracts rules and identifies if new parameters are needed
3. New parameters are created automatically
4. Rules are stored in normalized format

### 3. Application Submission
When an applicant submits a form:
1. Frontend fetches current parameters and builds form dynamically
2. Form data is validated against parameter definitions
3. Application is saved with JSONB storage for flexibility
4. Background task starts matching process

### 4. Matching Engine
The matching engine:
1. Loads all active lender policies
2. Evaluates each rule against application data
3. Supports operators: `>`, `<`, `>=`, `<=`, `=`, `!=`, `in`, `contains`
4. Calculates fit score from scoring rules
5. Stores detailed evaluation breakdown

### 5. Results Display
The frontend:
1. Polls for results while status is "processing"
2. Displays approved and declined lenders
3. Shows fit scores with circular progress indicators
4. Provides detailed reasoning for each match

## 🚧 Production Considerations

For production deployment, consider:

1. **Task Queue** - Replace FastAPI BackgroundTasks with Celery or Redis Queue
2. **Authentication** - Add JWT authentication for admin endpoints
3. **Caching** - Use Redis for parameter definitions
4. **File Storage** - Use S3 instead of local disk for PDFs
5. **Monitoring** - Add Prometheus metrics and health checks
6. **Rate Limiting** - Protect API endpoints from abuse