import cloudscraper
import re
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="LG Research - Professional OSINT")

# Intelligence extraction logic
def perform_osint(html_content):
    # Emails nikalna
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_content)))
    # Links nikalna (Top 15)
    links = list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', html_content)))[:15]
    return {"emails": emails, "links": links}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    
    try:
        while True:
            # User se URL lena
            target_url = await websocket.receive_text()
            if not target_url.startswith("http"):
                await websocket.send_json({"status": "Error: URL must start with http:// or https://"})
                continue

            await websocket.send_json({"status": "Bypassing Cloudflare..."})
            
            # Data fetch karna
            try:
                response = scraper.get(target_url, timeout=15)
                intel = perform_osint(response.text)
                
                # Real-time data frontend ko bhejna
                await websocket.send_json({
                    "status": "Scan Complete",
                    "target": target_url,
                    "data": intel
                })
            except Exception as e:
                await websocket.send_json({"status": f"Fetch Error: {str(e)}"})
                
    except WebSocketDisconnect:
        print("Client disconnected")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LG Research - Intelligence Graph</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #050505; color: #00ff41; font-family: 'Courier New', monospace; margin: 0; overflow: hidden; }
            #cy { width: 100vw; height: 85vh; background: radial-gradient(circle, #111 0%, #000 100%); }
            .terminal-ui { height: 15vh; background: #000; border-top: 2px solid #00ff41; padding: 10px; display: flex; align-items: center; justify-content: center; gap: 10px; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 12px; width: 40%; outline: none; font-size: 16px; }
            button { background: #00ff41; color: #000; border: none; padding: 12px 25px; font-weight: bold; cursor: pointer; transition: 0.3s; }
            button:hover { background: #fff; }
            #status { position: absolute; top: 10px; left: 10px; font-size: 12px; color: #00ff41; z-index: 10; }
        </style>
    </head>
    <body>
        <div id="status">System Ready: Waiting for Target...</div>
        <div id="cy"></div>
        <div class="terminal-ui">
            <input type="text" id="urlInput" placeholder="Enter Target (e.g., https://example.com)">
            <button onclick="runResearch()">RESEARCH</button>
        </div>

        <script>
            // SSL/Secure Socket Fix[cite: 2]
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var ws = new WebSocket(protocol + window.location.host + "/ws");

            var cy = cytoscape({
                container: document.getElementById('cy'),
                style: [
                    { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#00ff41', 'font-size': '10px', 'text-margin-y': '-10px' } },
                    { selector: 'edge', style: { 'width': 1, 'line-color': '#333', 'curve-style': 'bezier' } }
                ]
            });

            ws.onmessage = function(event) {
                var msg = JSON.parse(event.data);
                document.getElementById('status').innerText = "LOG: " + msg.status;
                
                if(msg.data) {
                    // Central Node[cite: 2]
                    cy.add({ data: { id: msg.target } });
                    
                    // Add Email Nodes
                    msg.data.emails.forEach(email => {
                        cy.add([{ data: { id: email } }, { data: { source: msg.target, target: email } }]);
                    });
                    
                    // Add Link Nodes
                    msg.data.links.forEach(link => {
                        cy.add([{ data: { id: link } }, { data: { source: msg.target, target: link } }]);
                    });
                    
                    cy.layout({ name: 'cose', animate: true }).run();
                }
            };

            function runResearch() {
                var url = document.getElementById('urlInput').value;
                if(url) {
                    cy.elements().remove(); // Clear old graph
                    ws.send(url);
                } else {
                    alert("Please enter a valid URL!");
                }
            }
            
            ws.onopen = () => { document.getElementById('status').innerText = "System Online: Connection Secure"; };
            ws.onclose = () => { document.getElementById('status').innerText = "System Offline: Reconnecting..."; };
        </script>
    </body>
    </html>
    """
