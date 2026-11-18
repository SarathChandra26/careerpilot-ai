import streamlit as st
import plotly.graph_objects as go
import textwrap

# Custom Plotly Template with modern human-designed color scheme
CHART_THEME = {
    "layout": {
        "font": {"family": "Plus Jakarta Sans, sans-serif", "color": "#1E293B"},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "colorway": ["#4F46E5", "#10B981", "#F59E0B", "#6366F1", "#EC4899", "#8B5CF6"],
        "xaxis": {
            "gridcolor": "#F1F5F9",
            "zerolinecolor": "#E2E8F0",
            "tickfont": {"size": 11, "color": "#64748B"},
        },
        "yaxis": {
            "gridcolor": "#F1F5F9",
            "zerolinecolor": "#E2E8F0",
            "tickfont": {"size": 11, "color": "#64748B"},
        },
    }
}

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

/* Remove default Streamlit top padding & footer decoration */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1280px !important;
}

#MainMenu, footer, header {
    visibility: hidden;
}

/* Sidebar styling: Minimalist, clean, deep slate */
section[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: 1px solid #1E293B !important;
}

section[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}

section[data-testid="stSidebar"] hr {
    border-color: #1E293B !important;
    margin: 1.25rem 0 !important;
}

section[data-testid="stSidebar"] .stSelectbox label, 
section[data-testid="stSidebar"] p {
    color: #94A3B8 !important;
    font-size: 0.85rem !important;
}

/* Sidebar navigation links */
ul[data-testid="stSidebarNavItems"] li a {
    border-radius: 8px !important;
    padding: 0.45rem 0.75rem !important;
    transition: all 0.15s ease !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    color: #94A3B8 !important;
}

ul[data-testid="stSidebarNavItems"] li a:hover {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #FFFFFF !important;
}

ul[data-testid="stSidebarNavItems"] li a[aria-current="page"] {
    background: #4F46E5 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Typography Hierarchy */
h1 {
    font-weight: 800 !important;
    letter-spacing: -0.035em !important;
    color: #0F172A !important;
    font-size: 1.85rem !important;
    margin-bottom: 0.35rem !important;
}

h2 {
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: #1E293B !important;
    font-size: 1.35rem !important;
    margin-top: 1rem !important;
    margin-bottom: 0.35rem !important;
}

h3 {
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    color: #1E293B !important;
    font-size: 1.1rem !important;
}

/* Transform Streamlit's native containers with border=True into sleek cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border: 1px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02) !important;
    padding: 1.25rem 1.4rem !important;
    margin-bottom: 0.85rem !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #CBD5E1 !important;
    box-shadow: 0 6px 16px -2px rgba(15, 23, 42, 0.06) !important;
}

/* Custom Card Classes */
.cp-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02);
    margin-bottom: 0.85rem;
}

.cp-card-hero {
    background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%);
    border-radius: 16px;
    padding: 1.75rem 2rem;
    color: #FFFFFF !important;
    box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
    margin-bottom: 1.25rem;
}

.cp-card-hero h1, .cp-card-hero h2, .cp-card-hero p {
    color: #FFFFFF !important;
}

/* Metric / Stat Card */
.cp-stat-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.cp-stat-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 0.25rem;
}

.cp-stat-value {
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #0F172A;
}

.cp-stat-sub {
    font-size: 0.78rem;
    font-weight: 500;
    color: #10B981;
    margin-top: 0.25rem;
}

/* Modern Chip / Pill Badges */
.cp-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.55rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
}

.cp-badge-neutral {
    background: #F1F5F9;
    color: #475569;
    border: 1px solid #E2E8F0;
}

.cp-badge-brand {
    background: #EEF2FF;
    color: #4F46E5;
    border: 1px solid #C7D2FE;
}

.cp-badge-success {
    background: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
}

.cp-badge-warning {
    background: #FFFBEB;
    color: #D97706;
    border: 1px solid #FDE68A;
}

.cp-badge-danger {
    background: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
}

/* Company Initials Avatar */
.cp-avatar {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    background: #0F172A;
    color: #FFFFFF;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: -0.02em;
    margin-right: 0.85rem;
    flex-shrink: 0;
}

/* Segmented Tabs Overhaul */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background-color: #F1F5F9;
    padding: 4px;
    border-radius: 10px;
    border-bottom: none !important;
}

.stTabs [data-baseweb="tab"] {
    height: 38px;
    padding: 0 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.875rem;
    color: #64748B;
    border: none !important;
    background-color: transparent !important;
}

.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

/* Button Refinement */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: -0.01em !important;
    padding: 0.45rem 0.95rem !important;
    transition: all 0.15s ease !important;
    border: 1px solid #CBD5E1 !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
}

.stButton > button:hover {
    border-color: #94A3B8 !important;
    background: #F8FAFC !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03) !important;
}

.stButton > button[kind="primary"] {
    background: #4F46E5 !important;
    color: #FFFFFF !important;
    border-color: #4F46E5 !important;
    box-shadow: 0 2px 4px rgba(79, 70, 229, 0.25) !important;
}

.stButton > button[kind="primary"]:hover {
    background: #4338CA !important;
    border-color: #4338CA !important;
    box-shadow: 0 4px 10px rgba(79, 70, 229, 0.35) !important;
}

/* Input & Select Box Refinement */
.stTextInput > div > div > input,
.stSelectbox [data-baseweb="select"] > div,
.stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    font-size: 0.875rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12) !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #4F46E5, #10B981) !important;
    border-radius: 9999px !important;
}

/* Chat Messages */
.stChatMessage {
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    border: 1px solid #E2E8F0 !important;
    background: #FFFFFF !important;
}

.stChatMessage[data-testid="stChatMessageUser"] {
    background: #EEF2FF !important;
    border-color: #C7D2FE !important;
}

/* Code block */
code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.825rem !important;
    background: #F1F5F9 !important;
    padding: 0.15rem 0.35rem !important;
    border-radius: 5px !important;
    color: #0F172A !important;
}
</style>
"""

def inject_custom_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_html(html_str: str):
    """
    Renders pure HTML without triggering Markdown's 4-space indented code block parser.
    Removes leading whitespace from all lines so that CommonMark treats every tag as native HTML.
    """
    clean_lines = [line.lstrip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)
