pythonimport streamlit as st

# Streamlit app
st.title("My AI Application")
st.write("Welcome to my app!")

# Example of user input
user_input = st.text_input("Enter something:")
if st.button("Submit"):
    st.write(f"You entered: {user_input}")

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
    """Generate enhanced content with human inputs - display everything on page"""
    try:
        # Parse subreddits
        target_subreddits = [s.strip() for s in subreddits.split(',') if s.strip()]
        
        # Create business context from form inputs
        business_context = {
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'content_goal': content_goal,
            'unique_value_prop': unique_value_prop,
            'brand_voice': brand_voice
        }
        
        # Create human inputs from form
        human_inputs = {
            'customer_insights': {
                'customer_pain_points': customer_pain_points,
                'frequent_questions': frequent_questions,
                'success_story': success_story
            },
            'business_expertise': {
                'unique_value_prop': unique_value_prop,
                'industry_knowledge': f"Expert in {industry}",
                'target_audience_understanding': target_audience
            }
        }
        
        # Generate content using the enhanced agent
        print(f"Generating content for: {topic}")
        
        # Step 1: Intent Classification
        intent_data = agent.intent_classifier.classify_intent(topic)
        
        # Step 2: Customer Journey Mapping
        journey_data = agent.journey_mapper.map_customer_journey(topic, intent_data)
        
        # Step 3: Reddit Research
        reddit_insights = agent.reddit_researcher.research_topic(topic, target_subreddits)
        
        # Step 4: Content Type Classification
        content_type_data = agent.content_type_classifier.classify_content_type(topic, intent_data, business_context)
        chosen_content_type = content_type_data['primary_recommendation']['type']
        
        # Step 5: E-E-A-T Assessment
        eeat_assessment = agent.eeat_assessor.assess_content_eeat_requirements(
            topic, chosen_content_type, business_context, human_inputs
        )
        
        # Step 6: Generate Complete Content
        complete_content = agent.content_generator.generate_complete_content(
            topic, chosen_content_type, reddit_insights, journey_data, 
            business_context, human_inputs, eeat_assessment
        )
        
        # Step 7: Score Content Quality
        quality_score = agent.quality_scorer.score_content_quality(
            complete_content, topic, business_context, human_inputs, eeat_assessment
        )
        
        # Extract key metrics
        eeat_score = eeat_assessment.get('overall_eeat_score', 'N/A')
        overall_quality = quality_score.get('overall_quality_score', 'N/A')
        performance_prediction = quality_score.get('performance_prediction', 'N/A')
        traffic_multiplier = quality_score.get('traffic_multiplier_estimate', 'N/A')
        
        # Generate comprehensive results page
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Your Enhanced Content Strategy</title>
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
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .metric-card {{
                    background: linear-gradient(135deg, #28a745, #20c997);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .metric-label {{
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .section {{
                    margin: 30px 0;
                    padding: 20px;
                    border-left: 4px solid #007bff;
                    background-color: #f8f9fa;
                    border-radius: 0 8px 8px 0;
                }}
                .content-box {{
                    background-color: white;
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
                .highlight {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #ffc107;
                    margin: 15px 0;
                }}
                pre {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    white-space: pre-wrap;
                    overflow-x: auto;
                }}
                .success {{
                    color: #28a745;
                    font-weight: bold;
                }}
                .improvement {{
                    background-color: #e7f3ff;
                    padding: 10px;
                    border-radius: 6px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← Create New Content Strategy</a>
                
                <div class="header">
                    <h1>🎉 Your Enhanced Content Strategy</h1>
                    <p><strong>Topic:</strong> {topic}</p>
                    <p><strong>Content Type:</strong> {chosen_content_type.replace('_', ' ').title()}</p>
                </div>

                <div class="section">
                    <h2>📊 Performance Metrics</h2>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">{eeat_score}/10</div>
                            <div class="metric-label">E-E-A-T Score</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{overall_quality}/10</div>
                            <div class="metric-label">Quality Score</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{traffic_multiplier}</div>
                            <div class="metric-label">Traffic Multiplier</div>
                        </div>
                    </div>
                    <div class="highlight">
                        <strong>Performance Prediction:</strong> {performance_prediction}
                    </div>
                </div>

                <div class="section">
                    <h2>🎯 Content Strategy Analysis</h2>
                    <div class="content-box">
                        <h3>Intent Classification</h3>
                        <p><strong>Primary Intent:</strong> {intent_data.get('primary_intent', 'N/A')}</p>
                        <p><strong>Search Stage:</strong> {intent_data.get('search_stage', 'N/A')}</p>
                        <p><strong>Target Audience:</strong> {intent_data.get('target_audience', 'N/A')}</p>
                    </div>
                    
                    <div class="content-box">
                        <h3>Customer Journey Insights</h3>
                        <p><strong>Primary Stage:</strong> {journey_data.get('primary_stage', 'N/A')}</p>
                        <p><strong>Key Pain Points:</strong></p>
                        <ul>
                            {"".join([f"<li>{pain}</li>" for pain in journey_data.get('key_pain_points', [])])}
                        </ul>
                    </div>
                    
                    <div class="content-box">
                        <h3>Reddit Customer Voice Analysis</h3>
                        <p><strong>Common Customer Language:</strong></p>
                        <ul>
                            {"".join([f"<li>{lang}</li>" for lang in reddit_insights.get('customer_voice', {}).get('common_language', [])])}
                        </ul>
                        <p><strong>Frequent Questions:</strong></p>
                        <ul>
                            {"".join([f"<li>{q}</li>" for q in reddit_insights.get('customer_voice', {}).get('frequent_questions', [])])}
                        </ul>
                    </div>
                </div>

                <div class="section">
                    <h2>✍️ Generated Content</h2>
                    <div class="content-box">
                        <h3>Your High-Performance {chosen_content_type.replace('_', ' ').title()}</h3>
                        <p><strong>Word Count:</strong> {len(complete_content.split())} words</p>
                        <pre>{complete_content}</pre>
                    </div>
                </div>

                <div class="section">
                    <h2>🚀 Quality Analysis & Improvements</h2>
                    <div class="content-box">
                        <h3>What Makes This High-Performance Content:</h3>
                        <div class="improvement">
                            <strong>✅ Human Expertise Integration:</strong> Your business knowledge and customer insights are woven throughout
                        </div>
                        <div class="improvement">
                            <strong>✅ Authentic Customer Voice:</strong> Uses real language from Reddit research
                        </div>
                        <div class="improvement">
                            <strong>✅ E-E-A-T Optimized:</strong> Built for search engine performance and user trust
                        </div>
                        <div class="improvement">
                            <strong>✅ Journey-Aware:</strong> Matches your audience's decision-making stage
                        </div>
                    </div>
                    
                    <div class="highlight">
                        <h3>🎯 Key Improvements vs AI-Only Content:</h3>
                        <ul>
                            {"".join([f"<li>{improvement}</li>" for improvement in quality_score.get('critical_improvements', [])])}
                        </ul>
                    </div>
                </div>

                <div class="section">
                    <h2>📈 Why This Outperforms AI-Only Content</h2>
                    <div class="content-box">
                        <p><strong>🧠 Human Intelligence:</strong> Your industry expertise and customer understanding</p>
                        <p><strong>💡 Authentic Voice:</strong> Real business perspective instead of generic AI patterns</p>
                        <p><strong>🎯 Customer-Centric:</strong> Based on actual customer research and pain points</p>
                        <p><strong>🏆 E-E-A-T Compliant:</strong> Built for search performance and user trust</p>
                        <p><strong>📊 Performance Predicted:</strong> <span class="success">{performance_prediction}</span></p>
                    </div>
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
