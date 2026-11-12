# Journey Intelligence

**Multi-Channel Customer Journey Analytics, Anomaly Detection & Decision Intelligence**

## Overview

Journey Intelligence is a customer journey analytics platform that captures and analyzes interactions across web, mobile, support, and purchase channels.

It identifies journey drop-offs, detects anomalous events, evaluates detection results against ground-truth labels, and provides dashboard-based insights.

## Key Features

- Multi-channel customer journey tracking.
- Customer, session, product, cart, order and support data modeling.
- Seven-stage conversion funnel analytics.
- Journey drop-off identification.
- Duplicate conversion detection.
- Out-of-order event detection.
- Consent-aware identity-link validation.
- Bot traffic anomaly detection.
- Session-level event timeline and traceability.
- Ground-truth-based evaluation.
- CSV, JSON and PostgreSQL SQL exports.
- Automated database, data-quality and API tests.

## Architecture

```text
Customer Interactions
   |
   v
Web / Mobile / Support / Purchase
   |
   v
FastAPI Backend
   |
   +------ PostgreSQL + pgvector
   |
   +------ Journey Event Processing
   |
   +------ Anomaly Detection
   |
   +------ Funnel & Outcome Analytics
   |
   v
React Dashboard
   |
   +------ Journey Funnel
   +------ Anomaly Monitoring
   +------ Evaluation Metrics
   +------ Session Timeline
```

## Technology Stack

| Layer          | Technologies               |
| -------------- | -------------------------- |
| Frontend       | React, Vite, CSS, Recharts |
| Backend        | Python, FastAPI            |
| Database       | PostgreSQL, pgvector       |
| ORM            | SQLAlchemy                 |
| Testing        | Pytest, FastAPI TestClient |
| Infrastructure | Docker                     |
| Data formats   | CSV, JSON, SQL             |

## Project Structure

```text
journey-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── export/
│   │   ├── generator/
│   │   ├── models/
│   │   ├── services/
│   │   └── validation/
│   ├── docs/
│   ├── exports/
│   ├── tests/
│   ├── requirements.txt
│   └── test_db.py
├── frontend/
├── docs/
└── README.md
```

## Setup and Execution

### 1. Start PostgreSQL

The project uses PostgreSQL through Docker.

Configure the database connection in `backend/.env`. Do not commit credentials.

### 2. Start the backend

```powershell
cd backend

python -m venv venv

.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend API:

`http://localhost:8000`

Swagger documentation:

`http://localhost:8000/docs`

### 3. Start the frontend

Open another terminal:

```powershell
cd frontend

npm install

npm run dev
```

Frontend:

`http://localhost:5173`

## Data Generation

From the backend directory:

```powershell
python -m app.generator.generate --sessions 1000 --seed 20261022
```

The generator supports configurable session counts and random seeds.

**Warning:** The `--reset` option truncates existing project data. Use it only when intentionally regenerating the database.

## Data Exports

Run:

```powershell
python -m app.export.export_data
```

Exports are written to `backend/exports/`.

- CSV: individual table exports.
- JSON: individual table exports.
- SQL: PostgreSQL database dump.
- Manifest: table names and exported row counts.

## Data Quality and Testing

Run:

```powershell
python -m pytest -v
```

The current automated test suite contains eight passing tests covering database connectivity, data quality and API endpoints.

## Current Demonstration Results

The current synthetic dataset contains:

- 1,000 sessions.
- 20,000 journey events.
- 5,000 customers.
- 100 products.
- 17 database tables.
- 30,542 total database records.

The anomaly detection demonstration identified 40 injected anomalies:

| Scenario                   | Detected |
| -------------------------- | -------: |
| Duplicate conversion       |       10 |
| Out-of-order event         |       10 |
| Unauthorized identity link |       10 |
| Bot traffic                |       10 |

These are synthetic test results and should not be interpreted as proof of production detection accuracy.

## Database Documentation

See `backend/docs/data_dictionary.md` for the database schema, columns, relationships, keys and constraints.

## Future Enhancements

The current prototype establishes the core Journey Intelligence architecture. The following enhancements are planned to strengthen its scalability, intelligence, and production readiness:

- Develop advanced behavioral bot detection using session activity patterns.
- Expand performance testing across large-scale datasets.
- Implement comprehensive event processing history and monitoring.
- Enhance identity resolution and cross-channel sessionization.
- Benchmark database and API performance at 100,000 sessions and 2 million events.
- Evaluate anomaly detection against more diverse and realistic scenarios.

## Project Repository

GitHub: https://github.com/Git-Mahesh06/journey-intelligence
