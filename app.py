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
    # Professional Browser Fingerprint bypass ke liye
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    try:
        while True:
            target_url = await websocket.receive_text()
            await websocket.send_json({"status": "Connecting to Target..."})
            
            try:
                response = scraper.get(target_url, timeout=15)
                if response.status_code == 200:
                    intel = perform_osint(response.text)
                    await websocket.send_json({"status": "Data Extracted", "target": target_url, "data": intel})
                else:
                    await websocket.send_json({"status": f"Blocked by CF (Code: {response.status_code})"})
            except Exception as e:
                await websocket.send_json({"status": f"Error: {str(e)}"})
    except WebSocketDisconnect:
        pass

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LG Research - Live Intelligence</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #000; color: #00ff41; margin: 0; font-family: 'Courier New', monospace; }
            .header-ui { position: fixed; top: 0; width: 100%; background: #111; padding: 15px; border-bottom: 2px solid #00ff41; z-index: 100; display: flex; gap: 10px; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; flex-grow: 1; outline: none; }
            button { background: #00ff41; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; }
            #cy { width: 100vw; height: 100vh; display: block; }
            #console { position: fixed; bottom: 0; width: 100%; background: rgba(0,0,0,0.8); font-size: 12px; padding: 5px; border-top: 1px solid #333; }
        </style>
    </head>
    <body>
        <div class="header-ui">
            <input type="text" id="urlInput" placeholder="https://target-site.com">
            <button onclick="runScan()">RESEARCH</button>
        </div>
        <div id="cy"></div>
        <div id="console">> System Ready...</div>

        <script>
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var ws = new WebSocket(protocol + window.location.host + "/ws");
            
            var cy = cytoscape({ 
                container: document.getElementById('cy'), 
                style: [
                    { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#00ff41', 'font-size': '10px' } },
                    { selector: 'edge', style: { 'line-color': '#333', 'curve-style': 'bezier' } }
                ]
            });

            ws.onmessage = function(e) {
                var msg = JSON.parse(e.data);
                document.getElementById('console').innerText = "> " + msg.status;
                
                if(msg.data) {
                    cy.add({ data: { id: msg.target } });
                    if(msg.data.emails.length > 0) {
                        msg.data.emails.forEach(em => { 
                            cy.add([{data:{id:em}}, {data:{source:msg.target, target:em}}]); 
                        });
                    }
                    if(msg.data.links.length > 0) {
                        msg.data.links.forEach(li => { 
                            cy.add([{data:{id:li}}, {data:{source:msg.target, target:li}}]); 
                        });
                    }
                    cy.layout({ name: 'cose', animate: true }).run();
                }
            };

            function runScan() {
                var url = document.getElementById('urlInput').value;
                if(url && url.startsWith('http')) {
                    cy.elements().remove();
                    ws.send(url);
                    document.getElementById('console').innerText = "> Request Sent to Engine...";
                } else {
                    alert("Poora URL daalein (e.g., https://site.com)");
                }
            }
        </script>
    </body>
    </html>
    """
