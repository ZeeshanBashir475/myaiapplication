import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def home():
    return HTMLResponse("""
    <html>
        <body>
            <h1>GPT-5 Content Generator</h1>
            <p>System is working! ✅</p>
            <p>OpenAI API Key: {'Configured' if os.getenv('Open_Api_Key') else 'Missing'}</p>
        </body>
    </html>
    """)

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "System operational"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8002)))
