import cloudscraper
import re
import socket
import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- Advanced Intelligence Logic ---
ADMIN_PATHS = ["/admin", "/wp-login.php", "/phpmyadmin", "/login.aspx", "/controlpanel", "/config.php.bak"]
SQL_PATTERNS = [r"id=\d+", r"select+", r"union+", r"insert+"]
COMMON_PORTS = [21, 22, 80, 443, 3306, 5432, 8080]

def advanced_recon(url):
    browsers = ['chrome', 'firefox', 'safari']
    scraper = cloudscraper.create_scraper(
        browser={'browser': random.choice(browsers), 'platform': 'windows', 'desktop': True}
    )
    
    intel = {"leaks": [], "admin": [], "sqli": [], "ports": [], "emails": [], "target": url}
    base = url if url.endswith('/') else url + '/'
    domain = url.split('//')[-1].split('/')[0]

    try:
        # 1. Port Scan (Nmap style)
        for port in COMMON_PORTS:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((domain, port)) == 0:
                    intel["ports"].append(port)

        # 2. Admin Panel & Sensitive File Hunter
        check_list = ADMIN_PATHS + [".env", "config.php", "database.json", ".htaccess", "web.config"]
        for path in check_list:
            try:
                res = scraper.get(base + path.lstrip("/"), timeout=5)
                if res.status_code == 200:
                    if any(x in path for x in ["admin", "login", "panel"]):
                        intel["admin"].append(path)
                    else:
                        intel["leaks"].append(path)
            except: continue

        # 3. SQLi & Email Extraction
        main_res = scraper.get(url, timeout=10)
        html = main_res.text
        for pattern in SQL_PATTERNS:
            found = re.findall(pattern, html, re.IGNORECASE)
            if found: intel["sqli"].append(found[0])
        
        intel["emails"] = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
        
    except: pass
    return intel

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            target = await websocket.receive_text()
            await websocket.send_json({"status": "⚡ LG Engine: Running Nmap & SQLi Scans..."})
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, advanced_recon, target)
            await websocket.send_json({"status": "✅ Recon Complete. Click nodes to open.", "data": data})
    except: pass

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #000; color: #00ff41; margin: 0; font-family: 'Courier New', monospace; overflow: hidden; }
            .ui-bar { position: fixed; top: 0; width: 100%; background: #111; padding: 15px; border-bottom: 2px solid #00ff41; z-index: 100; display: flex; gap: 5px; box-sizing: border-box; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 12px; flex-grow: 1; outline: none; font-family: monospace; }
            button { background: #00ff41; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; color: #000; }
            #cy { width: 100vw; height: 100vh; }
            #console { position: fixed; bottom: 0; width: 100%; background: rgba(0,0,0,0.9); font-size: 11px; padding: 8px; border-top: 1px solid #333; color: #00ff41; }
            .leak { background-color: #f00; }
        </style>
    </head>
    <body>
        <div class="ui-bar">
            <input type="text" id="targetUrl" placeholder="https://target-website.com">
            <button onclick="startScan()">ADVANCED RECON</button>
        </div>
        <div id="cy"></div>
        <div id="console">> LG Research System Ready...</div>

        <script>
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var ws = new WebSocket(protocol + window.location.host + "/ws");
            
            var cy = cytoscape({
                container: document.getElementById('cy'),
                style: [
                    { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#00ff41', 'font-size': '10px', 'text-margin-y': -10 } },
                    { selector: 'edge', style: { 'line-color': '#222', 'width': 1, 'curve-style': 'haystack' } },
                    { selector: '.admin', style: { 'background-color': '#ffcc00', 'color': '#ffcc00' } },
                    { selector: '.sqli', style: { 'background-color': '#ff00ff', 'color': '#ff00ff' } },
                    { selector: '.leak', style: { 'background-color': '#ff0000', 'color': '#ff0000', 'font-weight': 'bold' } },
                    { selector: '.port', style: { 'background-color': '#00ffff', 'color': '#00ffff' } }
                ]
            });

            // Click Logic to open Links
            cy.on('tap', 'node', function(evt){
                var node = evt.target;
                var id = node.id();
                var base = document.getElementById('targetUrl').value;
                if(!base.endsWith('/')) base += '/';

                if(id.includes('LEAK: ') || id.includes('ADMIN: ')) {
                    var path = id.split(': ')[1].replace(/^\//, '');
                    window.open(base + path, '_blank');
                }
            });

            ws.onmessage = function(e) {
                var m = JSON.parse(e.data);
                if(m.status) document.getElementById('console').innerText = "> " + m.status;
                if(m.data) {
                    var t = m.data.target;
                    cy.add({data: {id: t}});
                    m.data.ports.forEach(p => { cy.add([{data:{id:"PORT: "+p}, classes:'port'}, {data:{source:t, target:"PORT: "+p}}]); });
                    m.data.admin.forEach(a => { cy.add([{data:{id:"ADMIN: "+a}, classes:'admin'}, {data:{source:t, target:"ADMIN: "+a}}]); });
                    m.data.leaks.forEach(l => { cy.add([{data:{id:"LEAK: "+l}, classes:'leak'}, {data:{source:t, target:"LEAK: "+l}}]); });
                    m.data.sqli.forEach(s => { cy.add([{data:{id:"SQLi: "+s}, classes:'sqli'}, {data:{source:t, target:"SQLi: "+s}}]); });
                    m.data.emails.forEach(em => { cy.add([{data:{id:em}}, {data:{source:t, target:em}}]); });
                    cy.layout({name: 'cose', animate: true}).run();
                }
            };

            function startScan() {
                var url = document.getElementById('targetUrl').value;
                if(url.startsWith('http')) {
                    cy.elements().remove();
                    ws.send(url);
                } else { alert("Please enter full URL starting with http:// or https://"); }
            }
        </script>
    </body>
    </html>
    """
