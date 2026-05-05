import cloudscraper
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

def perform_osint(html):
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
    links = list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', html)))[:10]
    return {"emails": emails, "links": links}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    scraper = cloudscraper.create_scraper()
    try:
        while True:
            target_url = await websocket.receive_text()
            response = scraper.get(target_url, timeout=10)
            intel = perform_osint(response.text)
            await websocket.send_json({"status": "Complete", "target": target_url, "data": intel})
    except Exception:
        pass

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LG Research - OSINT</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #000; color: #00ff41; margin: 0; font-family: monospace; }
            /* Search Bar ko top par fix karne ke liye */
            .header-ui { 
                position: fixed; top: 0; width: 100%; background: #111; 
                padding: 15px; border-bottom: 2px solid #00ff41; z-index: 100;
                display: flex; gap: 10px; justify-content: center;
            }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; width: 60%; }
            button { background: #00ff41; border: none; padding: 10px; font-weight: bold; cursor: pointer; }
            #cy { width: 100vw; height: 100vh; display: block; margin-top: 60px; }
            #status { position: fixed; bottom: 10px; left: 10px; font-size: 10px; z-index: 100; }
        </style>
    </head>
    <body>
        <div class="header-ui">
            <input type="text" id="urlInput" placeholder="https://target-site.com">
            <button onclick="runScan()">SCAN</button>
        </div>
        <div id="status">Ready</div>
        <div id="cy"></div>

        <script>
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var ws = new WebSocket(protocol + window.location.host + "/ws");
            var cy = cytoscape({ container: document.getElementById('cy'), style: [
                { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#00ff41' } },
                { selector: 'edge', style: { 'line-color': '#333' } }
            ]});

            ws.onmessage = function(e) {
                var msg = JSON.parse(e.data);
                if(msg.data) {
                    cy.add({ data: { id: msg.target } });
                    msg.data.emails.forEach(em => { cy.add([{data:{id:em}}, {data:{source:msg.target, target:em}}]); });
                    cy.layout({ name: 'cose' }).run();
                }
                document.getElementById('status').innerText = msg.status;
            };

            function runScan() {
                var url = document.getElementById('urlInput').value;
                if(url) { cy.elements().remove(); ws.send(url); }
            }
        </script>
    </body>
    </html>
    """
