import cloudscraper
import re
import socket
import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- Advanced Intelligence Lists ---
ADMIN_PATHS = ["/admin", "/wp-login.php", "/phpmyadmin", "/login.aspx", "/controlpanel"]
SQL_PATTERNS = [r"id=\d+", r"select+", r"union+", r"insert+", r"config.php"]
COMMON_PORTS = [21, 22, 80, 443, 3306, 5432, 8080]

def advanced_recon(url):
    browsers = ['chrome', 'firefox']
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
        for path in ADMIN_PATHS + [".env", "config.php", "database.json"]:
            res = scraper.get(base + path.strip("/"), timeout=5)
            if res.status_code == 200:
                if "admin" in path or "login" in path:
                    intel["admin"].append(path)
                else:
                    intel["leaks"].append(path)

        # 3. SQLi Endpoint Search
        main_res = scraper.get(url, timeout=10)
        html = main_res.text
        for pattern in SQL_PATTERNS:
            found = re.findall(pattern, html, re.IGNORECASE)
            if found:
                intel["sqli"].append(found[0])

        # 4. Email Scraper
        intel["emails"] = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
        
    except: pass
    return intel

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            target = await websocket.receive_text()
            await websocket.send_json({"status": "Initializing Nmap & SQLi Scanners..."})
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, advanced_recon, target)
            
            await websocket.send_json({"status": "Deep Recon Complete", "data": data})
    except: pass

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
        <style>
            body { background: #000; color: #00ff41; margin: 0; font-family: monospace; overflow: hidden; }
            .header { position: fixed; top: 0; width: 100%; background: #111; padding: 15px; border-bottom: 2px solid #00ff41; z-index: 100; display: flex; gap: 5px; }
            input { background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; flex-grow: 1; outline: none; }
            button { background: #00ff41; border: none; padding: 10px 15px; font-weight: bold; cursor: pointer; }
            #cy { width: 100vw; height: 100vh; }
            #log { position: fixed; bottom: 0; width: 100%; background: rgba(0,0,0,0.9); font-size: 10px; padding: 5px; border-top: 1px solid #333; }
            /* Maltego Node Colors */
            .admin { background-color: #ffcc00 !important; } /* Yellow for Admin */
            .sqli { background-color: #ff00ff !important; }  /* Pink for SQLi */
            .leak { background-color: #ff0000 !important; }  /* Red for Leaks */
            .port { background-color: #00ffff !important; }  /* Cyan for Ports */
        </style>
    </head>
    <body>
        <div class="header">
            <input type="text" id="inp" placeholder="https://target.com">
            <button onclick="scan()">ADVANCED RECON</button>
        </div>
        <div id="cy"></div>
        <div id="log">> OSINT Engine Ready...</div>
        <script>
            var protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            var ws = new WebSocket(protocol + window.location.host + "/ws");
            var cy = cytoscape({ container: document.getElementById('cy'), style: [
                { selector: 'node', style: { 'label': 'data(id)', 'background-color': '#00ff41', 'color': '#00ff41', 'font-size': '8px' } },
                { selector: 'edge', style: { 'line-color': '#222', 'width': 1 } },
                { selector: '.admin', style: { 'background-color': '#fc0', 'color': '#fc0' } },
                { selector: '.sqli', style: { 'background-color': '#f0f', 'color': '#f0f' } },
                { selector: '.leak', style: { 'background-color': '#f00', 'color': '#f00' } },
                { selector: '.port', style: { 'background-color': '#0ff', 'color': '#0ff' } }
            ]});

            ws.onmessage = function(e) {
                var m = JSON.parse(e.data);
                if(m.status) document.getElementById('log').innerText = "> " + m.status;
                if(m.data) {
                    var t = m.data.target;
                    cy.add({data: {id: t}});
                    
                    // Display Intelligence Nodes
                    m.data.ports.forEach(p => { cy.add([{data:{id:"PORT: "+p}, classes:'port'}, {data:{source:t, target:"PORT: "+p}}]); });
                    m.data.admin.forEach(a => { cy.add([{data:{id:"ADMIN: "+a}, classes:'admin'}, {data:{source:t, target:"ADMIN: "+a}}]); });
                    m.data.leaks.forEach(l => { cy.add([{data:{id:"LEAK: "+l}, classes:'leak'}, {data:{source:t, target:"LEAK: "+l}}]); });
                    m.data.sqli.forEach(s => { cy.add([{data:{id:"SQLi: "+s}, classes:'sqli'}, {data:{source:t, target:"SQLi: "+s}}]); });
                    m.data.emails.forEach(em => { cy.add([{data:{id:em}}, {data:{source:t, target:em}}]); });
                    
                    cy.layout({name: 'cose', animate: true}).run();
                }
            };
            function scan() { var v = document.getElementById('inp').value; if(v.startsWith('http')) { cy.elements().remove(); ws.send(v); } }
        </script>
    </body>
    </html>
    """
