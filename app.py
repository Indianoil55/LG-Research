import undetected_chromedriver as uc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time

# LG Research API Setup
app = FastAPI(title="LG Research Cloudflare Bypass API")

# Request model for better validation
class ScrapeRequest(BaseModel):
    url: str

@app.post("/lg-fetch")
async def fetch_data(request: ScrapeRequest):
    """
    LG Research Tool: Cloudflare ko bypass karke data nikalne wala endpoint.
    """
    options = uc.ChromeOptions()
    # Headless mode (browser dikhega nahi par kaam karega)
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        # Browser shuru karna
        driver = uc.Chrome(options=options)
        
        # Target URL par jana
        driver.get(request.url)
        
        # Cloudflare Challenge solve karne ke liye wait (5-10 seconds)
        time.sleep(7) 
        
        # Pura Page Source ya specific data nikalna
        page_data = driver.page_source
        current_url = driver.current_url
        
        # Response return karna
        return {
            "tool_name": "LG Research",
            "status": "Success",
            "final_url": current_url,
            "data": page_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LG Research Error: {str(e)}")
    
    finally:
        # Browser band karna zaroori hai memory bachane ke liye
        driver.quit()

if __name__ == "__main__":
    import uvicorn
    # Server ko 8000 port par start karna
    uvicorn.run(app, host="0.0.0.0", port=8000)
