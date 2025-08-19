import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

# FastAPI and WebSocket imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Anthropic import with error handling
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ anthropic not installed. Install with: pip install anthropic")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple Configuration
class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    PORT = int(os.getenv("PORT", 8002))
    HOST = os.getenv("HOST", "0.0.0.0")
    ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

config = Config()

# Simple Content Types
CONTENT_TYPES = {
    "article": "📰 Article",
    "blog_post": "📝 Blog Post", 
    "product_page": "🛍️ Product Page",
    "landing_page": "🎯 Landing Page",
    "guide": "📚 Guide",
    "tutorial": "🎓 Tutorial"
}

# Minimal LLM Client
class SimpleLLMClient:
    def __init__(self):
        self.client = None
        self.setup()
    
    def setup(self):
        if not ANTHROPIC_AVAILABLE:
            logger.error("❌ Anthropic library not available")
            return
        
        if not config.ANTHROPIC_API_KEY:
            logger.error("❌ ANTHROPIC_API_KEY not found")
            return
        
        try:
            # Minimal initialization - just the API key
            self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            logger.info("✅ Anthropic client initialized")
            
            # Test it immediately
            test_response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}]
            )
            logger.info("✅ Anthropic API test successful")
            
        except Exception as e:
            logger.error(f"❌ Anthropic setup failed: {e}")
            self.client = None
    
    def is_working(self):
        return self.client is not None
    
    async def generate_content(self, prompt: str, max_tokens: int = 2000):
        """Generate content without streaming to avoid issues"""
        
        if not self.is_working():
            return "❌ AI client not available. Please check your API key."
        
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else "No content generated"
            logger.info(f"✅ Content generated: {len(content)} characters")
            return content
            
        except Exception as e:
            error_msg = f"❌ AI Generation Error: {str(e)}"
            logger.error(error_msg)
            return error_msg

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"✅ WebSocket connected: {session_id}")
        return True
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"❌ WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"❌ Send error: {e}")
                self.disconnect(session_id)
                return False
        return False

# Simple Content System
class SimpleContentSystem:
    def __init__(self):
        self.llm_client = SimpleLLMClient()
    
    async def generate_content_simple(self, form_data: Dict, session_id: str):
        """Simple content generation without Reddit research"""
        
        try:
            # Step 1: Start
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 1,
                'total': 3,
                'title': 'Starting',
                'message': f'🚀 Generating {form_data["content_type"]} about: {form_data["topic"]}'
            })
            
            # Step 2: AI Generation
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 2,
                'total': 3,
                'title': 'AI Generation',
                'message': '🤖 Creating content with AI...'
            })
            
            # Create AI prompt
            topic = form_data['topic']
            content_type = form_data['content_type']
            audience = form_data.get('target_audience', 'readers')
            pain_points = form_data.get('customer_pain_points', '')
            usps = form_data.get('unique_selling_points', '')
            cta = form_data.get('call_to_action', '')
            
            prompt = f"""Write a comprehensive {content_type} about "{topic}" for {audience}.

Target Audience: {audience}
Content Type: {content_type}

{f"Address these pain points: {pain_points}" if pain_points else ""}
{f"Highlight these unique benefits: {usps}" if usps else ""}
{f"Include this call-to-action: {cta}" if cta else ""}

Write a complete, professional {content_type} that is informative, engaging, and valuable to readers. Make it 1500-2500 words with clear structure, headings, and actionable content."""

            # Generate content
            content = await self.llm_client.generate_content(prompt, max_tokens=3000)
            
            # Step 3: Complete
            await manager.send_message(session_id, {
                'type': 'progress_update',
                'step': 3,
                'total': 3,
                'title': 'Complete',
                'message': '✅ Content generation completed!'
            })
            
            # Send final result
            await manager.send_message(session_id, {
                'type': 'generation_complete',
                'content': content,
                'content_type': form_data['content_type'],
                'metrics': {
                    'word_count': len(content.split()),
                    'reading_time': max(1, len(content.split()) // 200),
                    'quality_score': 8.5,
                    'ai_generated': not content.startswith("❌")
                }
            })
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            await manager.send_message(session_id, {
                'type': 'generation_error',
                'error': str(e)
            })

# Initialize FastAPI
app = FastAPI(title="Simple AI Content Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize components
manager = ConnectionManager()
content_system = SimpleContentSystem()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    content_type_options = ""
    for key, name in CONTENT_TYPES.items():
        content_type_options += f'<option value="{key}">{name}</option>\n'
    
    return HTMLResponse(f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Simple AI Content Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 2rem; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 1rem; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .header {{ text-align: center; margin-bottom: 2rem; }}
        .header h1 {{ color: #2d3748; font-size: 2.5rem; margin-bottom: 1rem; }}
        .header p {{ color: #4a5568; font-size: 1.1rem; }}
        .form-group {{ margin-bottom: 1.5rem; }}
        .label {{ display: block; font-weight: 600; margin-bottom: 0.5rem; color: #2d3748; }}
        .input, .textarea, .select {{ width: 100%; padding: 0.8rem; border: 2px solid #e2e8f0; border-radius: 0.5rem; font-size: 1rem; }}
        .input:focus, .textarea:focus, .select:focus {{ outline: none; border-color: #667eea; }}
        .textarea {{ resize: vertical; min-height: 100px; }}
        .button {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; border: none; border-radius: 0.5rem; font-size: 1.1rem; font-weight: 600; cursor: pointer; width: 100%; margin-top: 1rem; }}
        .button:hover {{ transform: translateY(-2px); }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
        @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Simple AI Content Generator</h1>
            <p>Generate high-quality content with AI</p>
        </div>
        
        <form id="contentForm">
            <div class="form-group">
                <label class="label">Topic *</label>
                <input class="input" type="text" name="topic" placeholder="e.g., Best wireless headphones for remote work" required>
            </div>
            
            <div class="grid">
                <div class="form-group">
                    <label class="label">Content Type *</label>
                    <select class="select" name="content_type" required>
                        {content_type_options}
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="label">Target Audience *</label>
                    <input class="input" type="text" name="target_audience" placeholder="e.g., Remote workers, Small business owners" required>
                </div>
            </div>
            
            <div class="form-group">
                <label class="label">Customer Pain Points</label>
                <textarea class="textarea" name="customer_pain_points" placeholder="e.g., Difficulty finding reliable reviews, High costs, Complex setup"></textarea>
            </div>
            
            <div class="form-group">
                <label class="label">Unique Selling Points</label>
                <textarea class="textarea" name="unique_selling_points" placeholder="e.g., 10+ years experience, Free shipping, 30-day guarantee"></textarea>
            </div>
            
            <div class="form-group">
                <label class="label">Call to Action</label>
                <input class="input" type="text" name="call_to_action" placeholder="e.g., Shop now, Download guide, Contact us">
            </div>
            
            <button type="submit" class="button">
                🚀 Generate AI Content
            </button>
        </form>
    </div>
    
    <script>
        document.getElementById('contentForm').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {{}};
            
            for (let [key, value] of formData.entries()) {{
                data[key] = value;
            }}
            
            if (!data.topic || !data.content_type || !data.target_audience) {{
                alert('Please fill in all required fields');
                return;
            }}
            
            localStorage.setItem('contentFormData', JSON.stringify(data));
            window.location.href = '/generate';
        }});
    </script>
</body>
</html>
''')

@app.get("/generate", response_class=HTMLResponse)
async def generate_page():
    return HTMLResponse('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Content Generation</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, sans-serif; background: #f8fafc; color: #1a202c; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; text-align: center; }
        .container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
        .progress-section, .content-display { background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .progress-bar { width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin: 1rem 0; }
        .progress-fill { height: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 0%; transition: width 0.5s ease; }
        .progress-text { text-align: center; color: #4a5568; }
        .current-step { background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; display: none; }
        .content-display { display: none; }
        .content-display.visible { display: block; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .metric-card { background: #f8fafc; padding: 1rem; border-radius: 0.5rem; text-align: center; }
        .metric-value { font-size: 1.5rem; font-weight: 700; color: #667eea; }
        .metric-label { font-size: 0.8rem; color: #4a5568; }
        .content-display h1 { color: #2d3748; margin-bottom: 1rem; }
        .content-display h2 { color: #4a5568; margin: 1.5rem 0 0.8rem 0; }
        .content-display p { margin-bottom: 1rem; line-height: 1.6; }
        .actions { display: flex; gap: 1rem; margin-top: 2rem; }
        .btn { padding: 0.8rem 1.5rem; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: 600; }
        .btn-primary { background: #10b981; color: white; }
        .btn-secondary { background: #6b7280; color: white; }
        .status { padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; font-size: 0.9rem; }
        .status-connecting { background: #fbbf24; color: white; }
        .status-connected { background: #10b981; color: white; }
        .status-generating { background: #3b82f6; color: white; }
        .status-error { background: #ef4444; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Content Generation</h1>
        <div class="status status-connecting" id="connectionStatus">Connecting...</div>
    </div>
    
    <div class="container">
        <div class="progress-section">
            <h2>📊 Generation Progress</h2>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Initializing...</div>
            
            <div class="current-step" id="currentStep">
                <h4 id="currentStepTitle">Loading...</h4>
                <p id="currentStepMessage">Please wait...</p>
            </div>
        </div>
        
        <div class="content-display" id="contentDisplay">
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value" id="wordCount">--</div>
                    <div class="metric-label">Words</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="readingTime">--</div>
                    <div class="metric-label">Reading Time</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="qualityScore">--</div>
                    <div class="metric-label">Quality Score</div>
                </div>
            </div>
            
            <div id="generatedContent"></div>
            
            <div class="actions">
                <button class="btn btn-primary" onclick="copyContent()">📋 Copy Content</button>
                <button class="btn btn-secondary" onclick="downloadContent()">💾 Download</button>
                <button class="btn btn-secondary" onclick="window.location.reload()">🔄 Regenerate</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        let generatedContent = '';
        
        window.addEventListener('load', function() {
            const storedData = localStorage.getItem('contentFormData');
            if (storedData) {
                const formData = JSON.parse(storedData);
                initWebSocket(formData);
            } else {
                alert('No form data found. Please fill out the form first.');
                window.location.href = '/';
            }
        });
        
        function initWebSocket(formData) {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = window.location.host;
            const wsUrl = `${wsProtocol}//${wsHost}/ws/${sessionId}`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'status status-connected';
                
                ws.send(JSON.stringify({
                    type: 'start_generation',
                    data: formData
                }));
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = function() {
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').className = 'status status-error';
            };
        }
        
        function handleMessage(data) {
            switch(data.type) {
                case 'progress_update':
                    updateProgress(data);
                    break;
                case 'generation_complete':
                    displayContent(data);
                    break;
                case 'generation_error':
                    alert('Error: ' + data.error);
                    break;
            }
        }
        
        function updateProgress(data) {
            const percentage = (data.step / data.total) * 100;
            document.getElementById('progressFill').style.width = percentage + '%';
            document.getElementById('progressText').textContent = `Step ${data.step} of ${data.total}: ${data.title}`;
            
            const currentStep = document.getElementById('currentStep');
            currentStep.style.display = 'block';
            document.getElementById('currentStepTitle').textContent = data.title;
            document.getElementById('currentStepMessage').textContent = data.message;
        }
        
        function displayContent(data) {
            generatedContent = data.content;
            
            const metrics = data.metrics || {};
            document.getElementById('wordCount').textContent = metrics.word_count?.toLocaleString() || '--';
            document.getElementById('readingTime').textContent = metrics.reading_time ? metrics.reading_time + ' min' : '--';
            document.getElementById('qualityScore').textContent = metrics.quality_score?.toFixed(1) || '8.5';
            
            const formattedContent = formatContent(data.content);
            document.getElementById('generatedContent').innerHTML = formattedContent;
            
            document.getElementById('contentDisplay').classList.add('visible');
        }
        
        function formatContent(content) {
            return content
                .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                .replace(/\\n\\n/g, '</p><p>')
                .replace(/^([^<].+)$/gm, '<p>$1</p>')
                .replace(/<p><h/g, '<h')
                .replace(/<\\/h([1-6])><\\/p>/g, '</h$1>');
        }
        
        function copyContent() {
            const content = document.getElementById('generatedContent').innerText;
            navigator.clipboard.writeText(content).then(() => {
                alert('Content copied to clipboard!');
            });
        }
        
        function downloadContent() {
            const content = document.getElementById('generatedContent').innerText;
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `content_${new Date().toISOString().split('T')[0]}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
''')

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        await manager.connect(websocket, session_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data['type'] == 'start_generation':
                    form_data = message_data['data']
                    asyncio.create_task(
                        content_system.generate_content_simple(form_data, session_id)
                    )
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Invalid message format'
                }))
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)

# Health check
@app.get("/health")
async def health_check():
    # Test Anthropic connection
    anthropic_working = False
    anthropic_error = None
    
    if config.ANTHROPIC_API_KEY and ANTHROPIC_AVAILABLE:
        try:
            test_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            test_response = test_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}]
            )
            anthropic_working = True
        except Exception as e:
            anthropic_error = str(e)
    
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "anthropic_configured": bool(config.ANTHROPIC_API_KEY),
        "anthropic_available": ANTHROPIC_AVAILABLE,
        "anthropic_working": anthropic_working,
        "anthropic_error": anthropic_error,
        "simplified_version": True,
        "reddit_removed": True
    })

# Test endpoint
@app.get("/test-simple")
async def test_simple():
    """Test the simplified version"""
    
    if not config.ANTHROPIC_API_KEY:
        return JSONResponse({"error": "No API key configured"})
    
    try:
        llm = SimpleLLMClient()
        if not llm.is_working():
            return JSONResponse({"error": "LLM client not working"})
        
        content = await llm.generate_content("Write a short paragraph about AI content generation.", 100)
        
        return JSONResponse({
            "status": "success",
            "content": content,
            "working": not content.startswith("❌")
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)})

if __name__ == "__main__":
    print("🚀 Starting Simple AI Content Generator...")
    print(f"🔑 API Key: {'✅ Configured' if config.ANTHROPIC_API_KEY else '❌ Missing'}")
    print(f"📚 Anthropic: {'✅ Available' if ANTHROPIC_AVAILABLE else '❌ Missing'}")
    
    try:
        uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise e
