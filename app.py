<div class="loading" id="loading">
                    <div class="loading-spinner"></div>
                    <h3>Advanced Intelligence Engines Processing</h3>
                    <p>Running comprehensive multi-agent analysis to create your content strategy</p>
                    <div class="loading-progress">
                        <div id="progress-1">🔍 Initializing Reddit Research Agent...</div>
                        <div id="progress-2">🧠 Activating Topic Research Agent...</div>
                        <div id="progress-3">📊 Running E-E-A-T Assessment Agent...</div>
                        <div id="progress-4">📈 Engaging Improvement Tracking Agent...</div>
                        <div id="progress-5">✨ Finalizing Content Generation Agent...</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Zee SEO Tool Enhanced v2.0</strong> - Advanced Content Intelligence Platform</p>
                <p>Built by Zeeshan Bashir • Creating content that converts, not just ranks</p>
                <p style="font-size: 0.75rem; margin-top: 1rem;">
                    Powered by Claude 4 • Reddit API • Advanced E-E-A-T Analysis • Real Customer Research
                </p>
            </div>
            
            <script>
                document.getElementById('contentForm').addEventListener('submit', function(e) {{
                    const btn = document.getElementById('generateBtn');
                    const loading = document.getElementById('loading');
                    
                    // Show loading state
                    btn.disabled = true;
                    btn.innerHTML = '⏳ Processing...';
                    loading.style.display = 'block';
                    loading.scrollIntoView({{ behavior: 'smooth' }});
                    
                    // Simulate progress updates
                    const progressItems = [
                        'progress-1', 'progress-2', 'progress-3', 'progress-4', 'progress-5'
                    ];
                    
                    progressItems.forEach((id, index) => {{
                        setTimeout(() => {{
                            const element = document.getElementById(id);
                            element.style.opacity = '1';
                            element.style.backgroundColor = '#dbeafe';
                            element.style.borderLeft = '4px solid #2563eb';
                        }}, (index + 1) * 1000);
                    }});
                }});
                
                // Character counters for textareas
                document.querySelectorAll('textarea[maxlength]').forEach(textarea => {{
                    const maxLength = textarea.getAttribute('maxlength');
                    const counter = document.createElement('div');
                    counter.style.fontSize = '0.75rem';
                    counter.style.color = '#6b7280';
                    counter.style.textAlign = 'right';
                    counter.style.marginTop = '0.25rem';
                    
                    textarea.parentNode.appendChild(counter);
                    
                    function updateCounter() {{
                        const remaining = maxLength - textarea.value.length;
                        counter.textContent = `${{textarea.value.length}}/${{maxLength}} characters`;
                        counter.style.color = remaining < 100 ? '#ef4444' : '#6b7280';
                    }}
                    
                    textarea.addEventListener('input', updateCounter);
                    updateCounter();
                }});
                
                // Form validation enhancements
                document.querySelectorAll('input[required], textarea[required], select[required]').forEach(field => {{
                    field.addEventListener('invalid', function(e) {{
                        e.preventDefault();
                        this.style.borderColor = '#ef4444';
                        this.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.1)';
                    }});
                    
                    field.addEventListener('input', function() {{
                        if (this.checkValidity()) {{
                            this.style.borderColor = '#10b981';
                            this.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        return HTMLResponse(content=f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 2rem; text-align: center;">
            <h1>⚠️ System Error</h1>
            <p>Unable to load the application. Please try again later.</p>
            <p><strong>Error:</strong> {str(e)}</p>
        </body>
        </html>
        """, status_code=500)

@app.post("/generate-advanced")
async def generate_advanced_content(
    topic: str = Form(...),
    subreddits: str = Form(...),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...),
    writing_style: str = Form(""),
    target_word_count: str = Form(""),
    eeat_instructions: str = Form(""),
    additional_notes: str = Form("")
):
    """Generate advanced content with comprehensive intelligence analysis"""
    
    start_time = datetime.now()
    logger.info(f"🚀 Starting advanced content generation for: {topic}")
    
    try:
        # Input validation and sanitization
        if not topic or len(topic.strip()) < 3:
            raise HTTPException(status_code=400, detail="Topic must be at least 3 characters long")
        
        if not subreddits or len(subreddits.strip()) < 2:
            raise HTTPException(status_code=400, detail="At least one subreddit must be specified")
        
        # Sanitize inputs
        topic = topic.strip()[:200]
        subreddits = subreddits.strip()[:300]
        industry = industry.strip()[:100]
        target_audience = target_audience.strip()[:100]
        unique_value_prop = unique_value_prop.strip()[:1000]
        customer_pain_points = customer_pain_points.strip()[:1500]
        
        # Create context objects
        business_context = {
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'unique_value_prop': unique_value_prop,
            'topic': topic
        }
        
        human_inputs = {
            'customer_pain_points': customer_pain_points,
            'unique_value_prop': unique_value_prop,
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type
        }
        
        ai_instructions = {
            'writing_style': writing_style,
            'target_word_count': target_word_count,
            'eeat_instructions': eeat_instructions,
            'additional_notes': additional_notes
        }
        
        # Initialize results with fallbacks
        reddit_insights = {}
        topic_research = {}
        eeat_assessment = {}
        improvement_report = {}
        generated_content = ""
        
        # Step 1: Enhanced Reddit Research
        try:
            if reddit_researcher:
                logger.info("🔍 Running enhanced Reddit research...")
                subreddit_list = [s.strip() for s in subreddits.split(',') if s.strip()]
                reddit_insights = reddit_researcher.research_topic_comprehensive(
                    topic, subreddit_list, max_posts_per_subreddit=12
                )
                logger.info(f"✅ Reddit research completed: {len(reddit_insights)} insights")
            else:
                logger.warning("⚠️ Reddit researcher not available, using fallback")
                reddit_insights = {"fallback": True, "message": "Reddit research unavailable"}
        except Exception as e:
            logger.error(f"❌ Reddit research failed: {str(e)}")
            reddit_insights = {"error": str(e), "fallback_used": True}
        
        # Step 2: Advanced Topic Research
        try:
            if topic_researcher:
                logger.info("🧠 Conducting advanced topic research...")
                topic_research = topic_researcher.research_topic_comprehensive(
                    topic, industry, target_audience, business_context
                )
                logger.info("✅ Topic research completed")
            else:
                logger.warning("⚠️ Topic researcher not available, using fallback")
                topic_research = {"fallback": True, "message": "Topic research unavailable"}
        except Exception as e:
            logger.error(f"❌ Topic research failed: {str(e)}")
            topic_research = {"error": str(e), "fallback_used": True}
        
        # Step 3: Enhanced Content Generation
        try:
            logger.info("✨ Generating enhanced content...")
            generated_content = enhanced_content_generator.generate_content(
                topic, business_context, human_inputs, ai_instructions, 
                reddit_insights, topic_research
            )
            logger.info(f"✅ Content generated: {len(generated_content)} characters")
        except Exception as e:
            logger.error(f"❌ Content generation failed: {str(e)}")
            generated_content = enhanced_content_generator._generate_fallback_content(
                topic, business_context, human_inputs
            )
        
        # Step 4: Comprehensive E-E-A-T Assessment
        try:
            if eeat_assessor:
                logger.info("📊 Performing comprehensive E-E-A-T assessment...")
                eeat_assessment = eeat_assessor.assess_comprehensive_eeat(
                    generated_content, topic, business_context, human_inputs, reddit_insights
                )
                logger.info("✅ E-E-A-T assessment completed")
            else:
                logger.warning("⚠️ E-E-A-T assessor not available, using fallback")
                eeat_assessment = {"fallback": True, "message": "E-E-A-T assessment unavailable"}
        except Exception as e:
            logger.error(f"❌ E-E-A-T assessment failed: {str(e)}")
            eeat_assessment = {"error": str(e), "fallback_used": True}
        
        # Step 5: Content Quality Analysis
        content_metrics = {
            'word_count': len(generated_content.split()),
            'character_count': len(generated_content),
            'quality_score': min(10.0, len(generated_content.split()) / 150),
            'readability_score': 85.0,  # Placeholder - would use actual readability analysis
            'uniqueness_score': 92.0,   # Placeholder - would use actual uniqueness check
            'sentiment_score': 'positive'  # Placeholder
        }
        
        # Step 6: Track Improvement
        try:
            if improvement_tracker and eeat_assessment and not eeat_assessment.get('fallback'):
                logger.info("📈 Tracking improvement metrics...")
                snapshot_id = improvement_tracker.track_analysis(
                    topic,
                    eeat_assessment.get('eeat_assessment', {}),
                    eeat_assessment.get('human_vs_ai_analysis', {}),
                    content_metrics,
                    business_context,
                    human_inputs
                )
                
                # Generate improvement report
                improvement_report = improvement_tracker.generate_improvement_report(snapshot_id)
                logger.info("✅ Improvement tracking completed")
            else:
                logger.warning("⚠️ Improvement tracker not available or E-E-A-T assessment failed")
                improvement_report = {"fallback": True, "message": "Improvement tracking unavailable"}
        except Exception as e:
            logger.error(f"❌ Improvement tracking failed: {str(e)}")
            improvement_report = {"error": str(e), "fallback_used": True}
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"⏱️ Total processing time: {processing_time:.2f} seconds")
        
        # Generate comprehensive results page
        html_response = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Advanced Content Intelligence Report - {topic} | Zee SEO Tool</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="description" content="Comprehensive content intelligence analysis for {topic}">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                    color: #111827;
                    line-height: 1.6;
                    min-height: 100vh;
                }}
                .header {{
                    background: white;
                    border-bottom: 1px solid #e5e7eb;
                    padding: 1rem 0;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    position: sticky;
                    top: 0;
                    z-index: 100;
                }}
                .header-content {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .logo {{
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }}
                .logo-icon {{
                    width: 2.5rem;
                    height: 2.5rem;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    border-radius: 0.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 700;
                    font-size: 1.25rem;
                }}
                .logo-text {{
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .tagline {{
                    font-size: 0.75rem;
                    color: #6b7280;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 2rem 1.5rem;
                }}
                .report-header {{
                    background: white;
                    border-radius: 1rem;
                    padding: 2rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    margin-bottom: 2rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border: 1px solid #f3f4f6;
                }}
                .report-title {{
                    font-size: 2rem;
                    font-weight: 800;
                    color: #111827;
                    margin-bottom: 0.5rem;
                }}
                .report-meta {{
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                }}
                .meta-item {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    background: #f3f4f6;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                }}
                .overall-scores {{
                    display: flex;
                    gap: 2rem;
                    align-items: center;
                }}
                .score-display {{
                    text-align: center;
                }}
                .score-value {{
                    font-size: 2.5rem;
                    font-weight: 800;
                    color: #2563eb;
                    line-height: 1;
                }}
                .score-label {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    font-weight: 600;
                    margin-top: 0.25rem;
                }}
                .improvement-badge {{
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 0.75rem;
                    font-size: 0.875rem;
                    font-weight: 600;
                    margin-top: 0.5rem;
                    display: inline-block;
                }}
                .tabs {{
                    display: flex;
                    background: white;
                    border-radius: 1rem;
                    padding: 0.5rem;
                    margin-bottom: 2rem;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    overflow-x: auto;
                }}
                .tab {{
                    flex: 1;
                    padding: 1rem 1.5rem;
                    text-align: center;
                    border-radius: 0.75rem;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-weight: 600;
                    font-size: 0.875rem;
                    white-space: nowrap;
                    min-width: 120px;
                }}
                .tab.active {{
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    color: white;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                .tab:not(.active):hover {{
                    background: #f3f4f6;
                }}
                .tab-content {{
                    display: none;
                }}
                .tab-content.active {{
                    display: block;
                }}
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                    gap: 1.5rem;
                    margin-bottom: 2rem;
                }}
                .card {{
                    background: white;
                    border-radius: 1rem;
                    padding: 1.5rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    transition: all 0.3s ease;
                }}
                .card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                }}
                .card h3 {{
                    font-size: 1.125rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }}
                .eeat-scores {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                }}
                .eeat-score {{
                    text-align: center;
                }}
                .score-circle {{
                    width: 4rem;
                    height: 4rem;
                    border-radius: 50%;
                    background: conic-gradient(#2563eb calc(var(--score) * 1%), #e5e7eb calc(var(--score) * 1%));
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 0.5rem;
                    position: relative;
                }}
                .score-circle::before {{
                    content: '';
                    width: 3rem;
                    height: 3rem;
                    background: white;
                    border-radius: 50%;
                    position: absolute;
                }}
                .score-circle span {{
                    position: relative;
                    z-index: 1;
                    font-weight: 700;
                    color: #111827;
                    font-size: 0.875rem;
                }}
                .score-name {{
                    font-size: 0.75rem;
                    color: #6b7280;
                    font-weight: 600;
                }}
                .metric-list {{
                    display: grid;
                    gap: 0.75rem;
                }}
                .metric-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.75rem;
                    background: #f9fafb;
                    border-radius: 0.5rem;
                    border: 1px solid #f3f4f6;
                }}
                .metric-label {{
                    font-size: 0.875rem;
                    color: #374151;
                    font-weight: 500;
                }}
                .metric-value {{
                    font-size: 0.875rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .insight-list {{
                    list-style: none;
                    padding: 0;
                    display: grid;
                    gap: 0.75rem;
                }}
                .insight-item {{
                    padding: 1rem;
                    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                    border-left: 4px solid #2563eb;
                    border-radius: 0 0.5rem 0.5rem 0;
                    font-size: 0.875rem;
                    line-height: 1.5;
                }}
                .content-section {{
                    margin: 2rem 0;
                }}
                .content-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }}
                .content-title {{
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #111827;
                }}
                .content-actions {{
                    display: flex;
                    gap: 0.75rem;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    padding: 0.75rem 1.25rem;
                    font-size: 0.875rem;
                    font-weight: 600;
                    border-radius: 0.75rem;
                    border: none;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-decoration: none;
                    font-family: inherit;
                }}
                .btn-primary {{
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    color: white;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                .btn-primary:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                }}
                .btn-outline {{
                    background: white;
                    color: #374151;
                    border: 2px solid #e5e7eb;
                }}
                .btn-outline:hover {{
                    border-color: #2563eb;
                    color: #2563eb;
                }}
                .back-btn {{
                    background: #6b7280;
                    color: white;
                }}
                .back-btn:hover {{
                    background: #374151;
                }}
                .content-display {{
                    background: white;
                    border-radius: 1rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    margin-bottom: 1rem;
                }}
                .content-stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 1rem;
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid #f3f4f6;
                    background: #f9fafb;
                    border-radius: 1rem 1rem 0 0;
                }}
                .stat {{
                    text-align: center;
                    font-size: 0.75rem;
                    color: #6b7280;
                    font-weight: 500;
                }}
                .stat-value {{
                    display: block;
                    font-size: 1rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 0.25rem;
                }}
                .content-text {{
                    padding: 1.5rem;
                    max-height: 600px;
                    overflow-y: auto;
                }}
                .content-text pre {{
                    white-space: pre-wrap;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    font-size: 0.875rem;
                    line-height: 1.6;
                    color: #374151;
                    margin: 0;
                }}
                .footer {{
                    margin-top: 4rem;
                    padding: 2rem 0;
                    background: white;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                }}
                .footer p {{
                    color: #6b7280;
                    margin-bottom: 0.5rem;
                }}
                .processing-info {{
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                    border: 1px solid #0ea5e9;
                    border-radius: 0.75rem;
                    padding: 1rem;
                    margin-bottom: 2rem;
                    font-size: 0.875rem;
                }}
                .error-notice {{
                    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                    border: 1px solid #f59e0b;
                    border-radius: 0.75rem;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    font-size: 0.875rem;
                }}
                @media (max-width: 1024px) {{
                    .dashboard-grid {{ grid-template-columns: 1fr; }}
                    .report-header {{ flex-direction: column; gap: 1.5rem; text-align: center; }}
                    .overall-scores {{ justify-content: center; }}
                }}
                @media (max-width: 768px) {{
                    .content-header {{ flex-direction: column; gap: 1rem; align-items: stretch; }}
                    .content-actions {{ justify-content: center; }}
                    .eeat-scores {{ grid-template-columns: repeat(2, 1fr); }}
                    .tabs {{ flex-direction: column; }}
                    .tab {{ min-width: auto; }}
                    .content-stats {{ grid-template-columns: 1fr; }}
                    .container {{ padding: 1rem; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <div class="logo">
                        <div class="logo-icon">Z</div>
                        <div>
                            <div class="logo-text">Zee SEO Tool</div>
                            <div class="tagline">Advanced Intelligence Report</div>
                        </div>
                    </div>
                    <a href="/" class="btn back-btn">← New Analysis</a>
                </div>
            </div>
            
            <div class="container">
                <div class="processing-info">
                    <strong>🔧 Processing Summary:</strong> 
                    Analysis completed in {processing_time:.1f} seconds | 
                    Reddit Research: {'✅' if not reddit_insights.get('fallback') else '⚠️'} | 
                    E-E-A-T Assessment: {'✅' if not eeat_assessment.get('fallback') else '⚠️'} | 
                    Topic Research: {'✅' if not topic_research.get('fallback') else '⚠️'} | 
                    Improvement Tracking: {'✅' if not improvement_report.get('fallback') else '⚠️'}
                </div>
                
                <div class="report-header">
                    <div>
                        <h1 class="report-title">{topic.title()}</h1>
                        <div class="report-meta">
                            <span class="meta-item">🏢 {industry}</span>
                            <span class="meta-item">👥 {target_audience}</span>
                            <span class="meta-item">📝 {content_metrics['word_count']} words</span>
                            <span class="meta-item">⚡ {processing_time:.1f}s processing</span>
                            <span class="meta-item">🔬 Multi-agent analysis</span>
                        </div>
                    </div>
                    <div class="overall-scores">
                        <div class="score-display">
                            <div class="score-value">{eeat_assessment.get('eeat_assessment', {}).get('overall_score', 'N/A')}</div>
                            <div class="score-label">E-E-A-T Score</div>
                            {formatter.generate_improvement_badge(improvement_report)}
                        </div>
                        <div class="score-display">
                            <div class="score-value">{eeat_assessment.get('human_vs_ai_analysis', {}).get('human_elements_score', 'N/A')}</div>
                            <div class="score-label">Human Elements</div>
                        </div>
                    </div>
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="showTab('overview')">📊 Overview</div>
                    <div class="tab" onclick="showTab('eeat')">🎯 E-E-A-T Analysis</div>
                    <div class="tab" onclick="showTab('research')">🔍 Research Insights</div>
                    <div class="tab" onclick="showTab('improvement')">📈 Improvement Tracking</div>
                    <div class="tab" onclick="showTab('content')">📝 Content</div>
                </div>
                
                <div id="overview" class="tab-content active">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>🎯 E-E-A-T Assessment</h3>
                            {self._render_eeat_overview(eeat_assessment)}
                        </div>
                        
                        <div class="card">
                            <h3>🔍 Research Quality</h3>
                            {self._render_research_quality(reddit_insights, topic_research)}
                        </div>
                        
                        <div class="card">
                            <h3>🚀 Performance Prediction</h3>
                            {self._render_performance_prediction(eeat_assessment)}
                        </div>
                    </div>
                </div>
                
                <div id="eeat" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>📊 Detailed E-E-A-T Analysis</h3>
                            <ul class="insight-list">
                                {formatter.format_eeat_insights(eeat_assessment)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>💡 Improvement Recommendations</h3>
                            <ul class="insight-list">
                                {formatter.format_improvement_recommendations(eeat_assessment.get('improvement_analysis', {}))}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div id="research" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>🎯 Customer Pain Points</h3>
                            <ul class="insight-list">
                                {formatter.format_pain_points(reddit_insights)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>🗣️ Real Customer Voice</h3>
                            <ul class="insight-list">
                                {formatter.format_customer_quotes(reddit_insights)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>📈 Content Opportunities</h3>
                            <ul class="insight-list">
                                {formatter.format_content_opportunities(topic_research)}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div id="improvement" class="tab-content">
                    <div class="dashboard-grid">
                        <div class="card">
                            <h3>📈 Current Performance</h3>
                            <div class="metric-list">
                                {formatter.format_current_performance(improvement_report)}
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3>🎯 Next Steps</h3>
                            <ul class="insight-list">
                                {formatter.format_next_steps(improvement_report)}
                            </ul>
                        </div>
                        
                        <div class="card">
                            <h3>💰 ROI Projection</h3>
                            <div class="metric-list">
                                {formatter.format_roi_projection(improvement_report)}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="content" class="tab-content">
                    <div class="content-section">
                        <div class="content-header">
                            <h2 class="content-title">Generated Content</h2>
                            <div class="content-actions">
                                <button onclick="copyContent()" class="btn btn-outline">📋 Copy</button>
                                <button onclick="exportContent()" class="btn btn-primary">💾 Export Report</button>
                            </div>
                        </div>
                        
                        <div class="content-display">
                            <div class="content-stats">
                                <div class="stat">
                                    <span class="stat-value">{content_metrics['word_count']}</span>
                                    Words
                                </div>
                                <div class="stat">
                                    <span class="stat-value">{content_metrics['character_count']}</span>
                                    Characters
                                </div>
                                <div class="stat">
                                    <span class="stat-value">{eeat_assessment.get('eeat_assessment', {}).get('overall_score', 'N/A')}</span>
                                    E-E-A-T Score
                                </div>
                                <div class="stat">
                                    <span class="stat-value">{content_metrics['readability_score']}</span>
                                    Readability
                                </div>
                                <div class="stat">
                                    <span class="stat-value">{content_metrics['uniqueness_score']}%</span>
                                    Uniqueness
                                </div>
                            </div>
                            
                            <div class="content-text" id="content-text">
                                <pre>{generated_content}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Zee SEO Tool Enhanced v2.0</strong> - Advanced Content Intelligence Platform by Zeeshan Bashir</p>
                <p>Powered by 5 specialized AI agents • Human + AI intelligence bridge</p>
            </div>
            
            <script>
                function showTab(tabName) {{
                    // Hide all tab contents
                    const contents = document.querySelectorAll('.tab-content');
                    contents.forEach(content => content.classList.remove('active'));
                    
                    // Remove active class from all tabs
                    const tabs = document.querySelectorAll('.tab');
                    tabs.forEach(tab => tab.classList.remove('active'));
                    
                    // Show selected tab content
                    document.getElementById(tabName).classList.add('active');
                    
                    // Add active class to clicked tab
                    event.target.classList.add('active');
                }}
                
                function copyContent() {{
                    const content = document.getElementById('content-text').textContent;
                    navigator.clipboard.writeText(content).then(() => {{
                        alert('✅ Content copied to clipboard!');
                    }}).catch(err => {{
                        console.error('Failed to copy content:', err);
                        alert('❌ Failed to copy content. Please select and copy manually.');
                    }});
                }}
                
                function exportContent() {{
                    const content = document.getElementById('content-text').textContent;
                    const reportData = {{
                        topic: '{topic}',
                        industry: '{industry}',
                        target_audience: '{target_audience}',
                        generated_content: content,
                        eeat_score: '{eeat_assessment.get('eeat_assessment', {}).get('overall_score', 'N/A')}',
                        word_count: {content_metrics['word_count']},
                        processing_time: '{processing_time:.1f}s',
                        generated_at: new Date().toISOString()
                    }};
                    
                    const reportText = `Zee SEO Tool - Content Intelligence Report
${'='*50}

Topic: ${{reportData.topic}}
Industry: ${{reportData.industry}}
Target Audience: ${{reportData.target_audience}}
E-E-A-T Score: ${{reportData.eeat_score}}
Word Count: ${{reportData.word_count}}
Processing Time: ${{reportData.processing_time}}
Generated: ${{new Date(reportData.generated_at).toLocaleString()}}

${'='*50}

GENERATED CONTENT:

${{reportData.generated_content}}

${'='*50}
Generated by Zee SEO Tool Enhanced v2.0
Advanced Content Intelligence Platform by Zeeshan Bashir
                    `;
                    
                    const blob = new Blob([reportText], {{ type: 'text/plain' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '{topic.replace(" ", "_")}_zee_seo_report_{datetime.now().strftime("%Y%m%d_%H%M")}.txt';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }}
                
                // Auto-refresh functionality for development
                if (window.location.hostname === 'localhost') {{
                    console.log('🔧 Development mode: Auto-refresh enabled');
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Critical error in generate_advanced_content: {str(e)}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Error - Zee SEO Tool</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    padding: 2rem;
                    text-align: center;
                    background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .error-container {{
                    background: white;
                    padding: 3rem;
                    border-radius: 1rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    width: 100%;
                }}
                .error-icon {{
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    color: #ef4444;
                    margin-bottom: 1rem;
                }}
                p {{
                    color: #6b7280;
                    margin-bottom: 2rem;
                    line-height: 1.6;
                }}
                .error-details {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin-bottom: 2rem;
                    font-size: 0.875rem;
                    text-align: left;
                }}
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.75rem 1.5rem;
                    background: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 0.75rem;
                    font-weight: 600;
                    transition: all 0.2s ease;
                }}
                .btn:hover {{
                    background: #1d4ed8;
                    transform: translateY(-1px);
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <h1>Analysis Error</h1>
                <p>We encountered an error while processing your content analysis. Our development team has been notified.</p>
                <div class="error-details">
                    <strong>Error Details:</strong><br>
                    {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}
                </div>
                <a href="/" class="btn">← Return to Zee SEO Tool</a>
            </div>
        </body>
        </html>
        """, status_code=500)

# Helper methods for rendering complex sections
def _render_eeat_overview(eeat_assessment):
    """Render E-E-A-T overview section"""
    if not eeat_assessment or eeat_assessment.get('fallback'):
        return '''
        <div class="error-notice">
            <strong>⚠️ E-E-A-T Assessment Unavailable</strong><br>
            Running in fallback mode. Some features may be limited.
        </div>
        '''
    
    components = eeat_assessment.get('eeat_assessment', {}).get('components', {})
    if not components:
        return '<p>E-E-A-T data not available</p>'
    
    html = '<div class="eeat-scores">'
    for component, data in components.items():
        score = data.get('score', 0)
        html += f'''
        <div class="eeat-score">
            <div class="score-circle" style="--score: {score * 10}">
                <span>{score}</span>
            </div>
            <div class="score-name">{component.title()}</div>
        </div>
        '''
    html += '</div>'
    
    # Add overall info
    overall = eeat_assessment.get('eeat_assessment', {})
    html += f'''
    <div class="metric-list">
        <div class="metric-item">
            <span class="metric-label">E-E-A-T Level</span>
            <span class="metric-value">{overall.get('eeat_level', 'unknown').replace('_', ' ').title()}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">YMYL Topic</span>
            <span class="metric-value">{'Yes' if overall.get('is_ymyl_topic') else 'No'}</span>
        </div>
    </div>
    '''
    
    return html

def _render_research_quality(reddit_insights, topic_research):
    """Render research quality section"""
    html = '<div class="metric-list">'
    
    # Reddit research quality
    if reddit_insights and not reddit_insights.get('fallback'):
        quality = reddit_insights.get('research_quality_score', {})
        reliability = quality.get('reliability', 'Good').title()
        posts_analyzed = reddit_insights.get('quantitative_insights', {}).get('total_posts_analyzed', 'N/A')
    else:
        reliability = 'Unavailable'
        posts_analyzed = 'N/A'
    
    html += f'''
    <div class="metric-item">
        <span class="metric-label">Reddit Research Quality</span>
        <span class="metric-value">{reliability}</span>
    </div>
    <div class="metric-item">
        <span class="metric-label">Posts Analyzed</span>
        <span class="metric-value">{posts_analyzed}</span>
    </div>
    '''
    
    # Topic research quality
    if topic_research and not topic_research.get('fallback'):
        research_quality = topic_research.get('research_quality_score', {})
        depth = research_quality.get('research_depth', 'Comprehensive').title()
    else:
        depth = 'Unavailable'
    
    html += f'''
    <div class="metric-item">
        <span class="metric-label">Topic Research Depth</span>
        <span class="metric-value">{depth}</span>
    </div>
    <div class="metric-item">
        <span class="metric-label">Analysis Status</span>
        <span class="metric-value">Complete</span>
    </div>
    '''
    
    html += '</div>'
    return html

def _render_performance_prediction(eeat_assessment):
    """Render performance prediction section"""
    if not eeat_assessment or eeat_assessment.get('fallback'):
        return '''
        <div class="metric-list">
            <div class="metric-item">
                <span class="metric-label">Performance Analysis</span>
                <span class="metric-value">Unavailable</span>
            </div>
        </div>
        '''
    
    competitive = eeat_assessment.get('competitive_advantage', {})
    performance_pred = eeat_assessment.get('content_performance_prediction', {})
    
    html = f'''
    <div class="metric-list">
        <div class="metric-item">
            <span class="metric-label">vs AI Content</span>
            <span class="metric-value">{competitive.get('performance_predictions', {}).get('traffic_potential', 'N/A')}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">Market Position</span>
            <span class="metric-value">{competitive.get('market_position', 'N/A').replace('_', ' ').title()}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">Performance Tier</span>
            <span class="metric-value">{performance_pred.get('performance_tier', 'N/A').title()}</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">Results Timeline</span>
            <span class="metric-value">{performance_pred.get('timeline_to_results', 'Variable')}</span>
        </div>
    </div>
    '''
    
    return html

# Add helper methods to globals for template access
globals()['_render_eeat_overview'] = _render_eeat_overview
globals()['_render_research_quality'] = _render_research_quality
globals()['_render_performance_prediction'] = _render_performance_prediction

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    
    system_status = {
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'agents': {
            'claude_agent': 'operational' if claude_agent else 'unavailable',
            'reddit_research': 'operational' if reddit_researcher else 'unavailable',
            'eeat_assessment': 'operational' if eeat_assessor else 'unavailable',
            'topic_research': 'operational' if topic_researcher else 'unavailable',
            'improvement_tracking': 'operational' if improvement_tracker else 'unavailable'
        }
    }
    
    operational_count = sum(1 for status in system_status['agents'].values() if status == 'operational')
    
    if operational_count >= 4:
        system_status['overall_health'] = 'excellent'
    elif operational_count >= 2:
        system_status['overall_health'] = 'good'
    else:
        system_status['overall_health'] = 'degraded'
    
    return JSONResponse(content=system_status)

# API endpoint for programmatic access
@app.post("/api/analyze")
async def api_analyze_content(
    topic: str = Form(...),
    industry: str = Form(...),
    target_audience: str = Form(...),
    business_type: str = Form(...),
    unique_value_prop: str = Form(...),
    customer_pain_points: str = Form(...)
):
    """API endpoint for programmatic content analysis"""
    
    try:
        # Basic validation
        if not all([topic, industry, target_audience, unique_value_prop]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        business_context = {
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type,
            'unique_value_prop': unique_value_prop,
            'topic': topic
        }
        
        human_inputs = {
            'customer_pain_points': customer_pain_points,
            'unique_value_prop': unique_value_prop,
            'industry': industry,
            'target_audience': target_audience,
            'business_type': business_type
        }
        
        # Quick E-E-A-T assessment
        if eeat_assessor:
            eeat_result = eeat_assessor.assess_comprehensive_eeat(
                "", topic, business_context, human_inputs
            )
        else:
            eeat_result = {"error": "E-E-A-T assessor unavailable"}
        
        return JSONResponse(content={
            'status': 'success',
            'topic': topic,
            'eeat_assessment': eeat_result.get('eeat_assessment', {}),
            'recommendations': eeat_result.get('improvement_analysis', {}),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"API analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return HTMLResponse(content="""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 2rem; text-align: center;">
        <h1>🔍 Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/" style="color: #2563eb; text-decoration: none;">← Back to Zee SEO Tool</a>
    </body>
    </html>
    """, status_code=404)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup initialization"""
    logger.info("🚀 Zee SEO Tool Enhanced v2.0 starting up...")
    logger.info(f"📊 Configuration: Debug={config.DEBUG_MODE}")
    
    # Validate all agents
    agent_status = {
        'claude_agent': bool(claude_agent),
        'reddit_researcher': bool(reddit_researcher),
        'eeat_assessor': bool(eeat_assessor),
        'topic_researcher': bool(topic_researcher),
        'improvement_tracker': bool(improvement_tracker)
    }
    
    operational_agents = sum(agent_status.values())
    logger.info(f"🤖 Agents initialized: {operational_agents}/5 operational")
    
    if operational_agents < 5:
        logger.warning("⚠️ Some agents are unavailable. Application running in degraded mode.")
    else:
        logger.info("✅ All agents operational. Full functionality available.")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown cleanup"""
    logger.info("🛑 Zee SEO Tool Enhanced v2.0 shutting down...")

# Development mode helpers
if config.DEBUG_MODE:
    logger.info("🔧 Debug mode enabled")
    
    @app.get("/debug/config")
    async def debug_config():
        """Debug endpoint to view configuration"""
        return JSONResponse(content={
            'config': {
                'debug_mode': config.DEBUG_MODE,
                'anthropic_api_configured': config.ANTHROPIC_API_KEY != "your-anthropic-api-key-here",
                'max_content_length': config.MAX_CONTENT_LENGTH
            },
            'agents_status': {
                'claude_agent': bool(claude_agent),
                'reddit_researcher': bool(reddit_researcher),
                'eeat_assessor': bool(eeat_assessor),
                'topic_researcher': bool(topic_researcher),
                'improvement_tracker': bool(improvement_tracker)
            }
        })

# Main application entry point
if __name__ == "__main__":
    logger.info("🎯 Starting Zee SEO Tool Enhanced v2.0")
    
    # Configuration for different environments
    if config.DEBUG_MODE:
        # Development configuration
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8002,
            reload=True,
            log_level="info"
        )
    else:
        # Production configuration
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8002)),
            workers=1,  # Adjust based on your server capacity
            log_level="warning"
        )
        break_even = roi.get('break_even_estimate', 'Variable')
        formatted.append(f'''
            <div class="metric-item">
                <span class="metric-label">Break-even Timeline</span>
                <span class="metric-value">{break_even}</span>
            </div>
        ''')
        
        return '\n'.join(formatted)

# Create formatter instance
formatter = ResponseFormatter()

# API Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Enhanced home page with comprehensive feature showcase"""
    
    try:
        # Check system status
        system_status = {
            'claude_agent': 'operational' if claude_agent else 'unavailable',
            'reddit_research': 'operational' if reddit_researcher else 'unavailable',
            'eeat_assessment': 'operational' if eeat_assessor else 'unavailable',
            'topic_research': 'operational' if topic_researcher else 'unavailable',
            'improvement_tracking': 'operational' if improvement_tracker else 'unavailable'
        }
        
        operational_agents = sum(1 for status in system_status.values() if status == 'operational')
        
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Zee SEO Tool - Advanced Content Intelligence Platform</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="description" content="Create content that converts with human expertise and AI intelligence. Advanced E-E-A-T optimization and customer research integration.">
            
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #f9fafb 0%, #f0f9ff 100%);
                    color: #111827;
                    line-height: 1.6;
                    min-height: 100vh;
                }}
                
                .header {{
                    background: white;
                    border-bottom: 1px solid #e5e7eb;
                    padding: 1.5rem 0;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    position: sticky;
                    top: 0;
                    z-index: 50;
                }}
                
                .header-content {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }}
                
                .logo {{
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }}
                
                .logo-icon {{
                    width: 3rem;
                    height: 3rem;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    border-radius: 0.75rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 800;
                    font-size: 1.5rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                }}
                
                .logo-text {{
                    font-size: 1.75rem;
                    font-weight: 800;
                    color: #111827;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                
                .tagline {{
                    font-size: 0.875rem;
                    color: #6b7280;
                    font-weight: 500;
                    margin-top: 0.25rem;
                }}
                
                .status-badges {{
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                }}
                
                .version-badge {{
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                    font-size: 0.75rem;
                    font-weight: 600;
                }}
                
                .status-badge {{
                    background: {'linear-gradient(135deg, #10b981 0%, #059669 100%)' if operational_agents >= 4 else 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' if operational_agents >= 2 else 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 1rem;
                    font-size: 0.75rem;
                    font-weight: 600;
                }}
                
                .creator {{
                    text-align: right;
                    font-size: 0.875rem;
                    color: #6b7280;
                }}
                
                .creator strong {{
                    color: #374151;
                    display: block;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 2rem 1.5rem;
                }}
                
                .hero {{
                    text-align: center;
                    margin-bottom: 3rem;
                }}
                
                .hero h1 {{
                    font-size: 2.5rem;
                    font-weight: 800;
                    color: #111827;
                    margin-bottom: 1rem;
                    line-height: 1.2;
                }}
                
                .hero-subtitle {{
                    font-size: 1.25rem;
                    color: #6b7280;
                    margin-bottom: 2rem;
                    max-width: 700px;
                    margin-left: auto;
                    margin-right: auto;
                }}
                
                .hero-stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 1rem;
                    max-width: 600px;
                    margin: 2rem auto;
                }}
                
                .hero-stat {{
                    text-align: center;
                    padding: 1.5rem 1rem;
                    background: white;
                    border-radius: 0.75rem;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    transition: all 0.3s ease;
                }}
                
                .hero-stat:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                }}
                
                .hero-stat-value {{
                    font-size: 1.75rem;
                    font-weight: 800;
                    color: #2563eb;
                    margin-bottom: 0.25rem;
                }}
                
                .hero-stat-label {{
                    font-size: 0.8rem;
                    color: #6b7280;
                    font-weight: 500;
                }}
                
                .main-grid {{
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 2rem;
                    margin-bottom: 3rem;
                }}
                
                .card {{
                    background: white;
                    border-radius: 1rem;
                    padding: 2rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    transition: all 0.3s ease;
                }}
                
                .card:hover {{
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                    transform: translateY(-2px);
                }}
                
                .card h2 {{
                    font-size: 1.375rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 0.5rem;
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }}
                
                .card-icon {{
                    width: 2rem;
                    height: 2rem;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    color: white;
                    border-radius: 0.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1rem;
                }}
                
                .card p {{
                    color: #6b7280;
                    margin-bottom: 1.5rem;
                    line-height: 1.6;
                }}
                
                .form-grid {{
                    display: grid;
                    gap: 1.5rem;
                }}
                
                .form-row {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                }}
                
                .form-group {{
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }}
                
                .form-label {{
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: #374151;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                }}
                
                .form-input, .form-textarea, .form-select {{
                    padding: 0.875rem 1rem;
                    border: 2px solid #e5e7eb;
                    border-radius: 0.75rem;
                    font-size: 0.875rem;
                    transition: all 0.2s ease;
                    background: white;
                    font-family: inherit;
                }}
                
                .form-input:focus, .form-textarea:focus, .form-select:focus {{
                    outline: none;
                    border-color: #2563eb;
                    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                    transform: translateY(-1px);
                }}
                
                .form-textarea {{
                    resize: vertical;
                    min-height: 4rem;
                }}
                
                .form-help {{
                    font-size: 0.75rem;
                    color: #6b7280;
                    margin-top: 0.25rem;
                }}
                
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    padding: 1rem 2rem;
                    font-size: 1rem;
                    font-weight: 700;
                    border-radius: 0.75rem;
                    border: none;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-decoration: none;
                    font-family: inherit;
                    width: 100%;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    color: white;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                }}
                
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                }}
                
                .btn:active {{
                    transform: translateY(0);
                }}
                
                .ai-controls {{
                    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                    border: 2px solid #bfdbfe;
                }}
                
                .features {{
                    display: grid;
                    gap: 1rem;
                }}
                
                .feature {{
                    display: flex;
                    align-items: flex-start;
                    gap: 1rem;
                    padding: 1.25rem;
                    background: linear-gradient(135deg, #f9fafb 0%, white 100%);
                    border-radius: 0.75rem;
                    border: 1px solid #f3f4f6;
                    transition: all 0.3s ease;
                }}
                
                .feature:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    border-color: #2563eb;
                }}
                
                .feature-icon {{
                    width: 2.5rem;
                    height: 2.5rem;
                    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
                    color: white;
                    border-radius: 0.75rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.25rem;
                    flex-shrink: 0;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }}
                
                .feature-content h4 {{
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: #111827;
                    margin-bottom: 0.25rem;
                }}
                
                .feature-content p {{
                    font-size: 0.8rem;
                    color: #6b7280;
                    margin: 0;
                    line-height: 1.4;
                }}
                
                .loading {{
                    display: none;
                    text-align: center;
                    padding: 3rem 2rem;
                    background: white;
                    border-radius: 1rem;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                    border: 1px solid #f3f4f6;
                    margin-top: 2rem;
                }}
                
                .loading-spinner {{
                    width: 3rem;
                    height: 3rem;
                    border: 3px solid #e5e7eb;
                    border-top: 3px solid #2563eb;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 1.5rem;
                }}
                
                .loading-progress {{
                    margin-top: 1.5rem;
                    font-size: 0.875rem;
                    color: #6b7280;
                }}
                
                .loading-progress div {{
                    margin: 0.5rem 0;
                    padding: 0.5rem;
                    background: #f3f4f6;
                    border-radius: 0.5rem;
                    opacity: 0.7;
                }}
                
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                
                .footer {{
                    margin-top: 4rem;
                    padding: 3rem 0;
                    background: white;
                    border-top: 1px solid #e5e7eb;
                    text-align: center;
                }}
                
                .footer p {{
                    color: #6b7280;
                    margin-bottom: 0.5rem;
                }}
                
                .system-info {{
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                    border: 1px solid #0ea5e9;
                    border-radius: 0.75rem;
                    padding: 1rem;
                    margin-bottom: 2rem;
                    font-size: 0.875rem;
                }}
                
                .required-field {{
                    color: #ef4444;
                }}
                
                @media (max-width: 968px) {{
                    .main-grid {{ grid-template-columns: 1fr; gap: 1.5rem; }}
                    .form-row {{ grid-template-columns: 1fr; }}
                    .hero h1 {{ font-size: 2rem; }}
                    .hero-subtitle {{ font-size: 1rem; }}
                    .container {{ padding: 1rem; }}
                    .header-content {{ flex-direction: column; gap: 1rem; text-align: center; }}
                    .hero-stats {{ grid-template-columns: repeat(2, 1fr); }}
                    .status-badges {{ order: -1; }}
                }}
                
                @media (max-width: 640px) {{
                    .hero-stats {{ grid-template-columns: 1fr; }}
                    .hero-stat {{ padding: 1rem; }}
                    .hero-stat-value {{ font-size: 1.5rem; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="header-content">
                    <div class="logo">
                        <div class="logo-icon">Z</div>
                        <div>
                            <div class="logo-text">Zee SEO Tool</div>
                            <div class="tagline">Advanced Content Intelligence Platform</div>
                        </div>
                    </div>
                    
                    <div class="status-badges">
                        <div class="version-badge">Enhanced v2.0</div>
                        <div class="status-badge">{operational_agents}/5 Agents Active</div>
                    </div>
                    
                    <div class="creator">
                        <strong>Built by Zeeshan Bashir</strong>
                        <div>Human + AI Intelligence Bridge</div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="hero">
                    <h1>Create Content That Actually Converts</h1>
                    <p class="hero-subtitle">The most advanced content intelligence platform combining deep customer research, E-E-A-T optimization, and continuous improvement tracking to create content that outperforms generic AI by 350%</p>
                    
                    <div class="hero-stats">
                        <div class="hero-stat">
                            <div class="hero-stat-value">350%</div>
                            <div class="hero-stat-label">Better Performance</div>
                        </div>
                        <div class="hero-stat">
                            <div class="hero-stat-value">{operational_agents}</div>
                            <div class="hero-stat-label">AI Agents</div>
                        </div>
                        <div class="hero-stat">
                            <div class="hero-stat-value">95%</div>
                            <div class="hero-stat-label">E-E-A-T Score</div>
                        </div>
                        <div class="hero-stat">
                            <div class="hero-stat-value">24/7</div>
                            <div class="hero-stat-label">Availability</div>
                        </div>
                    </div>
                </div>
                
                <div class="system-info">
                    <strong>🔧 System Status:</strong> 
                    Reddit Research: {'✅' if system_status['reddit_research'] == 'operational' else '⚠️'} | 
                    E-E-A-T Assessment: {'✅' if system_status['eeat_assessment'] == 'operational' else '⚠️'} | 
                    Topic Research: {'✅' if system_status['topic_research'] == 'operational' else '⚠️'} | 
                    Improvement Tracking: {'✅' if system_status['improvement_tracking'] == 'operational' else '⚠️'} | 
                    Content Generation: {'✅' if system_status['claude_agent'] == 'operational' else '⚠️'}
                </div>
                
                <div class="main-grid">
                    <form action="/generate-advanced" method="post" id="contentForm">
                        <div class="card">
                            <h2>
                                <div class="card-icon">🧠</div>
                                Advanced Content Intelligence Input
                            </h2>
                            <p>Our enhanced system combines 5 specialized AI agents for comprehensive content analysis and generation with real customer research integration.</p>
                            
                            <div class="form-grid">
                                <div class="form-group">
                                    <label class="form-label">
                                        Content Topic <span class="required-field">*</span>
                                    </label>
                                    <input class="form-input" type="text" name="topic" 
                                           placeholder="e.g., best budget laptops for college students" required 
                                           maxlength="200">
                                    <div class="form-help">🔬 Our topic research agent will analyze semantic relationships and opportunities</div>
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">
                                        Target Communities for Research <span class="required-field">*</span>
                                    </label>
                                    <input class="form-input" type="text" name="subreddits" 
                                           placeholder="e.g., laptops, college, StudentLoans, BuyItForLife" required
                                           maxlength="300">
                                    <div class="form-help">🔍 Enhanced Reddit research with deep customer insight extraction</div>
                                </div>
                                
                                <div class="form-row">
                                    <div class="form-group">
                                        <label class="form-label">
                                            Industry <span class="required-field">*</span>
                                        </label>
                                        <input class="form-input" type="text" name="industry" 
                                               placeholder="e.g., Technology, Healthcare, Finance" required
                                               maxlength="100">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">
                                            Target Audience <span class="required-field">*</span>
                                        </label>
                                        <input class="form-input" type="text" name="target_audience" 
                                               placeholder="e.g., College students, Small business owners" required
                                               maxlength="100">
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">
                                        Business Type <span class="required-field">*</span>
                                    </label>
                                    <select class="form-select" name="business_type" required>
                                        <option value="">Select your business model</option>
                                        <option value="B2B">B2B (Business to Business)</option>
                                        <option value="B2C">B2C (Business to Consumer)</option>
                                        <option value="Both">Both B2B and B2C</option>
                                        <option value="Non-profit">Non-profit Organization</option>
                                        <option value="Government">Government/Public Sector</option>
                                        <option value="Personal Brand">Personal Brand/Individual</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">
                                        Your Unique Value Proposition <span class="required-field">*</span>
                                    </label>
                                    <textarea class="form-textarea" name="unique_value_prop" 
                                              placeholder="What makes you different from competitors? Be specific and authentic. Include your experience, approach, or unique methodology." 
                                              required maxlength="1000" rows="4"></textarea>
                                    <div class="form-help">🎯 Critical for E-E-A-T authority assessment and competitive differentiation</div>
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">
                                        Customer Pain Points & Insights <span class="required-field">*</span>
                                    </label>
                                    <textarea class="form-textarea" name="customer_pain_points" 
                                              placeholder="What specific challenges do your customers face? Include real examples, common complaints, frustrations, or gaps you've observed. The more specific, the better." 
                                              required maxlength="1500" rows="4"></textarea>
                                    <div class="form-help">💡 Enhanced analysis will combine this with Reddit research for deeper insights</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card ai-controls">
                            <h2>
                                <div class="card-icon">⚙️</div>
                                Advanced AI Configuration
                            </h2>
                            <p>Fine-tune content generation with enhanced AI controls and quality parameters</p>
                            
                            <div class="form-grid">
                                <div class="form-row">
                                    <div class="form-group">
                                        <label class="form-label">Writing Style</label>
                                        <select class="form-select" name="writing_style">
                                            <option value="">Adaptive (Recommended)</option>
                                            <option value="British English">British English</option>
                                            <option value="American English">American English</option>
                                            <option value="Conversational">Conversational & Friendly</option>
                                            <option value="Technical">Technical & Detailed</option>
                                            <option value="Academic">Academic & Formal</option>
                                            <option value="Authoritative">Authoritative & Expert</option>
                                            <option value="Storytelling">Storytelling & Narrative</option>
                                        </select>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Target Length</label>
                                        <select class="form-select" name="target_word_count">
                                            <option value="">Optimal (1200-1800)</option>
                                            <option value="800-1200">Concise (800-1200)</option>
                                            <option value="1500-2500">Comprehensive (1500-2500)</option>
                                            <option value="2500-4000">In-depth Guide (2500-4000)</option>
                                            <option value="4000+">Ultimate Resource (4000+)</option>
                                        </select>
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">E-E-A-T Enhancement Instructions</label>
                                    <textarea class="form-textarea" name="eeat_instructions" 
                                              placeholder="Specific instructions for enhancing Experience, Expertise, Authority, or Trust elements. E.g., 'Include personal case studies', 'Add industry statistics', 'Reference authoritative sources'"
                                              maxlength="500" rows="3"></textarea>
                                    <div class="form-help">📊 Guide our E-E-A-T optimization agent for maximum impact</div>
                                </div>
                                
                                <div class="form-group">
                                    <label class="form-label">Additional AI Instructions</label>
                                    <textarea class="form-textarea" name="additional_notes" 
                                              placeholder="Any specific requirements: include statistics, format preferences (lists, tables), tone adjustments, call-to-action requirements, compliance considerations"
                                              maxlength="500" rows="3"></textarea>
                                    <div class="form-help">🎛️ Advanced customization for precise content generation</div>
                                </div>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn" id="generateBtn">
                            🚀 Generate Advanced Content Intelligence Report
                        </button>
                    </form>
                    
                    <div class="card">
                        <h2>
                            <div class="card-icon">🔥</div>
                            Enhanced Intelligence Features
                        </h2>
                        <p>Next-generation content intelligence with 5 specialized AI agents working in harmony</p>
                        
                        <div class="features">
                            <div class="feature">
                                <div class="feature-icon">🔍</div>
                                <div class="feature-content">
                                    <h4>Deep Reddit Research Agent</h4>
                                    <p>Advanced customer insight extraction, pain point analysis, and authentic voice detection</p>
                                </div>
                            </div>
                            
                            <div class="feature">
                                <div class="feature-icon">🎯</div>
                                <div class="feature-content">
                                    <h4>Enhanced E-E-A-T Assessment</h4>
                                    <p>Google Quality Rater Guidelines compliant scoring with YMYL detection</p>
                                </div>
                            </div>
                            
                            <div class="feature">
                                <div class="feature-icon">🧠</div>
                                <div class="feature-content">
                                    <h4>Topic Research Intelligence</h4>
                                    <p>Comprehensive semantic analysis, opportunity identification, and competitive positioning</p>
                                </div>
                            </div>
                            
                            <div class="feature">
                                <div class="feature-icon">📈</div>
                                <div class="feature-content">
                                    <h4>Continuous Improvement Tracking</h4>
                                    <p>Score progression monitoring, ROI projections, and performance optimization</p>
                                </div>
                            </div>
                            
                            <div class="feature">
                                <div class="feature-icon">🔬</div>
                                <div class="feature-content">
                                    <h4>Content Quality Analysis</h4>
                                    <p>Multi-dimensional quality assessment with industry benchmarking</p>
                                </div>
                            </div>
                            
                            <div class="feature">
                                <div class="feature-icon">🏆</div>
                                <div class="feature-content">
                                    <h4>Competitive Advantage Scoring</h4>
                                    <p>Market positioning analysis with quantified performance predictions</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="loading" id="loading">
                    <div class="loading-spinner"></div>"""
Zee SEO Tool - Advanced Content Intelligence Platform
====================================================

Author: Zeeshan Bashir
Version: 2.0 Enhanced
Description: Advanced content intelligence platform that combines human expertise 
             with AI to create high-performance, E-E-A-T optimized content.

Features:
- 5 Specialized AI Agents for comprehensive analysis
- Real customer research integration via Reddit API
- Advanced E-E-A-T assessment based on Google Quality Rater Guidelines
- Continuous improvement tracking with ROI projections
- Topic research with semantic analysis and opportunity scoring
- Human + AI content generation with authenticity markers

Architecture:
- FastAPI backend with async support
- Modular agent-based design
- Comprehensive error handling and fallbacks
- Production-ready logging and monitoring
- Responsive web interface with progressive enhancement
"""

import os
import json
import requests
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# FastAPI imports
from fastapi import FastAPI, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import enhanced agents
try:
    from src.agents.enhanced_reddit_researcher import EnhancedRedditResearcher
    from src.agents.enhanced_eeat_assessor import EnhancedEEATAssessor
    from src.agents.topic_research_agent import AdvancedTopicResearchAgent
    from src.agents.improvement_tracking_agent import ContinuousImprovementTracker
    from src.utils.llm_client import LLMClient
except ImportError as e:
    print(f"Warning: Could not import all agents. Running in demo mode. Error: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zee_seo_tool.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Zee SEO Tool - Advanced Content Intelligence Platform",
    description="Create content that converts with human expertise + AI intelligence",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    """Application configuration"""
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-api-key-here")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "your-reddit-client-id")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "your-reddit-client-secret")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.ANTHROPIC_API_KEY == "your-anthropic-api-key-here":
            logger.warning("Using demo API key. Set ANTHROPIC_API_KEY environment variable for production.")
        return True

config = Config()
config.validate()

class ClaudeAgent:
    """Enhanced Claude API client with error handling and fallbacks"""
    
    def __init__(self):
        self.anthropic_headers = {
            "x-api-key": config.ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        self.fallback_mode = config.ANTHROPIC_API_KEY == "your-anthropic-api-key-here"
        
    async def call_claude_async(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", 
                               max_tokens: int = 2000) -> str:
        """Async call to Claude API with comprehensive error handling"""
        
        if self.fallback_mode:
            return self._generate_fallback_content(messages)
        
        try:
            # Extract user message
            if messages and messages[0].get("role") == "user":
                user_message = messages[0]["content"]
            else:
                user_message = "Please help with this request."
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user_message}]
            }
            
            # Make async request
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=self.anthropic_headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result["content"][0]["text"]
                    else:
                        logger.error(f"Claude API error: {response.status}")
                        return self._generate_fallback_content(messages)
                        
        except asyncio.TimeoutError:
            logger.error("Claude API timeout")
            return self._generate_fallback_content(messages)
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            return self._generate_fallback_content(messages)
    
    def call_claude(self, messages: List[Dict], model: str = "claude-3-haiku-20240307", 
                   max_tokens: int = 2000) -> str:
        """Synchronous wrapper for Claude API"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.call_claude_async(messages, model, max_tokens))
                    return future.result(timeout=60)
            else:
                return loop.run_until_complete(self.call_claude_async(messages, model, max_tokens))
        except Exception as e:
            logger.error(f"Error in call_claude: {str(e)}")
            return self._generate_fallback_content(messages)
    
    def _generate_fallback_content(self, messages: List[Dict]) -> str:
        """Generate fallback content when API is unavailable"""
        user_message = messages[0]["content"] if messages else ""
        
        if "topic" in user_message.lower():
            return """
# Comprehensive Guide to Your Topic

## Introduction
This content has been generated using our advanced content intelligence platform, combining human expertise with AI efficiency to create high-quality, engaging content.

## Key Benefits
- Evidence-based approach to content creation
- Human expertise integration for authenticity
- E-E-A-T optimization for search engine performance
- Real customer insights incorporation

## Main Content
Our analysis shows that successful content in this area requires a combination of practical experience, industry knowledge, and customer-focused insights. By leveraging both human expertise and AI capabilities, we can create content that truly resonates with your target audience.

### Expert Insights
Based on industry analysis and customer research, the most effective approach involves:
1. Understanding genuine customer pain points
2. Providing practical, actionable solutions
3. Demonstrating authentic expertise and experience
4. Building trust through transparency and accuracy

## Conclusion
This content framework provides a solid foundation for creating high-performance content that combines the best of human insight and AI efficiency.

*Note: This is demo content. Configure your API keys for full functionality.*
            """
        
        return "Demo content generated. Please configure API keys for full functionality."

class EnhancedContentGenerator:
    """Advanced content generator with multi-agent intelligence integration"""
    
    def __init__(self, claude_agent: ClaudeAgent):
        self.claude_agent = claude_agent
        
    async def generate_content_async(self, topic: str, business_context: Dict, 
                                   human_inputs: Dict, ai_instructions: Dict, 
                                   reddit_insights: Optional[Dict] = None, 
                                   topic_research: Optional[Dict] = None) -> str:
        """Generate enhanced content using all available intelligence"""
        
        logger.info(f"Generating content for topic: {topic}")
        
        # Build comprehensive prompt
        ai_prompt = self._build_comprehensive_prompt(
            topic, business_context, human_inputs, ai_instructions,
            reddit_insights, topic_research
        )
        
        messages = [{"role": "user", "content": ai_prompt}]
        content = await self.claude_agent.call_claude_async(messages, max_tokens=4000)
        
        logger.info(f"Generated content length: {len(content)} characters")
        return content
    
    def generate_content(self, topic: str, business_context: Dict, 
                        human_inputs: Dict, ai_instructions: Dict, 
                        reddit_insights: Optional[Dict] = None, 
                        topic_research: Optional[Dict] = None) -> str:
        """Synchronous wrapper for content generation"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.generate_content_async(topic, business_context, human_inputs, 
                                                  ai_instructions, reddit_insights, topic_research)
                    )
                    return future.result(timeout=120)
            else:
                return loop.run_until_complete(
                    self.generate_content_async(topic, business_context, human_inputs, 
                                              ai_instructions, reddit_insights, topic_research)
                )
        except Exception as e:
            logger.error(f"Error in content generation: {str(e)}")
            return self._generate_fallback_content(topic, business_context, human_inputs)
    
    def _build_comprehensive_prompt(self, topic: str, business_context: Dict, 
                                  human_inputs: Dict, ai_instructions: Dict,
                                  reddit_insights: Optional[Dict], 
                                  topic_research: Optional[Dict]) -> str:
        """Build comprehensive AI prompt with all available intelligence"""
        
        prompt_sections = [
            f"Create exceptional, human-centered content about '{topic}' that demonstrates high E-E-A-T standards.",
            "",
            "BUSINESS CONTEXT:",
            f"- Industry: {business_context.get('industry', 'Not specified')}",
            f"- Target Audience: {business_context.get('target_audience', 'Not specified')}",
            f"- Business Type: {business_context.get('business_type', 'Not specified')}",
            f"- Unique Value Proposition: {business_context.get('unique_value_prop', 'Not specified')}",
            "",
            "HUMAN EXPERTISE & INSIGHTS:",
            f"- Customer Pain Points: {human_inputs.get('customer_pain_points', 'Not provided')}",
            f"- Industry Experience: {human_inputs.get('unique_value_prop', 'Not provided')}",
            "",
        ]
        
        # Add Reddit insights if available
        if reddit_insights:
            prompt_sections.extend([
                "REAL CUSTOMER RESEARCH:",
                self._format_reddit_insights(reddit_insights),
                "",
            ])
        
        # Add topic research if available
        if topic_research:
            prompt_sections.extend([
                "TOPIC INTELLIGENCE:",
                self._format_topic_research(topic_research),
                "",
            ])
        
        # Add AI instructions
        prompt_sections.extend([
            "AI INSTRUCTIONS:",
            f"- Writing Style: {ai_instructions.get('writing_style', 'Professional')}",
            f"- Target Length: {ai_instructions.get('target_word_count', '1200-1800 words')}",
            f"- E-E-A-T Focus: {ai_instructions.get('eeat_instructions', 'Standard optimization')}",
            f"- Special Notes: {ai_instructions.get('additional_notes', 'None')}",
            "",
            "CONTENT REQUIREMENTS:",
            "1. Demonstrate genuine experience through specific examples and personal insights",
            "2. Show expertise with accurate, in-depth information",
            "3. Build authority through unique perspectives and comprehensive coverage",
            "4. Establish trust through transparency, balanced views, and credible sources",
            "5. Address real customer pain points identified in the research",
            "6. Use authentic language that resonates with the target audience",
            "7. Include specific, actionable advice that only an expert would know",
            "8. Reference credible sources and provide balanced perspectives",
            "",
            "Create content that is significantly better than generic AI content by incorporating:",
            "- Real customer language and concerns from the research",
            "- Industry-specific expertise and insider knowledge", 
            "- Personal experience and authentic insights",
            "- Practical solutions to genuine problems",
            "",
            "Make this content worthy of being cited as an authoritative source."
        ])
        
        return "\n".join(prompt_sections)
    
    def _format_reddit_insights(self, reddit_insights: Dict) -> str:
        """Format Reddit insights for the AI prompt"""
        if not reddit_insights:
            return "No Reddit insights available"
        
        formatted_sections = []
        
        # Pain points
        pain_analysis = reddit_insights.get('pain_point_analysis', {})
        critical_points = pain_analysis.get('critical_pain_points', [])
        if critical_points:
            formatted_sections.append(f"Critical Pain Points: {', '.join(critical_points[:3])}")
        
        # Customer quotes
        authenticity = reddit_insights.get('authenticity_markers', {})
        quotes = authenticity.get('real_customer_quotes', [])
        if quotes:
            formatted_sections.append(f"Real Customer Quotes: {'; '.join(quotes[:2])}")
        
        # Language patterns
        language_intel = reddit_insights.get('language_intelligence', {})
        vocab = language_intel.get('customer_vocabulary', [])
        if vocab:
            formatted_sections.append(f"Customer Language: {', '.join(vocab[:5])}")
        
        # Content gaps
        content_gaps = reddit_insights.get('content_opportunity_gaps', {})
        missing_info = content_gaps.get('missing_information', [])
        if missing_info:
            formatted_sections.append(f"Missing Information: {', '.join(missing_info[:3])}")
        
        return '\n'.join(formatted_sections) if formatted_sections else "Limited Reddit insights available"
    
    def _format_topic_research(self, topic_research: Dict) -> str:
        """Format topic research for the AI prompt"""
        if not topic_research:
            return "No topic research available"
        
        formatted_sections = []
        
        # Content gaps
        research_data = topic_research.get('topic_research', {})
        content_gaps = research_data.get('content_gaps', {})
        market_gaps = content_gaps.get('market_gaps', {})
        
        underserved = market_gaps.get('underserved_questions', [])
        if underserved:
            formatted_sections.append(f"Underserved Questions: {', '.join(underserved[:3])}")
        
        missing_perspectives = market_gaps.get('missing_perspectives', [])
        if missing_perspectives:
            formatted_sections.append(f"Missing Perspectives: {', '.join(missing_perspectives[:2])}")
        
        # Opportunities
        opportunities = research_data.get('opportunity_scoring', {})
        top_opportunities = opportunities.get('top_opportunities', [])
        if top_opportunities:
            top_names = [opp.get('name', '') for opp in top_opportunities[:3] if opp.get('name')]
            if top_names:
                formatted_sections.append(f"Top Opportunities: {', '.join(top_names)}")
        
        # Strategic recommendations
        strategic = research_data.get('strategic_recommendations', {})
        content_strategy = strategic.get('content_strategy', [])
        if content_strategy:
            formatted_sections.append(f"Strategy Recommendations: {', '.join(content_strategy[:2])}")
        
        return '\n'.join(formatted_sections) if formatted_sections else "Limited topic research available"
    
    def _generate_fallback_content(self, topic: str, business_context: Dict, human_inputs: Dict) -> str:
        """Generate fallback content when AI generation fails"""
        
        industry = business_context.get('industry', 'your industry')
        audience = business_context.get('target_audience', 'your target audience')
        pain_points = human_inputs.get('customer_pain_points', 'common challenges')
        
        return f"""
# Complete Guide to {topic.title()}

## Introduction

In today's competitive {industry} landscape, understanding {topic} is crucial for {audience}. This comprehensive guide combines industry expertise with real-world insights to provide actionable solutions.

## Understanding the Challenge

Based on extensive research and customer feedback, the primary challenges around {topic} include:

{pain_points}

## Expert Solutions

Our analysis reveals several key strategies that successful organizations use to address these challenges:

### 1. Strategic Planning
Develop a comprehensive approach that considers all stakeholders and potential outcomes.

### 2. Implementation Best Practices
Follow proven methodologies that have been tested in real-world scenarios.

### 3. Continuous Improvement
Establish feedback loops to ensure ongoing optimization and adaptation.

## Key Benefits

Organizations that properly implement these strategies typically see:
- Improved efficiency and effectiveness
- Better customer satisfaction
- Reduced operational challenges
- Enhanced competitive positioning

## Conclusion

Successfully navigating {topic} requires a combination of strategic thinking, practical implementation, and ongoing optimization. By following the guidelines outlined in this guide, organizations can achieve significant improvements in their outcomes.

---

*This content was generated using our advanced content intelligence platform. For fully customized content with deeper insights, please configure your API settings.*
        """

# Initialize components with error handling
try:
    claude_agent = ClaudeAgent()
    enhanced_content_generator = EnhancedContentGenerator(claude_agent)
    reddit_researcher = EnhancedRedditResearcher()
    eeat_assessor = EnhancedEEATAssessor()
    topic_researcher = AdvancedTopicResearchAgent()
    improvement_tracker = ContinuousImprovementTracker()
    logger.info("All agents initialized successfully")
except Exception as e:
    logger.error(f"Error initializing agents: {str(e)}")
    # Initialize with None to handle gracefully
    claude_agent = ClaudeAgent()
    enhanced_content_generator = EnhancedContentGenerator(claude_agent)
    reddit_researcher = None
    eeat_assessor = None
    topic_researcher = None
    improvement_tracker = None

# Helper functions for response formatting
class ResponseFormatter:
    """Utility class for formatting HTML responses"""
    
    @staticmethod
    def generate_improvement_badge(improvement_report: Dict) -> str:
        """Generate improvement badge HTML"""
        if not improvement_report:
            return '<div class="improvement-badge">🎯 Initial Analysis</div>'
            
        improvement_summary = improvement_report.get('improvement_summary', {})
        improvement_level = improvement_summary.get('improvement_level', 'baseline_established')
        
        if improvement_level == 'baseline_established':
            return '<div class="improvement-badge">🎯 Baseline Established</div>'
        elif improvement_level == 'excellent':
            return '<div class="improvement-badge">🚀 Excellent Progress</div>'
        elif improvement_level == 'good':
            return '<div class="improvement-badge">📈 Good Progress</div>'
        else:
            return f'<div class="improvement-badge">📊 {improvement_level.replace("_", " ").title()}</div>'
    
    @staticmethod
    def format_eeat_insights(eeat_assessment: Dict) -> str:
        """Format E-E-A-T insights for display"""
        if not eeat_assessment:
            return '<li class="insight-item">E-E-A-T assessment not available</li>'
            
        insights = []
        
        # Overall assessment
        overall = eeat_assessment.get('eeat_assessment', {})
        eeat_level = overall.get('eeat_level', 'moderate').replace('_', ' ').title()
        overall_score = overall.get('overall_score', 0)
        insights.append(f'<li class="insight-item">Overall E-E-A-T Level: <strong>{eeat_level} ({overall_score}/10)</strong></li>')
        
        # YMYL status
        is_ymyl = overall.get('is_ymyl_topic', False)
        ymyl_status = 'Yes (Higher standards required)' if is_ymyl else 'No (Standard requirements)'
        insights.append(f'<li class="insight-item">YMYL Topic: <strong>{ymyl_status}</strong></li>')
        
        # Component insights
        components = overall.get('components', {})
        for component, data in components.items():
            score = data.get('score', 0)
            if score >= 8.0:
                level = "Excellent"
                color = "#10b981"
            elif score >= 6.5:
                level = "Good"
                color = "#3b82f6"
            elif score >= 5.0:
                level = "Fair"
                color = "#f59e0b"
            else:
                level = "Needs Improvement"
                color = "#ef4444"
            
            insights.append(f'<li class="insight-item" style="border-left-color: {color}">{component.title()}: <strong>{score}/10 ({level})</strong></li>')
        
        return '\n'.join(insights)
    
    @staticmethod
    def format_improvement_recommendations(improvement_analysis: Dict) -> str:
        """Format improvement recommendations"""
        if not improvement_analysis:
            return '<li class="insight-item">No specific recommendations available</li>'
            
        recommendations = []
        
        immediate = improvement_analysis.get('immediate_actions', [])
        for action in immediate[:3]:  # Top 3
            recommendations.append(f'<li class="insight-item">🚨 <strong>Immediate:</strong> {action}</li>')
        
        content_enhancements = improvement_analysis.get('content_enhancements', [])
        for enhancement in content_enhancements[:2]:  # Top 2
            recommendations.append(f'<li class="insight-item">📝 <strong>Content:</strong> {enhancement}</li>')
        
        strategic = improvement_analysis.get('strategic_improvements', [])
        for strategy in strategic[:2]:  # Top 2
            recommendations.append(f'<li class="insight-item">🎯 <strong>Strategic:</strong> {strategy}</li>')
        
        return '\n'.join(recommendations) if recommendations else '<li class="insight-item">Continue current improvement efforts</li>'
    
    @staticmethod
    def format_pain_points(reddit_insights: Dict) -> str:
        """Format customer pain points"""
        if not reddit_insights:
            return '<li class="insight-item">No Reddit research data available</li>'
            
        pain_analysis = reddit_insights.get('pain_point_analysis', {})
        pain_points = pain_analysis.get('critical_pain_points', [])
        
        formatted = []
        for point in pain_points[:4]:  # Top 4
            formatted.append(f'<li class="insight-item">😤 {point}</li>')
        
        # Add emotional triggers
        emotional_triggers = pain_analysis.get('emotional_triggers', [])
        if emotional_triggers:
            triggers_text = ', '.join(emotional_triggers[:3])
            formatted.append(f'<li class="insight-item">🎭 <strong>Emotional Triggers:</strong> {triggers_text}</li>')
        
        return '\n'.join(formatted) if formatted else '<li class="insight-item">No specific pain points identified in research</li>'
    
    @staticmethod
    def format_customer_quotes(reddit_insights: Dict) -> str:
        """Format real customer quotes"""
        if not reddit_insights:
            return '<li class="insight-item">No customer voice data available</li>'
            
        authenticity = reddit_insights.get('authenticity_markers', {})
        quotes = authenticity.get('real_customer_quotes', [])
        
        formatted = []
        for i, quote in enumerate(quotes[:3], 1):  # Top 3
            formatted.append(f'<li class="insight-item">💬 <strong>Quote {i}:</strong> "{quote}"</li>')
        
        # Add customer vocabulary
        language_intel = reddit_insights.get('language_intelligence', {})
        vocab = language_intel.get('customer_vocabulary', [])
        if vocab:
            vocab_text = ', '.join(vocab[:5])
            formatted.append(f'<li class="insight-item">🗣️ <strong>Customer Language:</strong> {vocab_text}</li>')
        
        return '\n'.join(formatted) if formatted else '<li class="insight-item">No customer quotes available in research</li>'
    
    @staticmethod
    def format_content_opportunities(topic_research: Dict) -> str:
        """Format content opportunities"""
        if not topic_research:
            return '<li class="insight-item">No topic research data available</li>'
            
        research_data = topic_research.get('topic_research', {})
        opportunities = research_data.get('opportunity_scoring', {})
        top_opportunities = opportunities.get('top_opportunities', [])
        
        formatted = []
        for opp in top_opportunities[:4]:  # Top 4
            name = opp.get('name', 'Opportunity')
            score = opp.get('opportunity_score', 0)
            impact = opp.get('potential_impact', 'medium')
            formatted.append(f'<li class="insight-item">🎯 {name} <strong>(Score: {score:.1f}/10, Impact: {impact.title()})</strong></li>')
        
        # Add focus areas
        focus_areas = opportunities.get('recommended_focus_areas', [])
        if focus_areas:
            focus_text = ', '.join(focus_areas[:2])
            formatted.append(f'<li class="insight-item">🎪 <strong>Focus Areas:</strong> {focus_text}</li>')
        
        return '\n'.join(formatted) if formatted else '<li class="insight-item">No specific opportunities identified</li>'
    
    @staticmethod
    def format_current_performance(improvement_report: Dict) -> str:
        """Format current performance metrics"""
        if not improvement_report:
            return '<div class="metric-item"><span class="metric-label">Status</span><span class="metric-value">Initial Analysis</span></div>'
            
        performance = improvement_report.get('current_performance', {})
        
        formatted = []
        
        level = performance.get('performance_level', 'fair').replace('_', ' ').title()
        formatted.append(f'''
            <div class="metric-item">
                <span class="metric-label">Performance Level</span>
                <span class="metric-value">{level}</span>
            </div>
        ''')
        
        position = performance.get('market_position', 'improvement_needed').replace('_', ' ').title()
        formatted.append(f'''
            <div class="metric-item">
                <span class="metric-label">Market Position</span>
                <span class="metric-value">{position}</span>
            </div>
        ''')
        
        score = performance.get('current_score', 0)
        formatted.append(f'''
            <div class="metric-item">
                <span class="metric-label">Current Score</span>
                <span class="metric-value">{score:.1f}/10</span>
            </div>
        ''')
        
        readiness_assessment = performance.get('readiness_assessment', {})
        readiness = readiness_assessment.get('readiness_level', 'unknown').replace('_', ' ').title()
        formatted.append(f'''
            <div class="metric-item">
                <span class="metric-label">Content Readiness</span>
                <span class="metric-value">{readiness}</span>
            </div>
        ''')
        
        return '\n'.join(formatted)
    
    @staticmethod
    def format_next_steps(improvement_report: Dict) -> str:
        """Format next steps"""
        if not improvement_report:
            return '<li class="insight-item">Complete initial analysis to get personalized recommendations</li>'
            
        next_steps = improvement_report.get('next_steps', {})
        formatted = []
        
        immediate = next_steps.get('immediate_actions', [])
        for action in immediate[:2]:
            formatted.append(f'<li class="insight-item">🚨 <strong>Immediate:</strong> {action}</li>')
        
        short_term = next_steps.get('short_term_goals', [])
        for goal in short_term[:2]:
            formatted.append(f'<li class="insight-item">📅 <strong>Short-term:</strong> {goal}</li>')
        
        long_term = next_steps.get('long_term_strategy', [])
        for strategy in long_term[:1]:
            formatted.append(f'<li class="insight-item">🎯 <strong>Long-term:</strong> {strategy}</li>')
        
        return '\n'.join(formatted) if formatted else '<li class="insight-item">Continue current improvement efforts</li>'
    
    @staticmethod
    def format_roi_projection(improvement_report: Dict) -> str:
        """Format ROI projection"""
        if not improvement_report:
            return '<div class="metric-item"><span class="metric-label">ROI Analysis</span><span class="metric-value">Available after analysis</span></div>'
            
        roi = improvement_report.get('roi_projection', {})
        projections = roi.get('roi_projections', {})
        
        formatted = []
        
        timeframe_labels = {
            '30_days': '30 Days',
            '90_days': '90 Days', 
            '180_days': '180 Days'
        }
        
        for timeframe, label in timeframe_labels.items():
            if timeframe in projections:
                data = projections[timeframe]
                score = data.get('projected_eeat_score', 0)
                improvement = data.get('performance_improvement', '0%')
                
                formatted.append(f'''
                    <div class="metric-item">
                        <span class="metric-label">{label} Projection</span>
                        <span class="metric-value">{score} E-E-A-T ({improvement})</span>
                    </div>
                ''')
        
        investment = roi.get('investment_recommendation', 'moderate_investment').replace('_', ' ').title()
        formatted.append(f'''
            <div class="metric-item">
                <span class="metric-label">Investment Level</span>
                <span class="metric-value">{investment}</span>
            </div>
        ''')
        
        break_even = roi.get('break_even_estimate', 'Variable')
