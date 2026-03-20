"""
Interactive Map Component
Real-time vibe visualization with Leaflet.js (free, open-source)
Alternative to Mapbox - no API key required for basic usage
"""

import os

MAP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vibemap Live - Interactive Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossorigin=""/>
    
    <!-- Tailwind -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <style>
        body { margin: 0; padding: 0; background: #000; color: #fff; font-family: 'Inter', sans-serif; }
        #map { height: 100vh; width: 100%; background: #0a0a0f; }
        
        /* Custom popup styles */
        .vibe-popup .leaflet-popup-content-wrapper {
            background: rgba(10, 10, 15, 0.95);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            color: #fff;
        }
        .vibe-popup .leaflet-popup-tip {
            background: rgba(10, 10, 15, 0.95);
            border: 1px solid rgba(99, 102, 241, 0.3);
        }
        
        /* Pulse animation for anchors */
        @keyframes pulse {
            0% { transform: scale(0.5); opacity: 1; }
            100% { transform: scale(2); opacity: 0; }
        }
        
        .pulse-ring {
            animation: pulse 2s ease-out infinite;
        }
        
        /* Vibe heat gradient */
        .vibe-heat-high { background: radial-gradient(circle, rgba(236,72,153,0.6) 0%, transparent 70%); }
        .vibe-heat-medium { background: radial-gradient(circle, rgba(99,102,241,0.5) 0%, transparent 70%); }
        .vibe-heat-low { background: radial-gradient(circle, rgba(34,211,238,0.4) 0%, transparent 70%); }
    </style>
</head>
<body>
    <!-- Header Overlay -->
    <div class="fixed top-4 left-4 z-[1000] glass rounded-2xl p-4 max-w-sm">
        <div class="flex items-center space-x-3 mb-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-cyan-500 to-pink-500 flex items-center justify-center">
                <span class="font-bold text-white text-lg">V</span>
            </div>
            <div>
                <h1 class="font-bold text-lg">Vibemap Live</h1>
                <p class="text-xs text-slate-400">Real-time vibe visualization</p>
            </div>
        </div>
        
        <div class="space-y-2 text-sm">
            <div class="flex items-center justify-between">
                <span class="text-slate-400">Active Anchors</span>
                <span class="text-cyan-400 font-mono" id="anchor-count">2</span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-slate-400">Ghost Agents</span>
                <span class="text-pink-400 font-mono" id="agent-count">100</span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-slate-400">Last Update</span>
                <span class="text-slate-500 font-mono text-xs" id="last-update">Just now</span>
            </div>
        </div>
        
        <div class="mt-4 pt-4 border-t border-white/10">
            <div class="flex items-center space-x-2">
                <span class="w-3 h-3 rounded-full bg-pink-500 animate-pulse"></span>
                <span class="text-xs text-pink-400">Live Data Stream</span>
            </div>
        </div>
    </div>
    
    <!-- Legend -->
    <div class="fixed bottom-4 right-4 z-[1000] glass rounded-2xl p-4">
        <h3 class="text-sm font-semibold mb-3">Vibe Energy</h3>
        <div class="space-y-2 text-xs">
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 rounded-full bg-pink-500"></div>
                <span class="text-slate-400">High (0.8-1.0)</span>
            </div>
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 rounded-full bg-indigo-500"></div>
                <span class="text-slate-400">Medium (0.5-0.8)</span>
            </div>
            <div class="flex items-center space-x-2">
                <div class="w-4 h-4 rounded-full bg-cyan-500"></div>
                <span class="text-slate-400">Low (0.0-0.5)</span>
            </div>
        </div>
    </div>
    
    <!-- Map Container -->
    <div id="map"></div>
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
            crossorigin=""></script>
    
    <script>
        // Initialize map centered between Wynwood and Seoul
        const map = L.map('map', {
            center: [31.5, -10],
            zoom: 2,
            minZoom: 2,
            maxZoom: 18,
            zoomControl: false
        });
        
        // Add zoom control to top-right
        L.control.zoom({
            position: 'topright'
        }).addTo(map);
        
        // Dark theme map tiles (CartoDB Dark Matter - free)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);
        
        // Genesis Anchors data
        const anchors = [
            {
                name: "Genesis Anchor - Wynwood",
                lat: 25.7997,
                lon: -80.1986,
                city: "Miami",
                country: "USA",
                vibe: { social: 0.75, creative: 0.90, commercial: 0.65, residential: 0.40 },
                agents: 50,
                color: "#ec4899"
            },
            {
                name: "Anchor #2 - Seoul",
                lat: 37.5665,
                lon: 126.9780,
                city: "Seoul",
                country: "South Korea",
                vibe: { social: 0.85, creative: 0.75, commercial: 0.95, residential: 0.60 },
                agents: 50,
                color: "#22d3ee"
            }
        ];
        
        // Custom anchor icon
        function createAnchorIcon(color) {
            return L.divIcon({
                className: 'custom-anchor',
                html: `<div style="
                    width: 24px;
                    height: 24px;
                    background: ${color};
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 0 20px ${color}, 0 0 40px ${color}80;
                    animation: pulse 2s ease-out infinite;
                "></div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });
        }
        
        // Add anchors to map
        anchors.forEach(anchor => {
            const marker = L.marker([anchor.lat, anchor.lon], {
                icon: createAnchorIcon(anchor.color)
            }).addTo(map);
            
            // Calculate average vibe
            const avgVibe = ((anchor.vibe.social + anchor.vibe.creative + 
                            anchor.vibe.commercial + anchor.vibe.residential) / 4).toFixed(2);
            
            // Popup content
            const popupContent = `
                <div class="p-2 min-w-[200px]">
                    <h3 class="font-bold text-lg mb-2" style="color: ${anchor.color}">${anchor.name}</h3>
                    <p class="text-xs text-slate-400 mb-3">${anchor.city}, ${anchor.country}</p>
                    
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-slate-400">Social</span>
                            <span class="text-pink-400">${anchor.vibe.social.toFixed(2)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-400">Creative</span>
                            <span class="text-purple-400">${anchor.vibe.creative.toFixed(2)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-400">Commercial</span>
                            <span class="text-cyan-400">${anchor.vibe.commercial.toFixed(2)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-400">Residential</span>
                            <span class="text-indigo-400">${anchor.vibe.residential.toFixed(2)}</span>
                        </div>
                    </div>
                    
                    <div class="mt-3 pt-3 border-t border-white/10">
                        <div class="flex justify-between text-sm">
                            <span class="text-slate-400">Avg Vibe</span>
                            <span class="font-bold" style="color: ${anchor.color}">${avgVibe}</span>
                        </div>
                        <div class="flex justify-between text-sm mt-1">
                            <span class="text-slate-400">Active Agents</span>
                            <span class="text-white">${anchor.agents}</span>
                        </div>
                    </div>
                </div>
            `;
            
            marker.bindPopup(popupContent, {
                className: 'vibe-popup',
                closeButton: false
            });
            
            // Add vibe heat circle
            const radius = 2000; // meters
            const fillOpacity = avgVibe * 0.3;
            
            L.circle([anchor.lat, anchor.lon], {
                radius: radius,
                fillColor: anchor.color,
                fillOpacity: fillOpacity,
                stroke: false
            }).addTo(map);
        });
        
        // Draw connection line between anchors
        const connectionLine = L.polyline(
            [[25.7997, -80.1986], [37.5665, 126.9780]],
            {
                color: '#6366f1',
                weight: 2,
                opacity: 0.5,
                dashArray: '10, 10'
            }
        ).addTo(map);
        
        // Add animated pulse along the connection
        let offset = 0;
        setInterval(() => {
            offset = (offset + 1) % 20;
            connectionLine.setStyle({ dashOffset: -offset });
        }, 100);
        
        // Simulate agent dots (random movement)
        const agentMarkers = [];
        
        function createAgentDot(lat, lon, color) {
            return L.circleMarker([lat, lon], {
                radius: 3,
                fillColor: color,
                fillOpacity: 0.8,
                stroke: false
            }).addTo(map);
        }
        
        // Spawn some random agents around each anchor
        anchors.forEach(anchor => {
            for (let i = 0; i < 10; i++) {
                const offsetLat = (Math.random() - 0.5) * 0.01;
                const offsetLon = (Math.random() - 0.5) * 0.01;
                const agent = createAgentDot(
                    anchor.lat + offsetLat,
                    anchor.lon + offsetLon,
                    anchor.color
                );
                agentMarkers.push({
                    marker: agent,
                    baseLat: anchor.lat,
                    baseLon: anchor.lon,
                    color: anchor.color
                });
            }
        });
        
        // Animate agents
        setInterval(() => {
            agentMarkers.forEach(agent => {
                const offsetLat = (Math.random() - 0.5) * 0.005;
                const offsetLon = (Math.random() - 0.5) * 0.005;
                agent.marker.setLatLng([
                    agent.baseLat + offsetLat,
                    agent.baseLon + offsetLon
                ]);
            });
        }, 2000);
        
        // Update timestamp
        setInterval(() => {
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }, 1000);
        
        // Fetch real vibe data periodically
        async function fetchVibeData() {
            try {
                // Fetch Wynwood vibe
                const wynwoodResponse = await fetch('/v1/vibe-pulse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        location: { lat: 25.7997, lon: -80.1986 },
                        radius_meters: 1000
                    })
                });
                
                if (wynwoodResponse.ok) {
                    const data = await wynwoodResponse.json();
                    console.log('Wynwood vibe:', data.vibe);
                }
                
                // Fetch Seoul vibe
                const seoulResponse = await fetch('/v1/vibe-pulse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        location: { lat: 37.5665, lon: 126.9780 },
                        radius_meters: 1000
                    })
                });
                
                if (seoulResponse.ok) {
                    const data = await seoulResponse.json();
                    console.log('Seoul vibe:', data.vibe);
                }
            } catch (e) {
                console.log('Using demo data');
            }
        }
        
        // Fetch data every 30 seconds
        fetchVibeData();
        setInterval(fetchVibeData, 30000);
    </script>
</body>
</html>
"""


def get_map_html() -> str:
    """Get the interactive map HTML."""
    return MAP_HTML_TEMPLATE


# Save map to file for serving
if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "..", "static", "map.html")
    with open(output_path, "w") as f:
        f.write(MAP_HTML_TEMPLATE)
    print(f"Map saved to {output_path}")