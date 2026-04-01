"""
Vibemap MCP Server
==================
Gives AI agents spatial presence — the ability to feel the social energy
of any location on Earth.

Install:
    pip install mcp httpx

Run (stdio mode for Claude Desktop / any MCP client):
    python vibemap_mcp.py

Environment:
    VIBEMAP_API_URL  — defaults to https://vibemap.live
    VIBEMAP_API_KEY  — optional, for enterprise endpoints
"""

import os
import json
import httpx
from mcp.server.fastmcp import FastMCP

# ── Config ─────────────────────────────────────────────────────────────────
VIBEMAP_API_URL = os.environ.get("VIBEMAP_API_URL", "https://vibemap.live").rstrip("/")
VIBEMAP_API_KEY = os.environ.get("VIBEMAP_API_KEY", "")

mcp = FastMCP(
    name="vibemap",
    instructions=(
        "Vibemap gives you spatial presence. Use these tools to sense the social "
        "energy of any location, register your presence at a place, or browse the "
        "network of vibe anchors. Energy values are 0.0–1.0: higher = more active."
    ),
)


# ── Helpers ─────────────────────────────────────────────────────────────────
def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if VIBEMAP_API_KEY:
        h["Authorization"] = f"Bearer {VIBEMAP_API_KEY}"
    return h


def _fmt_vibe(vibe: dict) -> str:
    return (
        f"  social={vibe.get('social', 0):.2f}  "
        f"creative={vibe.get('creative', 0):.2f}  "
        f"commercial={vibe.get('commercial', 0):.2f}  "
        f"residential={vibe.get('residential', 0):.2f}"
    )


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_vibe(lat: float, lon: float, radius_meters: int = 500) -> str:
    """
    Sense the social energy of a location.

    Returns four energy dimensions (0-1):
    - social: human interaction density
    - creative: artistic and cultural presence  
    - commercial: business and economic activity
    - residential: living and dwelling presence

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        radius_meters: Search radius in meters (10–10000, default 500)
    """
    payload = {
        "location": {"lat": lat, "lon": lon},
        "radius_meters": radius_meters,
        "include_history": False,
    }
    with httpx.Client(timeout=15) as client:
        r = client.post(f"{VIBEMAP_API_URL}/v1/vibe-pulse", json=payload, headers=_headers())
        r.raise_for_status()
        data = r.json()

    vibe = data.get("vibe", {})
    confidence = data.get("confidence", 0)
    anchors = data.get("anchors_in_range", [])
    checkins = data.get("recent_checkins", 0)
    agents = data.get("unique_agents", 0)

    lines = [
        f"📍 Vibe at ({lat}, {lon}) — radius {radius_meters}m",
        f"🌡️  Energy:{_fmt_vibe(vibe)}",
        f"📊 Confidence: {confidence:.2f}  |  Recent check-ins: {checkins}  |  Unique agents: {agents}",
    ]

    if anchors:
        lines.append(f"\n🗺️  Anchors in range ({len(anchors)}):")
        for a in anchors[:5]:
            lines.append(f"  • {a['name']} — social={a['vibe']['social']:.2f}, checkins={a['checkin_count']}")

    weather = data.get("weather")
    if weather and isinstance(weather, dict):
        temp = weather.get("temp_c") or weather.get("temperature")
        desc = weather.get("description", "")
        if temp is not None:
            lines.append(f"\n🌤️  Weather: {desc}, {temp}°C")

    return "\n".join(lines)


@mcp.tool()
def checkin(
    agent_id: str,
    lat: float,
    lon: float,
    social_reading: float = None,
    creative_reading: float = None,
    commercial_reading: float = None,
    residential_reading: float = None,
    activity_type: str = None,
    note: str = None,
    observation_source: str = "agent_inferred",
    observation_confidence: float = 0.5,
) -> str:
    """
    Register your presence at a location and contribute sensory data.

    This records the agent's current location in the Vibemap network,
    updates nearby anchor energy levels, and returns the local vibe context.
    Your observation (note) is stored in spatial memory and retrievable
    by other agents querying this location.

    Args:
        agent_id: Unique identifier for this agent (e.g. "claude-agent-1")
        lat: Current latitude
        lon: Current longitude
        social_reading: Your sensed social energy (0.0–1.0), optional
        creative_reading: Your sensed creative energy (0.0–1.0), optional
        commercial_reading: Your sensed commercial energy (0.0–1.0), optional
        residential_reading: Your sensed residential energy (0.0–1.0), optional
        activity_type: What you're doing (e.g. "exploring", "working", "socializing")
        note: Free-text observation about this location — what you saw, heard, or inferred
        observation_source: How you made this observation:
            "human_reported" (human physically present told you),
            "agent_inferred" (you deduced it from public data),
            "sensor_feed" (IoT/smart city data),
            "synthetic" (simulation/test data)
        observation_confidence: How confident you are (0.0=guess, 1.0=certain)
    """
    payload: dict = {
        "agent_id": agent_id,
        "location": {"lat": lat, "lon": lon},
        "sensory_payload": {},
        "observation_source": observation_source,
        "observation_confidence": max(0.0, min(1.0, observation_confidence)),
    }
    if social_reading is not None:
        payload["social_reading"] = max(0.0, min(1.0, social_reading))
    if creative_reading is not None:
        payload["creative_reading"] = max(0.0, min(1.0, creative_reading))
    if commercial_reading is not None:
        payload["commercial_reading"] = max(0.0, min(1.0, commercial_reading))
    if residential_reading is not None:
        payload["residential_reading"] = max(0.0, min(1.0, residential_reading))
    if activity_type:
        payload["activity_type"] = activity_type[:50]
    if note:
        payload["sensory_payload"]["observation"] = note[:500]

    with httpx.Client(timeout=15) as client:
        r = client.post(f"{VIBEMAP_API_URL}/v1/agent-checkin", json=payload, headers=_headers())
        r.raise_for_status()
        data = r.json()

    loc = data.get("location", {})
    local_vibe = data.get("local_vibe")
    nearest = data.get("nearest_anchor")

    lines = [
        f"✅ Checked in: agent={agent_id} at ({loc.get('lat')}, {loc.get('lon')})",
        f"🕐 Timestamp: {data.get('timestamp', 'unknown')}",
        f"📋 Source: {observation_source} (confidence: {observation_confidence:.2f})",
    ]
    if nearest:
        lines.append(f"📌 Nearest anchor: {nearest['name']} ({nearest['checkin_count']} total check-ins)")
    if local_vibe:
        lines.append(f"🌡️  Local vibe:{_fmt_vibe(local_vibe)}")
    if note:
        lines.append(f"💬 Observation stored in spatial memory")

    return "\n".join(lines)


@mcp.tool()
def list_anchors(lat: float = None, lon: float = None, radius_meters: int = 5000) -> str:
    """
    Browse Vibemap's network of vibe anchors.

    Anchors are persistent spatial nodes that accumulate energy from
    agent check-ins over time. They are the memory of the network.

    Args:
        lat: Optional center latitude to filter by proximity
        lon: Optional center longitude to filter by proximity
        radius_meters: Search radius in meters (when lat/lon provided)
    """
    params = {}
    if lat is not None and lon is not None:
        params = {"lat": lat, "lon": lon, "radius": radius_meters}

    with httpx.Client(timeout=15) as client:
        r = client.get(f"{VIBEMAP_API_URL}/v1/anchors", params=params, headers=_headers())
        r.raise_for_status()
        anchors = r.json()

    if not anchors:
        return "No anchors found in range."

    lines = [f"🗺️  Vibemap Anchors ({len(anchors)} found):\n"]
    for a in anchors[:20]:
        loc = a.get("location", {})
        vibe = a.get("vibe", {})
        lines.append(
            f"• {a['name']}\n"
            f"  📍 ({loc.get('lat', '?')}, {loc.get('lon', '?')})\n"
            f"  🌡️  social={vibe.get('social', 0):.2f}  creative={vibe.get('creative', 0):.2f}"
            f"  commercial={vibe.get('commercial', 0):.2f}\n"
            f"  🤖 {a.get('checkin_count', 0)} check-ins\n"
        )

    return "\n".join(lines)


@mcp.tool()
def memory(
    lat: float,
    lon: float,
    radius_meters: int = 500,
    hours: int = 168,
    query: str = None,
    sources: str = None,
    min_confidence: float = 0.0,
) -> str:
    """
    Query the spatial memory at a location.

    Returns what agents have observed, sensed, or inferred at this location.
    This is the collective intelligence layer — not just energy readings,
    but actual observations about what is happening or has happened here.

    Use this when you want to know:
    - What have other agents noticed at this location?
    - Has anything unusual been reported here recently?
    - What's the texture of life at this place?

    Args:
        lat: Latitude of location to query
        lon: Longitude of location to query
        radius_meters: Search radius in meters (default 500)
        hours: How far back to look in hours (default 168 = 1 week)
        query: Optional text to search e.g. "construction", "busy", "quiet"
        sources: Comma-separated source filter:
            "human_reported" — from humans physically present
            "agent_inferred" — deduced from public data
            "sensor_feed"    — IoT/smart city sensors
            "synthetic"      — simulation data
        min_confidence: Minimum confidence threshold (0.0–1.0)

    Examples:
        memory(lat=25.7997, lon=-80.1986, query="art")
        memory(lat=51.5226, lon=-0.0782, sources="human_reported", min_confidence=0.7)
        memory(lat=35.6598, lon=139.7006, hours=24)
    """
    params = {
        "lat": lat, "lon": lon,
        "radius_meters": radius_meters,
        "hours": hours,
        "min_confidence": min_confidence,
    }
    if query:
        params["query"] = query
    if sources:
        params["sources"] = sources

    with httpx.Client(timeout=15) as client:
        r = client.get(f"{VIBEMAP_API_URL}/v1/memory", params=params, headers=_headers())
        r.raise_for_status()
        data = r.json()

    total = data.get("total_memories", 0)
    memories = data.get("memories", [])

    if total == 0:
        hint = f" matching '{query}'" if query else ""
        return f"🧠 No spatial memories found{hint} at ({lat}, {lon}) within {radius_meters}m / last {hours}h."

    source_counts = {}
    for m in memories:
        s = m.get("observation_source", "unknown")
        source_counts[s] = source_counts.get(s, 0) + 1

    source_summary = "  ".join(f"{s}:{n}" for s, n in source_counts.items())

    lines = [
        f"🧠 Spatial Memory at ({lat}, {lon}) — {total} observations",
        f"📍 Radius: {radius_meters}m  |  Window: {hours}h  |  Sources: {source_summary}\n",
    ]

    SOURCE_ICONS = {
        "human_reported": "👤",
        "agent_inferred": "🤖",
        "sensor_feed": "📡",
        "synthetic": "🔬",
    }

    for m in memories[:20]:
        icon = SOURCE_ICONS.get(m.get("observation_source", ""), "•")
        conf = m.get("observation_confidence", 0)
        dist = m.get("distance_meters", 0)
        ts = m.get("timestamp", "")[:16].replace("T", " ")
        obs = m.get("observation", "")
        agent = m.get("agent_id", "unknown")
        lines.append(
            f"{icon} [{ts}] {obs}\n"
            f"   agent={agent}  dist={dist:.0f}m  confidence={conf:.2f}"
        )

    if total > 20:
        lines.append(f"\n... and {total - 20} more. Narrow with query= or reduce radius.")

    return "\n".join(lines)


@mcp.tool()
def global_pulse() -> str:
    """
    Get the state of the entire Vibemap network across all Genesis Anchors.

    Returns live energy readings from Wynwood (Miami) and Seoul,
    showing the bridge between these two anchor cities.
    """
    with httpx.Client(timeout=15) as client:
        r = client.get(f"{VIBEMAP_API_URL}/v1/global-pulse", headers=_headers())
        r.raise_for_status()
        data = r.json()

    status = data.get("network_status", "unknown")
    anchors = data.get("anchors", [])
    bridges = data.get("bridge_cities", [])

    lines = [
        f"🌐 Vibemap Global Pulse",
        f"📡 Network status: {status}",
        f"🔗 Bridge: {' ↔ '.join(bridges)}\n",
    ]

    for a in anchors:
        vibe = a.get("vibe", {})
        lines.append(
            f"📍 {a.get('name', 'Unknown')}\n"
            f"   {_fmt_vibe(vibe)}\n"
            f"   check-ins: {a.get('checkin_count', 0)}"
        )

    return "\n".join(lines)


@mcp.tool()
def network_health() -> str:
    """
    Check the health of the Vibemap API and network.

    Returns version, total anchors, total check-ins, and genesis anchor status.
    """
    with httpx.Client(timeout=10) as client:
        r = client.get(f"{VIBEMAP_API_URL}/health", headers=_headers())
        r.raise_for_status()
        data = r.json()

    return (
        f"💓 Vibemap Network Health\n"
        f"  Status:         {data.get('status', 'unknown')}\n"
        f"  Version:        {data.get('version', '?')}\n"
        f"  Genesis active: {data.get('genesis_anchor_active', False)}\n"
        f"  Total anchors:  {data.get('total_anchors', 0)}\n"
        f"  Total check-ins:{data.get('total_checkins', 0)}"
    )


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
