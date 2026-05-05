import cloudscraper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re # Maltego jaisa data nikalne ke liye

app = FastAPI(title="LG Research - OSINT Engine")

class ScrapeRequest(BaseModel):
    url: str

@app.post("/lg-fetch")
def fetch_and_analyze(request: ScrapeRequest):
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(request.url)
        html_content = response.text
        
        # --- Maltego Jaisa Intelligence Logic ---
        
        # 1. Emails dhundna (Regex se)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_content)
        
        # 2. Phone numbers dhundna
        phones = re.findall(r'\+?\d{10,12}', html_content)
        
        # 3. External Links dhundna (Social Media etc.)
        links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', html_content)
        social_links = [l for l in links if "facebook" in l or "twitter" in l or "t.me" in l]

        return {
            "tool": "LG Research OSINT",
            "target": request.url,
            "intelligence_report": {
                "emails_found": list(set(emails)),
                "phone_numbers": list(set(phones)),
                "social_profiles": list(set(social_links)),
                "total_links_scanned": len(links)
            },
            "status": "Success"
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "LG Research Intelligence Engine is Live"}
