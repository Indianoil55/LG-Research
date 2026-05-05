import cloudscraper
import re
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# Maltego-style Intelligence Logic
def extract_intel(html):
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
    links = list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', html)))[:15]
    return {"emails": emails, "links": links}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    scraper = cloudscraper.create_scraper()
    
    try:
        while True:
            # Frontend se target URL milne ka intezar
            target_url = await websocket.receive_text()
            await websocket.send_json({"status": "Scanning Cloudflare..."})
            
            # Data Fetching[cite: 1]
            response = scraper.get(target_url)
            intel = extract_intel(response.text)
            
            # Live Data wapas bhejna
            await websocket.send_json({
                "status": "Complete",
                "target": target_url,
                "nodes": intel
            })
    except Exception as e:
        await websocket.send_json({"status": "Error", "msg": str(e)})

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>LG Research - Live Graph</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #050505; color: #00ff41; font-family: monospace; }
            #cy { width: 100%; height: 80vh; background: #000; }
            .ui { padding: 10px; background: #111; text-align: center; border-top: 2px solid #00ff41; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; width: 300px; }
            button { background: #00ff41; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="cy"></div>
        <div class="ui">
            <input type="text" id="target" placeholder="Enter URL (https://site.com)">
            <button onclick="startScan()">Start Live Research</button>
            <p id="status">Ready</p>
        </div>

        <script>
            var ws = new WebSocket("ws://" + window.location.host + "/ws");
            var cy = cytoscape({
                container: document.getElementById('cy'),
                style: [
                    { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#fff', 'font-size': '10px' } },
                    { selector: 'edge', style: { 'width': 1, 'line-color': '#00ff41' } }
                ]
            });

            ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                document.getElementById('status').innerText = data.status;
                
                if(data.nodes) {
                    cy.add({ data: { id: data.target } });
                    data.nodes.emails.forEach(e => {
                        cy.add([{ data: { id: e } }, { data: { source: data.target, target: e } }]);
                    });
                    data.nodes.links.forEach(l => {
                        cy.add([{ data: { id: l } }, { data: { source: data.target, target: l } }]);
                    });
                    cy.layout({ name: 'cose' }).run();
                }
            };

            function startScan() {
                var url = document.getElementById('target').value;
                ws.send(url);
            }
        </script>
    </body>
    </html>
    """
