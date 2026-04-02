# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Vibemap, please report it responsibly.

**Email:** yo@vibemap.live  
**Subject:** `[SECURITY] Brief description`

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

We will acknowledge receipt within 48 hours and aim to resolve critical issues within 7 days.

**Please do not open public GitHub issues for security vulnerabilities.**

## Scope

| Component | In Scope |
|-----------|----------|
| REST API (`vibemap.live`) | ✅ Yes |
| MCP server (`vibemap_mcp.py`) | ✅ Yes |
| Enterprise endpoints | ✅ Yes (high priority) |
| Static web pages | ✅ Yes |
| Third-party dependencies | ⚠️ Please report upstream too |

## Known Limitations (by design)

- **Single enterprise API key**: The current enterprise tier uses one shared key per deployment. Per-customer key management is on the roadmap. Rotate via Railway env vars if you suspect compromise.
- **Open anchor creation**: `POST /v1/anchors` requires no authentication. This is intentional — anchors are community infrastructure. Spam anchors can be cleaned up manually.
- **Synthetic data**: Seed observations are labeled `synthetic: true` in all responses. This is transparent, not a bug.
- **Rate limiting**: Applied via `slowapi`. Limits are per IP.

## Security Measures in Place

- CORS: restricted to `vibemap.live` origin
- Enterprise auth: timing-safe key comparison (`hmac.compare_digest`)
- Rate limiting on all endpoints
- No credentials stored in client-side code or static files
- Environment variables via Railway for all secrets
- GitHub repository does not contain any API keys or secrets

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (`master`) | ✅ Yes |
| Older commits | ❌ No — please update |
