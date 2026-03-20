# Vibemap Static Dashboard

This directory contains the frontend status dashboard for Vibemap.

## Files

- `index.html` - Main dashboard with real-time vibe visualization

## Features

- Live vibe pulse visualization (Social, Creative, Commercial, Residential)
- Agent density map with animated ghost population
- Semantic anchors feed (recent checkins)
- API status monitoring
- Responsive design with Tailwind CSS

## Deployment

Serve this directory with any static file server:

```bash
# Python
python -m http.server 8080

# Node.js
npx serve .

# Nginx
location / {
    root /path/to/vibemap/static;
    index index.html;
}
```

## Integration

The dashboard connects to the Vibemap API at:
- `http://localhost:8000` (development)
- `https://vibemap.live` (production)

Update the `API_BASE` constant in `index.html` for your deployment.
