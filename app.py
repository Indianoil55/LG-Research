import cloudscraper
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

class Target(BaseModel):
    url: str

@app.post("/lg-fetch")
async def scan_logic(target: Target):
    scraper = cloudscraper.create_scraper()
    try:
        # Cloudflare bypass karke data nikalna
        response = scraper.get(target.url)
        text = response.text
        
        # Intelligence Extraction
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)))
        links = list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)))[:10] # Top 10 links
        
        return {"emails": emails, "links": links, "domain": target.url}
    except Exception as e:
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LG Research - Intelligence Graph</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #0a0a0a; color: #00ff41; font-family: monospace; margin: 0; }
            #cy { width: 100%; height: 500px; display: block; border-bottom: 1px solid #333; }
            .controls { padding: 20px; background: #111; text-align: center; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; width: 250px; }
            button { background: #00ff41; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; }
        </style>
    </head>
    <body>
        <div id="cy"></div>
        <div class="controls">
            <input type="text" id="urlInput" placeholder="Enter Target (e.g. https://site.com)">
            <button onclick="startResearch()">Start Research</button>
        </div>

        <script>
            var cy = cytoscape({
                container: document.getElementById('cy'),
                style: [
                    { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#fff' } },
                    { selector: 'edge', style: { 'width': 2, 'line-color': '#333', 'target-arrow-color': '#333', 'target-arrow-shape': 'triangle' } }
                ]
            });

            async function startResearch() {
                const targetUrl = document.getElementById('urlInput').value;
                if(!targetUrl) return alert("URL daalein!");

                const response = await fetch('/lg-fetch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: targetUrl})
                });
                const data = await response.json();

                // Graph Visualization Logic
                cy.add({ data: { id: 'Target' } });
                data.emails.forEach(email => {
                    cy.add([{ data: { id: email } }, { data: { source: 'Target', target: email } }]);
                });
                data.links.forEach(link => {
                    cy.add([{ data: { id: link } }, { data: { source: 'Target', target: link } }]);
                });
                cy.layout({ name: 'cose' }).run();
            }
        </script>
    </body>
    </html>
    """
