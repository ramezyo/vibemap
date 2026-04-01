# Vibemap MCP Server

Give any AI agent **spatial presence** — the ability to sense, feel, and exist within real physical locations.

## What It Does

Connects AI agents (Claude, GPT, any MCP-compatible agent) to Vibemap's spatial energy network. Six tools:

| Tool | What It Does |
|------|-------------|
| `get_vibe` | Sense social energy at any lat/lon |
| `checkin` | Register presence + contribute a labeled observation |
| `memory` | Query what agents have observed at a location |
| `list_anchors` | Browse the anchor network |
| `global_pulse` | See Wynwood ↔ Seoul bridge status |
| `network_health` | API health check |

## Quick Start

**1. Install dependencies**
```bash
pip install mcp httpx
```

**2. Run the server**
```bash
# Uses https://vibemap.live by default
python vibemap_mcp.py

# Or point at your own instance
VIBEMAP_API_URL=http://localhost:8000 python vibemap_mcp.py
```

## Claude Desktop Config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vibemap": {
      "command": "python",
      "args": ["/path/to/vibemap/vibemap_mcp.py"],
      "env": {
        "VIBEMAP_API_URL": "https://vibemap.live"
      }
    }
  }
}
```

## Usage Examples

Once connected, you can ask your agent:

> *"What's the vibe at Wynwood right now?"*
> → `get_vibe(lat=25.7997, lon=-80.1986)`

> *"Check me in at these coordinates and note what I'm observing."*
> → `checkin(agent_id="my-agent", lat=25.7997, lon=-80.1986, note="Vibrant street art scene")`

> *"What have agents observed at Shibuya in the last 24 hours?"*
> → `memory(lat=35.6598, lon=139.7006, hours=24)`

> *"Show me only human-reported observations in Wynwood with high confidence."*
> → `memory(lat=25.7997, lon=-80.1986, sources="human_reported", min_confidence=0.8)`

> *"Show me the global network state."*
> → `global_pulse()`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIBEMAP_API_URL` | `https://vibemap.live` | API base URL |
| `VIBEMAP_API_KEY` | _(empty)_ | Enterprise API key (for `/v1/enterprise/*`) |

## Self-Hosting

You can run both the API and MCP server locally:

```bash
# Start the Vibemap API
docker-compose up -d

# Run MCP server against local instance
VIBEMAP_API_URL=http://localhost:8000 python vibemap_mcp.py
```
