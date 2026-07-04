# FastAPI Blog Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.100%2B-green)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, high-performance blogging platform built with **FastAPI** and **SQLAlchemy**, featuring rich media support, asynchronous processing, and production-ready deployment.

## Table of Contents

- [Introduction](#introduction)
- [Core Features](#core-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Swagger Documentation](#Swagger-Documentation)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Introduction

**FastAPI Blog Platform** is an enterprise-grade application enabling the creation, management, and publication of blog articles with advanced capabilities. Designed to handle high request volumes while maintaining clean architecture and maintainability.

### Key Advantages

- **Asynchronous Processing**: Full async/await support throughout the stack
- **Automatic Documentation**: Interactive OpenAPI/Swagger documentation out-of-the-box
- **Type Safety**: Strict type checking with Pydantic v2
- **Database Agnostic**: SQLAlchemy ORM supporting multiple database backends
- **Containerized**: Ready-to-use Docker and docker-compose configuration

---

## Core Features

### Content Management
- **Asynchronous CRUD:** Dynamic, fully async article creation, retrieval, updates, and deletion mapping directly to PostgreSQL.
- **Cursor Pagination:** Performance-optimized queries using server-side limit and skip constraints (`/api/posts?skip=2&limit=2`).
- **Owner-Isolated Mutations:** Strict security checks ensuring users can only modify or delete their own posts.

### User & Authentication
- **OAuth2 JWT Authentication:** Secured endpoints using modern stateless JSON Web Tokens.
- **Secure Password Hashing:** Password storage built on secure cryptographic hashing functions.
- **Password Recovery Flow:** Dedicated data structures (`password_reset_tokens`) providing secure, short-lived reset workflows.

### Media Engine
- **Profile Asset Architecture:** User avatar asset storage framework with strict boundary limits.
- **Cloud Infrastructure Ready:** Architecture prepared for streaming uploads via cloud backends (Oracle Object Storage / local storage fallback).

---

## Technology Stack

| Category | Technologies | Key Attributes |
| :--- | :--- | :--- |
| **Framework** | FastAPI | Core ASGI engine, auto-OpenAPI generation, Pydantic v2 validation |
| **Database ORM** | SQLAlchemy 2.0 | Async Engine, declarative model mapping, contextual sessions |
| **DB Driver** | Asyncpg | High-throughput asynchronous PostgreSQL client |
| **Migrations** | Alembic | Schema versioning control and transactional DDL automation |
| **Package Engine**| UV | Next-gen lightning-fast dependency management and resolution |
| **Testing Suite** | Pytest | Integrated asynchronous functional API execution suite |

---

## System Architecture

The platform operates on a decoupled layered architecture using Dependency Injection (`Depends`) to manage database session lifecycles:

### Conceptual Design

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │                 Client Layer                     │   │
│  │                 (HTTP Clients / Swagger UI)      │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓ (Async JSON Requests)         │
│  ┌──────────────────────────────────────────────────┐   │
│  │                API Routing Layer                 │   │
│  │  (app/api/posts.py & app/api/users.py)           │   │
│  └──────────────────────────────────────────────────┘   │
│                 ↓  (Dependency Injection: get_db)       │
│  ┌──────────────────────────────────────────────────┐   │
│  │     Data Access Layer (Repositories/CRUD)        │   │
│  │ (SQLAlchemy AsyncSession/app/models/models.py)   │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │        Production Database (Port 5433)           │   │
│  │        Test Database       (Port 5434)           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
fastapi-blog/
├── app/                          # Main application package
│   ├── api/                      # API routing layers (Request/Response handling)
│   │   ├── posts.py              # Article management and pagination endpoints
│   │   └── users.py              # User account registration and management routes
│   ├── core/                     # Application core configuration and security
│   │   ├── auth.py               # JWT token generation, decoding, and password hashing
│   │   ├── config.py             # Pydantic BaseSettings for dynamic environment parsing
│   │   └── database.py           # Async SQLAlchemy engine and sessionmaker setup
│   ├── database/                 # Extra database configurations
│   │   └── schema.py             # Base system schema definitions
│   ├── models/                   # Database persistence layer
│   │   └── models.py             # SQLAlchemy ORM operational models (Post, User, etc.)
│   ├── services/                 # Business logic layer separating endpoints from DB models
│   │   ├── user_service.py       # Core logic for user management and validations
│   │   └── posts_service.py      # Core logic for processing and mutating blog posts
│   ├── static/                   # Static assets served by the application (Front-End)
│   │   ├── css/                  # Application stylesheets
│   │   ├── icons/                # System interface icons and vectors
│   │   ├── js/                   # Client-side JavaScript components
│   │   └── profile_pics/         # Local placeholder cache for user avatars
│   ├── templates/                # Jinja2 HTML templates for UI rendering
│   ├── utils/                    # Core utility helpers
│   │   ├── email.py              # Asynchronous email dispatching operations
│   │   └── image.py              # Image compression and optimization pipeline
│   └── main.py                   # FastAPI initialization, lifespan events, and middleware setup
├── media/                        # Root storage directory for user-generated content
│   └── profile_pics/             # Persistent directory for uploaded user avatars
├── populate_images/              # Utility workspace for mock image generation
├── scripts/                      # Independent operational and verification scripts
│   ├── check_oracle.py           # Cloud integration verification (Oracle Object Storage)
│   └── test_data.py              # Raw development script for verifying basic model operations
├── tests/                        # Automated testing suite running on isolated test runtime
│   ├── api/                      # Functional and integration route validation tests
│   │   ├── test_posts.py         # Test cases for article creation, viewing, and pagination
│   │   └── test_users.py         # Test cases for user registration, login, and auth flows
│   ├── conftest.py               # Shared transactional database fixtures and mock clients
│   └── __init__.py
├── .python-version               # Strict Python runtime version locking descriptor
├── Dockerfile                    # Blueprint for the multi-stage application image
├── docker-compose.yaml           # Multi-container orchestration (App, Postgres, Test DB)
├── pyproject.toml                # Project metadata, configurations, and UV dependencies
├── uv.lock                       # Deterministic, platform-agnostic locked dependency graph
├── README.md                     # Application documentation and deployment manual
└── .gitignore                    # Specifies intentionally untracked files to ignore
```

---

## Installation

### Prerequisites
- [Docker Desktop](https://docs.docker.com/get-docker/) (Includes Docker Compose v2)
- [Python 3.11+](https://www.python.org/downloads/) (Required for local test orchestration)
- [uv](https://github.com/astral-sh/uv) (Extremely fast local Python package manager)

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/fastapi-blog-platform.git](https://github.com/yourusername/fastapi-blog-platform.git)
   cd fastapi-blog-platform

### Docker Setup

#### Build & Run with Docker Compose
```bash
# Production-like environment
docker compose up -d --build

# View logs
docker logs fastapi_blog_app

# Stop services
docker compose down -v
```

---

## Development

### Database Schema Migrations

```bash
# Generate a new deterministic structural migration script
docker compose exec web alembic revision --autogenerate -m "Describe migration here"

# Apply all pending schema timeline mutations to head state
docker compose exec web alembic upgrade head

# Rollback the last applied schema migration state (-1 mutation)
docker compose exec web alembic downgrade -1

# Database Seed Ingestion
docker compose exec -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@fastapi_postgres:5432/postgres" web python -m scripts.test_db
```

---

---

### Swagger Documentation

The API automatically generates interactive documentation thanks to FastAPI and OpenAPI 3.0 specifications. Once the Docker cluster is fully operational, you can explore, test, and authenticate against the endpoints directly via your browser:

* **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Alternative ReDoc UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Testing

The platform enforces strict isolation between production data and test pipelines. Test execution runs locally on your host machine via `uv`, targeting an ephemeral, isolated test database container (`postgres_test`) exposed on **Port 5434**.

### Running Test Suites (Windows PowerShell)

Ensure your docker containers are active (`docker compose up -d`), then run any of the following commands directly from your local PowerShell terminal:

```powershell
# 1. Execute all test suites across the API directory
$env:DATABASE_URL_TEST="postgresql+asyncpg://postgres:postgres@localhost:5434/test_blog"; uv run pytest tests/api/ -v

# 2. Run only Post-related features validation
$env:DATABASE_URL_TEST="postgresql+asyncpg://postgres:postgres@localhost:5434/test_blog"; uv run pytest tests/api/test_posts.py -v

# 3. Run only User-related features validation
$env:DATABASE_URL_TEST="postgresql+asyncpg://postgres:postgres@localhost:5434/test_blog"; uv run pytest tests/api/test_users.py -v

# 4. Target a specific individual test function
$env:DATABASE_URL_TEST="postgresql+asyncpg://postgres:postgres@localhost:5434/test_blog"; uv run pytest tests/api/test_posts.py::test_get_posts_empty -v

# 5. Run tests and display standard output logs (print statements)
$env:DATABASE_URL_TEST="postgresql+asyncpg://postgres:postgres@localhost:5434/test_blog"; uv run pytest tests/api/ -v -s
```

---

### Environment Variables 

```env
SECRET_KEY=

DATABASE_URL=
DATABASE_URL_TEST=

NAMESPACE=
BUCKET_NAME=
REGION=
ACCESS_KEY_ID=
SECRET_ACCESS_KEY=
ORACLE_PAR_URL=

MAIL_SERVER=
MAIL_PORT=
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_USE_TLS=
FRONTEND_URL=
```

---
### Author
[DoctorVerRossi](https://github.com/vrstelios)

---

If you find this project helpful, please give it a star on GitHub!
