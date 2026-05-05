import cloudscraper
import re
import socket
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="LG Research - Deep OSINT Engine")

# --- BACKEND LOGIC ---

# In files ko tool automatic check karega
TARGET_FILES = [
    ".env", "config.php", "db.php", "database.json", 
    ".git/config", "settings.py", "web.config", ".htaccess", "admin/"
]

def deep_intelligence(url, scraper):
    html = ""
    found_leaks = []
    
    # 1. Main Page Fetch
    try:
        res = scraper.get(url, timeout=10)
        html = res.text
    except:
        pass

    # 2. Sensitive Files Hunter
    base_url = url if url.endswith('/') else url + '/'
    for file in TARGET_FILES:
        try:
            # Check if file exists and has sensitive keywords
            file_res = scraper.get(base_url + file, timeout=5)
            if file_res.status_code == 200:
                content = file_res.text.upper()
                if any(x in content for x in ['DB_', 'PASS', 'KEY', 'USER', 'SECRET']):
                    found_leaks.append(file)
        except:
            continue

    # 3. OSINT Extraction
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
    links = list(set(re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', html)))[:15]
    
    domain = url.replace('https://','').replace('http://','').split('/')[0]
    try:
        ip_addr = socket.gethostbyname(domain)
    except:
        ip_addr = "Unknown"

    return {
        "emails": emails,
        "links": links,
        "ip": ip_addr,
        "leaks": found_leaks,
        "target": url
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
    try:
        while True:
            target_url = await websocket.receive_text()
            if not target_url.startswith('http'):
                await websocket.send_json({"status": "Error: Use https://"})
                continue

            await websocket.send_json({"status": "Hunting for Leaks (.env, DB)..."})
            intel = deep_intelligence(target_url, scraper)
            await websocket.send_json({"status": "Deep Scan Complete", "data": intel})
    except:
        pass

# --- FRONTEND UI ---

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LG Research - Intelligence Graph</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #000; color: #00ff41; margin: 0; font-family: 'Courier New', monospace; overflow: hidden; }
            .header-ui { position: fixed; top: 0; width: 100%; background: #111; padding: 15px; border-bottom: 2px solid #00ff41; z-index: 100; display: flex; gap: 10px; box-sizing: border-box; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; flex-grow: 1; outline: none; }
            button { background: #00ff41; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; }
            #cy { width: 100vw; height: 100vh; display: block; }
            #console { position: fixed; bottom: 0; width: 100%; background: rgba(0,0,0,0.9); font-size: 11px; padding: 8px; border-top: 1px solid #333; color: #00ff41; z-index: 100; }
            /* Leak style for Red Nodes */
            .leak { background-color: #ff0000 !important; color: #ff0000 !important; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header-ui">
            <input type="text" id="urlInput" placeholder="https://target-site.com">
            <button onclick="runScan()">DEEP SCAN</button>
        </div>
        <div id="cy"></div>
        <div id="console">> System Ready...</div>

        <script>
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var ws = new WebSocket(protocol + window.location.host + "/ws");
            
            var cy = cytoscape({ 
                container: document.getElementById('cy'), 
                style: [
                    { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#00ff41', 'font-size': '9px' } },
                    { selector: 'edge', style: { 'line-color': '#222', 'target-arrow-color': '#222', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } },
                    { selector: '.leak', style: { 'background-color': '#ff0000', 'color': '#ff0000', 'font-size': '11px' } }
                ]
            });

            ws.onmessage = function(e) {
                var msg = JSON.parse(e.data);
                if(msg.status) document.getElementById('console').innerText = "> " + msg.status;
                
                if(msg.data) {
                    var target = msg.data.target;
                    cy.add({ data: { id: target } });
                    
                    // IP Node
                    cy.add([{data:{id: "IP: "+msg.data.ip}}, {data:{source: target, target: "IP: "+msg.data.ip}}]);

                    // Emails
                    msg.data.emails.forEach(em => { 
                        cy.add([{data:{id: em}}, {data:{source: target, target: em}}]); 
                    });

                    // Leaks (Red Nodes)
                    msg.data.leaks.forEach(file => { 
                        cy.add([
                            {data:{id: "⚠ LEAK: "+file}, classes: 'leak'}, 
                            {data:{source: target, target: "⚠ LEAK: "+file}}
                        ]); 
                    });

                    cy.layout({ name: 'cose', animate: true }).run();
                }
            };

            function runScan() {
                var url = document.getElementById('urlInput').value;
                if(url.startsWith('http')) {
                    cy.elements().remove();
                    ws.send(url);
                } else {
                    alert("Enter full URL (https://...)");
                }
            }
            
            ws.onopen = () => { document.getElementById('console').innerText = "> Connection Secured."; };
        </script>
    </body>
    </html>
    """
