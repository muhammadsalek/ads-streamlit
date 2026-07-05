"""
Academic Design Studio v3.1 - Fixed & Expanded Edition
================================================================================
Fixes in this version:
  * BUG FIX: st.download_button() was being called *inside* st.form(...) blocks
    in the CV, Assignment and Lab Report builders. Streamlit does not allow any
    interactive widget other than st.form_submit_button inside a form, which is
    exactly why the app crashed with StreamlitAPIException right after the
    preview rendered. All download logic has been moved OUTSIDE the form.
  * The CV builder now generates two independently downloadable, properly
    formatted Word documents: one in Academic CV style, one in Europass style
    (rather than one generic text dump reused for both).
  * Added working downloads (TXT + DOCX) for Thesis and Research Proposal,
    which previously only showed a success message and produced nothing.
  * Every download_button now has an explicit, unique `key=` so repeated
    reruns / page switches never collide on an auto-generated widget id.

Author: ADS Team
Version: 3.1.0
License: MIT
"""

import streamlit as st
import io
import hashlib
from datetime import datetime, timedelta

import docx
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

APP_CONFIG = {
    "name": "Academic Design Studio",
    "version": "3.1.0",
    "author": "ADS Research Team",
    "description": "Professional Academic Document Design Platform",
    "year": 2026,
    "institution": "Harvard Medical School",
    "department": "Global Health & Epidemiology",
}

st.set_page_config(
    page_title=f"{APP_CONFIG['name']} v{APP_CONFIG['version']}",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CSS
# ============================================================================

def load_css() -> str:
    return """
    <style>
        .main { padding: 0rem 1rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            padding: 3rem; border-radius: 20px; color: white; text-align: center;
            margin-bottom: 2rem; box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        .main-header h1 { font-size: 3rem; font-weight: 800; margin: 0; }
        .main-header p { font-size: 1.2rem; opacity: 0.95; margin-top: 0.5rem; }
        .feature-card {
            background: white; padding: 1.5rem; border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin: 0.5rem 0;
            border-left: 6px solid #667eea; height: 100%;
        }
        .stat-card {
            background: white; padding: 1.5rem; border-radius: 15px; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid rgba(102,126,234,0.1);
        }
        .cover-page {
            background: white; padding: 3rem; border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 1rem 0; border: 1px solid #e0e0e0;
        }
    </style>
    """

st.markdown(load_css(), unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================

def init_state():
    defaults = {
        "current_page": "Home",
        "projects": [],
        "cv_generated": False,
        "cv_data": None,
        "assignment_generated": False,
        "assignment_data": None,
        "lab_report_generated": False,
        "lab_report_data": None,
        "thesis_generated": False,
        "thesis_data": None,
        "proposal_generated": False,
        "proposal_data": None,
        "poster_generated": False,
        "qr_generated": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================================
# UTILITIES
# ============================================================================

def generate_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{ts}_{hashlib.md5(ts.encode()).hexdigest()[:6]}"

def add_project(name: str, doc_type: str):
    st.session_state.projects.append({
        "id": generate_id(),
        "name": name or "Untitled",
        "type": doc_type,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

def safe_filename(name: str) -> str:
    name = (name or "document").strip().replace(" ", "_")
    return "".join(c for c in name if c.isalnum() or c in ("_", "-")) or "document"

def set_cell_background(cell, color_hex: str):
    """Shade a docx table cell with a solid background color."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)

def add_heading_styled(doc, text, size=16, color=(44, 62, 80), bold=True, space_before=12, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(*color)
    run.font.name = "Times New Roman"
    return p

def add_body_text(doc, text, size=11):
    p = doc.add_paragraph(text or "")
    for run in p.runs:
        run.font.size = Pt(size)
        run.font.name = "Times New Roman"
    p.paragraph_format.space_after = Pt(8)
    return p

# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 1rem 0;">
                <div style="font-size: 3rem;">🎓</div>
                <h1 style="color: #667eea; margin: 0; font-size: 1.6rem;">ADS</h1>
                <p style="color: #888; margin: 0; font-size: 0.7rem;">Academic Design Studio v3.1</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        pages = {
            "🏠 Home": "Home",
            "📝 Assignment": "Assignment",
            "📊 Lab Report": "Lab Report",
            "📄 Thesis": "Thesis",
            "📑 Research Proposal": "Research Proposal",
            "🎨 Poster": "Poster",
            "📄 CV": "CV",
            "📱 QR Code": "QR",
            "📦 Export": "Export",
        }
        for label, page in pages.items():
            if st.button(label, key=f"nav_{page}", use_container_width=True,
                         type="primary" if st.session_state.current_page == page else "secondary"):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📂 Projects", len(st.session_state.projects))
        with col2:
            st.metric("📄 Pages", len(pages))
        st.markdown("---")
        st.caption(f"v{APP_CONFIG['version']} | © {APP_CONFIG['year']}")

# ============================================================================
# HOME
# ============================================================================

def render_home():
    st.markdown(
        f"""
        <div class="main-header">
            <h1>🎓 Academic Design Studio</h1>
            <p>Professional Academic Document Design Platform</p>
            <p style="font-size: 0.9rem; opacity: 0.75; margin-top: 1rem;">
                Assignment • Lab Report • Thesis • Proposal • Poster • CV • QR • Export
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    stats = [("📚", "Document Types", "6"), ("🎨", "Poster Themes", "10"),
             ("📄", "Export Formats", "TXT / DOCX"), ("📂", "Projects", str(len(st.session_state.projects)))]
    for col, (icon, label, value) in zip([col1, col2, col3, col4], stats):
        with col:
            st.markdown(
                f"""<div class="stat-card"><div style="font-size:2rem;">{icon}</div>
                <div style="color:#666;">{label}</div>
                <div style="font-size:1.4rem;font-weight:700;color:#667eea;">{value}</div></div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """<div class="feature-card"><h3>📝 Document Builder</h3>
            <ul><li>Assignment with Rubric</li><li>Lab Report</li>
            <li>Thesis (Full Structure)</li><li>Research Proposal</li></ul></div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """<div class="feature-card"><h3>🎨 Design Studio</h3>
            <ul><li>Poster (10 Themes)</li><li>CV — Academic or Europass</li>
            <li>QR Code Generator</li></ul></div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """<div class="feature-card"><h3>📦 Export & Management</h3>
            <ul><li>TXT + DOCX for every builder</li><li>Project tracking</li>
            <li>Bulk project export</li></ul></div>""",
            unsafe_allow_html=True,
        )

# ============================================================================
# COVER PAGE GENERATOR (HTML preview only)
# ============================================================================

COVER_TEMPLATES = {
    "classic": """
    <div class="cover-page" style="text-align:center;padding:3rem 2rem;">
        <div style="border-bottom:3px solid #667eea;padding-bottom:1.5rem;">
            <h1 style="color:#2c3e50;">{title}</h1><p style="color:#666;">{subtitle}</p>
        </div>
        <div style="margin:2rem 0;">
            <p><strong>Author:</strong> {author}</p>
            <p><strong>Institution:</strong> {institution}</p>
            <p><strong>Date:</strong> {date}</p>
            <p><strong>Course:</strong> {course}</p>
        </div>
    </div>""",
    "modern": """
    <div class="cover-page" style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:3rem 2rem;text-align:center;">
        <h1>{title}</h1><p style="opacity:0.9;">{subtitle}</p>
        <div style="margin:2rem 0;">
            <p><strong>Author:</strong> {author}</p>
            <p><strong>Institution:</strong> {institution}</p>
            <p><strong>Date:</strong> {date}</p>
        </div>
    </div>""",
    "minimal": """
    <div class="cover-page" style="padding:3rem 2rem;text-align:center;background:#fafafa;">
        <h1 style="font-weight:300;color:#2c3e50;">{title}</h1>
        <p style="font-weight:300;color:#666;">{subtitle}</p>
        <div style="border-top:1px solid #ddd;border-bottom:1px solid #ddd;padding:1.5rem 0;">
            <p><strong>{author}</strong></p><p style="color:#666;">{institution}</p><p style="color:#999;">{date}</p>
        </div>
    </div>""",
}

def generate_cover_page_html(content: dict, style: str) -> str:
    template = COVER_TEMPLATES.get(style, COVER_TEMPLATES["classic"])
    return template.format(
        title=content.get("title", "Academic Document"),
        subtitle=content.get("subtitle", ""),
        author=content.get("author", ""),
        institution=content.get("institution", APP_CONFIG["institution"]),
        date=content.get("date", datetime.now().strftime("%B %d, %Y")),
        course=content.get("course", ""),
    )

# ============================================================================
# ASSIGNMENT BUILDER  (fix: download logic moved OUTSIDE the form)
# ============================================================================

def render_assignment_builder():
    st.header("📝 Assignment Builder")
    st.caption("Create professional assignments with a cover page")

    with st.form("assignment_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Assignment Title *", placeholder="Machine Learning Project")
            course = st.text_input("Course Name *", placeholder="CS 101")
            instructor = st.text_input("Instructor Name *", placeholder="Dr. John Doe")
            max_score = st.number_input("Maximum Score", min_value=0, max_value=1000, value=100, step=5)
        with col2:
            due_date = st.date_input("Due Date", datetime.now() + timedelta(days=7))
            submission_type = st.selectbox("Submission Type", ["Individual", "Group", "Both"])
            department = st.text_input("Department", placeholder="Computer Science")
            level = st.selectbox("Academic Level", ["Undergraduate", "Graduate", "PhD", "Postdoc"])

        cover_style = st.selectbox("Cover Page Style", ["Classic", "Modern", "Minimal"])
        instructions = st.text_area("Instructions", height=150)
        grading_criteria = st.text_area("Grading Criteria", height=100)

        submitted = st.form_submit_button("📥 Generate Assignment", use_container_width=True)

    # --- everything below runs OUTSIDE the form: this is the actual bug fix ---
    if submitted:
        if not title or not course or not instructor:
            st.error("⚠️ Please fill in all required fields!")
        else:
            add_project(title, "Assignment")
            st.session_state.assignment_generated = True
            st.session_state.assignment_data = dict(
                title=title, course=course, instructor=instructor, max_score=max_score,
                due_date=due_date, submission_type=submission_type, department=department,
                level=level, cover_style=cover_style, instructions=instructions,
                grading_criteria=grading_criteria,
            )

    if st.session_state.assignment_generated and st.session_state.assignment_data:
        d = st.session_state.assignment_data
        st.success(f"✅ Assignment '{d['title']}' generated!")

        st.subheader("📄 Cover Page")
        cover = {
            "title": d["title"], "subtitle": d["course"], "author": d["instructor"],
            "institution": APP_CONFIG["institution"], "department": d["department"],
            "date": d["due_date"].strftime("%B %d, %Y"), "course": d["course"],
        }
        st.markdown(generate_cover_page_html(cover, d["cover_style"].lower()), unsafe_allow_html=True)

        st.subheader("📄 Assignment Preview")
        with st.expander("View Full Assignment", expanded=True):
            st.markdown(f"""
### {d['title']}

| | |
|---|---|
| **Course** | {d['course']} |
| **Instructor** | {d['instructor']} |
| **Due Date** | {d['due_date'].strftime('%B %d, %Y')} |
| **Max Score** | {d['max_score']} |
| **Submission Type** | {d['submission_type']} |
| **Level** | {d['level']} |

**Instructions**

{d['instructions']}

**Grading Criteria**

{d['grading_criteria']}
""")

        text = (
            f"ASSIGNMENT: {d['title']}\n{'='*60}\n"
            f"Course: {d['course']}\nInstructor: {d['instructor']}\n"
            f"Due Date: {d['due_date'].strftime('%B %d, %Y')}\nMax Score: {d['max_score']}\n"
            f"Submission Type: {d['submission_type']}\nLevel: {d['level']}\n\n"
            f"INSTRUCTIONS\n{'-'*40}\n{d['instructions']}\n\n"
            f"GRADING CRITERIA\n{'-'*40}\n{d['grading_criteria']}\n\n"
            f"Generated by {APP_CONFIG['name']} v{APP_CONFIG['version']}"
        )

        st.subheader("📥 Download")
        c1, c2 = st.columns(2)
        fname = safe_filename(d["title"])
        with c1:
            st.download_button("📄 Download TXT", data=text.encode("utf-8"),
                                file_name=f"{fname}_assignment.txt", mime="text/plain",
                                use_container_width=True, key="dl_assignment_txt")
        with c2:
            doc = docx.Document()
            doc.add_heading(d["title"], 0)
            doc.add_paragraph(f"Course: {d['course']}")
            doc.add_paragraph(f"Instructor: {d['instructor']}")
            doc.add_paragraph(f"Due Date: {d['due_date'].strftime('%B %d, %Y')}")
            doc.add_paragraph(f"Max Score: {d['max_score']}  |  Submission Type: {d['submission_type']}")
            doc.add_heading("Instructions", level=1)
            doc.add_paragraph(d["instructions"])
            doc.add_heading("Grading Criteria", level=1)
            doc.add_paragraph(d["grading_criteria"])
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📝 Download DOCX", data=buf.getvalue(),
                                file_name=f"{fname}_assignment.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True, key="dl_assignment_docx")

# ============================================================================
# LAB REPORT BUILDER  (same bug fix pattern)
# ============================================================================

def render_lab_report():
    st.header("📊 Lab Report Builder")
    st.caption("Create professional lab reports with structured sections")

    with st.form("lab_report_form"):
        col1, col2 = st.columns(2)
        with col1:
            report_title = st.text_input("Report Title *", "Lab Experiment Report")
            experiment_title = st.text_input("Experiment Title *")
            course_code = st.text_input("Course Code *")
        with col2:
            experiment_date = st.date_input("Experiment Date", datetime.now())
            lab_partners = st.text_input("Lab Partners")
            instructor = st.text_input("Instructor Name *")

        hypothesis = st.text_area("Hypothesis", height=80)
        methodology = st.text_area("Methodology", height=120)
        results = st.text_area("Results", height=120)
        discussion = st.text_area("Discussion", height=120)
        conclusion = st.text_area("Conclusion", height=80)
        references = st.text_area("References", height=80)

        submitted = st.form_submit_button("📊 Generate Lab Report", use_container_width=True)

    if submitted:
        if not report_title or not experiment_title or not course_code or not instructor:
            st.error("⚠️ Please fill in all required fields!")
        else:
            add_project(report_title, "Lab Report")
            st.session_state.lab_report_generated = True
            st.session_state.lab_report_data = dict(
                report_title=report_title, experiment_title=experiment_title, course_code=course_code,
                experiment_date=experiment_date, lab_partners=lab_partners, instructor=instructor,
                hypothesis=hypothesis, methodology=methodology, results=results,
                discussion=discussion, conclusion=conclusion, references=references,
            )

    if st.session_state.lab_report_generated and st.session_state.lab_report_data:
        d = st.session_state.lab_report_data
        st.success(f"✅ Lab Report '{d['report_title']}' generated!")

        st.subheader("📄 Report Preview")
        with st.expander("View Full Report", expanded=True):
            st.markdown(f"""
### {d['report_title']}

| | |
|---|---|
| **Experiment** | {d['experiment_title']} |
| **Course** | {d['course_code']} |
| **Date** | {d['experiment_date'].strftime('%B %d, %Y')} |
| **Instructor** | {d['instructor']} |
| **Partners** | {d['lab_partners']} |

**Hypothesis**\n\n{d['hypothesis']}

**Methodology**\n\n{d['methodology']}

**Results**\n\n{d['results']}

**Discussion**\n\n{d['discussion']}

**Conclusion**\n\n{d['conclusion']}

**References**\n\n{d['references']}
""")

        text = (
            f"LAB REPORT: {d['report_title']}\n{'='*60}\n"
            f"Experiment: {d['experiment_title']}\nCourse: {d['course_code']}\n"
            f"Date: {d['experiment_date'].strftime('%B %d, %Y')}\nInstructor: {d['instructor']}\n"
            f"Partners: {d['lab_partners']}\n\n"
            f"HYPOTHESIS\n{'-'*40}\n{d['hypothesis']}\n\n"
            f"METHODOLOGY\n{'-'*40}\n{d['methodology']}\n\n"
            f"RESULTS\n{'-'*40}\n{d['results']}\n\n"
            f"DISCUSSION\n{'-'*40}\n{d['discussion']}\n\n"
            f"CONCLUSION\n{'-'*40}\n{d['conclusion']}\n\n"
            f"REFERENCES\n{'-'*40}\n{d['references']}\n\n"
            f"Generated by {APP_CONFIG['name']} v{APP_CONFIG['version']}"
        )

        st.subheader("📥 Download Options")
        c1, c2 = st.columns(2)
        fname = safe_filename(d["report_title"])
        with c1:
            st.download_button("📄 Download TXT", data=text.encode("utf-8"),
                                file_name=f"{fname}_lab_report.txt", mime="text/plain",
                                use_container_width=True, key="dl_lab_txt")
        with c2:
            doc = docx.Document()
            doc.add_heading(d["report_title"], 0)
            doc.add_paragraph(f"Experiment: {d['experiment_title']}")
            doc.add_paragraph(f"Course: {d['course_code']}")
            doc.add_paragraph(f"Date: {d['experiment_date'].strftime('%B %d, %Y')}")
            doc.add_paragraph(f"Instructor: {d['instructor']}  |  Partners: {d['lab_partners']}")
            for label, content in [("Hypothesis", d["hypothesis"]), ("Methodology", d["methodology"]),
                                    ("Results", d["results"]), ("Discussion", d["discussion"]),
                                    ("Conclusion", d["conclusion"]), ("References", d["references"])]:
                doc.add_heading(label, level=1)
                doc.add_paragraph(content)
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📝 Download DOCX", data=buf.getvalue(),
                                file_name=f"{fname}_lab_report.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True, key="dl_lab_docx")

# ============================================================================
# THESIS BUILDER (previously had no working download at all — added)
# ============================================================================

def render_thesis():
    st.header("📄 Thesis Builder")
    st.caption("Create a structured thesis front-matter document")

    with st.form("thesis_form"):
        col1, col2 = st.columns(2)
        with col1:
            thesis_title = st.text_input("Thesis Title *")
            author_name = st.text_input("Author Name *")
            degree = st.text_input("Degree *")
            university = st.text_input("University *")
        with col2:
            department = st.text_input("Department *")
            supervisor = st.text_input("Supervisor *")
            defense_date = st.date_input("Defense Date", datetime.now() + timedelta(days=180))
            submission_date = st.date_input("Submission Date", datetime.now() + timedelta(days=150))

        abstract = st.text_area("Abstract *", height=150)
        chapter_count = st.number_input("Number of Chapters", min_value=3, max_value=10, value=5)
        chapters = []
        for i in range(int(chapter_count)):
            c1, c2 = st.columns([3, 1])
            with c1:
                ch_title = st.text_input(f"Chapter {i+1} Title", key=f"ch_title_{i}")
            with c2:
                ch_pages = st.number_input("Pages", min_value=1, max_value=200, value=20, key=f"ch_pages_{i}")
            chapters.append((ch_title, ch_pages))

        acknowledgements = st.text_area("Acknowledgements", height=100)
        submitted = st.form_submit_button("📄 Generate Thesis", use_container_width=True)

    if submitted:
        if not thesis_title or not author_name:
            st.error("⚠️ Please fill in required fields!")
        else:
            add_project(thesis_title, "Thesis")
            st.session_state.thesis_generated = True
            st.session_state.thesis_data = dict(
                thesis_title=thesis_title, author_name=author_name, degree=degree, university=university,
                department=department, supervisor=supervisor, defense_date=defense_date,
                submission_date=submission_date, abstract=abstract, chapters=chapters,
                acknowledgements=acknowledgements,
            )

    if st.session_state.thesis_generated and st.session_state.thesis_data:
        d = st.session_state.thesis_data
        st.success(f"✅ Thesis '{d['thesis_title']}' generated!")

        with st.expander("View Front Matter", expanded=True):
            st.markdown(f"""
### {d['thesis_title']}
**{d['author_name']}** — {d['degree']}, {d['university']}

**Department:** {d['department']}  |  **Supervisor:** {d['supervisor']}
**Submission:** {d['submission_date'].strftime('%B %d, %Y')}  |  **Defense:** {d['defense_date'].strftime('%B %d, %Y')}

**Abstract**

{d['abstract']}
""")
            for i, (ch_title, ch_pages) in enumerate(d["chapters"], start=1):
                st.markdown(f"- **Chapter {i}: {ch_title or '(untitled)'}** — approx. {ch_pages} pages")

        fname = safe_filename(d["thesis_title"])
        text = (
            f"THESIS: {d['thesis_title']}\n{'='*60}\n"
            f"Author: {d['author_name']}\nDegree: {d['degree']}\nUniversity: {d['university']}\n"
            f"Department: {d['department']}\nSupervisor: {d['supervisor']}\n"
            f"Submission Date: {d['submission_date'].strftime('%B %d, %Y')}\n"
            f"Defense Date: {d['defense_date'].strftime('%B %d, %Y')}\n\n"
            f"ABSTRACT\n{'-'*40}\n{d['abstract']}\n\n"
            f"CHAPTERS\n{'-'*40}\n"
            + "\n".join(f"Chapter {i}: {t or '(untitled)'} ({p} pages)" for i, (t, p) in enumerate(d["chapters"], 1))
            + f"\n\nACKNOWLEDGEMENTS\n{'-'*40}\n{d['acknowledgements']}\n\n"
            f"Generated by {APP_CONFIG['name']} v{APP_CONFIG['version']}"
        )

        st.subheader("📥 Download")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📄 Download TXT", data=text.encode("utf-8"),
                                file_name=f"{fname}_thesis.txt", mime="text/plain",
                                use_container_width=True, key="dl_thesis_txt")
        with c2:
            doc = docx.Document()
            doc.add_heading(d["thesis_title"], 0)
            sub = doc.add_paragraph()
            sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
            sub.add_run(f"{d['author_name']} — {d['degree']}, {d['university']}").italic = True
            doc.add_paragraph(f"Department: {d['department']}")
            doc.add_paragraph(f"Supervisor: {d['supervisor']}")
            doc.add_paragraph(f"Submission Date: {d['submission_date'].strftime('%B %d, %Y')}")
            doc.add_paragraph(f"Defense Date: {d['defense_date'].strftime('%B %d, %Y')}")
            doc.add_heading("Abstract", level=1)
            doc.add_paragraph(d["abstract"])
            doc.add_heading("Table of Chapters", level=1)
            for i, (ch_title, ch_pages) in enumerate(d["chapters"], start=1):
                doc.add_paragraph(f"Chapter {i}: {ch_title or '(untitled)'}  ({ch_pages} pages)", style="List Bullet")
            doc.add_heading("Acknowledgements", level=1)
            doc.add_paragraph(d["acknowledgements"])
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📝 Download DOCX", data=buf.getvalue(),
                                file_name=f"{fname}_thesis.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True, key="dl_thesis_docx")

# ============================================================================
# RESEARCH PROPOSAL BUILDER (previously had no working download — added)
# ============================================================================

def render_research_proposal():
    st.header("📑 Research Proposal Builder")
    st.caption("Create a funding-ready research proposal")

    with st.form("proposal_form"):
        col1, col2 = st.columns(2)
        with col1:
            proposal_title = st.text_input("Proposal Title *")
            pi_name = st.text_input("Principal Investigator *")
            institution = st.text_input("Institution *")
        with col2:
            department = st.text_input("Department *")
            funding_agency = st.text_input("Funding Agency")
            project_duration = st.selectbox("Project Duration", ["6 months", "1 year", "2 years", "3 years"])
            budget = st.number_input("Budget ($)", min_value=1000, max_value=10000000, value=100000, step=1000)

        abstract = st.text_area("Abstract *", height=120)
        research_question = st.text_area("Research Question", height=80)
        objectives = st.text_area("Objectives", height=100)
        methodology = st.text_area("Methodology", height=120)
        expected_outcomes = st.text_area("Expected Outcomes", height=100)

        submitted = st.form_submit_button("📑 Generate Proposal", use_container_width=True)

    if submitted:
        if not proposal_title or not pi_name:
            st.error("⚠️ Please fill in required fields!")
        else:
            add_project(proposal_title, "Research Proposal")
            st.session_state.proposal_generated = True
            st.session_state.proposal_data = dict(
                proposal_title=proposal_title, pi_name=pi_name, institution=institution,
                department=department, funding_agency=funding_agency, project_duration=project_duration,
                budget=budget, abstract=abstract, research_question=research_question,
                objectives=objectives, methodology=methodology, expected_outcomes=expected_outcomes,
            )

    if st.session_state.proposal_generated and st.session_state.proposal_data:
        d = st.session_state.proposal_data
        st.success(f"✅ Proposal '{d['proposal_title']}' generated!")

        with st.expander("View Proposal", expanded=True):
            st.markdown(f"""
### {d['proposal_title']}
**PI:** {d['pi_name']}  |  **Institution:** {d['institution']}  |  **Department:** {d['department']}
**Funding Agency:** {d['funding_agency'] or '—'}  |  **Duration:** {d['project_duration']}  |  **Budget:** ${d['budget']:,}

**Abstract**\n\n{d['abstract']}

**Research Question**\n\n{d['research_question']}

**Objectives**\n\n{d['objectives']}

**Methodology**\n\n{d['methodology']}

**Expected Outcomes**\n\n{d['expected_outcomes']}
""")

        fname = safe_filename(d["proposal_title"])
        text = (
            f"RESEARCH PROPOSAL: {d['proposal_title']}\n{'='*60}\n"
            f"Principal Investigator: {d['pi_name']}\nInstitution: {d['institution']}\n"
            f"Department: {d['department']}\nFunding Agency: {d['funding_agency']}\n"
            f"Duration: {d['project_duration']}\nBudget: ${d['budget']:,}\n\n"
            f"ABSTRACT\n{'-'*40}\n{d['abstract']}\n\n"
            f"RESEARCH QUESTION\n{'-'*40}\n{d['research_question']}\n\n"
            f"OBJECTIVES\n{'-'*40}\n{d['objectives']}\n\n"
            f"METHODOLOGY\n{'-'*40}\n{d['methodology']}\n\n"
            f"EXPECTED OUTCOMES\n{'-'*40}\n{d['expected_outcomes']}\n\n"
            f"Generated by {APP_CONFIG['name']} v{APP_CONFIG['version']}"
        )

        st.subheader("📥 Download")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📄 Download TXT", data=text.encode("utf-8"),
                                file_name=f"{fname}_proposal.txt", mime="text/plain",
                                use_container_width=True, key="dl_proposal_txt")
        with c2:
            doc = docx.Document()
            doc.add_heading(d["proposal_title"], 0)
            doc.add_paragraph(f"Principal Investigator: {d['pi_name']}")
            doc.add_paragraph(f"Institution: {d['institution']}  |  Department: {d['department']}")
            doc.add_paragraph(f"Funding Agency: {d['funding_agency'] or '—'}")
            doc.add_paragraph(f"Duration: {d['project_duration']}  |  Budget: ${d['budget']:,}")
            for label, content in [("Abstract", d["abstract"]), ("Research Question", d["research_question"]),
                                    ("Objectives", d["objectives"]), ("Methodology", d["methodology"]),
                                    ("Expected Outcomes", d["expected_outcomes"])]:
                doc.add_heading(label, level=1)
                doc.add_paragraph(content)
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📝 Download DOCX", data=buf.getvalue(),
                                file_name=f"{fname}_proposal.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True, key="dl_proposal_docx")

# ============================================================================
# CV BUILDER — Academic vs Europass, each with its own real docx layout
# ============================================================================

def build_academic_cv_docx(d: dict) -> bytes:
    """Traditional academic CV: centered header, clean section headings, Times New Roman."""
    doc = docx.Document()
    for section in doc.sections:
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_p.add_run(d["full_name"])
    run.bold = True
    run.font.size = Pt(20)
    run.font.name = "Times New Roman"

    contact_bits = [b for b in [d["email"], d["phone"], d["linkedin"], d["website"]] if b]
    contact_p = doc.add_paragraph()
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_run = contact_p.add_run(" | ".join(contact_bits))
    contact_run.font.size = Pt(10)
    contact_run.font.name = "Times New Roman"

    if d["position"] or d["institution"]:
        role_p = doc.add_paragraph()
        role_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        role_run = role_p.add_run(f"{d['position']}{' — ' if d['position'] and d['institution'] else ''}{d['institution']}")
        role_run.italic = True
        role_run.font.size = Pt(11)
        role_run.font.name = "Times New Roman"

    doc.add_paragraph().add_run("_" * 90).font.color.rgb = RGBColor(150, 150, 150)

    sections = [
        ("Professional Summary", d["professional_summary"]),
        ("Education", d["education"]),
        ("Experience", d["experience"]),
        ("Selected Publications", d["publications"]),
        ("Skills", d["skills"]),
        ("Awards & Honors", d["awards"]),
    ]
    for label, content in sections:
        if content:
            add_heading_styled(doc, label, size=13)
            add_body_text(doc, content)

    if d["research_areas"]:
        add_heading_styled(doc, "Research Areas", size=13)
        add_body_text(doc, d["research_areas"])

    add_heading_styled(doc, "Research Metrics", size=13)
    table = doc.add_table(rows=2, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    headers = ["Citations", "H-index", "i10-index"]
    values = [str(d["citations"]), str(d["h_index"]), str(d["i10_index"])]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, v in enumerate(values):
        cell = table.rows[1].cells[i]
        cell.text = v
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def build_europass_cv_docx(d: dict) -> bytes:
    """Europass-style CV: blue header banner + labeled two-column rows, matching the
    standard EU Europass layout conventions (personal info block, then labeled sections)."""
    doc = docx.Document()
    for section in doc.sections:
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    EU_BLUE = "003399"

    header_table = doc.add_table(rows=1, cols=1)
    cell = header_table.rows[0].cells[0]
    set_cell_background(cell, EU_BLUE)
    p = cell.paragraphs[0]
    run = p.add_run(d["full_name"])
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(255, 255, 255)
    run.font.name = "Arial"
    p2 = cell.add_paragraph()
    r2 = p2.add_run(f"{d['position']}{' | ' if d['position'] and d['institution'] else ''}{d['institution']}")
    r2.font.color.rgb = RGBColor(220, 230, 250)
    r2.font.size = Pt(11)
    r2.font.name = "Arial"

    doc.add_paragraph()

    def add_label_row(label, value):
        if not value:
            return
        t = doc.add_table(rows=1, cols=2)
        t.autofit = False
        t.columns[0].width = Inches(1.6)
        t.columns[1].width = Inches(5.2)
        lc, vc = t.rows[0].cells
        lr = lc.paragraphs[0].add_run(label)
        lr.bold = True
        lr.font.color.rgb = RGBColor(0, 51, 153)
        lr.font.size = Pt(10)
        lr.font.name = "Arial"
        vr = vc.paragraphs[0].add_run(str(value))
        vr.font.size = Pt(10)
        vr.font.name = "Arial"

    add_label_row("Email", d["email"])
    add_label_row("Phone", d["phone"])
    add_label_row("LinkedIn", d["linkedin"])
    add_label_row("Website", d["website"])

    doc.add_paragraph()

    def add_europass_section(title, content):
        if not content:
            return
        head = doc.add_paragraph()
        hr = head.add_run(title.upper())
        hr.bold = True
        hr.font.color.rgb = RGBColor(255, 255, 255)
        hr.font.size = Pt(11)
        hr.font.name = "Arial"
        head.paragraph_format.space_before = Pt(10)
        # shade the heading paragraph like Europass's blue section bars
        p_pr = head._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), EU_BLUE)
        p_pr.append(shd)

        body = doc.add_paragraph(content)
        for r in body.runs:
            r.font.name = "Arial"
            r.font.size = Pt(10)

    add_europass_section("Personal Statement", d["professional_summary"])
    add_europass_section("Work Experience", d["experience"])
    add_europass_section("Education and Training", d["education"])
    add_europass_section("Publications", d["publications"])
    add_europass_section("Skills", d["skills"])
    add_europass_section("Research Areas", d["research_areas"])

    metrics_head = doc.add_paragraph()
    mhr = metrics_head.add_run("RESEARCH METRICS")
    mhr.bold = True
    mhr.font.color.rgb = RGBColor(255, 255, 255)
    mhr.font.size = Pt(11)
    mhr.font.name = "Arial"
    p_pr = metrics_head._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), EU_BLUE)
    p_pr.append(shd)

    mt = doc.add_table(rows=1, cols=3)
    mt.style = "Table Grid"
    labels = ["Citations", "H-index", "i10-index"]
    values = [str(d["citations"]), str(d["h_index"]), str(d["i10_index"])]
    for i, (lab, val) in enumerate(zip(labels, values)):
        c = mt.rows[0].cells[i]
        c.text = f"{lab}: {val}"
        c.paragraphs[0].runs[0].font.size = Pt(10)
        c.paragraphs[0].runs[0].font.name = "Arial"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def render_cv_builder():
    st.header("📄 Academic CV Builder")
    st.caption("Fill this out once, then download BOTH the Academic-style and Europass-style CV as separate Word documents")

    with st.form("cv_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *", placeholder="Dr. John Doe")
            email = st.text_input("Email *", placeholder="john.doe@university.edu")
            phone = st.text_input("Phone", placeholder="+1-234-567-8900")
            linkedin = st.text_input("LinkedIn URL", placeholder="linkedin.com/in/username")
        with col2:
            position = st.text_input("Current Position", placeholder="Assistant Professor")
            institution = st.text_input("Institution", placeholder="Harvard University")
            research_areas = st.text_input("Research Areas", placeholder="Machine Learning, AI, NLP")
            website = st.text_input("Personal Website", placeholder="https://yourwebsite.com")

        professional_summary = st.text_area("Professional Summary", height=100)

        st.subheader("🎓 Education")
        education = st.text_area("Education", height=100, label_visibility="collapsed")
        st.subheader("💼 Experience")
        experience = st.text_area("Experience", height=100, label_visibility="collapsed")
        st.subheader("📚 Publications")
        publications = st.text_area("Selected Publications", height=100, label_visibility="collapsed")
        st.subheader("🛠️ Skills")
        skills = st.text_input("Skills", placeholder="Python, Machine Learning, Data Analysis", label_visibility="collapsed")
        st.subheader("🏆 Awards & Honors")
        awards = st.text_area("Awards & Honors", height=80, label_visibility="collapsed")

        st.subheader("📊 Research Metrics")
        c1, c2, c3 = st.columns(3)
        with c1:
            citations = st.number_input("Citations", min_value=0, max_value=999999, value=100)
        with c2:
            h_index = st.number_input("H-index", min_value=0, max_value=500, value=10)
        with c3:
            i10_index = st.number_input("i10-index", min_value=0, max_value=500, value=5)

        submitted = st.form_submit_button("📄 Generate CV", use_container_width=True)

    if submitted:
        if not full_name or not email:
            st.error("⚠️ Please fill in at least Name and Email!")
        else:
            add_project(full_name, "CV")
            st.session_state.cv_generated = True
            st.session_state.cv_data = dict(
                full_name=full_name, email=email, phone=phone, linkedin=linkedin,
                position=position, institution=institution, research_areas=research_areas,
                website=website, professional_summary=professional_summary, education=education,
                experience=experience, publications=publications, skills=skills, awards=awards,
                citations=citations, h_index=h_index, i10_index=i10_index,
            )

    if st.session_state.cv_generated and st.session_state.cv_data:
        d = st.session_state.cv_data
        st.success(f"✅ CV for {d['full_name']} generated!")

        preview_style = st.radio("Preview style", ["🎓 Academic", "🇪🇺 Europass"], horizontal=True, key="cv_preview_style")

        st.subheader("📄 CV Preview")
        with st.expander("View Full CV", expanded=True):
            if preview_style == "🇪🇺 Europass":
                st.markdown(f"""
<div style="background:white;padding:1.5rem;border-radius:10px;border:2px solid #003399;">
  <div style="background:#003399;color:white;padding:1rem;border-radius:5px;">
    <h2 style="color:white;margin:0;">{d['full_name']}</h2>
    <p style="color:#ccc;margin:0;">{d['position']} | {d['institution']}</p>
  </div>
  <p>📧 {d['email']} | 📞 {d['phone']}</p>
  <p>🔗 {d['linkedin']} | 🌐 {d['website']}</p>
  <hr>
  <h4>Personal Statement</h4><p>{d['professional_summary']}</p>
  <h4>Work Experience</h4><p>{d['experience']}</p>
  <h4>Education and Training</h4><p>{d['education']}</p>
  <h4>Publications</h4><p>{d['publications']}</p>
  <h4>Skills</h4><p>{d['skills']}</p>
  <div style="background:#f0f0f0;padding:1rem;border-radius:5px;">
    <strong>Citations:</strong> {d['citations']} &nbsp; <strong>H-index:</strong> {d['h_index']} &nbsp; <strong>i10-index:</strong> {d['i10_index']}
  </div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div style="background:white;padding:1.5rem;border-radius:10px;border:1px solid #667eea;">
  <h2 style="text-align:center;">{d['full_name']}</h2>
  <p style="text-align:center;">📧 {d['email']} | 📞 {d['phone']} | 🔗 {d['linkedin']}</p>
  <p style="text-align:center;font-style:italic;">{d['position']} at {d['institution']}</p>
  <hr>
  <h4>Professional Summary</h4><p>{d['professional_summary']}</p>
  <h4>Education</h4><p>{d['education']}</p>
  <h4>Experience</h4><p>{d['experience']}</p>
  <h4>Publications</h4><p>{d['publications']}</p>
  <h4>Skills</h4><p>{d['skills']}</p>
  <h4>Awards & Honors</h4><p>{d['awards']}</p>
  <hr>
  <strong>Citations:</strong> {d['citations']} &nbsp; <strong>H-index:</strong> {d['h_index']} &nbsp; <strong>i10-index:</strong> {d['i10_index']}
</div>""", unsafe_allow_html=True)

        st.subheader("📥 Download — choose one or both styles")
        fname = safe_filename(d["full_name"])
        c1, c2, c3 = st.columns(3)

        cv_text = (
            f"ACADEMIC CV: {d['full_name']}\n{'='*60}\n"
            f"Email: {d['email']}\nPhone: {d['phone']}\nLinkedIn: {d['linkedin']}\nWebsite: {d['website']}\n"
            f"Position: {d['position']}\nInstitution: {d['institution']}\nResearch Areas: {d['research_areas']}\n\n"
            f"PROFESSIONAL SUMMARY\n{'-'*40}\n{d['professional_summary']}\n\n"
            f"EDUCATION\n{'-'*40}\n{d['education']}\n\n"
            f"EXPERIENCE\n{'-'*40}\n{d['experience']}\n\n"
            f"PUBLICATIONS\n{'-'*40}\n{d['publications']}\n\n"
            f"SKILLS\n{'-'*40}\n{d['skills']}\n\n"
            f"AWARDS & HONORS\n{'-'*40}\n{d['awards']}\n\n"
            f"RESEARCH METRICS\n{'-'*40}\n"
            f"Citations: {d['citations']}\nH-index: {d['h_index']}\ni10-index: {d['i10_index']}\n\n"
            f"Generated by {APP_CONFIG['name']} v{APP_CONFIG['version']}"
        )

        with c1:
            st.download_button("📄 Download TXT", data=cv_text.encode("utf-8"),
                                file_name=f"{fname}_CV.txt", mime="text/plain",
                                use_container_width=True, key="dl_cv_txt")
        with c2:
            academic_bytes = build_academic_cv_docx(d)
            st.download_button("🎓 Download Academic DOCX", data=academic_bytes,
                                file_name=f"{fname}_Academic_CV.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True, key="dl_cv_academic_docx")
        with c3:
            europass_bytes = build_europass_cv_docx(d)
            st.download_button("🇪🇺 Download Europass DOCX", data=europass_bytes,
                                file_name=f"{fname}_Europass_CV.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True, key="dl_cv_europass_docx")

# ============================================================================
# QR CODE GENERATOR
# ============================================================================

def render_qr_generator():
    st.header("📱 QR Code Generator")
    st.caption("Generate QR codes for URLs, text, and academic IDs")

    col1, col2 = st.columns([1, 1])
    with col1:
        qr_data = st.text_area("Enter data to encode", height=100, placeholder="https://your-website.com")
        qr_size = st.slider("QR Code Size", min_value=100, max_value=500, value=250, step=25)
        qr_color = st.color_picker("QR Code Color", "#1E88E5")
        bg_color = st.color_picker("Background Color", "#FFFFFF")

        if st.button("🎨 Generate QR Code", use_container_width=True, type="primary", key="gen_qr"):
            if qr_data:
                try:
                    import qrcode
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
                                        box_size=10, border=4)
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color=qr_color, back_color=bg_color)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    st.session_state.qr_image = buf
                    st.session_state.qr_generated = True
                    add_project(f"QR_{qr_data[:20]}", "QR Code")
                except Exception as e:
                    st.error(f"Error generating QR code: {e}")
            else:
                st.warning("Please enter data")

    with col2:
        if st.session_state.get("qr_generated", False):
            st.subheader("🖼️ QR Code Preview")
            st.image(st.session_state.qr_image, width=qr_size)
            st.download_button("📥 Download QR Code (PNG)", data=st.session_state.qr_image.getvalue(),
                                file_name="qr_code.png", mime="image/png",
                                use_container_width=True, key="dl_qr_png")

# ============================================================================
# POSTER STUDIO
# ============================================================================

THEME_COLORS = {
    "Blue": {"bg": "#f0f4f8", "primary": "#1E88E5", "secondary": "#E3F2FD"},
    "Green": {"bg": "#f0f8f0", "primary": "#2E7D32", "secondary": "#E8F5E9"},
    "Purple": {"bg": "#f4f0f8", "primary": "#7B1FA2", "secondary": "#F3E5F5"},
    "Red": {"bg": "#f8f0f0", "primary": "#C62828", "secondary": "#FFEBEE"},
    "Dark": {"bg": "#1a1a2e", "primary": "#667eea", "secondary": "#16213e"},
    "Medical": {"bg": "#f0f8ff", "primary": "#00695C", "secondary": "#E0F7FA"},
    "Nature": {"bg": "#f5faf0", "primary": "#33691E", "secondary": "#F1F8E9"},
    "IEEE": {"bg": "#ffffff", "primary": "#1565C0", "secondary": "#BBDEFB"},
    "Vibrant": {"bg": "#fff3e0", "primary": "#E65100", "secondary": "#FFE0B2"},
    "Pastel": {"bg": "#fce4ec", "primary": "#AD1457", "secondary": "#F8BBD0"},
}

def render_poster_studio():
    st.header("🎨 Poster Studio")
    st.caption("Design a professional research poster preview")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("📐 Poster Settings")
        poster_title = st.text_input("Poster Title", "My Research Poster")
        poster_size = st.selectbox("Poster Size", ["A0", "A1", "A2", "A3", "36×48 in", "42×48 in", "48×60 in"], index=1)
        poster_theme = st.selectbox("Color Theme", list(THEME_COLORS.keys()), index=0)
        sections = st.multiselect(
            "Select sections",
            ["Title", "Authors", "Abstract", "Background", "Methods", "Results", "Discussion", "Conclusion", "References"],
            default=["Title", "Authors", "Abstract", "Methods", "Results", "Conclusion"],
        )

        if st.button("🎨 Generate Poster", use_container_width=True, type="primary", key="gen_poster"):
            st.session_state.poster_generated = True
            st.session_state.poster_title = poster_title
            st.session_state.poster_sections = sections
            st.session_state.poster_theme = poster_theme
            add_project(poster_title, "Poster")

    with col2:
        if st.session_state.get("poster_generated", False):
            st.subheader("🖼️ Poster Preview")
            colors = THEME_COLORS.get(st.session_state.poster_theme, THEME_COLORS["Blue"])
            fig, ax = plt.subplots(figsize=(12, 8.5))
            ax.set_facecolor(colors["bg"])
            ax.text(0.5, 0.95, st.session_state.poster_title, fontsize=24, ha="center", va="top",
                    fontweight="bold", color=colors["primary"])
            y_pos = 0.85
            for section in st.session_state.poster_sections[:5]:
                ax.text(0.08, y_pos, section.upper(), fontsize=14, fontweight="bold", color=colors["primary"])
                ax.text(0.08, y_pos - 0.04, f"Sample {section.lower()} content goes here...", fontsize=10)
                ax.add_patch(Rectangle((0.05, y_pos - 0.14), 0.9, 0.12, fill=True,
                                        facecolor=colors["secondary"], alpha=0.3,
                                        edgecolor=colors["primary"], linewidth=1))
                y_pos -= 0.16
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            plt.tight_layout()
            st.pyplot(fig)

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
            buf.seek(0)
            plt.close(fig)
            st.download_button("📥 Download Poster (PNG)", data=buf.getvalue(),
                                file_name=f"{safe_filename(st.session_state.poster_title)}.png",
                                mime="image/png", use_container_width=True, key="dl_poster_png")

# ============================================================================
# EXPORT MANAGER
# ============================================================================

def render_export_manager():
    st.header("📦 Export Manager")
    st.caption("Manage and review the documents you've generated this session")

    if st.session_state.projects:
        for idx, project in enumerate(st.session_state.projects):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(f"**{project.get('name', 'Untitled')}**")
                st.caption(f"Type: {project.get('type', 'Unknown')}")
            with c2:
                st.caption(f"Created: {project.get('created', 'N/A')}")
            with c3:
                if st.button("🗑️", key=f"del_{project['id']}"):
                    st.session_state.projects.pop(idx)
                    st.rerun()
            st.divider()
    else:
        st.info("No projects generated yet. Build something from the sidebar!")

# ============================================================================
# MAIN
# ============================================================================

def main():
    render_sidebar()
    page = st.session_state.current_page

    dispatch = {
        "Home": render_home,
        "Assignment": render_assignment_builder,
        "Lab Report": render_lab_report,
        "Thesis": render_thesis,
        "Research Proposal": render_research_proposal,
        "Poster": render_poster_studio,
        "CV": render_cv_builder,
        "QR": render_qr_generator,
        "Export": render_export_manager,
    }
    dispatch.get(page, render_home)()

    st.markdown("---")
    st.caption(f"🎓 {APP_CONFIG['name']} v{APP_CONFIG['version']} | © {APP_CONFIG['year']}")

if __name__ == "__main__":
    main()
