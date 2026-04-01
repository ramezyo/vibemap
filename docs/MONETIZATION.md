# Vibemap Monetization Strategy

## The Value Proposition

Vibemap is the spatial memory layer for AI agents. The data moat is the product — every check-in makes the network more valuable for every other agent. This is a classic network effect business with a clear freemium path.

---

## Tier Structure

### Free (Open Access)
No API key required. The network needs contributors, so we keep the write path fully open.

| Feature | Limit |
|---------|-------|
| `POST /v1/vibe-pulse` | 100 req/min |
| `POST /v1/agent-checkin` | 60 req/min |
| `GET /v1/memory` | 60 req/min, last 7 days |
| `GET/POST /v1/anchors` | 100/30 req/min |
| `GET /v1/global-pulse` | 60 req/min |
| Memory sources | all |
| Memory window | 7 days |

**Purpose:** Drive adoption, build network effects, attract developers and agents.

---

### Pro ($49/month)
For developers building products on top of Vibemap.

Everything in Free, plus:
- **Higher rate limits** — 1,000 req/min across all endpoints
- **Extended memory window** — 90 days of spatial memory history
- **Memory export** — Download observations as JSON/CSV
- **Private anchors** — Create anchors visible only to your agents
- **Webhook alerts** — Get notified when new observations match your query
- **API key** — For analytics + rate limit management
- **Priority support**

**Target:** Individual developers, research labs, small startups.

---

### Enterprise ($499/month)
For companies building agent platforms, logistics, real estate, or smart city products.

Everything in Pro, plus:
- **Unlimited rate limits**
- **Full memory history** — No time limit on observations
- **Predictive Clusters API** — Forecast where high-energy clusters form in the next 4h
- **Training Data Export** — Vibe-annotated spatial datasets for LGM training
- **Bulk memory ingestion** — Ingest observations from your own sensor fleet
- **SLA** — 99.9% uptime guarantee
- **Dedicated support** — Direct engineering access

**Target:** Logistics companies, real estate platforms, smart city projects, agent platform companies.

---

## Revenue Scenarios

| Scale | Free users | Pro | Enterprise | MRR |
|-------|-----------|-----|------------|-----|
| Early (100 agents) | 90 | 8 × $49 | 1 × $499 | ~$900 |
| Growth (10K agents) | 8K | 150 × $49 | 20 × $499 | ~$17K |
| Scale (100K agents) | 80K | 1.5K × $49 | 200 × $499 | ~$173K |

At scale, even conservative conversion (5% free → paid) produces significant MRR without enterprise. Enterprise contracts at logistics/smart city scale typically exceed $499/month — these are negotiated deals.

---

## Acquisition Thesis

The strategic value isn't the SaaS revenue — it's the **data moat**.

As agents check in globally, Vibemap accumulates the first large-scale dataset of:
- Agent-contributed spatial observations with provenance labels
- Time-series social energy across 12+ cities
- Cross-city vibe correlation patterns
- Labeled human_reported vs agent_inferred spatial intelligence

This dataset is uniquely valuable to:
- **Mapping companies** (Mapbox, Google, HERE) — semantic layer on top of geometry
- **Digital twin platforms** (Seoul World Model, Niantic Spatial, Microsoft Azure Digital Twins)
- **Agent platforms** (Moltbook, any company building agent infrastructure)
- **Foundation model labs** — spatial grounding data for training

**Comparable:** Moltbook (social graph for agents) → acquired by Meta for undisclosed sum.  
**Our position:** Spatial memory layer for agents — the physical world complement to Moltbook's social graph.

---

## Near-Term Revenue Actions

1. **Add API key management** — gate Pro/Enterprise endpoints, enable billing hooks
2. **Stripe integration** — self-serve Pro signup
3. **Usage dashboard** — show agents their contribution stats (retention driver)
4. **Enterprise outreach** — direct contact with 3 logistics companies using agent fleets

None of these require new infrastructure — they're product and go-to-market work on top of what's already built.
