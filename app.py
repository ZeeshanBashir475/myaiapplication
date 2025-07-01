from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="AI Content Creation Agent")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with form"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Interactive AI Content Creation Agent</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1000px; 
                margin: 0 auto; 
                padding: 20px; 
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .form-group { 
                margin-bottom: 20px; 
            }
            label { 
                display: block; 
                margin-bottom: 8px; 
                font-weight: bold; 
                color: #333;
            }
            input, textarea, select { 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #ddd; 
                border-radius: 6px; 
                font-size: 16px;
                box-sizing: border-box;
            }
            textarea {
                height: 60px;
                resize: vertical;
            }
            input:focus, textarea:focus, select:focus {
                border-color: #007bff;
                outline: none;
            }
            button { 
                background-color: #007bff; 
                color: white; 
                padding: 15px 30px; 
                border: none; 
                border-radius: 6px; 
                cursor: pointer; 
                font-size: 18px;
                font-weight: bold;
                width: 100%;
            }
            button:hover { 
                background-color: #0056b3; 
            }
            .section-title {
                color: #007bff;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
                margin: 30px 0 20px 0;
            }
            .help-text {
                font-size: 14px;
                color: #666;
                margin-top: 5px;
            }
            .features {
                background-color: #e7f3ff;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Interactive AI Content Creation Agent</h1>
            <p>Create high-performance content with human expertise integration</p>
            
            <div class="features">
                <h3>🚀 What You'll Get:</h3>
                <ul>
                    <li>✅ E-E-A-T optimized content for better rankings</li>
                    <li>✅ Performance prediction vs AI-only content</li>
                    <li>✅ Quality scoring and improvement recommendations</li>
                    <li>✅ Full content generated with your expertise</li>
                </ul>
            </div>
            
            <form action="/generate" method="post">
                <!-- Content Topic -->
                <div class="form-group">
                    <label for="topic">Content Topic:</label>
                    <input type="text" id="topic" name="topic" 
                           placeholder="e.g., best budget laptops for college students" required>
                </div>
                
                <!-- Subreddits -->
                <div class="form-group">
                    <label for="subreddits">Target Subreddits (comma-separated):</label>
                    <input type="text" id="subreddits" name="subreddits" 
                           placeholder="e.g., laptops, college, StudentLoans" required>
                </div>
                
                <h3 class="section-title">🏢 Your Business Context</h3>
                
                <!-- Industry -->
                <div class="form-group">
                    <label for="industry">What industry are you in?</label>
                    <input type="text" id="industry" name="industry" 
                           placeholder="e.g., Technology, Healthcare, Finance" required>
                    <div class="help-text">This helps optimize content for your industry standards</div>
                </div>
                
                <!-- Target Audience -->
                <div class="form-group">
                    <label for="target_audience">Who is your target audience?</label>
                    <input type="text" id="target_audience" name="target_audience" 
                           placeholder="e.g., College students, Small business owners" required>
                </div>
                
                <!-- Business Type -->
                <div class="form-group">
                    <label for="business_type">Business Type:</label>
                    <select id="business_type" name="business_type" required>
                        <option value="">Select...</option>
                        <option value="B2B">B2B (Business to Business)</option>
                        <option value="B2C">B2C (Business to Consumer)</option>
                        <option value="Both">Both B2B and B2C</option>
                    </select>
                </div>
                
                <!-- Content Goal -->
                <div class="form-group">
                    <label for="content_goal">What's the main goal for this content?</label>
                    <textarea id="content_goal" name="content_goal" 
                              placeholder="e.g., Educate customers, Generate leads, Build trust" required></textarea>
                </div>
                
                <!-- Unique Value Proposition -->
                <div class="form-group">
                    <label for="unique_value_prop">What makes you different from competitors?</label>
                    <textarea id="unique_value_prop" name="unique_value_prop" 
                              placeholder="e.g., 24/7 support, 10 years experience, patented technology" required></textarea>
                </div>
                
                <!-- Brand Voice -->
                <div class="form-group">
                    <label for="brand_voice">How would you describe your brand voice?</label>
                    <select id="brand_voice" name="brand_voice" required>
                        <option value="">Select...</option>
                        <option value="Professional">Professional</option>
                        <option value="Casual">Casual & Friendly</option>
                        <option value="Technical">Technical & Expert</option>
                        <option value="Empathetic">Empathetic & Caring</option>
                        <option value="Bold">Bold & Confident</option>
                    </select>
                </div>
                
                <h3 class="section-title">👥 Customer Insights</h3>
                
                <!-- Customer Pain Points -->
                <div class="form-group">
                    <label for="customer_pain_points">What are your customers' biggest challenges?</label>
                    <textarea id="customer_pain_points" name="customer_pain_points" 
                              placeholder="e.g., Limited budget, Too many options, Lack of time" required></textarea>
                </div>
                
                <!-- Frequent Questions -->
                <div class="form-group">
                    <label for="frequent_questions">What questions do customers ask most often?</label>
                    <textarea id="frequent_questions" name="frequent_questions" 
                              placeholder="e.g., How much does it cost? Is it reliable? How long does it take?" required></textarea>
                </div>
                
                <!-- Success Story -->
                <div class="form-group">
                    <label for="success_story">Share a brief customer success story:</label>
                    <textarea id="success_story" name="success_story" 
                              placeholder="e.g., Helped a customer save 50% on costs, reduced their time by 3 hours daily"></textarea>
                    <div class="help-text">Optional but helps add authenticity to your content</div>
                </div>
                
                <button type="submit">🚀 Create Enhanced Content Strategy</button>
            </form>
            
            <div id="loading" style="display: none; text-align: center; margin-top: 20px;">
                <h3>🔍 Creating your enhanced content strategy...</h3>
                <p>Analyzing your inputs, researching Reddit, and generating high-performance content...</p>
            </div>
        </div>
        
        <script>
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('loading').style.display = 'block';
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/generate")
async def generate_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    content_goal: str = Form(...),
    unique_value_prop: str = Form(...),
    brand_voice: str = Form(...),
    customer_pain_points: str = Form(...),
    frequent_questions: str = Form(...),
    success_story: str = Form("")
):
    """Generate enhanced content with human inputs - simplified version"""
    try:
        # Simplified content generation for demo
        generated_content = f"""
        # {topic.title()}
        
        ## Overview
        Based on your business expertise in {industry} and your target audience of {target_audience}, 
        here's a comprehensive content strategy.
        
        ## Key Points
        - Industry: {industry}
        - Target Audience: {target_audience}
        - Business Type: {business_type}
        - Brand Voice: {brand_voice}
        
        ## Customer Pain Points Addressed
        {customer_pain_points}
        
        ## Frequently Asked Questions
        {frequent_questions}
        
        ## Your Unique Value Proposition
        {unique_value_prop}
        
        ## Content Strategy
        This content has been optimized for your specific business context and customer needs.
        
        ## Success Story Integration
        {success_story if success_story else "No success story provided"}
        """
        
        # Generate results page
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Your Content Strategy - {topic}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background-color: #f5f5f5;
                    line-height: 1.6;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(135deg, #007bff, #0056b3);
                    color: white;
                    border-radius: 10px;
                }}
                .content-box {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #ddd;
                    margin: 15px 0;
                }}
                .back-btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #6c757d;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }}
                .back-btn:hover {{
                    background-color: #545b62;
                }}
                pre {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 6px;
                    white-space: pre-wrap;
                    overflow-x: auto;
                    border-left: 4px solid #007bff;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← Create New Content Strategy</a>
                
                <div class="header">
                    <h1>🎉 Your Content Strategy Generated!</h1>
                    <p><strong>Topic:</strong> {topic}</p>
                    <p><strong>Industry:</strong> {industry}</p>
                </div>

                <div class="content-box">
                    <h2>📄 Generated Content</h2>
                    <pre>{generated_content}</pre>
                </div>

                <div style="text-align: center; margin-top: 40px;">
                    <a href="/" class="back-btn" style="font-size: 18px; padding: 15px 30px;">Create Another Content Strategy</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_response)
        
    except Exception as e:
        error_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>❌ Error</h1>
            <p><strong>Error generating content:</strong> {str(e)}</p>
            <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 6px;">← Try Again</a>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
