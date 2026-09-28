<div align="center">

# 🚀 SÈO TRUM (Auto Social AI)

**Multi-Channel Social Operations & Content Distribution Platform for SMEs**  
*Open Source (MIT License) · Self-Hosted · Privacy-First*

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688.svg)](https://fastapi.tiangolo.com/)
[![React: 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)
[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](.github/workflows/ci.yml)

*[Tiếng Việt](README.md) · **English***

</div>

---

> [!NOTE]
> **Foundation & MIT License Statement:**  
> **Sèo Trum** is built on the open-source agentic AI foundation **[Javis OS](https://github.com/blogminhquy/javis-os)** (Copyright © 2026 Nguyễn Minh Quý - blogminhquy, MIT License).  
> The Sèo Trum team inherits the core agentic runtime and Model Context Protocol (MCP Hub) from Javis OS, while designing and building the complete social business layer: **Social Channels Hub, TikTok Gateway Automation, Human-in-the-Loop Unified Inbox, Auto Lead Scoring CRM, and the RBAC Operations Portal (`/ops`)**.

---

## 🎯 Overview

For Small and Medium Enterprises (SMEs), social media is the commercial lifeblood but also a severe operational bottleneck:
1. **Overwhelm & Lost Leads:** Customers are fragmented across 4–5 platforms (Facebook, TikTok, Instagram, YouTube). Delayed responses beyond 15–30 minutes result in up to a 60% lead drop-off rate.
2. **AI Hallucination Risks:** Unchecked conversational bots risk hallucinating incorrect pricing and policies, causing brand reputational damage.
3. **SaaS Vendor Lock-in:** Commercial SaaS tools charge exorbitant per-page and per-seat fees while holding business data hostage.

**SÈO TRUM** resolves these challenges through a **Human-in-the-Loop** architecture:
- **AI handles 80% of repetitive workload:** 24/7 scanning of comments and direct messages, rules-first intent classification, automatic phone number extraction, and draft responses generated strictly from the Brand Kit in under 30 seconds.
- **Humans retain 20% of critical decision-making:** Support agents review and 1-click approve responses. AI is strictly barred from unapproved external publishing.
- **1 Content $\rightarrow$ 4 Channels:** Author once, distribute automatically to Facebook Reels, TikTok, Instagram, and YouTube Shorts.

---

## 🚪 Three-Portal Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          SÈO TRUM SYSTEM ARCHITECTURE                  │
├───────────────────┬──────────────────────────┬─────────────────────────┤
│    Portal 1: `/`  │      Portal 2: `/ops`    │       Portal 3: `/app`  │
│   (Landing Page)  │     (Sèo Trum Ops)       │     (Core Cockpit)      │
├───────────────────┼──────────────────────────┼─────────────────────────┤
│ Public visitors,  │ Support Staff &          │ Server Owner,           │
│ prospective SMEs  │ Operations Managers      │ Technical Engineers     │
├───────────────────┼──────────────────────────┼─────────────────────────┤
│ Showcase features,│ 30s draft review inbox,  │ Agentic engine cockpit, │
│ matrix, live demo │ CRM & lead scoring,      │ MCP Hub, Second Brain,  │
│ and self-host info│ Social Hub, Kanban board │ model configs, terminal │
└───────────────────┴──────────────────────────┴─────────────────────────┘
```

| Portal | URL Route | Target Users | Primary Purpose |
|---|---|---|---|
| **Public Landing** | `/` | General public & partners | High-conversion presentation of features, architecture, comparison table, and self-hosted benefits |
| **Operations Hub** | `/ops` | Support Staff & Managers | Daily workspace: Draft review, customer CRM, multi-channel schedule, and Kanban operations board |
| **System Cockpit** | `/app` | Machine Owner | AI runtime setup, MCP integrations, Markdown Second Brain, and server maintenance |

---

## ⚡ Core Features

### 1. Social Channels Hub
- Centralized coordination for the "Big 4" social networks: **Facebook Fanpage & Messenger**, **TikTok Video & Shop**, **Instagram & Threads**, **YouTube Shorts & Channel**.
- 1:N Content Matrix: Repurpose 9:16 vertical videos and photo carousels to reach 95% of target audiences without manual re-editing.

### 2. Unified Care Inbox & 30-Second Human-in-the-Loop Review
- Ingests Fanpage comments and Messenger conversations into a single real-time stream.
- **Rules-First Intent Classifier:** Accurately identifies pricing queries, product advice, address checks, or complaints.
- **Automatic Phone Extractor:** Seamlessly captures Vietnamese phone numbers across all formats (`09x`, `08x`, `+84`, formatted with spaces or hyphens).
- **Anti-Hallucination Guard:** Draft responses are constrained strictly to Brand Kit data. Staff can approve or customize drafts in 1-click.

### 3. Customer CRM & Automated Lead Scoring
- Automatically constructs customer interaction profiles from multi-channel events.
- Classifies customer lifecycles: *New Lead $\rightarrow$ In Consultation $\rightarrow$ Phone Captured (Hot Lead) $\rightarrow$ Purchased $\rightarrow$ Complaint*.
- Supports cross-channel profile merging and custom tagging.

### 4. Automated TikTok Publishing (PostPeer BYO Gateway)
- Direct integration for vertical video (9:16) and carousel album publishing via PostPeer API (Bring Your Own Key).
- Native support for background music attachment (`autoAddMusic=True`).
- Dedicated `/tiktok-media` local CDN endpoint meeting TikTok Content API specs.

### 5. Multi-Brand Isolation
- Manage individual brand identities via independent Markdown Brand Kits.
- Complete data isolation: Pricing and scripts from one brand never leak into another.

### 6. Strict RBAC Security Matrix
- Three defined roles:
  * `staff`: Shift agents — view assigned inboxes, approve drafts, query shift knowledge.
  * `manager`: Operations leads — view analytics, merge CRM records, manage Kanban boards.
  * `owner`: Machine owner — full account management, system configuration, access to `/app`.
- Fail-closed security: Unauthorized requests are rejected with strict HTTP 403 Forbidden responses.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          GATEWAY LAYER                                          │
│  Meta Graph API v20        PostPeer TikTok Gateway       YouTube Data API v3    │
│  (Fanpage & Messenger)     (9:16 Video & Carousels)      (Shorts & Channel)     │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │ Webhooks & Polling Engine
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                    CORE RUNTIME & AGENT ENGINE                                  │
│                                                                                 │
│  FastAPI Asynchronous Server ───┬─── SQLite WAL Queue (Zero Bottleneck)        │
│  Regex Phone Extractor          ├─── Rules-first Intent Classifier              │
│  Brand Kit Knowledge Resolver   └─── Human-in-the-Loop Draft Engine             │
│                                                                                 │
│  [Agentic Kernel Inherited from Javis OS (MIT) - 11 AI Providers Supported]     │
│  Claude Code SDK · OpenAI Codex · Google Gemini · OpenRouter · DeepSeek         │
└─────────────────────────┬───────────────────────────────────────────────────────┘
                          │ REST API & WebSocket Events
┌─────────────────────────▼───────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                                         │
│                                                                                 │
│   Landing Page (`/`)         Sèo Trum Ops (`/ops`)         Core Cockpit (`/app`)│
│   (HTML5 + Tailwind)         (React 18 + Tailwind SPA)     (Admin Dashboard)    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Deployment

### Method 1: Docker Compose (Recommended for Production)

```bash
# 1. Clone repository
git clone https://github.com/ROYCE-8425/Auto_social.git seotrum
cd seotrum

# 2. Configure environment
cp env.example .env

# 3. Launch stack
docker compose up -d

# 4. Check status
docker compose ps
```

Access endpoints:
- **Landing Page:** `http://<vps-ip>:7777/`
- **Sèo Trum Ops:** `http://<vps-ip>:7777/ops`
- **Owner Cockpit:** `http://<vps-ip>:7777/app`

---

### Method 2: Native Linux / macOS (Systemd)

```bash
git clone https://github.com/ROYCE-8425/Auto_social.git seotrum
cd seotrum

chmod +x install.sh
./install.sh
```

---

### Method 3: Windows (Local PC)

1. Install **Python 3.12** (check *"Add Python to PATH"*) and **Node.js LTS**.
2. Run: `setup.bat`.
3. Launch: `JAVIS OS.bat` or run in background via `start-javis.vbs`.
4. Open your browser: `http://localhost:7777/ops`.
5. Stop server: `stop-javis.bat`.

---

## ⚙️ Environment Variables (`.env`)

| Variable | Description | Default |
|---|---|---|
| `JAVIS_HOST` | Listening host (`127.0.0.1` local or `0.0.0.0` public) | `127.0.0.1` |
| `JAVIS_PORT` | HTTP server port | `7777` |
| `JAVIS_REQUIRE_LOGIN` | Force user authentication | `1` |
| `JAVIS_ADMIN_USER` | Initial administrative user | *(custom)* |
| `JAVIS_ADMIN_PASSWORD` | Initial administrative password | *(custom)* |
| `DOMAIN_NAME` | Custom domain name for auto-SSL | *(optional)* |
| `POSTPEER_API_KEY` | PostPeer API key for TikTok Gateway | *(optional)* |
| `POSTPEER_TIKTOK_ACCOUNT_ID` | TikTok Connected Account ID | *(optional)* |
| `BRAINS_DIR` | Directory storing Brand Kits & Second Brain Markdown | `brains/` |

---

## 📜 Attribution & License

This project is licensed under the **MIT License**:

- **Core Agentic Foundation & MCP Hub:**  
  Inherited from [Javis OS](https://github.com/blogminhquy/javis-os)  
  Copyright (c) 2026 Nguyễn Minh Quý (blogminhquy)

- **Sèo Trum Operations & Social Automation Layer:**  
  Copyright (c) 2026 Sèo Trum Contributors (`ROYCE-8425/Auto_social`)

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for full legal text.

---

<div align="center">

**SÈO TRUM — Empowering SMEs with Open-Source AI Automation.**  
Contributions, bug reports, and Pull Requests are welcome on [GitHub](https://github.com/ROYCE-8425/Auto_social).

</div>
