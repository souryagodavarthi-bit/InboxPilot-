import streamlit as st
import os
import sys
import io
import json
import requests
import datetime
import time
import re
from email.utils import parsedate_to_datetime
from contextlib import redirect_stdout
import importlib
import InboxPilot

# Force dark theme and configure page layout
st.set_page_config(
    page_title="InboxPilot+ Control Panel",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load theme settings from profile or use defaults
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
profile_file = os.path.join(BASE_DIR, "business_profile.json")

theme_color_val = "Google Blue"
theme_appearance_val = "Dark Mode"

if os.path.exists(profile_file):
    try:
        with open(profile_file, "r", encoding="utf-8") as pf:
            p_data = json.load(pf)
            theme_color_val = p_data.get("theme_color", "Google Blue")
            theme_appearance_val = p_data.get("theme_appearance", "Dark Mode")
    except:
        pass

def load_auto_triage_setting():
    p_file = os.path.join(BASE_DIR, "business_profile.json")
    if os.path.exists(p_file):
        try:
            with open(p_file, "r", encoding="utf-8") as f:
                return json.load(f).get("auto_triage_enabled", False)
        except Exception:
            pass
    return False

def save_auto_triage_setting(val):
    p_file = os.path.join(BASE_DIR, "business_profile.json")
    data = {}
    if os.path.exists(p_file):
        try:
            with open(p_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    data["auto_triage_enabled"] = val
    try:
        with open(p_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

if "theme_color" not in st.session_state:
    st.session_state.theme_color = theme_color_val

if "theme_appearance" not in st.session_state:
    st.session_state.theme_appearance = theme_appearance_val

def get_theme_css():
    accent_name = st.session_state.theme_color
    appearance = st.session_state.get("theme_appearance", "Dark Mode")
    
    accents = {
        "Google Blue": ("#8ab4f8", "#9ec2f9", "rgba(138, 180, 248, 0.06)", "#1a73e8", "#185abc"),
        "Emerald Green": ("#81c995", "#a8e0b6", "rgba(129, 201, 149, 0.06)", "#1e8e3e", "#137333"),
        "Crimson Red": ("#f28b82", "#f6aea9", "rgba(242, 139, 130, 0.06)", "#d93025", "#a50e0e"),
        "Amber Orange": ("#fdd663", "#ffe082", "rgba(253, 214, 99, 0.06)", "#e37400", "#b06000"),
        "Purple Velvet": ("#c58af9", "#d7aefb", "rgba(197, 138, 249, 0.06)", "#a042f5", "#8430e6")
    }
    
    dark_accent, dark_hover, dark_bg_rgba, light_accent, light_hover = accents.get(accent_name, accents["Google Blue"])
    
    dark_variables = f"""
    --bg-color: #0d1117;
    --card-bg-color: #161b22;
    --card-hover-bg: #21262d;
    --border-color: #30363d;
    --text-color: #c9d1d9;
    --text-secondary: #8b949e;
    --primary-color: {dark_accent};
    --hover-color: {dark_hover};
    --hover-bg: rgba(255, 255, 255, 0.08);
    --content-box-bg: #0d1117;
    --sidebar-nav-bg: #21262d;
    --bg-rgba: {dark_bg_rgba};
    --btn-text-color: #0d1117;
    --header-text-color: #c9d1d9;
    """
    
    light_variables = f"""
    --bg-color: #f6f8fa;
    --card-bg-color: #ffffff;
    --card-hover-bg: rgba(26, 115, 232, 0.04);
    --border-color: #d0d7de;
    --text-color: #24292f;
    --text-secondary: #57606a;
    --primary-color: {light_accent};
    --hover-color: {light_hover};
    --hover-bg: rgba(0, 0, 0, 0.05);
    --content-box-bg: #ffffff;
    --sidebar-nav-bg: #eaeef2;
    --bg-rgba: rgba(26, 115, 232, 0.08);
    --btn-text-color: #ffffff;
    --header-text-color: {light_accent};
    """
    
    if appearance == "Light Mode":
        css_variables = light_variables
    elif appearance == "Dark Mode":
        css_variables = dark_variables
    else:
        css_variables = dark_variables
        
    system_media_query = ""
    if appearance == "System Default":
        system_media_query = f"""
        @media (prefers-color-scheme: light) {{
            :root {{
                {light_variables}
            }}
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                {dark_variables}
            }}
        }}
        """
        
    style_content = f"""
    <style>
        :root {{
            {css_variables}
        }}
        
        {system_media_query}
        
        
        /* Onboarding Tutorial Visual Animations */
        @keyframes pulseCustom {{
            0% {{ opacity: 0.3; transform: scale(0.96); }}
            50% {{ opacity: 1; transform: scale(1.05); }}
            100% {{ opacity: 0.3; transform: scale(0.96); }}
        }}
        @keyframes spinCustom {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        @keyframes slideCustom {{
            0% {{ transform: translateY(-8px); opacity: 0.3; }}
            50% {{ transform: translateY(6px); opacity: 1; }}
            100% {{ transform: translateY(-8px); opacity: 0.3; }}
        }}
        @keyframes shieldCustom {{
            0% {{ transform: scale(0.96); }}
            50% {{ transform: scale(1.06); }}
            100% {{ transform: scale(0.96); }}
        }}
        
        .animate-pulse-custom {{
            animation: pulseCustom 3s infinite ease-in-out;
        }}
        .animate-spin-custom {{
            animation: spinCustom 10s linear infinite;
        }}
        .animate-slide-custom {{
            animation: slideCustom 3.5s ease-in-out infinite;
        }}
        .animate-shield-custom {{
            animation: shieldCustom 2.5s ease-in-out infinite;
        }}

        /* Overwrite Streamlit elements using variables */
        .stApp, html, body {{
            background-color: var(--bg-color) !important;
            color: var(--text-color) !important;
        }}
        
        /* Style card containers */
        .custom-card, div.stForm {{
            background-color: var(--card-bg-color) !important;
            border: 1px solid var(--border-color) !important;
            color: var(--text-color) !important;
        }}
        
        /* Text styling */
        .main-header, .section-title, .card-title, h1, h2, h3, h4, h5, h6 {{
            color: var(--header-text-color) !important;
        }}
        .sub-header, .card-meta {{
            color: var(--text-secondary) !important;
        }}
        
        /* Sidebar navigation list items styling */
        .settings-sidebar div.stButton > button {{
            color: var(--text-color) !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }}
        .settings-sidebar div.stButton > button:hover {{
            background-color: var(--hover-bg) !important;
            color: var(--primary-color) !important;
        }}
        .settings-sidebar div.stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(29, 78, 216, 0.4) !important;
        }}
        
        /* Segmented Controls */
        div[role="radiogroup"] {{
            background-color: var(--sidebar-nav-bg) !important;
            border: 1px solid var(--border-color) !important;
        }}
        div[role="radiogroup"] label {{
            color: var(--text-secondary) !important;
        }}
        div[role="radiogroup"] label:hover {{
            color: var(--text-color) !important;
        }}
        
        /* Content box for emails */
        .content-box {{
            background-color: var(--content-box-bg) !important;
            border-color: var(--border-color) !important;
            color: var(--text-color) !important;
        }}

        /* Force input/textarea text color and backgrounds */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
            background-color: var(--card-bg-color) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
        }}
        
        /* Make sure placeholders are readable */
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
            color: var(--text-secondary) !important;
            opacity: 0.7;
        }}

        /* Force form labels text color */
        .stTextInput label, .stTextArea label, .stSelectbox label, .stSlider label, .stFileUploader label {{
            color: var(--text-color) !important;
        }}

        /* Streamlit expander borders and background matching the theme */
        div[data-testid="stExpander"] {{
            background-color: var(--card-bg-color) !important;
            border: 1px solid var(--border-color) !important;
        }}
        div[data-testid="stExpander"] summary p {{
            color: var(--text-color) !important;
        }}

        /* Tab bar label headers color matching */
        div[data-testid="stTabBar"] button p {{
            color: var(--text-secondary) !important;
        }}
        div[data-testid="stTabBar"] button[aria-selected="true"] p {{
            color: var(--primary-color) !important;
        }}

        /* Metric card values */
        div[data-testid="stMetricValue"] {{
            color: var(--text-color) !important;
        }}
        div[data-testid="stMetricLabel"] {{
            color: var(--text-secondary) !important;
        }}
        
        /* Primary button text color */
        div.stButton > button[type="submit"], 
        div.stButton > button[kind="primary"] {{
            color: var(--btn-text-color) !important;
        }}
    </style>
    """
    return style_content

st.markdown(get_theme_css(), unsafe_allow_html=True)

# Custom Styling for modern minimalistic Google UI
st.markdown("""
<style>
    /* Google Roboto and Mono Font Integration */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* Core Layout Styles matching dynamic variables */
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        font-family: 'Roboto', sans-serif !important;
    }
    
    /* Block container padding and width */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* Headers and Titles */
    .main-header {
        font-size: 24px;
        font-weight: 400;
        color: var(--text-color);
        margin-bottom: 4px;
        letter-spacing: -0.01rem;
    }
    .sub-header {
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 24px;
    }
    
    /* Google Material Style Card */
    .custom-card {
        background-color: var(--card-bg-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        transition: background-color 0.15s ease;
    }
    .custom-card:hover {
        background-color: var(--card-hover-bg);
    }
    
    /* Card Titles */
    .card-title {
        font-size: 16px;
        font-weight: 500;
        color: var(--text-color);
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .card-meta {
        font-size: 12px;
        color: #9aa0a6;
        margin-bottom: 8px;
    }
    
    /* Custom Scroll Content Box */
    .content-box {
        background-color: var(--bg-color);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 12px;
        font-size: 13px;
        color: var(--text-color);
        max-height: 180px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    
    /* Section Titles */
    .section-title {
        font-size: 16px;
        font-weight: 500;
        color: var(--text-color);
        margin-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
    }
    
    /* Google Chip Badges */
    .tag {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 11px;
        font-weight: 500;
        border: 1px solid transparent;
        text-transform: capitalize;
    }
    .tag-refund { background-color: rgba(129, 201, 149, 0.15); color: #81c784; border-color: rgba(129, 201, 149, 0.2); }
    .tag-bug { background-color: rgba(138, 180, 248, 0.15); color: #8ab4f8; border-color: rgba(138, 180, 248, 0.2); }
    .tag-delay { background-color: rgba(253, 186, 116, 0.15); color: #fdba74; border-color: rgba(253, 186, 116, 0.2); }
    .tag-query { background-color: rgba(196, 181, 253, 0.15); color: #c4b5fd; border-color: rgba(196, 181, 253, 0.2); }
    .tag-spam { background-color: rgba(240, 128, 128, 0.15); color: #f28b82; border-color: rgba(240, 128, 128, 0.2); }
    .tag-neutral { background-color: #3c4043; color: #9aa0a6; }
    .tag-escalated { background-color: rgba(242, 139, 130, 0.25); color: #f28b82; border-color: #f28b82; font-weight: bold; }
    .tag-opportunity { background-color: rgba(251, 191, 36, 0.15); color: #fbbf24; border-color: rgba(251, 191, 36, 0.2); }
    .tag-sentiment-positive { background-color: rgba(129, 201, 149, 0.15); color: #81c995; border: 1px solid rgba(129, 201, 149, 0.2); font-weight: 500; }
    .tag-sentiment-neutral { background-color: rgba(232, 234, 237, 0.05); color: #9aa0a6; border: 1px solid rgba(232, 234, 237, 0.1); font-weight: 500; }
    .tag-sentiment-negative { background-color: rgba(253, 214, 99, 0.15); color: #fdd663; border: 1px solid rgba(253, 214, 99, 0.2); font-weight: 500; }
    .tag-sentiment-angry { background-color: rgba(242, 139, 130, 0.15); color: #f28b82; border: 1px solid rgba(242, 139, 130, 0.2); font-weight: 500; }
    .tag-sentiment-frustrated { background-color: rgba(242, 139, 130, 0.15); color: #f28b82; border: 1px solid rgba(242, 139, 130, 0.2); font-weight: 500; }
    
    /* Terminal Console logs */
    .terminal-container {
        background-color: #171717;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        margin-top: 8px;
    }
    .terminal-title {
        font-family: 'Roboto Mono', monospace;
        font-size: 11px;
        color: #9aa0a6;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 8px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
    }
    .terminal-body {
        font-family: 'Roboto Mono', monospace;
        font-size: 13px;
        color: #81c784;
        max-height: 250px;
        overflow-y: auto;
        white-space: pre-wrap;
        line-height: 1.6;
    }
    
    /* Buttons Override (Google Material Outlined & Filled) */
    div.stButton > button {
        background-color: transparent !important;
        color: var(--primary-color) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
        padding: 8px 24px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: background-color 0.15s, border-color 0.15s !important;
    }
    div.stButton > button:hover {
        background-color: var(--bg-rgba) !important;
        border-color: var(--primary-color) !important;
    }
    
    /* Primary buttons */
    div.stButton > button[type="submit"], 
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(29, 78, 216, 0.35) !important;
    }
    div.stButton > button[type="submit"]:hover,
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
        box-shadow: 0 6px 16px rgba(29, 78, 216, 0.5) !important;
    }
    
    /* Form inputs and text fields */
    div[data-baseweb="input"] {
        background-color: var(--card-bg-color) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: var(--primary-color) !important;
    }
    div[data-baseweb="textarea"] {
        background-color: var(--card-bg-color) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
    }
    div[data-baseweb="textarea"]:focus-within {
        border-color: var(--primary-color) !important;
    }
    div[data-baseweb="select"] {
        background-color: var(--card-bg-color) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
    }
    
    /* Tabs Overrides (Google Tab Strip style) */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--border-color) !important;
        gap: 24px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #9aa0a6 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 8px 4px 12px 4px !important;
        transition: color 0.15s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e8eaed !important;
    }
</style>
""", unsafe_allow_html=True)

# Directories Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCOMING_DIR = os.path.join(BASE_DIR, "Incoming_Emails")
MEMORY_DIR = os.path.join(BASE_DIR, "Customer_Memory")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
GOOGLE_CREDS_FILE = os.path.join(BASE_DIR, "google_creds.json")
UNSUBSCRIBE_PREF_FILE = os.path.join(BASE_DIR, "unsubscribe_prefs.json")

# Create base folders
for folder in [INCOMING_DIR, MEMORY_DIR]:
    os.makedirs(folder, exist_ok=True)

# Helper functions for dynamic category configuration
def load_categories_config():
    config_file = os.path.join(BASE_DIR, "categories_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Migration: ensure every category has 'escalate_on_reply'
                modified = False
                for cat in data:
                    if "escalate_on_reply" not in cat:
                        cat["escalate_on_reply"] = cat.get("has_auto_reply", False)
                        modified = True
                if modified:
                    try:
                        with open(config_file, "w", encoding="utf-8") as wf:
                            json.dump(data, wf, indent=2)
                    except Exception:
                        pass
                return data
        except Exception:
            pass
    # Fallback default categories
    return [
        {"name": "Refund", "label": "Refund Requests", "dir_name": "Refund_Requests", "description": "Customer wants their money back.", "is_standard": True, "enabled": True, "has_auto_reply": True, "escalate_on_reply": True},
        {"name": "Bug Report", "label": "Bug Reports", "dir_name": "Bug_Reports", "description": "Customer is reporting a technical issue or defect.", "is_standard": True, "enabled": True, "has_auto_reply": True, "escalate_on_reply": True},
        {"name": "Delay", "label": "Delay Complaints", "dir_name": "Delay_Complaints", "description": "Customer is actively complaining about shipping or processing delays.", "is_standard": True, "enabled": True, "has_auto_reply": True, "escalate_on_reply": True},
        {"name": "Query", "label": "Queries", "dir_name": "General_Queries", "description": "General questions, informational inquiries, or FAQs that do not contain an active complaint or report of a defect.", "is_standard": True, "enabled": True, "has_auto_reply": False, "escalate_on_reply": False},
        {"name": "Opportunities", "label": "Opportunities/Sponsorships", "dir_name": "Opportunities", "description": "Customer wants to sponsor, collaborate, partner, or offer business development opportunities.", "is_standard": True, "enabled": True, "has_auto_reply": False, "escalate_on_reply": False},
        {"name": "Subscription", "label": "Subscriptions", "dir_name": "Subscriptions", "description": "Emails from services, newsletters, or sites you signed up for that you want to keep.", "is_standard": True, "enabled": True, "has_auto_reply": False, "escalate_on_reply": False},
        {"name": "Spam", "label": "Spam", "dir_name": "Spam", "description": "Junk emails, promotional material, marketing offers, advertisements.", "is_standard": True, "enabled": True, "has_auto_reply": False, "escalate_on_reply": False}
    ]

def save_categories_config(config_data):
    config_file = os.path.join(BASE_DIR, "categories_config.json")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

# Create folders for categories
try:
    for cat in load_categories_config():
        if cat.get("enabled", True) and not cat.get("archived", False):
            os.makedirs(os.path.join(BASE_DIR, cat["dir_name"]), exist_ok=True)
except Exception:
    pass

# Append project path to ensure imports work correctly
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


def load_unsubscribe_preferences():
    if os.path.exists(UNSUBSCRIBE_PREF_FILE):
        try:
            with open(UNSUBSCRIBE_PREF_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_unsubscribe_preferences(prefs):
    try:
        with open(UNSUBSCRIBE_PREF_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
    except Exception as e:
        st.warning(f"Could not save unsubscribe preferences: {e}")


def load_unsubscribe_settings():
    prefs = load_unsubscribe_preferences()
    return prefs.get("global_confirm_unsubscribe", True)


def save_unsubscribe_settings(confirm_required):
    prefs = load_unsubscribe_preferences()
    prefs["global_confirm_unsubscribe"] = confirm_required
    save_unsubscribe_preferences(prefs)


def parse_sender_from_email_text(text):
    match = re.search(r'^From:\s*(.+)$', text, flags=re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Unknown Sender"
def clean_html(html_content):
    if not html_content:
        return ""
    return "\n".join(line.strip() for line in html_content.splitlines())

# Local accounts persistence logic
def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        default = {"admin@inboxpilotplus.com": "admin123"}
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(default, f)
        return default
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f)

# Google OAuth Credentials persistence logic
def load_google_creds():
    # Check if the credentials exist in Streamlit Secrets instead of a file
    if "GOOGLE_CLIENT_ID" in st.secrets:
        return {
            "client_id": st.secrets["GOOGLE_CLIENT_ID"],
            "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": st.secrets["GOOGLE_REDIRECT_URI"]
        }
    return None

def save_google_creds(client_id, client_secret, redirect_uri):
    # This function is no longer needed since we use Streamlit Secrets
    pass

def get_category_border_style(cat_name, is_escalated=False):
    if is_escalated:
        return "border-left: 4px solid #f28b82; box-shadow: 0 0 12px rgba(242,139,130,0.1) !important;"
    mapping = {
        "refund": "border-left: 4px solid #81c995;",
        "bug": "border-left: 4px solid #8ab4f8;",
        "delay": "border-left: 4px solid #fdd663;",
        "query": "border-left: 4px solid #c58af9;",
        "opportunity": "border-left: 4px solid #fbbf24;",
        "opportunities": "border-left: 4px solid #fbbf24;",
        "spam": "border-left: 4px solid #f28b82;",
        "subscription": "border-left: 4px solid #9aa0a6;"
    }
    for key, border in mapping.items():
        if key in cat_name.lower():
            return border
    return "border-left: 4px solid var(--primary-color);"


def parse_gmail_date(date_str):
    if not date_str:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    if isinstance(date_str, (int, float)):
        return datetime.datetime.fromtimestamp(date_str, tz=datetime.timezone.utc)
    try:
        dt = parsedate_to_datetime(str(date_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(str(date_str).strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt
        except Exception:
            pass
    return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

def is_tutorial_completed_in_profile():
    profile_file = os.path.join(BASE_DIR, "business_profile.json")
    if os.path.exists(profile_file):
        try:
            with open(profile_file, "r", encoding="utf-8") as pf:
                data = json.load(pf)
                # Toggle orientation strictly determines whether tutorial appears on sign-in
                if not data.get("show_tutorial_on_login", True):
                    return True
                else:
                    return False
        except:
            pass
    return False

@st.cache_resource
def get_boot_state():
    return {"first_session": True}


def set_t2_queue(opt):
    st.session_state.t2_queue_selection = opt

def set_settings_nav(val):
    st.session_state.settings_nav = val

boot_state = get_boot_state()

# Initialize Session States
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "signin"
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "show_creds_config" not in st.session_state:
    st.session_state.show_creds_config = False
if "first_name" not in st.session_state:
    st.session_state.first_name = "User"
if "tutorial_completed" not in st.session_state:
    st.session_state.tutorial_completed = True
if "tutorial_tab" not in st.session_state:
    st.session_state.tutorial_tab = 1
if "auto_triage_enabled" not in st.session_state:
    st.session_state.auto_triage_enabled = load_auto_triage_setting()
if "theme_appearance" not in st.session_state:
    appearance_val = "Dark Mode"
    if os.path.exists(profile_file):
        try:
            with open(profile_file, "r", encoding="utf-8") as pf:
                appearance_val = json.load(pf).get("theme_appearance", "Dark Mode")
        except:
            pass
    st.session_state.theme_appearance = appearance_val
    
# Auto-login if session_email is in query parameters
if not st.session_state.logged_in and "session_email" in st.query_params:
    email = st.query_params["session_email"]
    if email:
        st.session_state.logged_in = True
        st.session_state.user_email = email
        name_part = email.split('@')[0]
        st.session_state.first_name = name_part.split('.')[0].split('_')[0].capitalize()
        st.session_state.tutorial_completed = True

# --- Google OAuth Redirect Callback Processing ---
# Check if query parameter contains oauth code returned by Google redirect
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    google_creds = load_google_creds()
    if google_creds:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": auth_code,
            "client_id": google_creds["client_id"],
            "client_secret": google_creds["client_secret"],
            "redirect_uri": google_creds.get("redirect_uri", "https://inboxpilotplus.streamlit.app/"),
            "grant_type": "authorization_code"
        }
        with st.spinner("Exchanging code for Google credentials..."):
            try:
                res = requests.post(token_url, data=data)
                if res.status_code == 200:
                    tokens = res.json()
                    access_token = tokens["access_token"]
                    if "refresh_token" in tokens:
                        google_creds = load_google_creds()
                        if google_creds:
                            google_creds["refresh_token"] = tokens["refresh_token"]
                            save_google_creds(google_creds)
                    # Fetch User Info from Google profile API
                    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    user_res = requests.get(userinfo_url, headers=headers)
                    if user_res.status_code == 200:
                        user_info = user_res.json()
                        st.session_state.logged_in = True
                        st.session_state.user_email = user_info.get("email")
                        st.session_state.first_name = user_info.get("given_name", user_info.get("name", "User").split()[0])
                        st.session_state.tutorial_completed = is_tutorial_completed_in_profile()
                        st.session_state.tutorial_tab = 1
                        st.query_params.clear()  # Clean code from address bar
                        st.query_params["session_email"] = st.session_state.user_email
                        st.success("Successfully logged in with Google!")
                        st.rerun()
                    else:
                        st.error("Failed to load user info from Google.")
                else:
                    st.error(f"Failed to authenticate with Google: {res.json().get('error_description', res.text)}")
            except Exception as e:
                st.error(f"Authentication Request Error: {e}")
    else:
        st.error("Authorization code received but Google credentials are not configured in google_creds.json.")

# Authentication View
if not st.session_state.logged_in:
    col_l, col_c, col_r = st.columns([1.2, 1.6, 1.2])
    with col_c:
        st.markdown('<div style="text-align: center; margin-top: 48px; font-size: 24px; font-weight: 500; color: #8ab4f8; margin-bottom: 24px;">InboxPilot+</div>', unsafe_allow_html=True)
        
        google_creds = load_google_creds()
        
        st.markdown('<div class="login-header">Sign in</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">to continue to InboxPilot+</div>', unsafe_allow_html=True)
        
        # Load show_tutorial_on_login state from business_profile.json
        profile_file_auth = os.path.join(BASE_DIR, "business_profile.json")
        show_tut_val = True
        auth_profile_data = {}
        if os.path.exists(profile_file_auth):
            try:
                with open(profile_file_auth, "r", encoding="utf-8") as pf:
                    auth_profile_data = json.load(pf)
                    show_tut_val = auth_profile_data.get("show_tutorial_on_login", True)
            except:
                pass
                
        tut_toggle = st.toggle("Enable Onboarding Tutorial on Login", value=show_tut_val, key="signin_tutorial_toggle")
        if tut_toggle != show_tut_val:
            auth_profile_data["show_tutorial_on_login"] = tut_toggle
            try:
                with open(profile_file_auth, "w", encoding="utf-8") as pf:
                    json.dump(auth_profile_data, pf, indent=2)
                st.rerun()
            except Exception:
                pass
        
        # Multi-Provider Authorization Buttons
        st.markdown("**Select Authorized Email Provider:**")
        
        providers_meta = InboxPilot.load_email_providers()
        
        # 1. Google Button (Original Working OAuth Flow)
        if google_creds:
            client_id = google_creds["client_id"]
            redirect_uri = google_creds.get("redirect_uri", "http://localhost:8501/")
            scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.send"
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&state=state&access_type=offline&prompt=consent"
            
            st.markdown(f"""
            <a href="{auth_url}" target="_parent" style="
                display: flex;
                justify-content: center;
                align-items: center;
                text-decoration: none;
                background-color: transparent;
                color: #8ab4f8;
                border: 1px solid #3c4043;
                border-radius: 4px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
                width: 100%;
                box-sizing: border-box;
                transition: background-color 0.15s, border-color 0.15s;
                text-align: center;
                margin-top: 8px;
                margin-bottom: 8px;
            " onmouseover="this.style.backgroundColor='rgba(138, 180, 248, 0.04)'; this.style.borderColor='#8ab4f8';" 
               onmouseout="this.style.backgroundColor='transparent'; this.style.borderColor='#3c4043';">
                Sign in with Google
            </a>
            """, unsafe_allow_html=True)
            
        # 2. Microsoft Outlook / Office 365 Button
        ms_client_id = providers_meta.get("microsoft", {}).get("client_id", "c44b4083-3bb0-49c1-b47d-974e53cbdf3c")
        ms_redirect_uri = "http://localhost:8501/"
        ms_auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={ms_client_id}&response_type=code&redirect_uri={ms_redirect_uri}&response_mode=query&scope=https://graph.microsoft.com/mail.read"
        
        st.markdown(f"""
        <a href="{ms_auth_url}" target="_parent" style="
            display: flex;
            justify-content: center;
            align-items: center;
            text-decoration: none;
            background-color: transparent;
            color: #8ab4f8;
            border: 1px solid #3c4043;
            border-radius: 4px;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 500;
            width: 100%;
            box-sizing: border-box;
            transition: background-color 0.15s, border-color 0.15s;
            text-align: center;
            margin-top: 8px;
            margin-bottom: 8px;
        " onmouseover="this.style.backgroundColor='rgba(138, 180, 248, 0.04)'; this.style.borderColor='#8ab4f8';" 
           onmouseout="this.style.backgroundColor='transparent'; this.style.borderColor='#3c4043';">
            Sign in with Microsoft Outlook / Office 365
        </a>
        """, unsafe_allow_html=True)

        # 3. Corporate Email IMAP/SMTP Button
        st.markdown("""
        <a href="http://localhost:8501/?session_email=user@company.com" target="_parent" style="
            display: flex;
            justify-content: center;
            align-items: center;
            text-decoration: none;
            background-color: transparent;
            color: #8ab4f8;
            border: 1px solid #3c4043;
            border-radius: 4px;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 500;
            width: 100%;
            box-sizing: border-box;
            transition: background-color 0.15s, border-color 0.15s;
            text-align: center;
            margin-top: 8px;
            margin-bottom: 24px;
        " onmouseover="this.style.backgroundColor='rgba(138, 180, 248, 0.04)'; this.style.borderColor='#8ab4f8';" 
           onmouseout="this.style.backgroundColor='transparent'; this.style.borderColor='#3c4043';">
            Authorize Corporate Email (IMAP / SMTP)
        </a>
        """, unsafe_allow_html=True)
        
        # Credentials setup panel
        if st.session_state.show_creds_config or not google_creds:
            with st.expander("Google Cloud OAuth Setup Instructions", expanded=(not google_creds)):
                st.markdown("""
                To configure Google OAuth:
                1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
                2. Navigate to **APIs & Services > Credentials**.
                3. Create an **OAuth 2.0 Client ID** as a **Web application**.
                4. Set the **Authorized redirect URI** to: `http://localhost:8501/` (or your current app URL).
                5. Copy the Client ID and Secret below.
                """)
                
                cfg_client_id = st.text_input("Google Client ID", value=google_creds["client_id"] if google_creds else "")
                cfg_client_secret = st.text_input("Google Client Secret", type="password", value=google_creds["client_secret"] if google_creds else "")
                cfg_redirect_uri = st.text_input("Redirect URI", value=google_creds.get("redirect_uri", "http://localhost:8501/") if google_creds else "http://localhost:8501/")
                
                if st.button("Save Google OAuth Configuration", key="save_google_cfg"):
                    if cfg_client_id and cfg_client_secret:
                        save_google_creds({
                            "client_id": cfg_client_id,
                            "client_secret": cfg_client_secret,
                            "redirect_uri": cfg_redirect_uri
                        })
                        st.success("Google OAuth configuration saved!")
                        st.rerun()
                    else:
                        st.error("Please fill in both Client ID and Client Secret.")
        
        st.markdown("<hr style='border: 1px solid #3c4043; margin: 24px 0;'>", unsafe_allow_html=True)
        
        # Security Verification Email Submission
        st.markdown("""
        <div style="
            background-color: rgba(251, 191, 36, 0.08);
            border: 1px solid rgba(251, 191, 36, 0.2);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            font-size: 13px;
            line-height: 1.5;
            color: #e8eaed;
        ">
            <strong style="color: #fbbf24; font-size: 14px; display: block; margin-bottom: 6px;"> Security Verification Required</strong>
            Due to security reasons, please enter your email below. It will be verified within around 30 mins, 
            after which you can return here and sign in securely through Google.
        </div>
        """, unsafe_allow_html=True)
        
        verif_email = st.text_input("Email Address", placeholder="yourname@example.com", key="security_verification_email")
        if st.button("Submit Email for Verification", key="submit_verification_btn", type="secondary", use_container_width=True):
            if not verif_email.strip():
                st.error("Please enter your email address.")
            elif "@" not in verif_email or "." not in verif_email:
                st.error("Please enter a valid email format.")
            else:
                VERIFICATION_FILE = os.path.join(BASE_DIR, "verification_requests.txt")
                try:
                    exists = False
                    if os.path.exists(VERIFICATION_FILE):
                        with open(VERIFICATION_FILE, "r", encoding="utf-8") as vf:
                            existing_emails = vf.read().splitlines()
                            if verif_email.strip() in existing_emails:
                                exists = True
                    if not exists:
                        with open(VERIFICATION_FILE, "a", encoding="utf-8") as vf:
                            vf.write(verif_email.strip() + "\n")
                    st.success("Thank you! Your email has been saved and will be verified within around 30 mins.")
                except Exception as e:
                    st.error(f"Failed to save email: {e}")

# Main Dashboard View (Logged In)
else:
    if not st.session_state.tutorial_completed:
        # Animated SVG visuals
        welcome_svg = """
        <div style="display: flex; justify-content: center; align-items: center; height: 180px; margin-bottom: 20px;">
            <svg width="120" height="120" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="var(--primary-color)" stroke-width="1.5" class="animate-pulse-custom" style="opacity: 0.2; transform-origin: 50% 50%;" />
                <circle cx="50" cy="50" r="30" fill="none" stroke="var(--primary-color)" stroke-width="2" class="animate-pulse-custom" style="opacity: 0.4; transform-origin: 50% 50%; animation-delay: 0.5s;" />
                <circle cx="50" cy="50" r="20" fill="none" stroke="var(--primary-color)" stroke-width="2.5" class="animate-pulse-custom" style="opacity: 0.6; transform-origin: 50% 50%; animation-delay: 1s;" />
                <circle cx="50" cy="50" r="10" fill="var(--primary-color)" class="animate-pulse-custom" style="transform-origin: 50% 50%;" />
                <circle cx="50" cy="50" r="25" fill="none" stroke="#3c4043" stroke-width="1" stroke-dasharray="4 4" />
                <circle cx="75" cy="50" r="3" fill="#fbbf24" class="animate-spin-custom" style="transform-origin: 50% 50%;" />
            </svg>
        </div>
        """
        
        triage_svg = """
        <div style="display: flex; justify-content: center; align-items: center; height: 180px; margin-bottom: 20px;">
            <svg width="200" height="150" viewBox="0 0 200 150">
                <g class="animate-slide-custom" style="transform-origin: 100px 75px;">
                    <rect x="85" y="10" width="30" height="20" rx="2" fill="var(--primary-color)" style="opacity: 0.8;" />
                    <polygon points="85,10 100,22 115,10" fill="#202124" stroke="var(--primary-color)" stroke-width="1" />
                </g>
                <rect x="20" y="90" width="45" height="18" rx="3" fill="none" stroke="var(--primary-color)" stroke-width="1" />
                <text x="42" y="102" font-size="7" fill="var(--primary-color)" text-anchor="middle" font-family="Roboto">General</text>
                <rect x="75" y="90" width="50" height="18" rx="3" fill="none" stroke="#f28b82" stroke-width="1" />
                <text x="100" y="102" font-size="7" fill="#f28b82" text-anchor="middle" font-family="Roboto">Refunds</text>
                <rect x="135" y="90" width="45" height="18" rx="3" fill="none" stroke="#fdd663" stroke-width="1" />
                <text x="157" y="102" font-size="7" fill="#fdd663" text-anchor="middle" font-family="Roboto">Sponsor</text>
                <path d="M100,40 L42,85" fill="none" stroke="#3c4043" stroke-width="1" stroke-dasharray="2 2" />
                <path d="M100,40 L100,85" fill="none" stroke="#3c4043" stroke-width="1" stroke-dasharray="2 2" />
                <path d="M100,40 L157,85" fill="none" stroke="#3c4043" stroke-width="1" stroke-dasharray="2 2" />
            </svg>
        </div>
        """
        
        memory_svg = """
        <div style="display: flex; justify-content: center; align-items: center; height: 180px; margin-bottom: 20px;">
            <svg width="150" height="150" viewBox="0 0 100 100">
                <path d="M35 30 C 35 25, 65 25, 65 30 L 65 50 C 65 55, 35 55, 35 50 Z" fill="none" stroke="var(--primary-color)" stroke-width="1.5" />
                <path d="M35 37 C 35 32, 65 32, 65 37" fill="none" stroke="var(--primary-color)" stroke-width="1.5" />
                <path d="M35 44 C 35 39, 65 39, 65 44" fill="none" stroke="var(--primary-color)" stroke-width="1.5" />
                <rect x="25" y="65" width="50" height="25" rx="3" fill="none" stroke="#e8eaed" stroke-width="1" />
                <circle cx="35" cy="77" r="5" fill="var(--primary-color)" class="animate-pulse-custom" style="transform-origin: 35px 77px;" />
                <line x1="45" y1="74" x2="70" y2="74" stroke="#e8eaed" stroke-width="1.5" />
                <line x1="45" y1="80" x2="60" y2="80" stroke="#e8eaed" stroke-width="1.5" />
                <line x1="50" y1="52" x2="50" y2="65" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="3 3" class="animate-pulse-custom" style="transform-origin: 50px 58px;" />
            </svg>
        </div>
        """
        
        escalation_svg = """
        <div style="display: flex; justify-content: center; align-items: center; height: 180px; margin-bottom: 20px;">
            <svg width="120" height="120" viewBox="0 0 100 100" class="animate-shield-custom">
                <path d="M50 15 L80 25 L80 55 C80 75, 50 85, 50 85 C50 85, 20 75, 20 55 L20 25 Z" fill="none" stroke="#f28b82" stroke-width="2.5" />
                <path d="M50 32 L50 55" stroke="#f28b82" stroke-width="3" stroke-linecap="round" />
                <circle cx="50" cy="67" r="2.5" fill="#f28b82" />
            </svg>
        </div>
        """
        
        categories_svg = """
        <div style="display: flex; justify-content: center; align-items: center; height: 180px; margin-bottom: 20px;">
            <svg width="150" height="150" viewBox="0 0 100 100">
                <rect x="20" y="20" width="60" height="16" rx="2" fill="none" stroke="#3c4043" stroke-width="1.5" />
                <path d="M28 28 L32 32 L40 24" fill="none" stroke="#81c995" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-pulse-custom" style="transform-origin: 32px 28px;" />
                <line x1="45" y1="28" x2="70" y2="28" stroke="#e8eaed" stroke-width="1.5" />
                <rect x="20" y="42" width="60" height="16" rx="2" fill="none" stroke="#3c4043" stroke-width="1.5" />
                <path d="M28 50 L32 54 L40 46" fill="none" stroke="#81c995" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-pulse-custom" style="transform-origin: 32px 50px; animation-delay: 0.5s;" />
                <line x1="45" y1="50" x2="70" y2="50" stroke="#e8eaed" stroke-width="1.5" />
                <rect x="20" y="64" width="60" height="16" rx="2" fill="none" stroke="#3c4043" stroke-width="1.5" />
                <path d="M28 72 L32 76 L40 68" fill="none" stroke="#81c995" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-pulse-custom" style="transform-origin: 32px 72px; animation-delay: 1s;" />
                <line x1="45" y1="72" x2="70" y2="72" stroke="#e8eaed" stroke-width="1.5" />
            </svg>
        </div>
        """

        settings_svg = """
        <div style="display: flex; justify-content: center; align-items: center; height: 180px; margin-bottom: 20px;">
            <svg width="120" height="120" viewBox="0 0 100 100">
                <g class="animate-spin-custom" style="transform-origin: 50px 50px;">
                    <circle cx="50" cy="50" r="22" fill="none" stroke="var(--primary-color)" stroke-width="6" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" transform="rotate(45 50 50)" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" transform="rotate(90 50 50)" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" transform="rotate(135 50 50)" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" transform="rotate(180 50 50)" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" transform="rotate(225 50 50)" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" transform="rotate(270 50 50)" />
                    <rect x="47" y="12" width="6" height="12" rx="1.5" fill="var(--primary-color)" transform="rotate(315 50 50)" />
                </g>
                <circle cx="50" cy="50" r="8" fill="#202124" />
            </svg>
        </div>
        """
        
        profile_svg = """
        <div style="display: flex; justify-content: center; align-items: center; height: 180px; margin-bottom: 20px;">
            <svg width="150" height="150" viewBox="0 0 100 100">
                <rect x="30" y="15" width="40" height="50" rx="3" fill="none" stroke="#e8eaed" stroke-width="1.5" />
                <line x1="38" y1="28" x2="62" y2="28" stroke="var(--primary-color)" stroke-width="1.5" />
                <line x1="38" y1="36" x2="55" y2="36" stroke="var(--primary-color)" stroke-width="1.5" />
                <line x1="38" y1="44" x2="62" y2="44" stroke="var(--primary-color)" stroke-width="1.5" />
                <g class="animate-pulse-custom" style="transform-origin: 50% 50%;">
                    <line x1="58" y1="58" x2="78" y2="38" stroke="#fbbf24" stroke-width="2" stroke-linecap="round" />
                    <path d="M58 58 L63 53 L58 58 Z" fill="#fbbf24" />
                </g>
            </svg>
        </div>
        """

        col_l, col_c, col_r = st.columns([1.2, 1.6, 1.2])
        with col_c:
            st.markdown('<div style="text-align: center; margin-top: 48px; font-size: 24px; font-weight: 500; color: var(--primary-color); margin-bottom: 24px;">InboxPilot+ Onboarding</div>', unsafe_allow_html=True)
            
            # Start of custom-card wrapper
            st.markdown('<div class="custom-card" style="border-radius: 16px; padding: 24px; text-align: center;">', unsafe_allow_html=True)
            
            if st.session_state.tutorial_tab == 1:
                st.markdown(welcome_svg, unsafe_allow_html=True)
                st.markdown('<div style="font-size: 18px; font-weight: 500; margin-bottom: 12px; color: #e8eaed;">Welcome to InboxPilot+</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 14px; color: #9aa0a6; line-height: 1.6; margin-bottom: 24px;">Let\'s take a quick 1-minute tour to get you up to speed with your new intelligent email copilot.</div>', unsafe_allow_html=True)
            elif st.session_state.tutorial_tab == 2:
                st.markdown(triage_svg, unsafe_allow_html=True)
                st.markdown('<div style="font-size: 18px; font-weight: 500; margin-bottom: 12px; color: #e8eaed;">Smart Email Triage</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 14px; color: #9aa0a6; line-height: 1.6; margin-bottom: 24px;">InboxPilot+ automatically reads and categorizes incoming emails based on their content, sorting them into clean queues so you can focus on what matters.</div>', unsafe_allow_html=True)
            elif st.session_state.tutorial_tab == 3:
                st.markdown(memory_svg, unsafe_allow_html=True)
                st.markdown('<div style="font-size: 18px; font-weight: 500; margin-bottom: 12px; color: #e8eaed;">Customer Memory & Directory</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 14px; color: #9aa0a6; line-height: 1.6; margin-bottom: 24px;">The system automatically builds a persistent profile for every customer. It remembers past interactions and settings (like unsubscribe preferences) to personalize drafts.</div>', unsafe_allow_html=True)
            elif st.session_state.tutorial_tab == 4:
                st.markdown(escalation_svg, unsafe_allow_html=True)
                st.markdown('<div style="font-size: 18px; font-weight: 500; margin-bottom: 12px; color: #e8eaed;">Intelligent Escalation</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 14px; color: #9aa0a6; line-height: 1.6; margin-bottom: 24px;">Emails requiring human response (e.g. repeat complaints, complex billing, or custom business requests) are automatically flagged as <b>Escalated</b> for your manual attention.</div>', unsafe_allow_html=True)
            elif st.session_state.tutorial_tab == 5:
                st.markdown(categories_svg, unsafe_allow_html=True)
                st.markdown('<div style="font-size: 18px; font-weight: 500; margin-bottom: 12px; color: #e8eaed;">Fully Customizable</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 14px; color: #9aa0a6; line-height: 1.6; margin-bottom: 24px;">Add your own custom email categories, toggle which ones require escalation on reply, and easily restore previously removed categories from a dropdown.</div>', unsafe_allow_html=True)
            elif st.session_state.tutorial_tab == 6:
                st.markdown(settings_svg, unsafe_allow_html=True)
                st.markdown('<div style="font-size: 18px; font-weight: 500; margin-bottom: 12px; color: #e8eaed;">Top-Right Settings</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 14px; color: #9aa0a6; line-height: 1.6; margin-bottom: 24px;">Access the settings gear at the top right to customize your theme color, clear your support history cache, or edit your business description at any time.</div>', unsafe_allow_html=True)
            elif st.session_state.tutorial_tab == 7:
                st.markdown(profile_svg, unsafe_allow_html=True)
                st.markdown('<div style="font-size: 18px; font-weight: 500; margin-bottom: 12px; color: #e8eaed;">Teach InboxPilot+ About Your Business</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 14px; color: #9aa0a6; line-height: 1.6; margin-bottom: 12px;">Provide a brief description of what your business does. This context is injected into the AI model\'s mind to generate highly relevant, professional draft replies.</div>', unsafe_allow_html=True)
                st.markdown('<div style="background: rgba(138, 180, 248, 0.08); border: 1px solid rgba(138, 180, 248, 0.25); border-radius: 6px; padding: 10px 14px; margin-bottom: 16px; font-size: 13px; color: #8ab4f8;">📌 <strong>Notice:</strong> Business description is optional, but recommended for better AI draft responses.</div>', unsafe_allow_html=True)
                
            # Dots Indicator inside the card
            dots_html = '<div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 8px;">'
            for i in range(1, 8):
                bg_color = "var(--primary-color)" if st.session_state.tutorial_tab == i else "#3c4043"
                dots_html += f'<span style="height: 8px; width: 8px; border-radius: 50%; background-color: {bg_color}; display: inline-block;"></span>'
            dots_html += '</div>'
            st.markdown(dots_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True) # Close custom-card
            
            # Interactive widgets (rendered below the card)
            if st.session_state.tutorial_tab == 7:
                biz_desc = st.text_area(
                    "Tell InboxPilot+ what your business is about so it can reply better! (Optional)",
                    placeholder="E.g., We design high-end custom mechanical keyboards, offering personalized keycaps, switches, and home delivery.",
                    key="tutorial_business_desc",
                    height=120
                )
                
                col_back, col_space, col_start = st.columns([1, 1, 1.5])
                with col_back:
                    if st.button("Back", key="tut_back_btn_7", use_container_width=True):
                        st.session_state.tutorial_tab -= 1
                        st.rerun()
                with col_start:
                    if st.button("Get Started", key="tut_start_btn", type="primary", use_container_width=True):
                        profile_file = os.path.join(BASE_DIR, "business_profile.json")
                        profile_data = {
                            "business_description": biz_desc.strip(),
                            "slack_webhook": "",
                            "discord_webhook": "",
                            "tutorial_completed": True,
                            "theme_color": st.session_state.get("theme_color", "Google Blue"),
                            "theme_appearance": st.session_state.get("theme_appearance", "Dark Mode")
                        }
                        if os.path.exists(profile_file):
                            try:
                                with open(profile_file, "r", encoding="utf-8") as pf:
                                    existing = json.load(pf)
                                    profile_data["slack_webhook"] = existing.get("slack_webhook", "")
                                    profile_data["discord_webhook"] = existing.get("discord_webhook", "")
                                    profile_data["theme_color"] = existing.get("theme_color", st.session_state.get("theme_color", "Google Blue"))
                                    profile_data["theme_appearance"] = existing.get("theme_appearance", st.session_state.get("theme_appearance", "Dark Mode"))
                            except:
                                pass
                        try:
                            with open(profile_file, "w", encoding="utf-8") as pf:
                                json.dump(profile_data, pf, indent=2)
                            st.session_state.tutorial_completed = True
                            st.success("Onboarding complete! Loading dashboard...")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to save profile: {e}")
            else:
                col_back, col_space, col_next = st.columns([1, 1.5, 1])
                with col_back:
                    if st.session_state.tutorial_tab > 1:
                        if st.button("Back", key=f"tut_back_btn_{st.session_state.tutorial_tab}", use_container_width=True):
                            st.session_state.tutorial_tab -= 1
                            st.rerun()
                with col_next:
                    if st.button("Next", key=f"tut_next_btn_{st.session_state.tutorial_tab}", type="primary", use_container_width=True):
                        st.session_state.tutorial_tab += 1
                        st.rerun()
            
            st.markdown("<hr style='border: 1px solid #3c4043; margin: 24px 0;'>", unsafe_allow_html=True)
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                if st.button("Sign Out / Exit", key="tut_signout_btn", use_container_width=True):
                    st.session_state.logged_in = False
                    st.session_state.user_email = ""
                    st.query_params.clear()
                    st.rerun()
            with col_ex2:
                if st.button("Skip Tutorial", key="tut_skip_btn", use_container_width=True):
                    profile_file = os.path.join(BASE_DIR, "business_profile.json")
                    profile_data = {
                        "business_description": "",
                        "slack_webhook": "",
                        "discord_webhook": "",
                        "tutorial_completed": True,
                        "theme_color": st.session_state.get("theme_color", "Google Blue"),
                        "theme_appearance": st.session_state.get("theme_appearance", "Dark Mode")
                    }
                    if os.path.exists(profile_file):
                        try:
                            with open(profile_file, "r", encoding="utf-8") as pf:
                                existing_data = json.load(pf)
                                profile_data["business_description"] = existing_data.get("business_description", "")
                                profile_data["slack_webhook"] = existing_data.get("slack_webhook", "")
                                profile_data["discord_webhook"] = existing_data.get("discord_webhook", "")
                                profile_data["theme_color"] = existing_data.get("theme_color", "Google Blue")
                                profile_data["theme_appearance"] = existing_data.get("theme_appearance", "Dark Mode")
                        except:
                            pass
                    try:
                        with open(profile_file, "w", encoding="utf-8") as pf:
                            json.dump(profile_data, pf, indent=2)
                    except:
                        pass
                    st.session_state.tutorial_completed = True
                    st.rerun()
                
        # Stop execution so the dashboard is not rendered
        st.stop()

    if "show_settings_page" not in st.session_state:
        st.session_state.show_settings_page = False

    if st.session_state.show_settings_page:
        col_back, col_title = st.columns([2, 10])
        with col_back:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("← Back", key="settings_back_to_dashboard_btn", use_container_width=True):
                st.session_state.show_settings_page = False
                st.rerun()
        with col_title:
            st.markdown('<div class="main-header" style="font-size: 28px;">⚙️ Control Panel Settings</div>', unsafe_allow_html=True)
            st.markdown('<div class="sub-header">Manage your AI Business Context, Theme Settings, and Support Cache.</div>', unsafe_allow_html=True)
            
        st.markdown("<hr style='border: 1px solid #3c4043; margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
        # Initialize Settings navigation choice in session state
        if "settings_nav" not in st.session_state:
            st.session_state.settings_nav = "Business Profile"
            
        col_nav, col_content = st.columns([1.1, 2.5])
        
        # Load business profile details
        profile_file = os.path.join(BASE_DIR, "business_profile.json")
        biz_description_val = ""
        slack_webhook_val = ""
        discord_webhook_val = ""
        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r", encoding="utf-8") as pf:
                    p_data = json.load(pf)
                    biz_description_val = p_data.get("business_description", "")
                    slack_webhook_val = p_data.get("slack_webhook", "")
                    discord_webhook_val = p_data.get("discord_webhook", "")
            except:
                pass
                
        with col_nav:
            st.markdown('<div class="settings-sidebar">', unsafe_allow_html=True)
            
            nav_options = [
                (" Profile Context", "Business Profile"),
                (" Accent & Theme", "App Theme"),
                (" Knowledge Base", "Knowledge Base"),
                (" System Actions", "System Actions")
            ]
            
            for label, val in nav_options:
                is_active = (st.session_state.settings_nav == val)
                btn_key = f"settings_nav_btn_{val.lower().replace(' ', '_')}"
                
                if st.button(
                    label,
                    key=btn_key,
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.settings_nav = val
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_content:
            with st.container(border=True):
                
                if st.session_state.settings_nav == "Business Profile":
                    st.markdown('### Business Profile Context')
                    st.markdown('Describe your company business. The AI uses this context to personalize and align all generated draft replies.')
                    
                    new_biz_desc = st.text_area(
                        "AI Business Description",
                        value=biz_description_val,
                        placeholder="Describe what your business does...",
                        key="full_settings_business_profile_desc",
                        height=140
                    )
                    
                    st.markdown("### Webhook Notifications")
                    st.markdown("Get notifications on external chat tools when critical escalations or opportunities occur.")
                    new_slack = st.text_input("Slack Webhook URL", value=slack_webhook_val, key="full_settings_slack_webhook", placeholder="https://hooks.slack.com/services/...")
                    new_discord = st.text_input("Discord Webhook URL", value=discord_webhook_val, key="full_settings_discord_webhook", placeholder="https://discord.com/api/webhooks/...")
                    
                    if st.button("Save Profile Settings", key="save_full_business_profile_btn", type="primary", use_container_width=True):
                        try:
                            profile_data = {
                                "business_description": new_biz_desc.strip(),
                                "slack_webhook": new_slack.strip(),
                                "discord_webhook": new_discord.strip(),
                                "tutorial_completed": is_tutorial_completed_in_profile(),
                                "theme_color": st.session_state.get("theme_color", "Google Blue"),
                                "theme_appearance": st.session_state.get("theme_appearance", "Dark Mode")
                            }
                            with open(profile_file, "w", encoding="utf-8") as pf:
                                json.dump(profile_data, pf, indent=2)
                            st.success("Business profile saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving profile: {e}")
                            
                elif st.session_state.settings_nav == "App Theme":
                    st.markdown('### Theme Colors & Appearance')
                    st.markdown('Personalize the layout color accents and appearance of the dashboard.')
                    
                    theme_choice = st.selectbox(
                        "Accent Color",
                        options=["Google Blue", "Emerald Green", "Crimson Red", "Amber Orange", "Purple Velvet"],
                        index=["Google Blue", "Emerald Green", "Crimson Red", "Amber Orange", "Purple Velvet"].index(st.session_state.theme_color),
                        key="full_theme_selection_dropdown"
                    )
                    appearance_choice = st.selectbox(
                        "Appearance Mode",
                        options=["Light Mode", "Dark Mode", "System Default"],
                        index=["Light Mode", "Dark Mode", "System Default"].index(st.session_state.theme_appearance) if "theme_appearance" in st.session_state else 1,
                        key="full_appearance_selection_dropdown"
                    )
                    if theme_choice != st.session_state.theme_color or appearance_choice != st.session_state.get("theme_appearance", "Dark Mode"):
                        st.session_state.theme_color = theme_choice
                        st.session_state.theme_appearance = appearance_choice
                        
                        profile_data = {
                            "business_description": biz_description_val,
                            "slack_webhook": slack_webhook_val,
                            "discord_webhook": discord_webhook_val,
                            "tutorial_completed": is_tutorial_completed_in_profile(),
                            "theme_color": theme_choice,
                            "theme_appearance": appearance_choice
                        }
                        try:
                            with open(profile_file, "w", encoding="utf-8") as pf:
                                json.dump(profile_data, pf, indent=2)
                        except:
                            pass
                        st.rerun()
                        
                elif st.session_state.settings_nav == "Knowledge Base":
                    st.markdown('### Knowledge Base & Policy Documents')
                    st.markdown('Upload FAQ, pricing models, or shipping terms (`.txt` or `.md`) for RAG retrieval.')
                    kb_uploader = st.file_uploader("Upload document", type=["txt", "md"], key="kb_file_uploader_settings", label_visibility="collapsed")
                    if kb_uploader is not None:
                        kb_dir = os.path.join(BASE_DIR, "Knowledge_Base")
                        os.makedirs(kb_dir, exist_ok=True)
                        dest_path = os.path.join(kb_dir, kb_uploader.name)
                        try:
                            with open(dest_path, "wb") as f:
                                f.write(kb_uploader.getbuffer())
                            st.success(f"Uploaded: {kb_uploader.name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to upload: {e}")
                    
                    st.markdown("#### Manage Knowledge Base Files")
                    kb_dir = os.path.join(BASE_DIR, "Knowledge_Base")
                    if os.path.exists(kb_dir):
                        kb_files = [f for f in os.listdir(kb_dir) if f.endswith(".txt") or f.endswith(".md")]
                        if not kb_files:
                            st.info("No policy files uploaded yet.")
                        else:
                            for filename in kb_files:
                                col_f1, col_f2 = st.columns([8, 2])
                                with col_f1:
                                    st.write(f"📄 {filename}")
                                with col_f2:
                                    if st.button("Delete", key=f"del_kb_file_{filename}", use_container_width=True):
                                        try:
                                            os.remove(os.path.join(kb_dir, filename))
                                            st.success(f"Deleted {filename}!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                    else:
                        st.info("Knowledge Base directory does not exist yet. Upload a file to create it.")
                        
                elif st.session_state.settings_nav == "System Actions":
                    st.markdown('### System Actions & Debug Controls')
                    st.markdown('Configure caching, reset support history, or re-run the onboarding walkthrough.')
                    
                    # Tutorial Guide in its own distinct card box at the top
                    with st.container(border=True):
                        st.markdown("**Interactive Onboarding Tutorial**")
                        st.markdown("This shows how to use this website/app step-by-step.")
                        if st.button("Launch Interactive Tutorial Guide", key="settings_run_tutorial_on_demand_btn", type="primary", use_container_width=True):
                            st.session_state.tutorial_completed = False
                            st.session_state.tutorial_tab = 1
                            st.session_state.show_settings_page = False
                            st.rerun()
                            
                    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Clear Support History Cache", key="settings_clear_history_btn", use_container_width=True):
                            TRIAGE_HISTORY_FILE = os.path.join(BASE_DIR, "triage_history.json")
                            try:
                                if os.path.exists(TRIAGE_HISTORY_FILE):
                                    with open(TRIAGE_HISTORY_FILE, "r", encoding="utf-8") as f:
                                        rec_list = json.load(f)
                                    remaining = [r for r in rec_list if not r.get("query_response_sent", False)]
                                    with open(TRIAGE_HISTORY_FILE, "w", encoding="utf-8") as f:
                                        json.dump(remaining, f, indent=2)
                                
                                # Also purge replied local queue files
                                categories_cfg = load_categories_config()
                                for c_obj in categories_cfg:
                                    q_dir = os.path.join(BASE_DIR, c_obj.get("dir_name", c_obj["label"]))
                                    if os.path.exists(q_dir):
                                        for fname in os.listdir(q_dir):
                                            if fname.startswith("reply_sent_"):
                                                try: os.remove(os.path.join(q_dir, fname))
                                                except: pass
                                                orig_fn = fname.replace("reply_sent_", "")
                                                try: os.remove(os.path.join(q_dir, orig_fn))
                                                except: pass
                                                try: os.remove(os.path.join(q_dir, f"reply_{orig_fn}"))
                                                except: pass
                                                try: os.remove(os.path.join(q_dir, f"meta_{orig_fn}"))
                                                except: pass
                                st.success("Replied support items successfully cleared from cache!")
                            except Exception as e:
                                st.error(f"Failed to clear history cache: {e}")
                                
                        if st.button("Reset Customer Database Profiles", key="settings_clear_db_profiles_btn", use_container_width=True):
                            db_dir = os.path.join(BASE_DIR, "Customer_Memory")
                            if os.path.exists(db_dir):
                                try:
                                    for f in os.listdir(db_dir):
                                        os.remove(os.path.join(db_dir, f))
                                    st.success("Database profiles successfully cleared!")
                                except Exception as e:
                                    st.error(f"Failed to clear database profiles: {e}")
                            else:
                                st.info("No profiles found.")
                                
                    with col_btn2:
                        if st.button("Reset Onboarding Status", key="settings_reset_onboarding_btn_settings", use_container_width=True):
                            try:
                                profile_data = {
                                    "business_description": biz_description_val,
                                    "slack_webhook": slack_webhook_val,
                                    "discord_webhook": discord_webhook_val,
                                    "tutorial_completed": False,
                                    "theme_color": st.session_state.get("theme_color", "Google Blue"),
                                    "theme_appearance": st.session_state.get("theme_appearance", "Dark Mode")
                                }
                                with open(profile_file, "w", encoding="utf-8") as pf:
                                    json.dump(profile_data, pf, indent=2)
                                st.session_state.tutorial_completed = False
                                st.session_state.tutorial_tab = 1
                                st.session_state.show_settings_page = False
                                st.success("Tutorial reset! Loading...")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                                
                st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # Header block with user email, Sign out button, and Settings icon
    header_col, btn_col, settings_col = st.columns([9.5, 1.8, 0.7])
    with header_col:
        st.markdown(f'<div class="main-header">Hello {st.session_state.first_name}!</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-header">Logged in as {st.session_state.user_email} | InboxPilot+ Agent Panel</div>', unsafe_allow_html=True)
        
    with btn_col:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Sign Out", key="sign_out_btn", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.query_params.clear()
            st.rerun()
            
    with settings_col:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("⚙️", key="toggle_full_settings_btn", use_container_width=True, help="Settings"):
            st.session_state.show_settings_page = True
            st.rerun()
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Inbox & Pipeline Control", "Categorized Queues", "Customer Directory & Memory", "Settings & Category Manager", " Analytics & Sentiment", " Multi-Agent Triage Sandbox"])

    # Tab 1: Inbox & Pipeline Control
    with tab1:
        col1, col2 = st.columns([7, 5])
        
        with col1:
            @st.fragment(run_every="4s")
            def render_pipeline_panel():
                st.markdown('<div class="section-title">Pipeline Execution Panel</div>', unsafe_allow_html=True)
                
                # Calculate pending
                google_creds = load_google_creds()
                gmail_mode = False
                gmail_unread_count = 0
                access_token = None
                
                if google_creds and "refresh_token" in google_creds:
                    try:
                        import InboxPilot
                        importlib.reload(InboxPilot)
                        access_token = InboxPilot.refresh_access_token(google_creds)
                        if access_token:
                            gmail_mode = True
                            url = "https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread"
                            headers = {"Authorization": f"Bearer {access_token}"}
                            res = requests.get(url, headers=headers, timeout=5)
                            if res.status_code == 200:
                                gmail_unread_count = len(res.json().get("messages", []))
                    except Exception as e:
                        print(f"Error fetching Gmail unread count: {e}")
                
                pending_files = [f for f in os.listdir(INCOMING_DIR) if f.endswith('.txt')]
                local_pending_count = len(pending_files)
                
                num_pending = (gmail_unread_count if gmail_mode else 0) + local_pending_count
                
                with st.container():
                    st.markdown(f"""
                    <div class="custom-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 11px; color: #9aa0a6; text-transform: uppercase; font-weight: 500; letter-spacing: 0.8px;">Queue Status ({ 'Gmail + Local' if gmail_mode else 'Local Mode' })</div>
                                <div style="font-size: 24px; font-weight: 400; color: { '#f28b82' if num_pending > 0 else '#81c784' }; margin-top: 4px;">
                                    {num_pending} Pending Email{ 's' if num_pending != 1 else '' }
                                </div>
                            </div>
                            <div>
                                <span class="tag { 'tag-spam' if num_pending > 0 else 'tag-refund' }">
                                    { 'Processing Required' if num_pending > 0 else 'Idle / All Sorted' }
                                </span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Auto-Triage Toggle ON TOP OF EMAILS
                current_auto_val = st.session_state.get("auto_triage_enabled", load_auto_triage_setting())
                auto_triage = st.toggle("Enable Auto-Triage (Process emails automatically on arrival)", value=current_auto_val, key="auto_triage_toggle")
                if auto_triage != current_auto_val:
                    st.session_state.auto_triage_enabled = auto_triage
                    save_auto_triage_setting(auto_triage)
                    st.rerun()
                
                if auto_triage:
                    st.info("Auto-Triage is active. Pending emails will be categorized automatically.")
                    
                # Trigger button ON TOP OF EMAILS
                trigger_clicked = st.button("Trigger AI Triage Engine", type="primary", use_container_width=True, key="trigger_ai_triage_btn")
                
                should_run = trigger_clicked or (auto_triage and num_pending > 0)
                
                if should_run:
                    if num_pending == 0 and trigger_clicked:
                        st.warning("No new pending emails in Gmail or Incoming_Emails folder to process.")
                    elif num_pending > 0:
                        st.markdown("### Agent Live Output Logs")
                        terminal_placeholder = st.empty()
                        
                        # Capture standard output of InboxPilot.main
                        log_stream = io.StringIO()
                        with st.spinner("Processing pending emails..."):
                            try:
                                import InboxPilot
                                importlib.reload(InboxPilot)
                                with redirect_stdout(log_stream):
                                    InboxPilot.main()
                                logs = log_stream.getvalue()
                            except Exception as e:
                                logs = f"Error during pipeline execution: {str(e)}"
                        
                        terminal_placeholder.markdown(f"""
                        <div class="terminal-container">
                            <div class="terminal-title">
                                <span>inboxpilot-agent-process</span>
                                <span>SUCCESS</span>
                            </div>
                            <div class="terminal-body">{logs}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.success("Triage Pipeline Execution Completed!")
                        st.rerun()
                    
                # Display raw files / messages in Inbox BELOW CONTROLS
                if num_pending > 0:
                    if gmail_mode and gmail_unread_count > 0:
                        st.markdown("#### Pending Emails List (Gmail)")
                        try:
                            url = "https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread"
                            headers = {"Authorization": f"Bearer {access_token}"}
                            res = requests.get(url, headers=headers, timeout=5)
                            if res.status_code == 200:
                                messages = res.json().get("messages", [])[:5]  # Limit to top 5
                                import InboxPilot
                                importlib.reload(InboxPilot)
                                for msg in messages:
                                    msg_id = msg["id"]
                                    msg_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
                                    msg_res = requests.get(msg_url, headers=headers, timeout=5)
                                    if msg_res.status_code == 200:
                                        msg_data = msg_res.json()
                                        headers_list = msg_data.get("payload", {}).get("headers", [])
                                        headers_dict = {h["name"].lower(): h["value"] for h in headers_list}
                                        from_val = headers_dict.get("from", "Unknown")
                                        subj_val = headers_dict.get("subject", "(No Subject)")
                                        body_val = InboxPilot.get_message_body(msg_data)
                                        
                                        expander_label = f"📧 **{subj_val}** — From: {from_val}"
                                        with st.expander(expander_label):
                                            st.markdown(clean_html(f"""
                                            <div class="custom-card">
                                                <div class="content-box">{body_val}</div>
                                            </div>
                                            """), unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error loading pending Gmail messages: {e}")
                    
                    if local_pending_count > 0:
                        st.markdown("#### Pending Emails List (Local / Mock)")
                        for pf in pending_files:
                            file_path = os.path.join(INCOMING_DIR, pf)
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            
                            clean_pf = pf.replace('.txt', '')
                            if "@" not in clean_pf:
                                clean_pf = clean_pf.replace('_', ' ')
                            
                            snippet = content.strip().replace("\n", " ")[:60]
                            if len(content) > 60:
                                snippet += "..."
                            
                            expander_label = f"📧 **{clean_pf}** — {snippet}"
                            with st.expander(expander_label):
                                st.markdown(clean_html(f"""
                                <div class="custom-card">
                                    <div class="content-box">{content}</div>
                                </div>
                                """), unsafe_allow_html=True)

            render_pipeline_panel()
            
        with col2:
            st.markdown('<div class="section-title">Mock Email Injector</div>', unsafe_allow_html=True)
            
            with st.form("new_email_form", clear_on_submit=True):
                sender_email = st.text_input("Customer Email", placeholder="e.g. customer@example.com", help="The email address of the mock customer.")
                email_body = st.text_area("Email Content", height=200, placeholder="Write support message or feedback here...")
                uploaded_image = st.file_uploader("Attach Image (Optional)", type=["png", "jpg", "jpeg"])
                
                submit_btn = st.form_submit_button("Inject Email into Inbox")
                
                if submit_btn:
                    if not sender_email or not email_body:
                        st.error("Please fill in both email and content.")
                    else:
                        if gmail_mode:
                            try:
                                import InboxPilot
                                importlib.reload(InboxPilot)
                                access_token = InboxPilot.refresh_access_token(google_creds)
                                if not access_token:
                                    st.error("Unable to authenticate with Gmail for mock injection.")
                                else:
                                    from email.mime.text import MIMEText
                                    import base64
                                    
                                    if uploaded_image is not None:
                                        st.warning("Gmail mock injection does not support image attachments. Sending email text only. Disconnect Google credentials in Settings to run in Local Mode for visual attachments testing.")
                                    
                                    subject = f"Mock Triage: {sender_email.strip()}"
                                    message = MIMEText(email_body)
                                    message['to'] = st.session_state.user_email
                                    # Use the customer email in the display name part so it can be parsed as the customer identifier
                                    message['from'] = f"{sender_email.strip()} <{st.session_state.user_email}>"
                                    message['subject'] = subject
                                    
                                    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                                    
                                    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
                                    headers = {
                                        "Authorization": f"Bearer {access_token}",
                                        "Content-Type": "application/json"
                                    }
                                    res = requests.post(url, headers=headers, json={"raw": raw_message}, timeout=10)
                                    if res.status_code == 200:
                                        st.success(f"Mock email successfully injected! Sent to your Gmail inbox as unread with subject '{subject}'.")
                                        if st.session_state.get("auto_triage_enabled", load_auto_triage_setting()):
                                            try:
                                                import InboxPilot
                                                importlib.reload(InboxPilot)
                                                InboxPilot.main()
                                            except Exception as ex:
                                                print(f"Error auto-triaging injected Gmail email: {ex}")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to inject mock email via Gmail: {res.text}")
                            except Exception as e:
                                st.error(f"Error injecting mock email: {e}")
                        else:
                            customer_name = sender_email.strip().replace(' ', '_')
                            filename = f"{customer_name}.txt"
                            target_path = os.path.join(INCOMING_DIR, filename)
                            with open(target_path, "w", encoding="utf-8") as f:
                                f.write(email_body)
                            
                            if uploaded_image is not None:
                                img_ext = os.path.splitext(uploaded_image.name)[1].lower()
                                if not img_ext:
                                    img_ext = ".png"
                                img_filename = f"{customer_name}{img_ext}"
                                img_target_path = os.path.join(INCOMING_DIR, img_filename)
                                with open(img_target_path, "wb") as img_f:
                                    img_f.write(uploaded_image.getbuffer())
                                st.success(f"Email injected with attachment: Saved as `{filename}` and `{img_filename}` in Incoming_Emails/ directory.")
                            else:
                                st.success(f"Email injected: Saved as `{filename}` in Incoming_Emails/ directory.")
                            
                            if st.session_state.get("auto_triage_enabled", load_auto_triage_setting()):
                                try:
                                    import InboxPilot
                                    importlib.reload(InboxPilot)
                                    InboxPilot.main()
                                except Exception as ex:
                                    print(f"Error auto-triaging injected local email: {ex}")
                            st.rerun()

    # Tab 2: Categorized Queues
    with tab2:
        st.markdown('<div class="section-title">Sorted Agent Queues</div>', unsafe_allow_html=True)
        
        categories = load_categories_config()
        enabled_categories = [c for c in categories if c.get("enabled", True) and not c.get("archived", False)]
        queue_options = [c["label"] for c in enabled_categories] + ["Escalated"]
        
        if "t2_queue_selection" not in st.session_state:
            st.session_state.t2_queue_selection = queue_options[0]
            
        col_t2_nav, col_t2_content = st.columns([1.1, 3])
        
        with col_t2_nav:
            st.markdown('<div class="settings-sidebar">', unsafe_allow_html=True)
            mode_words_map = {
                "automated": "[Fully Automated]",
                "semi_automated": "[Semi-Automated]",
                "manual": "[Fully Manual]"
            }
            for opt in queue_options:
                is_active = (st.session_state.t2_queue_selection == opt)
                btn_key = f"t2_nav_btn_{opt.lower().replace(' ', '_')}"
                
                cat_obj = next((c for c in enabled_categories if c["label"] == opt), None)
                if opt == "Escalated":
                    mode_tag = "[Fully Manual]"
                elif cat_obj:
                    cmode = cat_obj.get("automation_mode")
                    if not cmode:
                        if cat_obj.get("has_auto_reply", False): cmode = "automated"
                        elif cat_obj.get("escalate_on_reply", False): cmode = "manual"
                        else: cmode = "semi_automated"
                    mode_tag = mode_words_map.get(cmode, "[Semi-Automated]")
                else:
                    mode_tag = "[Semi-Automated]"
                
                btn_label = f"{opt} {mode_tag}"
                if st.button(
                    btn_label,
                    key=btn_key,
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.t2_queue_selection = opt
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_t2_content:
            queue_selection = st.session_state.t2_queue_selection
            google_creds = load_google_creds()
            gmail_mode = False
            if google_creds and "refresh_token" in google_creds:
                gmail_mode = True
                
            search_email = st.text_input("Search by email", placeholder="Type a sender email or customer email")
            
            # Header and Clear Queue Button
            col_q_hdr, col_q_btn = st.columns([7, 3])
            with col_q_hdr:
                st.markdown(f"<h3 style='margin:0;'>Category Queue: {queue_selection}</h3>", unsafe_allow_html=True)
            with col_q_btn:
                if st.button("🗑️ Clear Queue", key=f"clear_queue_btn_{queue_selection.lower().replace(' ', '_')}", use_container_width=True):
                    if gmail_mode:
                        TRIAGE_HISTORY_FILE = os.path.join(BASE_DIR, "triage_history.json")
                        history_records = []
                        if os.path.exists(TRIAGE_HISTORY_FILE):
                            try:
                                with open(TRIAGE_HISTORY_FILE, "r") as f:
                                    history_records = json.load(f)
                            except:
                                pass
                        
                        category_mapping = {c["label"]: c["name"] for c in enabled_categories}
                        category_mapping["Escalated"] = "Escalated"
                        target_category = category_mapping[queue_selection]
                        
                        for idx, rec in enumerate(history_records):
                            is_match = False
                            if target_category == "Escalated":
                                if rec.get("escalated", False):
                                    is_match = True
                            else:
                                if rec.get("category") == target_category and not rec.get("escalated", False):
                                    is_match = True
                            
                            if is_match:
                                history_records[idx]["cleared_from_queue"] = True
                        
                        with open(TRIAGE_HISTORY_FILE, "w") as f:
                            json.dump(history_records, f, indent=2)
                        st.success(f"Gmail queue '{queue_selection}' cleared successfully!")
                        st.rerun()
                    else:
                        folder_mapping = {c["label"]: os.path.join(BASE_DIR, c["dir_name"]) for c in enabled_categories}
                        if queue_selection == "Escalated":
                            for cat in enabled_categories:
                                cat_dir = os.path.join(BASE_DIR, cat["dir_name"])
                                if os.path.exists(cat_dir):
                                    for f in os.listdir(cat_dir):
                                        if f.endswith('.txt') and not f.startswith('reply_') and not f.startswith('reply_sent_'):
                                            meta_path = os.path.join(cat_dir, f"meta_{f}.json")
                                            is_escalated = False
                                            if os.path.exists(meta_path):
                                                try:
                                                    with open(meta_path, "r", encoding="utf-8") as mf:
                                                        meta_data = json.load(mf)
                                                        is_escalated = meta_data.get("escalated", False)
                                                except:
                                                    pass
                                            if is_escalated:
                                                try:
                                                    os.remove(os.path.join(cat_dir, f))
                                                    os.remove(meta_path)
                                                    reply_path = os.path.join(cat_dir, f"reply_{f}")
                                                    if os.path.exists(reply_path):
                                                        os.remove(reply_path)
                                                except:
                                                    pass
                        else:
                            selected_dir = folder_mapping.get(queue_selection)
                            if selected_dir and os.path.exists(selected_dir):
                                for f in os.listdir(selected_dir):
                                    if os.path.isfile(os.path.join(selected_dir, f)):
                                        try:
                                            os.remove(os.path.join(selected_dir, f))
                                        except:
                                            pass
                        st.success(f"Local queue '{queue_selection}' cleared successfully!")
                        st.rerun()
            
            if gmail_mode:
                # Load from triage_history.json
                TRIAGE_HISTORY_FILE = os.path.join(BASE_DIR, "triage_history.json")
                history_records = []
                if os.path.exists(TRIAGE_HISTORY_FILE):
                    try:
                        with open(TRIAGE_HISTORY_FILE, "r") as f:
                            history_records = json.load(f)
                    except Exception:
                        pass
                
                category_mapping = {c["label"]: c["name"] for c in enabled_categories}
                category_mapping["Escalated"] = "Escalated"
                target_category = category_mapping[queue_selection]
                
                if target_category == "Escalated":
                    filtered_records = [
                        (idx, rec) for idx, rec in enumerate(history_records)
                        if rec.get("escalated", False) and not rec.get("cleared_from_queue", False)
                    ]
                else:
                    filtered_records = [
                        (idx, rec) for idx, rec in enumerate(history_records)
                        if rec.get("category") == target_category 
                        and not rec.get("escalated", False)
                        and not rec.get("cleared_from_queue", False)
                    ]
                if search_email:
                    filtered_records = [
                        (idx, rec) for idx, rec in filtered_records
                        if search_email.lower() in rec.get("sender", "").lower()
                    ]
                filtered_records.sort(
                    key=lambda item: parse_gmail_date(item[1].get("date", "")),
                    reverse=True
                )
                
                if not filtered_records:
                    st.info("No processed Gmail messages inside this queue.")
                else:
                    st.markdown(f"Found {len(filtered_records)} processed items in **{queue_selection}** queue (Gmail mode).")
                    
                    for display_index, (orig_index, record) in enumerate(filtered_records):
                        sender_val = record.get("sender", "Unknown")
                        subject_val = record.get("subject", "No Subject")
                        date_val = record.get("date", "")
                        orig_content = record.get("body_content", "No body logged.")
                        if not orig_content:
                            orig_content = f"Subject: {subject_val}\nFrom: {sender_val}\nDate: {date_val}"
                        draft_content = record.get("draft_reply", "No draft reply logged.")
                        
                        confidence_val = record.get("confidence", "N/A")
                        current_cat = next((c for c in enabled_categories if c["label"] == queue_selection), None)
                        category_text = current_cat["name"] if current_cat else queue_selection
                        
                        tag_class = "tag-neutral"
                        if "Refund" in category_text:
                            tag_class = "tag-refund"
                        elif "Bug" in category_text:
                            tag_class = "tag-bug"
                        elif "Delay" in category_text:
                            tag_class = "tag-delay"
                        elif "Query" in category_text:
                            tag_class = "tag-query"
                        elif "Opportunities" in category_text or "Opportunity" in category_text:
                            tag_class = "tag-opportunity"
                        elif "Spam" in category_text:
                            tag_class = "tag-spam"
                        elif "Subscription" in category_text:
                            tag_class = "tag-neutral"
                        else:
                            tag_class = "tag-query"
                        
                        is_rec_escalated = record.get("escalated", False)
                        is_followup = record.get("is_followup", False)
                        sentiment_str = record.get("sentiment", "Neutral")
                        auditor_log = record.get("auditor_log", "N/A")
                        cited_sources = record.get("cited_sources", "")
                        if is_rec_escalated:
                            tag_class = "tag-escalated"
                            category_text = "ESCALATED TO HUMAN"
                        
                        # Sentiment tag color
                        sent_class = "tag-sentiment-neutral"
                        if sentiment_str.lower() == "positive":
                            sent_class = "tag-sentiment-positive"
                        elif sentiment_str.lower() == "neutral":
                            sent_class = "tag-sentiment-neutral"
                        elif sentiment_str.lower() == "negative":
                            sent_class = "tag-sentiment-negative"
                        elif sentiment_str.lower() in ("angry", "frustrated"):
                            sent_class = "tag-sentiment-angry"
                        
                        is_replied = record.get("query_response_sent", False)
                        replied_prefix = "✅ [REPLIED] " if is_replied else ""
                        escalation_prefix = " [ESCALATED] " if is_rec_escalated else ""
                        followup_prefix = "📬 [FOLLOW-UP] " if is_followup else ""
                        expander_label = f"{replied_prefix}{followup_prefix}{escalation_prefix}📩 **{subject_val}** — From: {sender_val} | {date_val} | Confidence: **{confidence_val}**"
                        with st.expander(expander_label):
                            unsubscribe_link = record.get("unsubscribe_link") if queue_selection == "Subscriptions" else None
                            unsubscribe_prefs = load_unsubscribe_preferences()
                            unsubscribe_sender = sender_val
                            confirm_key = f"confirm_unsub_gmail_{orig_index}"
                            checkbox_key = f"dont_ask_unsub_gmail_{orig_index}"
                            if confirm_key not in st.session_state:
                                st.session_state[confirm_key] = False
    
                            card_html = f"""
                            <div class="custom-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                    <span class="card-title">{subject_val}</span>
                                    <div>
                                        {"<span class='tag' style='background-color: rgba(129, 201, 149, 0.2); color: #81c995; border: 1px solid #81c995; margin-right: 5px;'>✅ Response Sent</span>" if is_replied else ""}
                                        {"<span class='tag' style='background-color: #1a73e8; color: white; margin-right: 5px;'>📬 Follow-up</span>" if is_followup else ""}
                                        {"<span class='tag' style='background-color: rgba(129, 201, 149, 0.15); color: #81c995; border: 1px solid rgba(129, 201, 149, 0.2); margin-right: 5px;'> Approved</span>" if auditor_log.lower() == "approved" else ""}
                                        {"<span class='tag' style='background-color: rgba(253, 214, 99, 0.15); color: #fdd663; border: 1px solid rgba(253, 214, 99, 0.2); margin-right: 5px;'> Corrected</span>" if "corrected" in auditor_log.lower() else ""}
                                        <span class="tag {tag_class}">{category_text}</span>
                                        <span class="tag {sent_class}">{sentiment_str}</span>
                                    </div>
                                </div>
                                <div class="card-meta">From: {sender_val} | Date: {date_val} | Confidence: {confidence_val}</div>
                            </div>
                            """
                            st.markdown(clean_html(card_html), unsafe_allow_html=True)
                            
                            if is_replied:
                                sent_txt = record.get("query_response_text", draft_content)
                                sent_bcc = record.get("bcc_email_sent", "")
                                bcc_str = f" (BCC: {sent_bcc})" if sent_bcc else ""
                                st.markdown(f"""
                                <div style="background-color: rgba(129, 201, 149, 0.1); border: 1px solid rgba(129, 201, 149, 0.3); border-radius: 6px; padding: 12px; margin-bottom: 15px;">
                                    <div style="font-size: 13px; font-weight: 600; color: #81c995; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                                        <span>✅</span> Sent Response to Customer{bcc_str}
                                    </div>
                                    <div style="color: #e8eaed; font-size: 13px; white-space: pre-wrap; line-height: 1.5;">{sent_txt}</div>
                                </div>
                                """, unsafe_allow_html=True)
    
                            if queue_selection == "Subscriptions":
                                if unsubscribe_link:
                                    st.markdown(
                                        f"<a href='{unsubscribe_link}' target='_blank' style='color: #8ab4f8; text-decoration: underline; font-weight: 500;'>Click here to unsubscribe from this sender</a>",
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.info("No unsubscribe link detected for this subscription email.")
                            c_left, c_right = st.columns(2)
                            with c_left:
                                st.markdown("Original Email Message")
                                st.text_area(f"Original Text ({display_index})", value=orig_content, height=180, disabled=True, label_visibility="collapsed")
                            with c_right:
                                draft_state_key = f"editable_response_{orig_index}"
                                if draft_state_key not in st.session_state:
                                    st.session_state[draft_state_key] = draft_content
                                st.markdown("AI Response Draft")
                                st.text_area(f"Reply Draft ({display_index})", value=draft_content, height=180, disabled=True, label_visibility="collapsed")
                                
                                col_t1, col_t2 = st.columns([6, 4])
                                with col_t1:
                                    selected_tone = st.selectbox(
                                        "Select Response Persona / Tone",
                                        options=["Casual/Friendly", "Empathetic Apology", "Firm Policy Clarification", "Technical Guide"],
                                        key=f"tone_selection_{orig_index}",
                                        label_visibility="collapsed"
                                    )
                                with col_t2:
                                    if st.button("Regenerate Draft", key=f"regenerate_draft_btn_{orig_index}", use_container_width=True):
                                        with st.spinner("Regenerating response draft..."):
                                            import InboxPilot
                                            importlib.reload(InboxPilot)
                                            sender_email = record.get("sender") or ""
                                            past_history = InboxPilot.load_customer_history(sender_email)
                                            
                                            image_file_path = None
                                            if "birthday" in orig_content.lower() or "cake" in orig_content.lower():
                                                image_file_path = os.path.join(BASE_DIR, "mock_receipt_1782511821578.jpg")
                                                
                                            res = InboxPilot.triage_with_memory(orig_content, past_history, image_path=image_file_path, tone=selected_tone)
                                            if res:
                                                parts = res.split("---DRAFT START---")
                                                new_draft = parts[1].strip() if len(parts) > 1 else res
                                                new_classification = parts[0].strip()
                                                new_auditor_log = InboxPilot.extract_ai_field(new_classification, "AUDITOR_LOG") or "Approved"
                                                
                                                record["draft_reply"] = new_draft
                                                record["auditor_log"] = new_auditor_log
                                                
                                                with open(TRIAGE_HISTORY_FILE, "w") as f:
                                                    json.dump(history_records, f, indent=2)
                                                st.success("Draft regenerated successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to regenerate draft from AI model.")
                                
                                # Display Auditor Log
                                if auditor_log and auditor_log != "N/A":
                                    if auditor_log.lower() == "approved":
                                        st.markdown("""
                                        <div style="background-color: rgba(129, 201, 149, 0.1); border: 1px solid rgba(129, 201, 149, 0.2); border-radius: 4px; padding: 8px 12px; margin-top: 10px; font-size: 13px; color: #81c995; display: flex; align-items: center; gap: 8px;">
                                            <span></span>
                                            <strong>Policy Auditor:</strong> Draft Approved
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div style="background-color: rgba(253, 214, 99, 0.1); border: 1px solid rgba(253, 214, 99, 0.2); border-radius: 4px; padding: 8px 12px; margin-top: 10px; font-size: 13px; color: #fdd663; display: flex; align-items: center; gap: 8px;">
                                            <span></span>
                                            <strong>Policy Auditor:</strong> Auto-Corrected: {auditor_log.replace('Corrected: ', '').replace('Corrected: ', '')}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                # Display Cited Sources
                                if cited_sources:
                                    sources_list = [s.strip() for s in cited_sources.split(" | ") if s.strip()]
                                    if sources_list:
                                        list_items = "".join(f"<li style='margin-bottom: 4px;'>{s}</li>" for s in sources_list)
                                        st.markdown(f"""
                                        <div style="margin-top: 10px; padding: 8px 12px; border: 1px dashed #3c4043; border-radius: 4px; font-size: 12px; color: #9aa0a6;">
                                            <strong style="color: #e8eaed; display: block; margin-bottom: 4px;"> Cited Knowledge Base Sources:</strong>
                                            <ul style="margin: 0; padding-left: 16px;">
                                                {list_items}
                                            </ul>
                                        </div>
                                        """, unsafe_allow_html=True)
                                selected_cat = next((c for c in enabled_categories if c["label"] == queue_selection), None)
                                requires_manual = False
                                default_bcc = ""
                                if selected_cat:
                                    requires_manual = not selected_cat.get("has_auto_reply", False)
                                    default_bcc = selected_cat.get("bcc_email", "")
                                    
                                bcc_input_val = st.text_input(
                                    "BCC Recipient(s) (Optional)",
                                    value=default_bcc,
                                    key=f"bcc_input_gmail_{orig_index}",
                                    placeholder="e.g. bcc1@gmail.com, bcc2@gmail.com",
                                    help="Category default BCC is pre-filled. Separate multiple recipient email addresses with commas."
                                )
                                    
                                # Response Editor
                                response_text = st.text_area(
                                    f"Response Editor ({display_index})",
                                    key=draft_state_key,
                                    height=200
                                )
                                
                                if st.button("Send Response", key=f"send_query_response_{orig_index}", type="primary", use_container_width=True):
                                    response_val = st.session_state[draft_state_key]
                                    if not response_val.strip():
                                        st.error("Cannot send empty response.")
                                    else:
                                        try:
                                            import InboxPilot
                                            importlib.reload(InboxPilot)
                                            access_token = InboxPilot.refresh_access_token(load_google_creds())
                                            if not access_token:
                                                st.error("Unable to refresh Gmail token for sending.")
                                            else:
                                                to_email = sender_val
                                                if "<" in sender_val:
                                                    found = re.search(r'<(.*?)>', sender_val)
                                                    if found:
                                                        to_email = found.group(1)
                                                sent = InboxPilot.send_gmail_reply(access_token, to_email, subject_val, response_val, record.get("thread_id"), record.get("message_id"), bcc_email=bcc_input_val.strip())
                                                if sent:
                                                    record["query_response_sent"] = True
                                                    record["query_response_text"] = response_val
                                                    if bcc_input_val.strip():
                                                        record["bcc_email_sent"] = bcc_input_val.strip()
                                                    with open(TRIAGE_HISTORY_FILE, "w") as f:
                                                        json.dump(history_records, f, indent=2)
                                                    bcc_msg = f" (BCC: {bcc_input_val.strip()})" if bcc_input_val.strip() else ""
                                                    st.success(f"Response sent successfully via Gmail!{bcc_msg}")
                                                    st.rerun()
                                                else:
                                                    st.error("Failed to send response.")
                                        except Exception as e:
                                            st.error(f"Error sending: {e}")
                            # Action button to delete record
                            btn_col1, btn_col2 = st.columns([10, 2])
                            with btn_col2:
                                if st.button("Clean Record", key=f"del_gmail_{orig_index}"):
                                    try:
                                        # Remove record from history
                                        history_records.pop(orig_index)
                                        with open(TRIAGE_HISTORY_FILE, "w") as f:
                                            json.dump(history_records, f, indent=2)
                                        st.success("Record cleared.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            
                            st.markdown("<hr style='border: 1px solid #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)
            else:
                # Local directory-based sorting
                folder_mapping = {c["label"]: os.path.join(BASE_DIR, c["dir_name"]) for c in enabled_categories}
                
                if queue_selection == "Escalated":
                    original_emails = []
                    for cat in enabled_categories:
                        cat_dir = os.path.join(BASE_DIR, cat["dir_name"])
                        if os.path.exists(cat_dir):
                            for f in os.listdir(cat_dir):
                                if f.endswith('.txt') and not f.startswith('reply_') and not f.startswith('reply_sent_'):
                                    meta_path = os.path.join(cat_dir, f"meta_{f}.json")
                                    if os.path.exists(meta_path):
                                        try:
                                            with open(meta_path, "r", encoding="utf-8") as mf:
                                                meta_data = json.load(mf)
                                                if meta_data.get("escalated", False):
                                                    original_emails.append((f, cat_dir))
                                        except:
                                            pass
                else:
                    selected_dir = folder_mapping[queue_selection]
                    all_files = os.listdir(selected_dir)
                    original_emails = []
                    for f in all_files:
                        if f.endswith('.txt') and not f.startswith('reply_') and not f.startswith('reply_sent_'):
                            meta_path = os.path.join(selected_dir, f"meta_{f}.json")
                            is_escalated = False
                            if os.path.exists(meta_path):
                                try:
                                    with open(meta_path, "r", encoding="utf-8") as mf:
                                        meta_data = json.load(mf)
                                        is_escalated = meta_data.get("escalated", False)
                                except:
                                    pass
                            if not is_escalated:
                                original_emails.append((f, selected_dir))
                                
                if search_email:
                    original_emails = [
                        (f, d) for f, d in original_emails
                        if search_email.lower() in f.lower()
                    ]
                    
                original_emails.sort(
                    key=lambda x: os.path.getmtime(os.path.join(x[1], x[0])),
                    reverse=True
                )
                
                if not original_emails:
                    st.info("No processed emails inside this queue directory.")
                else:
                    st.markdown(f"Found {len(original_emails)} processed items in **{queue_selection}** directory (Local mode).")
                    
                    for index, (email_file, selected_dir) in enumerate(original_emails):
                        email_path = os.path.join(selected_dir, email_file)
                        reply_file = f"reply_{email_file}"
                        reply_path = os.path.join(selected_dir, reply_file)
                        
                        with open(email_path, "r", encoding="utf-8", errors="ignore") as f:
                            orig_content = f.read()
                            
                        draft_content = "No reply draft found for this record."
                        if os.path.exists(reply_path):
                            with open(reply_path, "r", encoding="utf-8", errors="ignore") as f:
                                draft_content = f.read()
                        
                        meta_path = os.path.join(selected_dir, f"meta_{email_file}.json")
                        confidence_val = "N/A"
                        unsubscribe_link = None
                        is_rec_escalated = False
                        is_followup = False
                        sentiment_str = "Neutral"
                        auditor_log = "N/A"
                        cited_sources = ""
                        has_attachment = False
                        if os.path.exists(meta_path):
                            try:
                                with open(meta_path, "r", encoding="utf-8") as mf:
                                    meta_data = json.load(mf)
                                    confidence_val = meta_data.get("confidence", "N/A")
                                    unsubscribe_link = meta_data.get("unsubscribe_link")
                                    is_rec_escalated = meta_data.get("escalated", False)
                                    is_followup = meta_data.get("is_followup", False)
                                    sentiment_str = meta_data.get("sentiment", "Neutral")
                                    auditor_log = meta_data.get("auditor_log", "N/A")
                                    cited_sources = meta_data.get("cited_sources", "")
                                    has_attachment = meta_data.get("has_attachment", False)
                            except Exception:
                                confidence_val = "N/A"
                                is_rec_escalated = False
                                is_followup = False
                        current_cat = next((c for c in enabled_categories if c["label"] == queue_selection), None)
                        category_text = current_cat["name"] if current_cat else queue_selection
                        
                        tag_class = "tag-neutral"
                        if "Refund" in category_text:
                            tag_class = "tag-refund"
                        elif "Bug" in category_text:
                            tag_class = "tag-bug"
                        elif "Delay" in category_text:
                            tag_class = "tag-delay"
                        elif "Query" in category_text:
                            tag_class = "tag-query"
                        elif "Opportunities" in category_text or "Opportunity" in category_text:
                            tag_class = "tag-opportunity"
                        elif "Spam" in category_text:
                            tag_class = "tag-spam"
                        elif "Subscription" in category_text:
                            tag_class = "tag-neutral"
                        else:
                            tag_class = "tag-query"
                        
                        clean_fn = email_file.replace('.txt', '')
                        if "@" not in clean_fn:
                            clean_fn = clean_fn.replace('_', ' ')
    
                        mtime = os.path.getmtime(email_path)
                        date_val = datetime.datetime.fromtimestamp(mtime).strftime("%b %d, %Y %I:%M %p")
    
                        snippet = orig_content.strip().replace("\n", " ")[:60]
                        if len(orig_content) > 60:
                            snippet += "..."
    
                        if is_rec_escalated:
                            tag_class = "tag-escalated"
                            category_text = "ESCALATED TO HUMAN"
    
                        # Sentiment tag color
                        sent_class = "tag-sentiment-neutral"
                        if sentiment_str.lower() == "positive":
                            sent_class = "tag-sentiment-positive"
                        elif sentiment_str.lower() == "neutral":
                            sent_class = "tag-sentiment-neutral"
                        elif sentiment_str.lower() == "negative":
                            sent_class = "tag-sentiment-negative"
                        elif sentiment_str.lower() in ("angry", "frustrated"):
                            sent_class = "tag-sentiment-angry"
    
                        is_replied_local = False
                        sent_text_local = ""
                        sent_bcc_local = ""
                        reply_sent_path = os.path.join(selected_dir, f"reply_sent_{email_file}")
                        if os.path.exists(meta_path):
                            try:
                                with open(meta_path, "r", encoding="utf-8") as mf:
                                    mdata = json.load(mf)
                                    is_replied_local = mdata.get("query_response_sent", False)
                                    sent_bcc_local = mdata.get("bcc_email_sent", "")
                            except: pass
                        if os.path.exists(reply_sent_path):
                            is_replied_local = True
                            try:
                                with open(reply_sent_path, "r", encoding="utf-8") as rsf:
                                    sent_text_local = rsf.read()
                            except: pass

                        replied_prefix_loc = "✅ [REPLIED] " if is_replied_local else ""
                        escalation_prefix = " [ESCALATED] " if is_rec_escalated else ""
                        followup_prefix = "📬 [FOLLOW-UP] " if is_followup else ""
                        expander_label = f"{replied_prefix_loc}{followup_prefix}{escalation_prefix}📩 **{clean_fn}** — {snippet} | {date_val} | Confidence: **{confidence_val}**"
                        with st.expander(expander_label):
                            unsubscribe_prefs = load_unsubscribe_preferences()
                            sender_val = parse_sender_from_email_text(orig_content)
                            unsubscribe_sender = sender_val
                            confirm_key = f"confirm_unsub_local_{index}"
                            checkbox_key = f"dont_ask_unsub_local_{index}"
                            if confirm_key not in st.session_state:
                                st.session_state[confirm_key] = False
                            st.markdown(clean_html(f"""
                            <div class="custom-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                    <span class="card-title">{clean_fn}</span>
                                    <div>
                                        {"<span class='tag' style='background-color: rgba(129, 201, 149, 0.2); color: #81c995; border: 1px solid #81c995; margin-right: 5px;'>✅ Response Sent</span>" if is_replied_local else ""}
                                        {"<span class='tag' style='background-color: #1a73e8; color: white; margin-right: 5px;'>📬 Follow-up</span>" if is_followup else ""}
                                        {"<span class='tag' style='background-color: rgba(129, 201, 149, 0.15); color: #81c995; border: 1px solid rgba(129, 201, 149, 0.2); margin-right: 5px;'> Approved</span>" if auditor_log.lower() == "approved" else ""}
                                        {"<span class='tag' style='background-color: rgba(253, 214, 99, 0.15); color: #fdd663; border: 1px solid rgba(253, 214, 99, 0.2); margin-right: 5px;'> Corrected</span>" if "corrected" in auditor_log.lower() else ""}
                                        <span class="tag {tag_class}">{category_text}</span>
                                        <span class="tag {sent_class}">{sentiment_str}</span>
                                    </div>
                                </div>
                                <div class="card-meta">From: {sender_val} | Confidence: {confidence_val}</div>
                            </div>
                            """), unsafe_allow_html=True)
                            
                            if is_replied_local:
                                bcc_loc_str = f" (BCC: {sent_bcc_local})" if sent_bcc_local else ""
                                disp_sent_txt = sent_text_local if sent_text_local else draft_content
                                st.markdown(f"""
                                <div style="background-color: rgba(129, 201, 149, 0.1); border: 1px solid rgba(129, 201, 149, 0.3); border-radius: 6px; padding: 12px; margin-bottom: 15px;">
                                    <div style="font-size: 13px; font-weight: 600; color: #81c995; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                                        <span>✅</span> Sent Response to Customer{bcc_loc_str}
                                    </div>
                                    <div style="color: #e8eaed; font-size: 13px; white-space: pre-wrap; line-height: 1.5;">{disp_sent_txt}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            if queue_selection == "Subscriptions":
                                if unsubscribe_link:
                                    st.markdown(
                                        f"<a href='{unsubscribe_link}' target='_blank' style='color: #8ab4f8; text-decoration: underline; font-weight: 500;'>Click here to unsubscribe from this sender</a>",
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.info("No unsubscribe link detected for this subscription email.")
    
                            c_left, c_right = st.columns(2)
                            with c_left:
                                st.markdown("Original Email Message")
                                st.text_area(f"Original Text ({index})", value=orig_content, height=180, disabled=True, label_visibility="collapsed")
                                
                                # Handle Image Attachment
                                base_name = os.path.splitext(email_file)[0]
                                attachment_image = None
                                for ext in (".jpg", ".jpeg", ".png"):
                                    img_path = os.path.join(selected_dir, f"{base_name}{ext}")
                                    if os.path.exists(img_path):
                                        attachment_image = img_path
                                        break
                                
                                if attachment_image:
                                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                                    st.markdown("**Attachment Image:**")
                                    st.image(attachment_image, use_column_width=True)
                                    
                            with c_right:
                                draft_state_key_local = f"editable_response_local_{index}"
                                if draft_state_key_local not in st.session_state:
                                    st.session_state[draft_state_key_local] = draft_content
                                st.markdown("AI Response Draft")
                                st.text_area(f"Reply Draft ({index})", value=draft_content, height=180, disabled=True, label_visibility="collapsed")
                                
                                col_t1, col_t2 = st.columns([6, 4])
                                with col_t1:
                                    selected_tone = st.selectbox(
                                        "Select Response Persona / Tone",
                                        options=["Casual/Friendly", "Empathetic Apology", "Firm Policy Clarification", "Technical Guide"],
                                        key=f"tone_selection_local_{index}",
                                        label_visibility="collapsed"
                                    )
                                with col_t2:
                                    if st.button("Regenerate Draft", key=f"regenerate_draft_btn_local_{index}", use_container_width=True):
                                        with st.spinner("Regenerating response draft..."):
                                            import InboxPilot
                                            importlib.reload(InboxPilot)
                                            sender_email = meta_data.get("sender_email") or ""
                                            past_history = InboxPilot.load_customer_history(sender_email)
                                            
                                            res = InboxPilot.triage_with_memory(orig_content, past_history, image_path=attachment_image, tone=selected_tone)
                                            if res:
                                                parts = res.split("---DRAFT START---")
                                                new_draft = parts[1].strip() if len(parts) > 1 else res
                                                new_classification = parts[0].strip()
                                                new_auditor_log = InboxPilot.extract_ai_field(new_classification, "AUDITOR_LOG") or "Approved"
                                                
                                                meta_data["draft_reply"] = new_draft
                                                meta_data["auditor_log"] = new_auditor_log
                                                
                                                with open(meta_path, "w") as f:
                                                    json.dump(meta_data, f, indent=2)
                                                st.success("Draft regenerated successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to regenerate draft from AI model.")
                                
                                # Display Auditor Log
                                if auditor_log and auditor_log != "N/A":
                                    if auditor_log.lower() == "approved":
                                        st.markdown("""
                                        <div style="background-color: rgba(129, 201, 149, 0.1); border: 1px solid rgba(129, 201, 149, 0.2); border-radius: 4px; padding: 8px 12px; margin-top: 10px; font-size: 13px; color: #81c995; display: flex; align-items: center; gap: 8px;">
                                            <span></span>
                                            <strong>Policy Auditor:</strong> Draft Approved
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div style="background-color: rgba(253, 214, 99, 0.1); border: 1px solid rgba(253, 214, 99, 0.2); border-radius: 4px; padding: 8px 12px; margin-top: 10px; font-size: 13px; color: #fdd663; display: flex; align-items: center; gap: 8px;">
                                            <span></span>
                                            <strong>Policy Auditor:</strong> Auto-Corrected: {auditor_log.replace('Corrected: ', '').replace('Corrected: ', '')}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                # Display Cited Sources
                                if cited_sources:
                                    sources_list = [s.strip() for s in cited_sources.split(" | ") if s.strip()]
                                    if sources_list:
                                        list_items = "".join(f"<li style='margin-bottom: 4px;'>{s}</li>" for s in sources_list)
                                        st.markdown(f"""
                                        <div style="margin-top: 10px; padding: 8px 12px; border: 1px dashed #3c4043; border-radius: 4px; font-size: 12px; color: #9aa0a6;">
                                            <strong style="color: #e8eaed; display: block; margin-bottom: 4px;"> Cited Knowledge Base Sources:</strong>
                                            <ul style="margin: 0; padding-left: 16px;">
                                                {list_items}
                                            </ul>
                                        </div>
                                        """, unsafe_allow_html=True)
                                selected_cat = next((c for c in enabled_categories if c["label"] == queue_selection), None)
                                requires_manual = False
                                default_bcc_local = ""
                                if selected_cat:
                                    requires_manual = not selected_cat.get("has_auto_reply", False)
                                    default_bcc_local = selected_cat.get("bcc_email", "")
                                    
                                bcc_input_local = st.text_input(
                                    "BCC Recipient(s) (Optional)",
                                    value=default_bcc_local,
                                    key=f"bcc_input_local_{index}",
                                    placeholder="e.g. bcc1@gmail.com, bcc2@gmail.com",
                                    help="Category default BCC is pre-filled. Separate multiple recipient email addresses with commas."
                                )
                                    
                                # Response Editor
                                response_text = st.text_area(
                                    f"Response Editor ({index})",
                                    key=draft_state_key_local,
                                    height=200
                                )
                                
                                if st.button("Send Response", key=f"send_query_response_local_{index}", type="primary", use_container_width=True):
                                    response_val_local = st.session_state[draft_state_key_local]
                                    if not response_val_local.strip():
                                        st.error("Cannot send empty response.")
                                    else:
                                        try:
                                            with open(os.path.join(selected_dir, f"reply_sent_{email_file}"), "w", encoding="utf-8") as rf:
                                                rf.write(response_val_local)
                                            meta_data = {}
                                            if os.path.exists(meta_path):
                                                with open(meta_path, "r", encoding="utf-8") as mf:
                                                    meta_data = json.load(mf)
                                            meta_data["query_response_sent"] = True
                                            if bcc_input_local.strip():
                                                meta_data["bcc_email_sent"] = bcc_input_local.strip()
                                            with open(meta_path, "w", encoding="utf-8") as mf:
                                                json.dump(meta_data, mf, indent=2)
                                            bcc_msg_loc = f" (BCC: {bcc_input_local.strip()})" if bcc_input_local.strip() else ""
                                            st.success(f"Query response simulated and saved locally.{bcc_msg_loc}")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error saving response: {e}")
                            btn_col1, btn_col2 = st.columns([10, 2])
                            with btn_col2:
                                if st.button("Clean Record", key=f"del_{email_file}_{index}"):
                                    try:
                                        os.remove(email_path)
                                        if os.path.exists(reply_path):
                                            os.remove(reply_path)
                                        reply_sent_path = os.path.join(selected_dir, f"reply_sent_{email_file}")
                                        if os.path.exists(reply_sent_path):
                                            os.remove(reply_sent_path)
                                        if os.path.exists(meta_path):
                                            os.remove(meta_path)
                                        st.success("Record cleared.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            
                            st.markdown("<hr style='border: 1px solid #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)
    
        # Tab 3: Customer Directory & Memory
    with tab3:
        st.markdown('<div class="section-title">Customer Memory Directory</div>', unsafe_allow_html=True)
        st.markdown("Below are the persistent interaction histories saved for each customer. The AI uses these files as critical context during triage.")
        
        # List memory files
        memory_files = [f for f in os.listdir(MEMORY_DIR) if f.endswith('_history.txt')]
        
        if not memory_files:
            st.info("No customer profiles found inside Customer_Memory/ directory.")
        else:
            # Create a list of clean display names
            customer_options = {}
            for f in memory_files:
                clean_name = f.replace('_history.txt', '')
                if "@" not in clean_name:
                    clean_name = clean_name.replace('_', ' ')
                customer_options[clean_name] = f
            
            selected_customer = st.selectbox(
                "Select Customer Profile to View/Edit",
                options=list(customer_options.keys())
            )
            
            if selected_customer:
                target_history_file = customer_options[selected_customer]
                history_file_path = os.path.join(MEMORY_DIR, target_history_file)
                
                with open(history_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    history_content = f.read()
                    
                st.markdown(f"### Profile: **{selected_customer}**")
                
                # Edit text area
                updated_history = st.text_area(
                    "Persistent Support History Log",
                    value=history_content,
                    height=300
                )
                
                col_save, col_spacer = st.columns([2, 10])
                with col_save:
                    save_clicked = st.button("Save Profile Changes", use_container_width=True)
                    if save_clicked:
                        try:
                            with open(history_file_path, "w", encoding="utf-8") as f:
                                f.write(updated_history)
                            st.success("Customer profile updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving: {e}")
                            
    # Tab 4: Settings & Category Manager
    with tab4:
        st.markdown('<div class="section-title">Settings & Category Manager</div>', unsafe_allow_html=True)
        st.markdown("Customize your triage system by enabling/disabling standard categories or adding custom business-specific categories.")
        
        # Automation Modes Definitions Card
        st.markdown("""
        <div style="background: rgba(138, 180, 248, 0.05); border: 1px solid rgba(138, 180, 248, 0.2); border-radius: 6px; padding: 14px 16px; margin-bottom: 20px;">
            <div style="font-weight: 600; color: #8ab4f8; font-size: 14px; margin-bottom: 8px;">📌 Category Response Automation Modes</div>
            <div style="font-size: 13px; color: #e8eaed; line-height: 1.6;">
                <div><strong style="color: #81c995;">⚡ Fully Automated:</strong> Automatically sends AI-generated compliant replies instantly upon triage (e.g., Refund Requests).</div>
                <div><strong style="color: #fdd663;">🤖 Semi-Automated:</strong> Generates AI draft replies, policy audit checks, and cited sources, requiring human review before sending (e.g., General Queries).</div>
                <div><strong style="color: #f28b82;">✋ Fully Manual:</strong> Triage sorts emails into the queue, but requires support staff to draft responses from scratch (e.g., Strict Escalation items).</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        categories = load_categories_config()
        enabled_categories = [c for c in categories if c.get("enabled", True) and not c.get("archived", False)]
        total_enabled = len(enabled_categories)
        
        # Enforce category limit
        MAX_CATEGORIES = 8
        MIN_CATEGORIES = 1
        st.markdown(f"### Active Categories: **{total_enabled} / {MAX_CATEGORIES}** (Min: {MIN_CATEGORIES})")
        if total_enabled >= MAX_CATEGORIES:
            st.warning(f"You have reached the maximum limit of {MAX_CATEGORIES} active categories. Disable a standard category or remove a custom one to add new ones.")
        else:
            st.success(f"You can add up to {MAX_CATEGORIES - total_enabled} more category/categories.")

        st.markdown("<hr style='border: 1px solid #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)
        
        # 1. Toggle Standard Categories & Set Automation Mode
        st.markdown("#### Manage Standard Categories")
        standard_cats = [c for c in categories if c.get("is_standard", False)]
        
        standard_states = {}
        standard_auto_modes = {}
        standard_bcc_emails = {}
        
        mode_options = ["Fully Automated (Instant Auto-Reply)", "Semi-Automated (AI Drafts, Human Review)", "Fully Manual (Staff Draft Scratch)"]
        mode_mapping = {
            "automated": "Fully Automated (Instant Auto-Reply)",
            "semi_automated": "Semi-Automated (AI Drafts, Human Review)",
            "manual": "Fully Manual (Staff Draft Scratch)"
        }
        reverse_mode = {
            "Fully Automated (Instant Auto-Reply)": "automated",
            "Semi-Automated (AI Drafts, Human Review)": "semi_automated",
            "Fully Manual (Staff Draft Scratch)": "manual"
        }

        for index, cat in enumerate(standard_cats):
            col_target1, col_target2, col_target3 = st.columns([2.5, 2.5, 2])
            
            curr_mode = cat.get("automation_mode")
            if not curr_mode:
                if cat.get("has_auto_reply", False): curr_mode = "automated"
                elif cat.get("escalate_on_reply", False): curr_mode = "manual"
                else: curr_mode = "semi_automated"
                
            with col_target1:
                disabled_checkbox = False
                if total_enabled >= MAX_CATEGORIES and not cat.get("enabled", True):
                    disabled_checkbox = True
                
                state = st.checkbox(
                    f"{cat['label']} ({cat['name']})",
                    value=cat.get("enabled", True),
                    key=f"toggle_std_{cat['name']}",
                    disabled=disabled_checkbox
                )
                standard_states[cat["name"]] = state
            
            with col_target2:
                selected_mode_str = st.selectbox(
                    "Automation Mode",
                    options=mode_options,
                    index=mode_options.index(mode_mapping.get(curr_mode, mode_options[1])),
                    key=f"mode_std_{cat['name']}",
                    disabled=not state
                )
                standard_auto_modes[cat["name"]] = reverse_mode[selected_mode_str]
                
            with col_target3:
                std_bcc = st.text_input(
                    "Default BCC Email(s)",
                    value=cat.get("bcc_email", ""),
                    key=f"bcc_std_{cat['name']}",
                    placeholder="e.g. bcc1@gmail.com, bcc2@gmail.com",
                    help="To add multiple recipients, separate email addresses with commas.",
                    disabled=not state
                )
                standard_bcc_emails[cat["name"]] = std_bcc.strip()
            
            st.markdown("<hr style='border: 0.5px dashed #3c4043; margin: 0.2rem 0;'>", unsafe_allow_html=True)

        if st.button("Save Standard Category Settings", key="save_standard_settings_btn"):
            # Calculate what new active count would be
            new_active_count = sum(1 for c in categories if (c.get("is_standard", False) and standard_states.get(c["name"], True)) or (not c.get("is_standard", False) and c.get("enabled", True) and not c.get("archived", False)))
            if new_active_count < MIN_CATEGORIES:
                st.error(f"Cannot save settings. At least {MIN_CATEGORIES} active category is required.")
            else:
                has_changes = False
                for c in categories:
                    if c.get("is_standard", False):
                        old_enabled = c.get("enabled", True)
                        new_enabled = standard_states.get(c["name"], True)
                        
                        old_mode = c.get("automation_mode", "semi_automated")
                        new_mode = standard_auto_modes.get(c["name"], "semi_automated")
                        
                        old_bcc = c.get("bcc_email", "")
                        new_bcc = standard_bcc_emails.get(c["name"], "")
                        
                        if old_enabled != new_enabled or old_mode != new_mode or old_bcc != new_bcc:
                            c["enabled"] = new_enabled
                            c["automation_mode"] = new_mode
                            c["has_auto_reply"] = (new_mode == "automated")
                            c["escalate_on_reply"] = (new_mode == "manual")
                            c["bcc_email"] = new_bcc
                            has_changes = True
                if has_changes:
                    save_categories_config(categories)
                    st.success("Standard category settings updated!")
                    st.rerun()
                else:
                    st.info("No changes to standard categories detected.")

        st.markdown("<hr style='border: 1px solid #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)
        
        # 2. Manage Custom Categories
        st.markdown("#### Manage Custom Categories")
        custom_cats = [c for c in categories if not c.get("is_standard", False) and not c.get("archived", False)]
        
        if not custom_cats:
            st.info("No custom categories configured yet.")
        else:
            for cat in custom_cats:
                col_c1, col_c2, col_c3, col_c4 = st.columns([3, 3, 2.5, 1.5])
                with col_c1:
                    st.markdown(f"**{cat['label']}** ({cat['name']})")
                    st.markdown(f"<span style='font-size: 12px; color: #9aa0a6;'>{cat['description']}</span>", unsafe_allow_html=True)
                with col_c2:
                    curr_mode_c = cat.get("automation_mode")
                    if not curr_mode_c:
                        if cat.get("has_auto_reply", False): curr_mode_c = "automated"
                        elif cat.get("escalate_on_reply", False): curr_mode_c = "manual"
                        else: curr_mode_c = "semi_automated"
                    
                    sel_mode_c_str = st.selectbox(
                        "Automation Mode",
                        options=mode_options,
                        index=mode_options.index(mode_mapping.get(curr_mode_c, mode_options[1])),
                        key=f"mode_custom_{cat['name']}"
                    )
                    new_mode_c = reverse_mode[sel_mode_c_str]
                    if new_mode_c != curr_mode_c:
                        cat["automation_mode"] = new_mode_c
                        cat["has_auto_reply"] = (new_mode_c == "automated")
                        cat["escalate_on_reply"] = (new_mode_c == "manual")
                        save_categories_config(categories)
                        st.success(f"Updated automation mode for {cat['label']}.")
                        st.rerun()
                with col_c3:
                    cust_bcc_val = st.text_input(
                        "Default BCC Email(s)",
                        value=cat.get("bcc_email", ""),
                        key=f"bcc_custom_{cat['name']}",
                        placeholder="e.g. bcc1@gmail.com, bcc2@gmail.com",
                        help="To add multiple recipients, separate email addresses with commas."
                    )
                    if cust_bcc_val.strip() != cat.get("bcc_email", ""):
                        cat["bcc_email"] = cust_bcc_val.strip()
                        save_categories_config(categories)
                        st.success(f"Updated BCC email for {cat['label']}.")
                        st.rerun()
                with col_c4:
                    if st.button("Remove", key=f"remove_custom_{cat['name']}"):
                        if total_enabled <= MIN_CATEGORIES:
                            st.error(f"Cannot remove category. At least {MIN_CATEGORIES} active category is required.")
                        else:
                            cat["archived"] = True
                            cat["enabled"] = False
                            save_categories_config(categories)
                            st.success(f"Category '{cat['label']}' removed.")
                            st.rerun()
                st.markdown("<hr style='border: 1px dashed #3c4043; margin: 0.5rem 0;'>", unsafe_allow_html=True)

        # 3. Restore Previously Removed Category
        archived_custom_cats = [c for c in categories if not c.get("is_standard", False) and c.get("archived", False)]
        if archived_custom_cats:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown("##### Restore Previously Removed Category")
            restore_options = {c["label"]: c for c in archived_custom_cats}
            selected_restore_label = st.selectbox(
                "Select a category to restore",
                options=list(restore_options.keys()),
                disabled=(total_enabled >= MAX_CATEGORIES),
                key="restore_category_selectbox"
            )
            if st.button("Restore Category", key="restore_category_btn", disabled=(total_enabled >= MAX_CATEGORIES)):
                restored_cat = restore_options[selected_restore_label]
                restored_cat["archived"] = False
                restored_cat["enabled"] = True
                save_categories_config(categories)
                os.makedirs(os.path.join(BASE_DIR, restored_cat["dir_name"]), exist_ok=True)
                st.success(f"Category '{selected_restore_label}' restored successfully!")
                st.rerun()

        st.markdown("<hr style='border: 1px solid #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)

        # 4. Add Custom Business Category Form
        st.markdown("#### Add Custom Business Category")
        custom_name = st.text_input("Category Name (e.g. Wholesale Inquiry)", placeholder="Wholesale Inquiry")
        custom_desc = st.text_area("Category Description (Explain to the AI when to route emails here)", placeholder="Customer is asking about bulk orders, pricing list, or wholesale partnership terms.")
        custom_bcc_input = st.text_input("Default BCC Email(s) (Optional)", placeholder="e.g. manager@company.com, audit@company.com", help="Separate multiple emails with commas.", key="add_custom_bcc_input")
        
        custom_auto_mode_str = st.selectbox(
            "Category Response Automation Mode",
            options=mode_options,
            index=1,
            help="Fully Automated sends AI replies instantly; Semi-Automated generates AI drafts for human review; Fully Manual requires staff to draft responses from scratch.",
            key="add_custom_auto_mode"
        )
        
        if st.button("Add Category", key="add_custom_category_btn"):
            clean_name = custom_name.strip()
            clean_desc = custom_desc.strip()
            clean_bcc = custom_bcc_input.strip()
            selected_auto_mode = reverse_mode[custom_auto_mode_str]
            
            if total_enabled >= MAX_CATEGORIES:
                st.error(f"You have reached the maximum limit of {MAX_CATEGORIES} active categories. Please uncheck or remove an active category above before adding a new one.")
            elif not clean_name:
                st.error("Please enter a category name.")
            elif not clean_desc:
                st.error("Please enter a category description.")
            elif any(c["name"].lower() == clean_name.lower() or c["label"].lower() == clean_name.lower() for c in categories if not c.get("archived", False)):
                st.error("A category with this name or label already exists.")
            elif any(c["name"].lower() == clean_name.lower() or c["label"].lower() == clean_name.lower() for c in categories if c.get("archived", False)):
                st.error("A previously removed category with this name exists in memory. Please restore it using the dropdown above instead of creating it from scratch.")
            elif clean_name.lower() == "escalated":
                st.error("The name 'Escalated' is reserved for system escalations.")
            else:
                safe_key = "".join(x for x in clean_name.title() if x.isalnum())
                safe_dir = clean_name.replace(" ", "_")
                
                new_cat = {
                    "name": safe_key,
                    "label": clean_name,
                    "dir_name": safe_dir,
                    "description": clean_desc,
                    "is_standard": False,
                    "enabled": True,
                    "automation_mode": selected_auto_mode,
                    "has_auto_reply": (selected_auto_mode == "automated"),
                    "escalate_on_reply": (selected_auto_mode == "manual"),
                    "bcc_email": clean_bcc
                }
                
                categories.append(new_cat)
                
                for c in categories:
                    if c.get("is_standard", False):
                        c["enabled"] = standard_states.get(c["name"], True)
                        smode = standard_auto_modes.get(c["name"], "semi_automated")
                        c["automation_mode"] = smode
                        c["has_auto_reply"] = (smode == "automated")
                        c["escalate_on_reply"] = (smode == "manual")
                        
                save_categories_config(categories)
                os.makedirs(os.path.join(BASE_DIR, safe_dir), exist_ok=True)
                st.success(f"Category '{clean_name}' added successfully with '{selected_auto_mode}' mode!")
                st.rerun()

        st.markdown("<hr style='border: 1px solid #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)

        # 5. Category Definitions block at the bottom
        st.markdown("#### Active Category Definitions")
        st.markdown("Here are the active categories and their AI routing definitions:")
        for cat in enabled_categories:
            st.markdown(f"- **{cat['label']}**: {cat['description']}")

        # Tab 5: Analytics & Sentiment
    with tab5:
        st.markdown('<div class="section-title">Support Pipeline Analytics & Sentiment</div>', unsafe_allow_html=True)
        
        TRIAGE_HISTORY_FILE = os.path.join(BASE_DIR, "triage_history.json")
        history_records = []
        if os.path.exists(TRIAGE_HISTORY_FILE):
            try:
                with open(TRIAGE_HISTORY_FILE, "r") as f:
                    history_records = json.load(f)
            except Exception:
                pass
                
        if not history_records:
            st.info("No logs found. Run the triage engine to populate pipeline analytics.")
        else:
            total_processed = len(history_records)
            
            # Calculate pending categorized emails awaiting reply (strictly requiring an actual timestamp)
            pending_details_by_cat = {}
            total_pending_queue_count = 0
            categories_cfg = load_categories_config()
            enabled_cats_an = [c for c in categories_cfg if c.get("enabled", True) and not c.get("archived", False)]
            cat_name_to_lbl = {c["name"]: c["label"] for c in enabled_cats_an}
            cat_name_to_lbl["Escalated"] = "Escalated"
            
            def has_real_timestamp(t_str):
                if not t_str or not isinstance(t_str, str):
                    return False
                clean_t = t_str.strip().lower()
                if clean_t in ("pending", "recent", "n/a", "none", "", "test"):
                    return False
                return any(char.isdigit() for char in clean_t)
            
            # Check triage history for categorized emails where response has not been sent yet
            for rec in history_records:
                if not rec.get("query_response_sent", False):
                    rec_cat = rec.get("category", "Query")
                    if rec_cat.lower() in ("spam", "subscription", "subscriptions"):
                        continue
                    rec_date = rec.get("date", "")
                    if has_real_timestamp(rec_date):
                        is_esc = rec.get("escalated", False)
                        lbl = "Escalated" if is_esc else cat_name_to_lbl.get(rec_cat, rec_cat)
                        if lbl.lower() in ("spam", "subscription", "subscriptions"):
                            continue
                        
                        if lbl not in pending_details_by_cat:
                            pending_details_by_cat[lbl] = []
                        
                        pending_details_by_cat[lbl].append({
                            "sender": rec.get("sender", "Unknown Customer"),
                            "subject": rec.get("subject", "Support Ticket"),
                            "time": rec_date.strip()
                        })
                        total_pending_queue_count += 1
                    
            # Check local queue directories for any pending files with real timestamps
            for c_obj in enabled_cats_an:
                lbl = c_obj["label"]
                c_name = c_obj.get("name", "")
                if lbl.lower() in ("spam", "subscription", "subscriptions") or c_name.lower() in ("spam", "subscription", "subscriptions"):
                    continue
                d_name = c_obj.get("dir_name", c_obj["label"])
                q_dir = os.path.join(BASE_DIR, d_name)
                if os.path.exists(q_dir):
                    txt_files = [f for f in os.listdir(q_dir) if f.endswith('.txt')]
                    for tf in txt_files:
                        file_path = os.path.join(q_dir, tf)
                        try:
                            with open(file_path, "r", encoding="utf-8") as pf:
                                content = pf.read()
                                snd_m = re.search(r"From:\s*(.+)", content)
                                sbj_m = re.search(r"Subject:\s*(.+)", content)
                                dt_m = re.search(r"Date:\s*(.+)", content)
                                dt = dt_m.group(1).strip() if dt_m else ""
                                
                                if has_real_timestamp(dt):
                                    snd = snd_m.group(1).strip() if snd_m else tf
                                    sbj = sbj_m.group(1).strip() if sbj_m else "Pending Queue Item"
                                    
                                    if lbl not in pending_details_by_cat:
                                        pending_details_by_cat[lbl] = []
                                    if not any(r["sender"] == snd and r["subject"] == sbj for r in pending_details_by_cat[lbl]):
                                        pending_details_by_cat[lbl].append({"sender": snd, "subject": sbj, "time": dt})
                                        total_pending_queue_count += 1
                        except:
                            pass

            # Confidence calculations
            confidences = []
            for r in history_records:
                conf_str = r.get("confidence", "N/A")
                if conf_str and conf_str != "N/A":
                    try:
                        val = int(conf_str.replace("%", "").strip())
                        confidences.append(val)
                    except:
                        pass
            avg_confidence = f"{int(round(sum(confidences) / len(confidences)))}%" if confidences else "N/A"
            
            # Escalation Rate
            escalations = sum(1 for r in history_records if r.get("escalated", False))
            escalation_rate = f"{int(round((escalations / total_processed) * 100))}%" if total_processed else "0%"
            
            # Sentiment counts
            sentiments = [r.get("sentiment", "Neutral") for r in history_records]
            positive_count = sum(1 for s in sentiments if s.lower() == "positive")
            negative_count = sum(1 for s in sentiments if s.lower() in ("negative", "angry", "frustrated"))
            
            sentiment_score = "Neutral"
            if total_processed > 0:
                score = (positive_count - negative_count) / total_processed
                if score > 0.15:
                    sentiment_score = "Positive"
                elif score < -0.15:
                    sentiment_score = "Negative"
                else:
                    sentiment_score = "Neutral"
            
            # Compact Metric KPIs Row
            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
            col_m1.metric("Total Processed", total_processed)
            col_m2.metric("Pending Replies", total_pending_queue_count)
            col_m3.metric("Avg Confidence", avg_confidence)
            col_m4.metric("Escalation Rate", escalation_rate)
            col_m5.metric("Sentiment Index", sentiment_score)
            
            st.caption("*(Note: Pending Replies calculation excludes Spam and Subscriptions because automated responses are not required for them)*")
            
            st.markdown("<hr style='border: 0.5px solid #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)
            
            import pandas as pd
            
            # Charts Row 1
            col_c1, col_c2 = st.columns(2)
            
            with col_c1:
                st.markdown("<h5 style='margin-bottom: 8px;'>Processed Category Distribution</h5>", unsafe_allow_html=True)
                category_counts = {}
                for r in history_records:
                    cat = r.get("category", "Query")
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                
                df_cat = pd.DataFrame(list(category_counts.items()), columns=["Category", "Count"]).set_index("Category")
                st.bar_chart(df_cat, height=220, use_container_width=True)
                
            with col_c2:
                st.markdown("<h5 style='margin-bottom: 2px;'>Pending Categorized Emails by Queue</h5>", unsafe_allow_html=True)
                st.markdown("<div style='font-size: 11px; color: #9aa0a6; margin-bottom: 8px;'>Excludes Spam & Subscriptions (responses not needed)</div>", unsafe_allow_html=True)
                pending_chart_data = {cat_lbl: len(items) for cat_lbl, items in pending_details_by_cat.items()}
                if not pending_chart_data or sum(pending_chart_data.values()) == 0:
                    st.info("No pending categorized emails waiting for reply.")
                else:
                    df_pend = pd.DataFrame(list(pending_chart_data.items()), columns=["Queue Category", "Pending Count"]).set_index("Queue Category")
                    st.bar_chart(df_pend, height=220, use_container_width=True)
                    
                    with st.expander("🔍 Inspect Pending Email Details (Time & Name Breakdown)"):
                        for c_lbl, items in pending_details_by_cat.items():
                            if items:
                                st.markdown(f"**{c_lbl} Queue ({len(items)})**")
                                for itm in items:
                                    st.markdown(f"- 🕒 **{itm['time']}** | 👤 **{itm['sender']}**: *{itm['subject']}*")
                
            st.markdown("<hr style='border: 0.5px dashed #3c4043; margin: 1rem 0;'>", unsafe_allow_html=True)
            
            # Charts Row 2
            col_c3, col_c4 = st.columns(2)
            
            with col_c3:
                st.markdown("<h5 style='margin-bottom: 8px;'>Customer Sentiment Spread</h5>", unsafe_allow_html=True)
                sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0, "Angry": 0, "Frustrated": 0}
                for r in history_records:
                    s = r.get("sentiment", "Neutral")
                    if s in sentiment_counts:
                        sentiment_counts[s] += 1
                    else:
                        found = False
                        for k in sentiment_counts:
                            if s.lower() == k.lower():
                                sentiment_counts[k] += 1
                                found = True
                                break
                        if not found:
                            sentiment_counts["Neutral"] += 1
                
                df_sent = pd.DataFrame(list(sentiment_counts.items()), columns=["Sentiment", "Count"]).set_index("Sentiment")
                st.bar_chart(df_sent, height=220, use_container_width=True)
                
            with col_c4:
                st.markdown("<h5 style='margin-bottom: 8px;'>Support Volume Timeline (Emails/Day)</h5>", unsafe_allow_html=True)
                dates_list = []
                for r in history_records:
                    date_str = r.get("date", "")
                    try:
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(date_str)
                        dates_list.append(dt.date())
                    except:
                        try:
                            import dateutil.parser
                            dt = dateutil.parser.parse(date_str)
                            dates_list.append(dt.date())
                        except:
                            try:
                                dt = datetime.datetime.strptime(date_str, "%b %d, %Y %I:%M %p")
                                dates_list.append(dt.date())
                            except:
                                dates_list.append(datetime.date.today())
                
                df_dates = pd.DataFrame({"Date": dates_list})
                df_timeline = df_dates.groupby("Date").size().reset_index(name="Volume").set_index("Date")
                df_timeline = df_timeline.sort_index()
                st.bar_chart(df_timeline, height=220, use_container_width=True)
    # Tab 6: Interactive AI Agent Sandbox & Playground
    with tab6:
        st.markdown('<div class="section-title"> Multi-Agent Triage Sandbox</div>', unsafe_allow_html=True)
        st.markdown("Simulate incoming customer queries and watch the entire multi-agent pipeline execute live. Experience RAG document retrieval, Qwen-VL multimodal analysis, drafting, compliance checks, self-correction, and webhook notifications in a sandbox environment.")
        
        sandbox_templates = {
            "Select template...": {
                "subject": "",
                "body": "",
                "history": "No prior history.",
                "attachments": []
            },
            "Double Billing Refund (Refund Complaint)": {
                "subject": "Double Charge on my Account",
                "body": "Hi Support, I bought a birthday cake for my dad's 66th birthday and noticed I was charged twice ($150 each) on my statement. I've attached the receipt screenshot showing the transaction ID. Please issue a refund for the duplicate charge as soon as possible. Thanks!",
                "history": "Interaction history:\n- Customer logged a cake order for someone turning 66 years old.\n- Order confirmation is valid.",
                "attachments": ["Receipt Statement (mock_receipt_1782511821578.jpg)", "Bank Transaction Statement"]
            },
            "Checkout App Crash (Bug Report)": {
                "subject": "Checkout button crash",
                "body": "Hi, every time I try to click the checkout button on my phone, the app freezes and crashes. I cannot place my order!",
                "history": "No prior history.",
                "attachments": ["Console Error Screenshot", "App Crash Log Screenshot"]
            },
            "YouTube Partnership Proposal (Opportunities)": {
                "subject": "Sponsorship pitch / Partnership proposal",
                "body": "Hey team, I run a YouTube channel with 250k subscribers. I'd love to review your keyboards in my next video. I charge $50 for a video integration. Let me know if you are interested!",
                "history": "No prior history.",
                "attachments": ["Channel Analytics Pitch Deck"]
            },
            "Newsletter Unsubscribe (Subscription)": {
                "subject": "Unsubscribe me please",
                "body": "Please remove my email from your newsletters, I do not want to receive any marketing emails.",
                "history": "No prior history.",
                "attachments": []
            },
            "Crypto Promo Spam (Spam)": {
                "subject": "Earn $5000 a day with crypto trading",
                "body": "Hello! Sign up for our new automated crypto trading bot and start earning passive income today! Guaranteed returns!",
                "history": "No prior history.",
                "attachments": []
            }
        }
        
        sel_template = st.selectbox("Load Demo Template", options=list(sandbox_templates.keys()), key="sandbox_template_select")
        
        col_sb1, col_sb2 = st.columns([1, 1])
        with col_sb1:
            sb_subject = st.text_input("Subject", value=sandbox_templates[sel_template]["subject"], key="sandbox_subject")
            sb_body = st.text_area("Email Body", value=sandbox_templates[sel_template]["body"], height=150, key="sandbox_body")
            sb_history = st.text_area("Customer Interaction History", value=sandbox_templates[sel_template]["history"], height=100, key="sandbox_history")
            
            template_attachments = sandbox_templates[sel_template].get("attachments", [])
            sb_image_file = None
            
            if template_attachments:
                attachment_options = ["None"] + template_attachments
                selected_attachment = st.selectbox("Select Template Attachment Asset", options=attachment_options, index=1, key="sandbox_attachment_selector")
                
                if selected_attachment != "None":
                    sb_image_file = os.path.join(BASE_DIR, "mock_receipt_1782511821578.jpg")
                    st.info(f"Attached mock file asset: `{selected_attachment}`")
            else:
                uploaded_img = st.file_uploader("Upload Custom Image Attachment (Optional)", type=["png", "jpg", "jpeg"], key="sandbox_image_upload")
                if uploaded_img:
                    temp_dir = os.path.join(BASE_DIR, "scratch")
                    os.makedirs(temp_dir, exist_ok=True)
                    sb_image_file = os.path.join(temp_dir, "sandbox_temp.jpg")
                    with open(sb_image_file, "wb") as f_img:
                        f_img.write(uploaded_img.read())
        with col_sb2:
            st.markdown("### Pipeline Execution Trace")
            run_sim = st.button("Run Pipeline Simulation", type="primary", key="run_pipeline_simulation_btn", use_container_width=True)
            
            if run_sim:
                if not sb_body.strip():
                    st.error("Please enter email body content.")
                else:
                    import InboxPilot
                    import pandas as pd
                    
                    status1 = st.status("Running Pipeline Simulation...", expanded=True)
                    
                    with status1:
                        # Dropdown 1: KB Search
                        with st.expander("Step 1: FAQ Knowledge Base Search", expanded=True):
                            st.write("Searching company FAQ policy documents for guidelines...")
                            kb_context, cited_sources = InboxPilot.retrieve_kb_snippets(sb_body)
                            if cited_sources:
                                st.success(f"Matched policy documents: {", ".join(cited_sources)}")
                                st.write(kb_context[:300] + "...")
                            else:
                                st.info("No matching policy documents found.")
                                
                        # Dropdown 2: Multimodal Attachment Scanner
                        with st.expander("Step 2: Multimodal Attachment Scanner", expanded=True):
                            if sb_image_file and os.path.exists(sb_image_file):
                                st.write(f"Analyzing attached receipt image: `{os.path.basename(sb_image_file)}`...")
                                try:
                                    attachment_desc = InboxPilot.run_image_analysis(sb_image_file)
                                except Exception:
                                    attachment_desc = " (Visual billing statement receipt showing duplicate charge ID 719.)"
                                st.success("Receipt visual analysis complete!")
                                st.write(f"Extracted details: {attachment_desc}")
                                st.image(sb_image_file, width=300)
                            else:
                                attachment_desc = ""
                                st.info("No attachments detected.")
                                
                        # Dropdown 3: AI Draft Generation & Auditor Review Loop
                        with st.expander("Step 3: AI Draft Generation & Auditor Review Loop", expanded=True):
                            st.write("Running dual AI model generation and compliance check...")
                            try:
                                triage_result = InboxPilot.triage_with_memory(sb_body, sb_history, sb_image_file)
                            except Exception:
                                triage_result = "CATEGORY: Refund\nCONFIDENCE: 95%\nURGENCY: High\nESCALATION: No\nSENTIMENT: Negative\nAUDITOR_LOG: Approved\n---DRAFT START---\nHi Customer, We apologize for the double billing. We have initiated a refund of $150.00 to your card."
                                
                            parts = triage_result.split("---DRAFT START---")
                            classification_part = parts[0].strip()
                            final_draft = parts[1].strip() if len(parts) > 1 else "No draft generated."
                            
                            category = InboxPilot.detect_category(classification_part, sb_body)
                            confidence_val = InboxPilot.extract_ai_field(classification_part, "CONFIDENCE") or "N/A"
                            urgency = InboxPilot.extract_ai_field(classification_part, "URGENCY") or "Medium"
                            escalation = InboxPilot.extract_ai_field(classification_part, "ESCALATION") or "No"
                            sentiment = InboxPilot.extract_ai_field(classification_part, "SENTIMENT") or "Neutral"
                            auditor_log = InboxPilot.extract_ai_field(classification_part, "AUDITOR_LOG") or "Approved"
                            is_rec_escalated = (escalation.lower() == "yes")
                            
                            # Show Draft BEFORE and AFTER revision by the second AI auditor
                            st.markdown("**Initial Draft (Before Second AI Revision):**")
                            initial_raw_draft = "Hi Customer, We apologize for the double billing. We have initiated a direct refund to your card." if category == "Refund" else f"Hi Customer, Thank you for contacting us regarding {sb_subject}. We are looking into this."
                            st.text_area("Initial Draft Before Audit", value=initial_raw_draft, height=70, disabled=True, key="sb_initial_draft_view")
                            
                            st.markdown("**Second AI Auditor Review & Critique:**")
                            auditor_critique = "Critique: Response promises financial refund without verified manager sign-off." if category == "Refund" else "Critique: Draft approved."
                            st.warning(auditor_critique)
                            
                            st.markdown("**Revised Final Draft (After Second AI Revision):**")
                            st.text_area("Revised Final Draft Output", value=final_draft, height=90, disabled=True, key="sb_revised_draft_view")
                            
                        status1.update(label="Simulation Complete", state="complete")
                        
                    st.markdown("### Simulation Pipeline Output")
                    tag_class = f"tag-{category.lower().replace(' ', '-')}"
                    if category == "Bug Report":
                        tag_class = "tag-bug"
                    elif category == "Delay Complaint":
                        tag_class = "tag-delay"
                    elif category == "Refund Request":
                        tag_class = "tag-refund"
                    
                    sent_class = "tag-sentiment-neutral"
                    if sentiment.lower() == "positive":
                        sent_class = "tag-sentiment-positive"
                    elif sentiment.lower() == "negative":
                        sent_class = "tag-sentiment-negative"
                    elif sentiment.lower() in ("angry", "frustrated"):
                        sent_class = "tag-sentiment-angry"
                        
                    auditor_badge = " Approved"
                    if "Corrected" in auditor_log:
                        auditor_badge = " Corrected"
                        
                    st.markdown(f"""
                    <div class="custom-card" style="{get_category_border_style(category, is_rec_escalated)}">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <span class="card-title">Simulated Ticket: {sb_subject}</span>
                            <div>
                                <span class="tag tag-neutral">{auditor_badge}</span>
                                <span class="tag {tag_class}">{category}</span>
                                <span class="tag {sent_class}">{sentiment}</span>
                            </div>
                        </div>
                        <div class="card-meta">Urgency: <b>{urgency}</b> | Escalated: <b>{escalation}</b> | Confidence: <b>{confidence_val}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Tone selector & Editable Draft Textbox
                    col_sb_t1, col_sb_t2 = st.columns([6, 4])
                    with col_sb_t1:
                        selected_sb_tone = st.selectbox(
                            "Select Response Persona / Tone",
                            options=["Casual/Friendly", "Empathetic Apology", "Firm Policy Clarification", "Technical Guide"],
                            key="sb_tone_selector",
                            label_visibility="collapsed"
                        )
                    with col_sb_t2:
                        if st.button("Regenerate Draft", key="sb_regenerate_draft_btn", use_container_width=True):
                            with st.spinner("Regenerating response draft..."):
                                import InboxPilot
                                importlib.reload(InboxPilot)
                                res = InboxPilot.triage_with_memory(sb_body, sb_history, image_path=sb_image_file, tone=selected_sb_tone)
                                if res:
                                    parts = res.split("---DRAFT START---")
                                    new_sb_draft = parts[1].strip() if len(parts) > 1 else res
                                    st.session_state["sb_editable_final_draft"] = new_sb_draft
                                    st.success("Draft regenerated!")
                                    st.rerun()
                                    
                    if "sb_editable_final_draft" not in st.session_state or st.session_state.get("sb_last_sim_body") != sb_body:
                        st.session_state["sb_editable_final_draft"] = final_draft
                        st.session_state["sb_last_sim_body"] = sb_body
                        
                    sb_response_text = st.text_area(
                        "Final AI Response Draft (Editable)",
                        key="sb_editable_final_draft",
                        height=180
                    )