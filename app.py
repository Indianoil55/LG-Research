import cloudscraper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LG Research - Advanced OSINT")

class ScrapeRequest(BaseModel):
    url: str

@app.post("/lg-fetch")
def fetch_data(request: ScrapeRequest):
    # Cloudscraper instance banana
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        # Request bhejna
        response = scraper.get(request.url)
        
        if response.status_code == 200:
            return {
                "tool": "LG Research",
                "status": "Success",
                "status_code": response.status_code,
                "data": response.text[:5000] # Pehla 5000 characters
            }
        else:
            return {"status": "Failed", "error": f"Blocked with code {response.status_code}"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "LG Research Tool is Live"}
