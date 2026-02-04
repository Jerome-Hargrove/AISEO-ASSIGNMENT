"""Streamlit GUI for SEO Article Generator."""
import streamlit as st
import requests
import time
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="SEO Article Generator",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #00d4aa;
    }
    .article-content {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📝 SEO Article Generator")
st.markdown("Generate SEO-optimized articles using AI-powered competitive analysis")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    api_url = st.text_input("API URL", value=API_BASE_URL)
    
    st.divider()
    st.header("📊 Quick Actions")
    if st.button("🔄 Refresh Jobs"):
        st.rerun()
    
    if st.button("🏥 Health Check"):
        try:
            r = requests.get(f"{api_url}/health", timeout=5)
            if r.status_code == 200:
                st.success("✅ API is healthy!")
            else:
                st.error("❌ API error")
        except:
            st.error("❌ Cannot connect to API")

# Main tabs
tab1, tab2, tab3 = st.tabs(["🆕 Generate Article", "📋 All Jobs", "📖 View Article"])

# Tab 1: Generate New Article
with tab1:
    st.header("Generate New Article")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic = st.text_input(
            "Topic/Keyword",
            placeholder="e.g., best productivity tools for remote teams",
            help="Enter the main topic or keyword for your article"
        )
    
    with col2:
        word_count = st.slider("Target Word Count", 500, 3000, 1500, 100)
    
    language = st.selectbox("Language", ["en", "es", "fr", "de"], index=0)
    
    if st.button("🚀 Generate Article", type="primary", disabled=not topic):
        with st.spinner("Submitting job..."):
            try:
                response = requests.post(
                    f"{api_url}/generate",
                    json={
                        "topic": topic,
                        "target_word_count": word_count,
                        "language": language
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ Job created! ID: `{data['job_id']}`")
                    st.session_state['current_job_id'] = data['job_id']
                    
                    # Auto-track progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    while True:
                        job_response = requests.get(f"{api_url}/jobs/{data['job_id']}")
                        job = job_response.json()
                        
                        progress = job.get('progress_percentage', 0)
                        status = job.get('status', 'unknown')
                        message = job.get('status_message', '')
                        
                        progress_bar.progress(progress / 100)
                        status_text.text(f"Status: {status} - {message}")
                        
                        if status == 'completed':
                            st.balloons()
                            st.success("🎉 Article generated successfully!")
                            break
                        elif status == 'failed':
                            st.error(f"❌ Job failed: {job.get('error_message', 'Unknown error')}")
                            break
                        
                        time.sleep(2)
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

# Tab 2: All Jobs
with tab2:
    st.header("All Jobs")
    
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "pending", "serp_analysis", "outline_generation", "content_generation", "completed", "failed"]
    )
    
    try:
        url = f"{api_url}/jobs"
        if status_filter != "All":
            url += f"?status={status_filter}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            jobs = response.json()
            
            if not jobs:
                st.info("No jobs found.")
            else:
                for job in jobs:
                    with st.expander(f"📄 {job['job_id'][:8]}... - {job['status'].upper()}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Status", job['status'])
                        with col2:
                            st.metric("Progress", f"{job['progress_percentage']}%")
                        with col3:
                            st.metric("Created", job['created_at'][:10])
                        
                        st.text(f"Message: {job.get('status_message', 'N/A')}")
                        
                        if job['status'] == 'completed' and job.get('result'):
                            if st.button(f"📖 View Article", key=f"view_{job['job_id']}"):
                                st.session_state['view_job_id'] = job['job_id']
                        
                        if job['status'] == 'failed':
                            if st.button(f"🔄 Resume", key=f"resume_{job['job_id']}"):
                                r = requests.post(f"{api_url}/jobs/{job['job_id']}/resume")
                                if r.status_code == 200:
                                    st.success("Job resumed!")
                                    st.rerun()
        else:
            st.error("Failed to fetch jobs")
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

# Tab 3: View Article
with tab3:
    st.header("View Generated Article")
    
    job_id = st.text_input("Enter Job ID", value=st.session_state.get('view_job_id', ''))
    
    if st.button("🔍 Load Article") and job_id:
        try:
            response = requests.get(f"{api_url}/jobs/{job_id}", timeout=10)
            
            if response.status_code == 200:
                job = response.json()
                
                if job['status'] != 'completed' or not job.get('result'):
                    st.warning(f"Job status: {job['status']} - Article not ready yet")
                else:
                    result = job['result']
                    
                    # Metrics row
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Quality Score", f"{result.get('quality_score', 0):.0f}/100")
                    with col2:
                        st.metric("📝 Words", result.get('total_word_count', 0))
                    with col3:
                        st.metric("⏱️ Reading Time", f"{result.get('reading_time_minutes', 0)} min")
                    with col4:
                        st.metric("✅ Quality Check", "Pass" if result.get('passes_quality_check') else "Needs Work")
                    
                    st.divider()
                    
                    # SEO Metadata
                    with st.expander("🔍 SEO Metadata", expanded=True):
                        seo = result.get('seo_metadata', {})
                        st.text_input("Title Tag", value=seo.get('title_tag', ''), disabled=True)
                        st.text_area("Meta Description", value=seo.get('meta_description', ''), disabled=True, height=80)
                        st.text_input("Primary Keyword", value=seo.get('primary_keyword', ''), disabled=True)
                    
                    # Article Content
                    with st.expander("📄 Article Content", expanded=True):
                        st.markdown(f"# {result.get('title', 'Untitled')}")
                        st.markdown(result.get('introduction', ''))
                        
                        for section in result.get('sections', []):
                            level = section.get('heading_level', 'h2')
                            heading = section.get('heading', '')
                            
                            if level == 'h2':
                                st.markdown(f"## {heading}")
                            elif level == 'h3':
                                st.markdown(f"### {heading}")
                            else:
                                st.markdown(f"**{heading}**")
                            
                            st.markdown(section.get('content', ''))
                            
                            # Handle subsections
                            for sub in section.get('subsections', []):
                                st.markdown(f"### {sub.get('heading', '')}")
                                st.markdown(sub.get('content', ''))
                        
                        st.markdown("## Conclusion")
                        st.markdown(result.get('conclusion', ''))
                    
                    # FAQ Section
                    if result.get('faq_section'):
                        with st.expander("❓ FAQ Section", expanded=False):
                            for faq in result['faq_section']:
                                st.markdown(f"**Q: {faq.get('question', '')}**")
                                st.markdown(f"A: {faq.get('answer', '')}")
                                st.divider()
                    
                    # Internal Links
                    if result.get('internal_links'):
                        with st.expander("🔗 Internal Links", expanded=False):
                            for link in result['internal_links']:
                                st.markdown(f"- **{link.get('anchor_text', '')}** → {link.get('target_topic', '')}")
                                st.caption(link.get('context', ''))
                    
                    # External References
                    if result.get('external_references'):
                        with st.expander("📚 External References", expanded=False):
                            for ref in result['external_references']:
                                st.markdown(f"- **{ref.get('source_name', '')}** ({ref.get('source_type', '')})")
                                st.caption(f"Placement: {ref.get('suggested_placement', '')}")
                    
                    # Quality Issues
                    if result.get('quality_issues'):
                        with st.expander("⚠️ Quality Issues", expanded=False):
                            for issue in result['quality_issues']:
                                severity = issue.get('severity', 'low')
                                icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
                                st.markdown(f"{icon} **{issue.get('message', '')}**")
                                st.caption(issue.get('suggestion', ''))
                    
                    # Download button
                    st.divider()
                    markdown_content = f"# {result.get('title', '')}\n\n{result.get('introduction', '')}\n\n"
                    for section in result.get('sections', []):
                        markdown_content += f"## {section.get('heading', '')}\n\n{section.get('content', '')}\n\n"
                    markdown_content += f"## Conclusion\n\n{result.get('conclusion', '')}"
                    
                    st.download_button(
                        "📥 Download as Markdown",
                        data=markdown_content,
                        file_name=f"article_{job_id[:8]}.md",
                        mime="text/markdown"
                    )
            else:
                st.error(f"Job not found: {job_id}")
        except Exception as e:
            st.error(f"Error loading article: {str(e)}")

# Footer
st.divider()
st.caption("SEO Article Generator | Powered by FastAPI + OpenAI")
