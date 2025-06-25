# Technical Design Document – Autonomica “Marketing Team” Pilot for **thegptshop.online**

---

## 1. Product Overview

### Purpose

Autonomica aims to automate SEO research, content production, repurposing and cross‑channel publication for **thegptshop.online**, a storefront selling one‑use claim codes that unlock custom GPTs. By delegating these marketing workflows to an OWL/CAMEL multi‑agent workforce, the pilot seeks to cut manual effort, grow traffic and validate token‑per‑click unit economics before investing in a full SaaS platform.

### Target Audience

- **Primary Persona – Solo Founder/Marketer**: runs thegptshop.online, needs predictable web traffic and brand presence but lacks time for daily marketing tasks.
- **Secondary Persona – AI‑Maker Early Adopter**: looks for reliable sources of custom GPTs; follows social channels for discovery. Pain‑points: finds few authoritative resources and inconsistent updates.

### Expected Outcomes

| Outcome                   | KPI                                   | Target             |
| ------------------------- | ------------------------------------- | ------------------ |
| Organic visibility uplift | Google Search Console impressions     | +25 % in 30 days   |
| Engagement boost          | Avg. CTR per social post              | ≥3 %               |
| Cost efficiency           | ≤50 OpenAI tokens per qualified click | Maintain for pilot |
| Time savings              | Manual editing time per post          | <30 min            |

---

## 2. Design Details

### 2.1 Architectural Overview

```
┌────────────┐     HTTP       ┌────────────────────┐
│ Next.js UI │──────────────►│  Python API (OWL)  │
└────────────┘  (Vercel Edge)│   • Workforce      │
                             │   • Agent toolkit   │
                             └────────┬───────────┘
                                      │ async jobs (Redis)
                                      ▼
                             ┌────────────────────┐
                             │  Worker Pod        │
                             │  (Railway Docker)  │
                             │  • Playwright      │
                             │  • SEMrush calls   │
                             └────────────────────┘
```

- **UI** – Next.js dashboard (Vercel) streams chat via Vercel AI SDK.
- **API** – Python Serverless Function boots OWL Workforce per request (<30 s) or off‑loads long jobs to worker pod through Redis queue.
- **Worker Pod** – Docker on Railway runs Playwright scrapes & publishes to social APIs.
- **Data** – SQLite for pilot; CSV exports; Supabase bucket for logs (future SaaS).

### 2.2 Data Structures & Algorithms

| Entity          | Structure                                | Notes                                 |
| --------------- | ---------------------------------------- | ------------------------------------- |
| `Task`          | `{id, goal, status, cost_tokens}`        | Primary unit passed to Workforce.     |
| `AgentMemory`   | Vector‑store (FAISS) keyed by `agent_id` | Stores past messages for RAG context. |
| `KeywordRecord` | `{keyword, volume, cpc, kd, source_url}` | Parsed from SEMrush / SERP HTML.      |

Algorithms:

- **Keyword clustering** – cosine similarity on keyword embeddings to group long‑tails.
- **Content repurposing** – LangChain `Stuff → Summarise` pipeline for blog ➜ tweet/thread/carousel.
- **Posting schedule** – simple greedy algorithm selecting next slot with highest predicted CTR based on historical channel data.

### 2.3 System Interfaces

- **OpenAI ChatCompletion v1** – content generation & reasoning.
- **SEMrush API** – `/domain/v2/` endpoints for keyword metrics.
- **Google Search Console API** – `searchanalytics.query` for impressions/clicks.
- **Twitter v2** – `POST /tweets` for publishing.
- **Facebook Graph API** – `/{page‑id}/feed` for link posts.
- **Redis** – pub/sub queue between API and worker pod.

### 2.4 User Interfaces

- **Dashboard** – Lists active tasks, agent chat stream, cost ticker, and KPI charts.
- **Content Approval Modal** – Approve/Reject drafts before they are queued for publish.
- **Settings** – Enter API keys, posting cadence, brand voice guidelines.

### 2.5 Hardware Interfaces

None required; all compute runs on cloud VMs/containers. Headless Chrome within worker pod uses virtual framebuffer (Xvfb).

---

## 3. Testing Plan

### 3.1 Test Strategies

| Layer         | Tests                               | Goal                                   |
| ------------- | ----------------------------------- | -------------------------------------- |
| Agents (unit) | Prompt unit tests with fixed seeds  | Verify role adherence                  |
| API           | Pytest HTTP tests                   | Ensure 200/400/500 paths               |
| Integration   | Simulated end‑to‑end run on staging | Validate agent delegation & tool calls |
| Performance   | Locust hitting `/api/agents`        | Stay <2 s P95 latency                  |

### 3.2 Testing Tools

- **Pytest** – unit + integration.
- **Playwright Test** – validate browser scrapes.
- **Locust** – load tests.
- **Coverage.py + Codecov** – coverage tracking.

### 3.3 Testing Environments

- **Local dev** – Docker Compose spins Redis + worker.
- **Staging (Railway)** – mirrors prod container images.
- **Prod (Vercel + Railway)** – canary deployment to 5 % traffic.

### 3.4 Test Cases (samples)

1. **Keyword Mining Happy Path** – Given “custom GPT”, expect CSV with ≥10 rows containing `volume` field.
2. **Content Approval Rejection** – Reject draft, ensure Social Scheduler skips posting.
3. **Token Guardrail** – Simulate 10 K token burst; CEO agent aborts task.

### 3.5 Reporting & Metrics

- **CI summary** – GitHub Actions posts Pytest/Locust results.
- **Grafana Dashboard** – latency, queue length, token cost per request.

---

## 4. Deployment Plan

### 4.1 Deployment Environment

- **Frontend & API** – Vercel Hobby (Edge + Python Runtime).
- **Worker** – Railway free Docker (500 h/mo), autoscale 0→1.
- **Database** – SQLite file in Railway volume (pilot scope).

### 4.2 Deployment Tools

- **GitHub Actions** – lint, test, build.
- **Vercel CLI** – push preview & prod.
- **Railway CLI** – build & deploy worker image.

### 4.3 Deployment Steps

1. Merge to `main` triggers CI → tests.
2. Vercel builds preview; human QA.
3. Tag `vX.Y.Z` → GitHub Action builds Docker, pushes to Railway.
4. Promote Vercel preview to prod.
5. Run smoke test `/api/agents?goal=ping`.

### 4.4 Post‑Deployment Verification

- Check Grafana dashboards: error rate <1 %.
- Hit `/health` endpoints; ensure Redis queue length <5.
- Manual approval of first generated post.

### 4.5 Continuous Deployment

CD flagged **on** after pilot once tests >90 % pass‑rate. Automated canary (5 %) then full rollout; automatic rollback via Vercel if error rate >5 % over 10 min.

---

*Document owner: Jai (Product Lead)*\
*Last updated: 30 May 2025*

