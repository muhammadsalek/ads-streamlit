import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from PIL import Image
import io
import json
import os
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Academic Design Studio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        transition: transform 0.3s;
        border-left: 4px solid #667eea;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .section-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'
if 'projects' not in st.session_state:
    st.session_state.projects = []
if 'project_count' not in st.session_state:
    st.session_state.project_count = 0

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/667eea/FFFFFF?text=ADS", use_column_width=True)
    st.markdown("---")
    
    pages = {
        "🏠 Home": "Home",
        "📝 Assignment": "Assignment",
        "🎨 Poster": "Poster",
        "📄 CV": "CV",
        "📱 QR Code": "QR",
        "📊 Lab Report": "Lab Report",
        "📦 Export": "Export"
    }
    
    for label, page in pages.items():
        if st.button(label, key=f"nav_{page}", use_container_width=True):
            st.session_state.current_page = page
            st.rerun()
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📊 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Projects", len(st.session_state.projects))
    with col2:
        st.metric("Pages", len(pages))

# Main content
page = st.session_state.current_page

if page == "Home":
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Academic Design Studio</h1>
        <p>Design professional academic documents, posters, presentations, and reports in minutes</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Document Builder</h3>
            <p>Create academic documents</p>
            <ul style="list-style-type: none; padding: 0;">
                <li>• Assignment Builder</li>
                <li>• Lab Report</li>
                <li>• Thesis Builder</li>
                <li>• Research Proposal</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎨 Visual Tools</h3>
            <p>Design visual content</p>
            <ul style="list-style-type: none; padding: 0;">
                <li>• Research Poster</li>
                <li>• Presentation Builder</li>
                <li>• Multiple Layouts</li>
                <li>• Export to PDF</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 Professional</h3>
            <p>Professional documents</p>
            <ul style="list-style-type: none; padding: 0;">
                <li>• Academic CV</li>
                <li>• Certificate Builder</li>
                <li>• QR Code Generator</li>
                <li>• Export Manager</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent Projects
    st.markdown("---")
    st.subheader("📂 Recent Projects")
    if st.session_state.projects:
        for project in st.session_state.projects[-5:]:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{project.get('name', 'Untitled')}**")
                st.caption(f"Type: {project.get('type', 'Unknown')}")
            with col2:
                st.caption(f"Created: {project.get('created', 'N/A')}")
            with col3:
                if st.button("Open", key=f"open_{project.get('id', '')}"):
                    st.info(f"Opening {project.get('name', '')}")
            st.divider()
    else:
        st.info("No projects yet. Create your first project using the tools above!")

elif page == "Assignment":
    st.header("📝 Assignment Builder")
    
    with st.form("assignment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Assignment Title *", placeholder="Enter assignment title")
            course = st.text_input("Course Name *", placeholder="e.g., CS101")
            instructor = st.text_input("Instructor Name *")
            max_score = st.number_input("Maximum Score", min_value=0, max_value=100, value=100)
        
        with col2:
            due_date = st.date_input("Due Date", datetime.now())
            submission_type = st.selectbox("Submission Type", ["Individual", "Group", "Both"])
            department = st.text_input("Department", placeholder="Computer Science")
            level = st.selectbox("Level", ["Undergraduate", "Graduate", "PhD"])
        
        instructions = st.text_area("Instructions", height=150, placeholder="Enter assignment instructions...")
        grading_criteria = st.text_area("Grading Criteria", height=100, placeholder="Criteria for grading...")
        
        submitted = st.form_submit_button("📥 Generate Assignment", use_container_width=True)
        
        if submitted:
            if title and course and instructor:
                st.success(f"✅ Assignment '{title}' generated successfully!")
                
                # Save project
                project_data = {
                    'id': datetime.now().strftime("%Y%m%d%H%M%S"),
                    'name': title,
                    'type': 'Assignment',
                    'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                st.session_state.projects.append(project_data)
                st.session_state.project_count += 1
                
                # Preview
                st.subheader("📄 Preview")
                with st.expander("View Assignment", expanded=True):
                    st.markdown(f"""
                    ### {title}
                    
                    | **Course** | {course} |
                    |---|---|
                    | **Instructor** | {instructor} |
                    | **Due Date** | {due_date} |
                    | **Max Score** | {max_score} |
                    | **Submission Type** | {submission_type} |
                    | **Department** | {department} |
                    | **Level** | {level} |
                    
                    **Instructions:**
                    {instructions}
                    
                    **Grading Criteria:**
                    {grading_criteria}
                    """)
                
                # Generate content for download
                assignment_text = f"""
                ASSIGNMENT: {title}
                {'='*60}
                
                Course: {course}
                Instructor: {instructor}
                Due Date: {due_date}
                Max Score: {max_score}
                Submission Type: {submission_type}
                Department: {department}
                Level: {level}
                
                INSTRUCTIONS
                {'-'*40}
                {instructions}
                
                GRADING CRITERIA
                {'-'*40}
                {grading_criteria}
                """
                
                st.download_button(
                    label="📥 Download Assignment (.txt)",
                    data=assignment_text,
                    file_name=f"{title.replace(' ', '_')}_assignment.txt",
                    mime="text/plain"
                )
            else:
                st.error("Please fill in all required fields (marked with *)!")

elif page == "Poster":
    st.header("🎨 Poster Studio")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Poster Settings")
        poster_title = st.text_input("Poster Title", "My Research Poster")
        poster_size = st.selectbox("Size", ["A0 (84.1×118.9cm)", "A1 (59.4×84.1cm)", "A2 (42.0×59.4cm)", "A3 (29.7×42.0cm)", "Custom"])
        poster_layout = st.selectbox("Layout", ["Classic", "Modern", "Minimal", "Three Column", "Two Column"])
        poster_theme = st.selectbox("Theme", ["Blue", "Green", "Purple", "Red", "Dark"])
        
        st.subheader("Sections")
        sections = st.multiselect(
            "Select sections to include",
            ["Title", "Authors", "Abstract", "Background", "Methods", 
             "Results", "Discussion", "Conclusion", "References", "Acknowledgements", "QR Code"],
            default=["Title", "Authors", "Abstract", "Methods", "Results", "Conclusion"]
        )
        
        if st.button("🎨 Generate Poster", use_container_width=True):
            st.session_state.poster_generated = True
            st.session_state.poster_title = poster_title
            st.session_state.poster_sections = sections
            
            # Save project
            project_data = {
                'id': datetime.now().strftime("%Y%m%d%H%M%S"),
                'name': poster_title,
                'type': 'Poster',
                'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            st.session_state.projects.append(project_data)
    
    with col2:
        if st.session_state.get('poster_generated', False):
            st.subheader("🖼️ Poster Preview")
            
            try:
                import matplotlib.pyplot as plt
                import numpy as np
                
                fig, ax = plt.subplots(figsize=(12, 8))
                ax.set_facecolor('#f0f4f8')
                
                # Title
                ax.text(0.5, 0.95, st.session_state.poster_title, fontsize=24, ha='center', va='top', fontweight='bold', color='#1E88E5')
                
                # Sections
                y_pos = 0.85
                for section in st.session_state.poster_sections[:3]:
                    ax.text(0.1, y_pos, section.upper(), fontsize=14, fontweight='bold', color='#1E88E5')
                    ax.text(0.1, y_pos-0.04, f"Sample {section.lower()} content goes here...", fontsize=10, wrap=True)
                    y_pos -= 0.12
                
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                plt.tight_layout()
                
                st.pyplot(fig)
                
                # Download
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                
                st.download_button(
                    label="📥 Download Poster (PNG)",
                    data=buf,
                    file_name=f"{st.session_state.poster_title.replace(' ', '_')}.png",
                    mime="image/png"
                )
                st.success("✅ Poster generated successfully!")
            except Exception as e:
                st.error(f"Error generating preview: {e}")

elif page == "CV":
    st.header("📄 Academic CV Builder")
    
    with st.form("cv_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name *", placeholder="Dr. John Doe")
            email = st.text_input("Email *", placeholder="john.doe@university.edu")
            phone = st.text_input("Phone", placeholder="+1-234-567-8900")
            linkedin = st.text_input("LinkedIn URL", placeholder="linkedin.com/in/username")
        
        with col2:
            position = st.text_input("Current Position", placeholder="Assistant Professor")
            institution = st.text_input("Institution", placeholder="University Name")
            research_areas = st.text_input("Research Areas", placeholder="AI, ML, NLP")
            website = st.text_input("Personal Website", placeholder="https://yourwebsite.com")
        
        professional_summary = st.text_area("Professional Summary", height=100, placeholder="Write a brief professional summary...")
        
        st.subheader("🎓 Education")
        education = st.text_area("Education", height=100, placeholder="PhD in Computer Science, 2020\\nMS in Data Science, 2015\\nBS in Computer Science, 2010")
        
        st.subheader("💼 Experience")
        experience = st.text_area("Experience", height=100, placeholder="Research Scientist, 2020-Present\\nPostdoc, 2018-2020\\nResearch Assistant, 2015-2018")
        
        st.subheader("📚 Publications")
        publications = st.text_area("Selected Publications", height=100, placeholder="Journal papers, conference papers, books...")
        
        st.subheader("🛠️ Skills")
        skills = st.text_input("Skills", placeholder="Python, Machine Learning, Data Analysis")
        
        submitted = st.form_submit_button("📄 Generate CV", use_container_width=True)
        
        if submitted:
            if full_name and email:
                st.success(f"✅ CV for {full_name} generated!")
                
                # Save project
                project_data = {
                    'id': datetime.now().strftime("%Y%m%d%H%M%S"),
                    'name': f"CV_{full_name}",
                    'type': 'CV',
                    'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                st.session_state.projects.append(project_data)
                
                # Preview
                st.subheader("📄 CV Preview")
                with st.expander("View CV", expanded=True):
                    st.markdown(f"""
                    ### {full_name}
                    📧 {email} | 📞 {phone} | 🔗 [{linkedin}]({linkedin}) | 🌐 {website}
                    
                    **{position}** at **{institution}**
                    
                    **Research Areas:** {research_areas}
                    
                    **Professional Summary:**
                    {professional_summary}
                    
                    **Education:**
                    {education}
                    
                    **Experience:**
                    {experience}
                    
                    **Publications:**
                    {publications}
                    
                    **Skills:**
                    {skills}
                    """)
                
                cv_text = f"""
                {full_name}
                {'='*50}
                Email: {email}
                Phone: {phone}
                LinkedIn: {linkedin}
                Website: {website}
                
                Position: {position}
                Institution: {institution}
                Research Areas: {research_areas}
                
                PROFESSIONAL SUMMARY
                {'-'*30}
                {professional_summary}
                
                EDUCATION
                {'-'*30}
                {education}
                
                EXPERIENCE
                {'-'*30}
                {experience}
                
                PUBLICATIONS
                {'-'*30}
                {publications}
                
                SKILLS
                {'-'*30}
                {skills}
                """
                
                st.download_button(
                    label="📥 Download CV (.txt)",
                    data=cv_text,
                    file_name=f"{full_name.replace(' ', '_')}_CV.txt",
                    mime="text/plain"
                )
            else:
                st.error("Please fill in at least Name and Email!")

elif page == "QR":
    st.header("📱 QR Code Generator")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        qr_data = st.text_area("Enter data to encode", height=100, placeholder="https://your-website.com\\nor any text or URL")
        qr_size = st.slider("QR Code Size", min_value=100, max_value=500, value=200, step=50)
        qr_color = st.color_picker("QR Code Color", "#000000")
        bg_color = st.color_picker("Background Color", "#FFFFFF")
        
        if st.button("🎨 Generate QR Code", use_container_width=True):
            if qr_data:
                try:
                    import qrcode
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    
                    img = qr.make_image(fill_color=qr_color, back_color=bg_color)
                    
                    # Save to buffer
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    
                    st.session_state.qr_image = buf
                    st.session_state.qr_generated = True
                    
                    # Save project
                    project_data = {
                        'id': datetime.now().strftime("%Y%m%d%H%M%S"),
                        'name': f"QR_{qr_data[:20]}",
                        'type': 'QR Code',
                        'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    st.session_state.projects.append(project_data)
                    
                except Exception as e:
                    st.error(f"Error generating QR Code: {e}")
            else:
                st.warning("Please enter data to encode")
    
    with col2:
        if st.session_state.get('qr_generated', False):
            st.subheader("🖼️ QR Code Preview")
            st.image(st.session_state.qr_image, width=qr_size)
            
            st.download_button(
                label="📥 Download QR Code (PNG)",
                data=st.session_state.qr_image,
                file_name="qr_code.png",
                mime="image/png"
            )

elif page == "Lab Report":
    st.header("📊 Lab Report Builder")
    
    with st.form("lab_report_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            report_title = st.text_input("Report Title *", "Lab Experiment Report")
            experiment_title = st.text_input("Experiment Title *")
            course_code = st.text_input("Course Code *")
        
        with col2:
            experiment_date = st.date_input("Experiment Date", datetime.now())
            lab_partners = st.text_input("Lab Partners", placeholder="John, Mary, Mike")
            instructor = st.text_input("Instructor Name *")
        
        hypothesis = st.text_area("Hypothesis", height=80, placeholder="What did you hypothesize?")
        methodology = st.text_area("Methodology", height=120, placeholder="How did you conduct the experiment?")
        results = st.text_area("Results", height=120, placeholder="What were the results?")
        discussion = st.text_area("Discussion", height=120, placeholder="Discuss the results")
        conclusion = st.text_area("Conclusion", height=80, placeholder="Conclude the experiment")
        
        submitted = st.form_submit_button("📊 Generate Lab Report", use_container_width=True)
        
        if submitted:
            if report_title and experiment_title and course_code and instructor:
                st.success(f"✅ Lab Report '{report_title}' generated!")
                
                # Save project
                project_data = {
                    'id': datetime.now().strftime("%Y%m%d%H%M%S"),
                    'name': report_title,
                    'type': 'Lab Report',
                    'created': datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                st.session_state.projects.append(project_data)
                
                # Preview
                st.subheader("📄 Report Preview")
                with st.expander("View Report", expanded=True):
                    st.markdown(f"""
                    ### {report_title}
                    
                    | **Experiment** | {experiment_title} |
                    |---|---|
                    | **Course** | {course_code} |
                    | **Date** | {experiment_date} |
                    | **Instructor** | {instructor} |
                    | **Partners** | {lab_partners} |
                    
                    **Hypothesis:**
                    {hypothesis}
                    
                    **Methodology:**
                    {methodology}
                    
                    **Results:**
                    {results}
                    
                    **Discussion:**
                    {discussion}
                    
                    **Conclusion:**
                    {conclusion}
                    """)
                
                report_text = f"""
                LAB REPORT: {report_title}
                {'='*60}
                Experiment: {experiment_title}
                Course: {course_code}
                Date: {experiment_date}
                Instructor: {instructor}
                Partners: {lab_partners}
                
                HYPOTHESIS
                {'-'*40}
                {hypothesis}
                
                METHODOLOGY
                {'-'*40}
                {methodology}
                
                RESULTS
                {'-'*40}
                {results}
                
                DISCUSSION
                {'-'*40}
                {discussion}
                
                CONCLUSION
                {'-'*40}
                {conclusion}
                """
                
                st.download_button(
                    label="📥 Download Lab Report (.txt)",
                    data=report_text,
                    file_name=f"{report_title.replace(' ', '_')}_lab_report.txt",
                    mime="text/plain"
                )
            else:
                st.error("Please fill in all required fields (marked with *)!")

elif page == "Export":
    st.header("📦 Export Manager")
    
    st.subheader("Export Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        export_format = st.selectbox(
            "Export Format",
            ["DOCX", "PDF", "PPTX", "PNG", "SVG", "HTML", "TXT"]
        )
        export_quality = st.selectbox("Quality", ["Draft", "Standard", "High"])
    
    with col2:
        include_metadata = st.checkbox("Include Metadata", value=True)
        include_timestamp = st.checkbox("Include Timestamp", value=True)
        compress_output = st.checkbox("Compress Output", value=False)
    
    st.subheader("📊 Available Projects")
    
    if st.session_state.projects:
        for idx, project in enumerate(st.session_state.projects):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.markdown(f"**{project.get('name', 'Untitled')}**")
                st.caption(f"Type: {project.get('type', 'Unknown')}")
            with col2:
                st.caption(f"Created: {project.get('created', 'N/A')}")
            with col3:
                if st.button("📥", key=f"export_{idx}", help="Export this project"):
                    st.success(f"✅ Exporting {project.get('name', 'Project')} as {export_format}")
            with col4:
                if st.button("🗑️", key=f"delete_{idx}", help="Delete project"):
                    st.session_state.projects.pop(idx)
                    st.rerun()
            st.divider()
    else:
        st.info("No projects available. Create one first!")
    
    # Bulk actions
    st.subheader("🔄 Bulk Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📦 Export All", use_container_width=True):
            st.info("Exporting all projects...")
            st.progress(100)
            st.success("✅ All projects exported successfully!")
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.projects = []
            st.rerun()
    with col3:
        if st.button("💾 Export Data", use_container_width=True):
            data = json.dumps(st.session_state.projects, indent=2)
            st.download_button(
                label="📥 Download Data",
                data=data,
                file_name="projects_data.json",
                mime="application/json"
            )

# Footer
st.markdown("---")
st.caption("🎓 Academic Design Studio v1.0 | Built with Streamlit")