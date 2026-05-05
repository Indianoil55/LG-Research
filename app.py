import cloudscraper
import re
import socket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

def deep_intelligence(url, html):
    # Basic Extraction
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
    links = list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', html)))[:12]
    
    # Domain/IP Extraction
    domain = url.replace('https://','').replace('http://','').split('/')[0]
    try:
        ip_addr = socket.gethostbyname(domain)
    except:
        ip_addr = "Unknown IP"
        
    return {
        "emails": emails,
        "links": links,
        "ip": ip_addr,
        "domain": domain
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    try:
        while True:
            target_url = await websocket.receive_text()
            await websocket.send_json({"status": f"Analyzing {target_url}..."})
            
            try:
                response = scraper.get(target_url, timeout=15)
                intel = deep_intelligence(target_url, response.text)
                
                await websocket.send_json({
                    "status": "Deep Scan Complete", 
                    "target": target_url, 
                    "data": intel
                })
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
        <title>LG Research v2.0</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #000; color: #00ff41; margin: 0; font-family: monospace; overflow: hidden; }
            .header-ui { position: fixed; top: 0; width: 100%; background: #111; padding: 15px; border-bottom: 2px solid #00ff41; z-index: 100; display: flex; gap: 10px; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; flex-grow: 1; }
            button { background: #00ff41; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; }
            #cy { width: 100vw; height: 100vh; display: block; }
            #console { position: fixed; bottom: 0; width: 100%; background: rgba(0,255,65,0.1); font-size: 11px; padding: 5px; border-top: 1px solid #00ff41; color: #00ff41; }
        </style>
    </head>
    <body>
        <div class="header-ui">
            <input type="text" id="urlInput" placeholder="https://target-site.com">
            <button onclick="runScan()">DEEP RESEARCH</button>
        </div>
        <div id="cy"></div>
        <div id="console">> LG Intelligence System Online...</div>

        <script>
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var ws = new WebSocket(protocol + window.location.host + "/ws");
            
            var cy = cytoscape({ 
                container: document.getElementById('cy'), 
                style: [
                    { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#00ff41', 'font-size': '8px', 'width': '10px', 'height': '10px' } },
                    { selector: 'edge', style: { 'line-color': '#222', 'width': 1, 'curve-style': 'haystack' } },
                    { selector: '.target', style: { 'background-color': '#fff', 'width': '15px', 'height': '15px' } }
                ]
            });

            ws.onmessage = function(e) {
                var msg = JSON.parse(e.data);
                document.getElementById('console').innerText = "> " + msg.status;
                
                if(msg.data) {
                    // Add Target Node
                    cy.add({ data: { id: msg.target }, classes: 'target' });
                    
                    // Add IP Node
                    if(msg.data.ip) {
                        cy.add([{data:{id: "IP: "+msg.data.ip}}, {data:{source:msg.target, target:"IP: "+msg.data.ip}}]);
                    }

                    // Add Emails & Links
                    msg.data.emails.forEach(em => { 
                        cy.add([{data:{id: em}}, {data:{source:msg.target, target: em}}]); 
                    });
                    msg.data.links.forEach(li => { 
                        cy.add([{data:{id: li}}, {data:{source:msg.target, target: li}}]); 
                    });

                    cy.layout({ name: 'cose', animate: true, nodeRepulsion: 4000 }).run();
                }
            };

            function runScan() {
                var url = document.getElementById('urlInput').value;
                if(url.startsWith('http')) {
                    cy.elements().remove();
                    ws.send(url);
                }
            }
        </script>
    </body>
    </html>
    """
