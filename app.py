from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import cloudscraper

app = FastAPI()

# Yeh function ek sundar Dark-UI Dashboard dikhayega
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return """
    <html>
        <head>
            <title>LG Research - Intelligence Graph</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { background: #0e0e0e; color: #00ff00; font-family: 'Courier New'; }
                .container { padding: 20px; }
                #graph { width: 80%; margin: auto; border: 1px solid #333; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛡️ LG Research: Intelligence Graph</h1>
                <input type="text" id="target" placeholder="Enter Domain (e.g. site.com)">
                <button onclick="scan()">Start Research</button>
                <canvas id="myChart"></canvas>
            </div>
            <script>
                // Yahan Graph ka JavaScript code aayega jo API se data lekar 
                // Maltego jaisa relationship dikhayega
            </script>
        </body>
    </html>
    """
