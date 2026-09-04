# MindLens — Human-First Clinical Intelligence Platform

MindLens is a counselor-facing early-signal platform for adolescent wellbeing. It synthesizes clinical insights across three perspectives (Parent, Teacher, Adolescent) across six dimensions and provides an auditable evidence chain.

## Core Principle
- **The backend surfaces signals; the counselor makes the decision.**
- No individual mental-health or self-harm risk score is calculated or stored.

## Technology Stack
- **Backend:** FastAPI (Python 3.10+), SQLModel, Pydantic, ReportLab (PDF), Pytest
- **Database:** PostgreSQL 15+
- **Frontend:** Next.js 14 (App Router), Vanilla CSS with "Serene Logic" design system tokens
- **Orchestration:** Docker Compose

## Quick Start (Local Docker Compose)

```bash
docker-compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Demo Flow
1. Open http://localhost:3000 and click **Counselor Portal** to log in.
2. View existing student cases (e.g. Alex Morgan).
3. Click into a case to review the **Perspective Heatmap**.
4. Check **Surfaced Signals** and click **"Why was this flagged?"** to inspect the auditable **Evidence Chain Drawer**.
5. Submit a clinical action choice (**Monitor**, **Reach Out**, or **Refer**) with notes.
6. Click **Download PDF Report** to view the generated ReportLab document containing the mandatory clinical disclaimer.
