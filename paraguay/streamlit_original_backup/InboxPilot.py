import imaplib
import smtplib
import os
import json
import re
import base64
import requests
from email.mime.text import MIMEText
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1. Folder Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCOMING_DIR = os.path.join(BASE_DIR, "Incoming_Emails")
MEMORY_DIR = os.path.join(BASE_DIR, "Customer_Memory")

# Create base folders
for folder in [INCOMING_DIR, MEMORY_DIR]:
    os.makedirs(folder, exist_ok=True)

# Helper functions for dynamic category configuration
def make_date_local(date_str):
    if not date_str:
        import datetime
        return datetime.datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M:%S %z")
    try:
        import datetime
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone().strftime("%a, %d %b %Y %H:%M:%S %z")
    except Exception:
        try:
            import datetime
            import dateutil.parser
            dt = dateutil.parser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone().strftime("%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            return date_str

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

def load_business_profile():
    profile_file = os.path.join(BASE_DIR, "business_profile.json")
    if os.path.exists(profile_file):
        try:
            with open(profile_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"business_description": "A general enterprise business."}

def get_category_directory(category_name):
    categories = load_categories_config()
    for cat in categories:
        if cat["name"].lower() == category_name.lower():
            dir_path = os.path.join(BASE_DIR, cat["dir_name"])
            os.makedirs(dir_path, exist_ok=True)
            return dir_path
    # Fallback directory
    fallback_path = os.path.join(BASE_DIR, "General_Queries")
    os.makedirs(fallback_path, exist_ok=True)
    return fallback_path

# Create folders for all configured categories on startup
try:
    for cat in load_categories_config():
        if cat.get("enabled", True) and not cat.get("archived", False):
            os.makedirs(os.path.join(BASE_DIR, cat["dir_name"]), exist_ok=True)
except Exception:
    pass

# 2. Setup Qwen Client
api_key = os.environ.get("GEMINI_API_KEY", "DEMO_KEY_PLACEHOLDER")
try:
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
except Exception as e:
    client = None
    print(f"Notice: LLM Client initialized in demo mode: {e}")

KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "Knowledge_Base")
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

def run_image_analysis(image_path):
    if not os.path.exists(image_path):
        return ""
    try:
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/jpeg"
        if ext in (".png", ".png"):
            mime_type = "image/png"
        elif ext == ".gif":
            mime_type = "image/gif"
        
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        data_url = f"data:{mime_type};base64,{encoded_string}"
        
        response = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this support ticket attachment image. What issue does it show? Extract key transaction IDs, invoices, errors, or defects. Keep your analysis concise and factual (under 100 words)."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        analysis_text = response.choices[0].message.content
        return f"\n[ATTACHMENT ANALYSIS (Qwen-VL): {analysis_text.strip()}]"
    except Exception as e:
        print(f"Error in visual analysis: {e}")
        return f"\n[ATTACHMENT ANALYSIS ERROR: Failed to parse visual attachment due to error: {e}]"

def retrieve_kb_snippets(email_text):
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        return "", []
    
    files = [f for f in os.listdir(KNOWLEDGE_BASE_DIR) if f.endswith(('.txt', '.md'))]
    if not files:
        return "", []
        
    snippets = []
    stop_words = {"the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "is", "for", "with", "on", "at", "by", "from", "i", "we", "you", "my", "your", "this", "that"}
    email_words = set(re.findall(r'[a-zA-Z0-9]+', email_text.lower())) - stop_words
    
    for filename in files:
        file_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = re.split(r'\n\s*\n|###', content)
            for chunk in chunks:
                chunk = chunk.strip()
                if len(chunk) < 20:
                    continue
                chunk_words = set(re.findall(r'[a-zA-Z0-9]+', chunk.lower())) - stop_words
                overlap = email_words.intersection(chunk_words)
                score = len(overlap)
                if score > 0:
                    snippets.append((score, filename, chunk))
        except Exception as e:
            print(f"Error reading KB file {filename}: {e}")
            
    snippets.sort(key=lambda x: x[0], reverse=True)
    top_snippets = snippets[:2]
    
    if not top_snippets:
        return "", []
        
    formatted_str = "\nRELEVANT BUSINESS POLICIES & FAQ:\n---\n"
    sources = []
    for idx, (score, source, text) in enumerate(top_snippets, 1):
        formatted_str += f"Source: {source}\n{text}\n\n"
        sources.append(f"{source}: {text[:100]}...")
    formatted_str += "---"
    return formatted_str, sources

def run_auditor_check(email_text, initial_draft, business_desc):
    auditor_prompt = f"""You are the InboxPilot+ Quality & Policy Compliance Auditor.
Your job is to inspect the generated response draft to ensure it complies with company policies:
1. Never promise refunds, free shipping, credits, or exchanges unless the email is explicitly a valid refund request and matches the business context.
2. Keep the tone supportive, polite, professional, and helpful.
3. Never mention internal database systems, code names, or the fact that you are an AI.
4. Ensure all customer questions in the original email are addressed.

Review the:
- Original Email: {email_text}
- Business Profile: {business_desc}
- Generated Response Draft: {initial_draft}

Output strictly in this format:
APPROVED: [Yes/No]
FEEDBACK: [If not approved, explain what needs to be changed in a single sentence. If approved, leave this blank.]
"""
    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "You are a strict quality compliance auditor. Output decisions exactly in the requested format."},
                {"role": "user", "content": auditor_prompt}
            ],
            max_tokens=150
        )
        result = response.choices[0].message.content
        approved = "APPROVED: Yes" in result
        feedback = ""
        feedback_match = re.search(r"FEEDBACK:\s*(.*)", result, re.IGNORECASE)
        if feedback_match:
            feedback = feedback_match.group(1).strip()
            
        return approved, feedback
    except Exception as e:
        print(f"Auditor Error: {e}")
        return True, ""

def send_webhook_notifications(subject, sender, category, snippet, is_escalated):
    import datetime
    profile = load_business_profile()
    slack_url = profile.get("slack_webhook", "")
    discord_url = profile.get("discord_webhook", "")
    
    if not slack_url and not discord_url:
        return
        
    title = " InboxPilot+ Urgent Escalation" if is_escalated else " New Opportunity / Partnership Alert"
    color = 15158332 if is_escalated else 3066993
    
    if slack_url:
        try:
            slack_payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": title}
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*From:* `{sender}`\n*Subject:* {subject}\n*Category:* `{category}`\n*Snippet:* _{snippet}_"
                        }
                    }
                ]
            }
            requests.post(slack_url, json=slack_payload, timeout=5)
            print("Sent Slack webhook notification.")
        except Exception as e:
            print(f"Slack webhook error: {e}")
            
    if discord_url:
        try:
            discord_payload = {
                "embeds": [
                    {
                        "title": title,
                        "color": color,
                        "fields": [
                            {"name": "Sender", "value": sender, "inline": True},
                            {"name": "Category", "value": category, "inline": True},
                            {"name": "Subject", "value": subject, "inline": False}
                        ],
                        "description": snippet,
                        "timestamp": datetime.datetime.now().astimezone().isoformat()
                    }
                ]
            }
            requests.post(discord_url, json=discord_payload, timeout=5)
            print("Sent Discord webhook notification.")
        except Exception as e:
            print(f"Discord webhook error: {e}")

def triage_with_memory(email_text, past_history, image_path=None, tone=None):
    categories = load_categories_config()
    enabled_categories = [c for c in categories if c.get("enabled", True) and not c.get("archived", False)]
    
    profile = load_business_profile()
    business_desc = profile.get("business_description", "A general enterprise business.")
    
    # 1. RAG Retrieve KB FAQ Context
    kb_context, cited_sources = retrieve_kb_snippets(email_text)
    
    # 2. Process image with Qwen-VL if available
    attachment_desc = ""
    if image_path:
        print(f"Running visual analysis on attachment: {image_path}")
        attachment_desc = run_image_analysis(image_path)
        
    full_email_text = email_text + attachment_desc
    
    category_list_str = ", ".join(c["name"] for c in enabled_categories)
    category_descriptions = ""
    for cat in enabled_categories:
        category_descriptions += f"    - {cat['name']}: {cat['description']}\n"
 
    escalate_on_reply_cats = [c["name"] for c in enabled_categories if c.get("escalate_on_reply", False)]
    escalation_instruction = ""
    if escalate_on_reply_cats:
        cats_str = ", ".join(escalate_on_reply_cats)
        escalation_instruction = f"Specifically, if the history shows this customer is following up/replying to our response and their email falls into one of these categories: [{cats_str}], you MUST set ESCALATION to Yes."
 
    tone_requirement = ""
    if tone:
        tone_requirement = f"You MUST write the customer response draft in this communication style / tone: {tone}."
 
    system_prompt = f"""
    You are InboxPilot+, an intelligent enterprise triage agent with persistent memory.
    
    BUSINESS CONTEXT (Your company's business profile):
    {business_desc}
    
    {kb_context}
    
    CRITICAL CONTEXT (Past Interactions with this Customer):
    {past_history}
    
    Analyze the incoming email and categorize it into one of these categories:
{category_descriptions}
    Provide a CONFIDENCE score as a whole-number percentage from 0-100%.
    Use a numeric percent format like "72%" and do not leave this blank.
    If you cannot estimate confidence, output "0%" rather than omitting it.
 
    If the history shows this customer is writing again about an unresolved issue, you MUST mark the URGENCY as Critical and set ESCALATION to Yes. {escalation_instruction}
    
    Determine if this email is a follow-up or reply. If the email references past correspondence, has "Re:"/"Fwd:" in subject, or past history exists, set IS_FOLLOWUP to Yes. Otherwise set IS_FOLLOWUP to No.

    Output your decision strictly in this format:
    CATEGORY: [{category_list_str}]
    CONFIDENCE: [0-100]%
    URGENCY: [High, Medium, Low, Critical]
    ESCALATION: [Yes/No]
    IS_FOLLOWUP: [Yes/No]
    SENTIMENT: [Positive, Neutral, Negative, Angry, Frustrated]
    ---DRAFT START---
    [Write a customer response draft. If escalated, apologize for the repeated trouble, acknowledge their prior history, and mention a human manager is reviewing it to resolve it.]
    {tone_requirement}
    """
    
    ai_output = None
    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_email_text}
            ]
        )
        ai_output = response.choices[0].message.content
    except Exception as e:
        print(f"API Error: {e}")
        return None

    if not ai_output:
        return None

    # Parse and run Auditor loop
    parts = ai_output.split("---DRAFT START---")
    classification_part = parts[0].strip()
    draft_reply = parts[1].strip() if len(parts) > 1 else "No draft generated."
    
    category = detect_category(classification_part, email_text)
    sentiment = extract_ai_field(classification_part, "SENTIMENT") or "Neutral"
    
    auditor_log = "N/A"
    if category not in ("Spam", "Subscription"):
        approved, feedback = run_auditor_check(email_text, draft_reply, business_desc)
        if not approved:
            print(f"Auditor compliance check failed: {feedback}. Regenerating draft...")
            try:
                reg_prompt = f"""
                The compliance auditor rejected your response draft with this feedback: "{feedback}".
                Please rewrite the draft reply to satisfy this feedback, keeping the exact same classification headers.
                """
                reg_response = client.chat.completions.create(
                    model="qwen-plus",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_email_text},
                        {"role": "assistant", "content": ai_output},
                        {"role": "user", "content": reg_prompt}
                    ]
                )
                reg_output = reg_response.choices[0].message.content
                if reg_output:
                    reg_parts = reg_output.split("---DRAFT START---")
                    if len(reg_parts) > 1:
                        draft_reply = reg_parts[1].strip()
                auditor_log = f"Corrected: {feedback}"
            except Exception as e:
                print(f"Error in regeneration: {e}")
                auditor_log = f"Failed correction: {e}"
        else:
            auditor_log = "Approved"

    # Reconstruct headers including sentiment, auditor_log, and cited_sources
    new_lines = []
    for line in classification_part.splitlines():
        if line.strip() and not line.strip().startswith("SENTIMENT:"):
            new_lines.append(line.strip())
            
    new_lines.append(f"SENTIMENT: {sentiment}")
    new_lines.append(f"AUDITOR_LOG: {auditor_log}")
    if cited_sources:
        new_lines.append(f"CITED_SOURCES: {' | '.join(cited_sources)}")
    if attachment_desc:
        new_lines.append("ATTACHMENT_INFO: Processed successfully")

    reconstructed_headers = "\n".join(new_lines)
    return f"{reconstructed_headers}\n---DRAFT START---\n{draft_reply}"

GOOGLE_CREDS_FILE = os.path.join(BASE_DIR, "google_creds.json")
TRIAGE_HISTORY_FILE = os.path.join(BASE_DIR, "triage_history.json")

def load_google_creds():
    if os.path.exists(GOOGLE_CREDS_FILE):
        try:
            with open(GOOGLE_CREDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def refresh_access_token(creds):
    if not creds or "refresh_token" not in creds:
        return None
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }
    try:
        res = requests.post(token_url, data=data, timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token")
        else:
            print(f"Error refreshing access token: {res.text}")
    except Exception as e:
        print(f"Exception refreshing token: {e}")
    return None

def sanitize_customer_name(from_header):
    if "<" in from_header:
        name_part = from_header.split("<")[0].strip()
        if name_part:
            name_part = name_part.strip('"').strip("'")
            if name_part:
                return re.sub(r'[^a-zA-Z0-9_]', '_', name_part.replace(' ', '_'))
    
    email_part = from_header
    if "<" in from_header:
        match = re.search(r'<(.*?)>', from_header)
        if match:
            email_part = match.group(1)
    email_prefix = email_part.split("@")[0]
    return re.sub(r'[^a-zA-Z0-9_]', '_', email_prefix)

def load_customer_history(sender_email):
    customer_name = sanitize_customer_name(sender_email)
    memory_file_path = os.path.join(MEMORY_DIR, f"{customer_name}_history.txt")
    if os.path.exists(memory_file_path):
        try:
            with open(memory_file_path, "r", encoding="utf-8") as mf:
                return mf.read()
        except:
            pass
    return "No prior history. This is a brand new customer."

def extract_body(part):
    mime_type = part.get('mimeType', '')
    body_data = part.get('body', {}).get('data', '')
    if mime_type == 'text/plain' and body_data:
        try:
            return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        except Exception:
            pass
    if 'parts' in part:
        for subpart in part['parts']:
            body = extract_body(subpart)
            if body:
                return body
    return ""

def get_message_body(message_data):
    payload = message_data.get('payload', {})
    body = extract_body(payload)
    if not body:
        body_data = payload.get('body', {}).get('data', '')
        if body_data:
            try:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            except Exception:
                pass
    return body or ""


def extract_ai_field(text, field_name):
    pattern = re.compile(rf"^{re.escape(field_name)}\s*:\s*(.+)$", re.IGNORECASE)
    for line in text.splitlines():
        stripped = line.strip()
        match = pattern.match(stripped)
        if match:
            return match.group(1).strip()
        if field_name.lower() in stripped.lower() and ":" in stripped:
            parts = stripped.split(":", 1)
            if parts[0].strip().lower().startswith(field_name.lower()):
                return parts[1].strip()
    return None


def normalize_confidence_value(raw_value):
    if not raw_value:
        return "N/A"
    text = raw_value.strip()
    search = re.search(r"(\d+(?:\.\d+)?)", text)
    if not search:
        return "N/A"
    try:
        value = float(search.group(1))
    except ValueError:
        return "N/A"
    if '%' not in text and 0.0 <= value <= 1.0:
        value *= 100.0
    value = max(0.0, min(100.0, value))
    return f"{int(round(value))}%"


def extract_urgency(classification_part):
    urgency = "Low"
    if not classification_part:
        return urgency
    for line in classification_part.splitlines():
        if "URGENCY:" in line.upper():
            parts = line.split(":", 1)
            if len(parts) > 1:
                value = parts[1].strip()
                return value if value else urgency
    return urgency


def has_subscription_hint(text):
    if not text:
        return False
    normalized = text.lower()
    return any(
        kw in normalized
        for kw in [
            "unsubscribe", "newsletter", "manage preferences", "manage subscription",
            "subscription settings", "opt-out", "optout", "cancel subscription",
            "subscription renewal", "update preferences", "view in browser",
            "view online", "mailing list", "email preference", "received this email because",
            "email list", "unsubscribe here", "preferences update", "mailout", "bulletin"
        ]
    )


def has_spam_hint(text):
    if not text:
        return False
    normalized = text.lower()
    return any(
        kw in normalized
        for kw in [
            "buy now", "click here", "limited time", "special offer",
            "promotion", "free trial", "act now", "order now", "advertisement"
        ]
    )


def detect_category(classification_part, body_text=None):
    categories = load_categories_config()
    enabled_categories = [c for c in categories if c.get("enabled", True) and not c.get("archived", False)]
    
    # Prefer explicit CATEGORY: line if provided by the model
    explicit = None
    try:
        explicit = extract_ai_field(classification_part, "CATEGORY")
    except Exception:
        explicit = None

    if explicit:
        val = explicit.strip().lower()
        # First match exact names or labels
        for cat in enabled_categories:
            name_lower = cat["name"].lower()
            label_lower = cat.get("label", "").lower()
            if val == name_lower or val == label_lower or name_lower in val or label_lower in val:
                return cat["name"]
        
        # Opportunities special mappings
        if any(c["name"] == "Opportunities" for c in enabled_categories):
            if any(k in val for k in ["opportunity", "opportunities", "sponsorship", "partner", "collab"]):
                return "Opportunities"
                
        # Query/Spam standard checks
        if "query" in val:
            if any(c["name"] == "Subscription" for c in enabled_categories):
                if has_subscription_hint(classification_part) or (body_text and has_subscription_hint(body_text)):
                    return "Subscription"
            if any(c["name"] == "Query" for c in enabled_categories):
                return "Query"
        if "spam" in val:
            if any(c["name"] == "Subscription" for c in enabled_categories):
                if body_text and has_subscription_hint(body_text):
                    return "Subscription"
            if any(c["name"] == "Spam" for c in enabled_categories):
                return "Spam"

    normalized = classification_part.lower()
    if "category:" in normalized:
        # Check standard & custom categories
        for cat in enabled_categories:
            name_lower = cat["name"].lower()
            label_lower = cat.get("label", "").lower()
            if name_lower in normalized or label_lower in normalized:
                return cat["name"]
        
        # Opportunities fallback
        if any(c["name"] == "Opportunities" for c in enabled_categories):
            if any(k in normalized for k in ["opportunity", "opportunities", "sponsorship", "partner", "collab"]):
                return "Opportunities"

        if "query" in normalized:
            if any(c["name"] == "Subscription" for c in enabled_categories):
                if has_subscription_hint(classification_part) or (body_text and has_subscription_hint(body_text)):
                    return "Subscription"
            if any(c["name"] == "Query" for c in enabled_categories):
                return "Query"
        if "spam" in normalized:
            if any(c["name"] == "Subscription" for c in enabled_categories):
                if body_text and has_subscription_hint(body_text):
                    return "Subscription"
            if any(c["name"] == "Spam" for c in enabled_categories):
                return "Spam"

    # Fallback heuristics
    if body_text and has_subscription_hint(body_text) and any(c["name"] == "Subscription" for c in enabled_categories):
        return "Subscription"
    if body_text and has_spam_hint(body_text) and any(c["name"] == "Spam" for c in enabled_categories):
        return "Spam"

    if has_subscription_hint(classification_part) and any(c["name"] == "Subscription" for c in enabled_categories):
        return "Subscription"
    if has_spam_hint(classification_part) and any(c["name"] == "Spam" for c in enabled_categories):
        return "Spam"

    # Default fallback
    if any(c["name"] == "Query" for c in enabled_categories):
        return "Query"
    if enabled_categories:
        return enabled_categories[0]["name"]
    return "Query"


def extract_unsubscribe_info_from_headers(headers_dict):
    unsubscribe_url = None
    unsubscribe_mailto = None
    raw = headers_dict.get("list-unsubscribe") or headers_dict.get("List-Unsubscribe")
    if raw:
        mailto_match = re.search(r"mailto:([^>\s]+)", raw, flags=re.IGNORECASE)
        if mailto_match:
            unsubscribe_mailto = mailto_match.group(1).strip()
        url_match = re.search(r"https?://[^>,\s]+", raw, flags=re.IGNORECASE)
        if url_match:
            unsubscribe_url = url_match.group(0).strip()
    return unsubscribe_url, unsubscribe_mailto


def extract_unsubscribe_info_from_text(text):
    if not text:
        return None
    # Prefer explicit unsubscribe links
    links = re.findall(r'href=["\'](https?://[^"\']+)["\']', text, flags=re.IGNORECASE)
    for url in links:
        if "unsubscribe" in url.lower() or "optout" in url.lower() or "opt-out" in url.lower():
            return url.strip()
    # Search for plain URLs containing unsubscribe keywords
    text_urls = re.findall(r'https?://[^\s\)\]\"\']+', text)
    for url in text_urls:
        if "unsubscribe" in url.lower() or "optout" in url.lower() or "opt-out" in url.lower():
            return url.strip()
    mailto_match = re.search(r'mailto:([^>\s]+)', text, flags=re.IGNORECASE)
    if mailto_match:
        return f"mailto:{mailto_match.group(1).strip()}"
    return None


def save_local_metadata(folder, filename, category, urgency, confidence, unsubscribe_link=None, escalated=False, is_followup=False, sentiment="Neutral", auditor_log="N/A", cited_sources="", has_attachment=False):
    meta_data = {
        "category": category,
        "urgency": urgency,
        "confidence": confidence,
        "source_file": filename,
        "unsubscribe_link": unsubscribe_link,
        "escalated": escalated,
        "is_followup": is_followup,
        "sentiment": sentiment,
        "auditor_log": auditor_log,
        "cited_sources": cited_sources,
        "has_attachment": has_attachment
    }
    meta_path = os.path.join(folder, f"meta_{filename}.json")
    try:
        with open(meta_path, "w") as mf:
            json.dump(meta_data, mf, indent=2)
    except Exception as e:
        print(f"Error saving metadata for {filename}: {e}")


def log_triage_to_history(sender, subject, category, urgency, draft_reply, date_str, body_content="", confidence="N/A", thread_id=None, message_id=None):
    history = []
    if os.path.exists(TRIAGE_HISTORY_FILE):
        try:
            with open(TRIAGE_HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            pass
    
    history.append({
        "sender": sender,
        "subject": subject,
        "category": category,
        "urgency": urgency,
        "draft_reply": draft_reply,
        "date": date_str,
        "body_content": body_content,
        "confidence": confidence,
        "thread_id": thread_id,
        "message_id": message_id,
        "unsubscribe_link": None,
        "query_response_sent": False
    })
    
    try:
        with open(TRIAGE_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving triage history: {e}")

def send_gmail_reply(access_token, to_email, subject, body, thread_id, in_reply_to_msg_id):
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
        
    message = MIMEText(body)
    message['to'] = to_email
    message['subject'] = subject
    if in_reply_to_msg_id:
        message['In-Reply-To'] = in_reply_to_msg_id
        message['References'] = in_reply_to_msg_id
        
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {"raw": raw_message}
    if thread_id:
        payload["threadId"] = thread_id
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"Successfully sent reply to {to_email}")
            return True
        else:
            print(f"Error sending email reply: {res.text}")
    except Exception as e:
        print(f"Exception sending email: {e}")
    return False

def mark_as_read(access_token, message_id):
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "removeLabelIds": ["UNREAD"]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            return True
        else:
            print(f"Error marking message {message_id} as read: {res.text}")
    except Exception as e:
        print(f"Exception marking message as read: {e}")
    return False

def run_gmail_triage(creds):
    access_token = refresh_access_token(creds)
    if not access_token:
        print("Failed to obtain fresh access token for Gmail triage.")
        return
        
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            print(f"Error fetching unread messages: {res.text}")
            return
    except Exception as e:
        print(f"Exception fetching unread messages: {e}")
        return
        
    messages_data = res.json()
    messages = messages_data.get("messages", [])
    if not messages:
        print("No new unread emails found in Gmail.")
        return
        
    print(f"Found {len(messages)} unread messages to process.")
    
    for msg in messages:
        msg_id = msg["id"]
        thread_id = msg["threadId"]
        
        msg_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
        try:
            msg_res = requests.get(msg_url, headers=headers, timeout=10)
            if msg_res.status_code != 200:
                print(f"Error fetching details for message {msg_id}: {msg_res.text}")
                continue
            message_data = msg_res.json()
        except Exception as e:
            print(f"Exception fetching details for message {msg_id}: {e}")
            continue
            
        headers_list = message_data.get("payload", {}).get("headers", [])
        headers_dict = {h["name"].lower(): h["value"] for h in headers_list}
        
        from_header = headers_dict.get("from", "")
        subject_header = headers_dict.get("subject", "(No Subject)")
        message_id_header = headers_dict.get("message-id", "")
        date_header = headers_dict.get("date", "")
        
        email_body = get_message_body(message_data)
        unsubscribe_url, unsubscribe_mailto = extract_unsubscribe_info_from_headers(headers_dict)
        if not unsubscribe_url:
            unsubscribe_url = extract_unsubscribe_info_from_text(email_body)
        unsubscribe_link = unsubscribe_url or unsubscribe_mailto
        
        print(f"--- Processing Gmail Message: '{subject_header}' from {from_header} ---")
        
        customer_name = sanitize_customer_name(from_header)
        memory_file_path = os.path.join(MEMORY_DIR, f"{customer_name}_history.txt")
        
        is_followup = False
        subj_lower = subject_header.lower()
        if subj_lower.startswith("re:") or subj_lower.startswith("fwd:") or "reply" in subj_lower or "follow" in subj_lower:
            is_followup = True

        if os.path.exists(memory_file_path):
            with open(memory_file_path, "r") as mf:
                customer_history = mf.read()
            print(f"[Memory Found] This customer has contacted us before:\n{customer_history.strip()}")
            is_followup = True
        else:
            customer_history = "No prior history. This is a brand new customer."
            print("[New Customer] No prior history found.")
            
        ai_output = triage_with_memory(email_body, customer_history)
        
        if ai_output:
            parts = ai_output.split("---DRAFT START---")
            classification_part = parts[0]
            draft_reply_part = parts[1] if len(parts) > 1 else "No draft generated."
            
            print(f"\nAI Decision:\n{classification_part.strip()}")
            
            raw_confidence = extract_ai_field(classification_part, "CONFIDENCE")
            confidence = normalize_confidence_value(raw_confidence)
            urgency = extract_urgency(classification_part)
            category = detect_category(classification_part, email_body)
            if unsubscribe_link:
                category = "Subscription"
            current_issue = "Spam"
            if category == "Refund":
                current_issue = "Refund Request"
            elif category == "Bug Report":
                current_issue = "Bug Report"
            elif category == "Delay":
                current_issue = "Delay Complaint"
            elif category == "Query":
                current_issue = "General Query"
            elif category == "Subscription":
                current_issue = "Subscription"
            
            if category not in ("Spam", "Subscription"):
                with open(memory_file_path, "a") as mf:
                    mf.write(f"- Interaction: Logged a {current_issue}.\n")
                    
            recipient_email = from_header
            if "<" in from_header:
                match = re.search(r'<(.*?)>', from_header)
                if match:
                    recipient_email = match.group(1)
            
            # If AI confidence is low, escalate to Query to prevent wrong automatic replies
            conf_val = 100
            if confidence and confidence != "N/A":
                try:
                    conf_val = int(confidence.replace("%", "").strip())
                except Exception:
                    conf_val = 100

            categories = load_categories_config()
            enabled_categories = [c for c in categories if c.get("enabled", True) and not c.get("archived", False)]
            
            # Find category config details dynamically
            cat_config = next((c for c in enabled_categories if c["name"] == category), None)
            
            # If low confidence on auto-reply category, force to Query fallback (or general fallback)
            if cat_config and cat_config.get("has_auto_reply", False) and conf_val <= 80:
                print(f"Low AI confidence ({conf_val}%) for category {category}. Overriding to Query for manual review.")
                category = "Query" if any(c["name"] == "Query" for c in enabled_categories) else enabled_categories[0]["name"]
                cat_config = next((c for c in enabled_categories if c["name"] == category), None)

            # Bulletproof check: double-check that this is not spam or subscription before calling send_gmail_reply
            is_subscription = (
                category == "Subscription" or
                unsubscribe_link is not None or
                has_subscription_hint(email_body) or
                has_subscription_hint(subject_header)
            )
            is_spam = (
                category == "Spam" or
                ((has_spam_hint(email_body) or has_spam_hint(subject_header)) and category != "Opportunities")
            )

            # Ensure subscription override takes precedence over spam
            if is_subscription and any(c["name"] == "Subscription" for c in enabled_categories):
                category = "Subscription"
                current_issue = "Subscription"
            elif is_spam and any(c["name"] == "Spam" for c in enabled_categories):
                category = "Spam"
                current_issue = "Spam"

            is_escalated = "ESCALATION: Yes" in classification_part
            if "IS_FOLLOWUP: Yes" in classification_part:
                is_followup = True

            if is_followup:
                cat_config = next((c for c in enabled_categories if c["name"] == category), None)
                if cat_config and cat_config.get("escalate_on_reply", False):
                    print(f"Force escalating follow-up email for category: {category}")
                    is_escalated = True
            draft_text = draft_reply_part.strip()
            
            # Determine if auto-reply should be sent
            has_auto_reply = cat_config.get("has_auto_reply", False) if cat_config else False
                            
            if category in ("Spam", "Subscription"):
                print(f"Aborting automatic reply: Category is {category}.")
                sent_success = False
            elif is_escalated:
                print("Aborting automatic reply: Email is flagged for ESCALATION to human.")
                sent_success = False
            elif not has_auto_reply:
                print(f"Aborting automatic reply: Category is {category} (manual response required).")
                sent_success = False
            else:
                sent_success = send_gmail_reply(access_token, recipient_email, subject_header, draft_text, thread_id, message_id_header)
            
            if sent_success:
                mark_as_read(access_token, msg_id)
                print(f"Marked message {msg_id} as read on Gmail.")
            else:
                # Mark query, spam, subscription, opportunities, and escalated emails as read to prevent reprocessing
                if not has_auto_reply or category in ("Spam", "Subscription") or is_escalated:
                    mark_as_read(access_token, msg_id)
                    print(f"Marked {category.lower()} message {msg_id} as read on Gmail.")

            sentiment = extract_ai_field(classification_part, "SENTIMENT") or "Neutral"
            auditor_log = extract_ai_field(classification_part, "AUDITOR_LOG") or "N/A"

            log_entry = {
                "sender": from_header,
                "subject": subject_header,
                "category": category,
                "urgency": urgency,
                "draft_reply": draft_text,
                "date": make_date_local(date_header),
                "body_content": email_body,
                "confidence": confidence,
                "thread_id": thread_id,
                "message_id": message_id_header,
                "unsubscribe_link": unsubscribe_link,
                "query_response_sent": False,
                "escalated": is_escalated,
                "is_followup": is_followup,
                "sentiment": sentiment,
                "auditor_log": auditor_log
            }
            history = []
            if os.path.exists(TRIAGE_HISTORY_FILE):
                try:
                    with open(TRIAGE_HISTORY_FILE, "r") as f:
                        history = json.load(f)
                except Exception:
                    pass
            history.append(log_entry)
            try:
                with open(TRIAGE_HISTORY_FILE, "w") as f:
                    json.dump(history, f, indent=2)
            except Exception as e:
                print(f"Error saving triage history: {e}")

            # Send Slack/Discord webhooks for Opportunities or Escalated alerts
            send_webhook_notifications(subject_header, from_header, category, email_body[:200], is_escalated)
            
            if is_escalated:
                print(" [ALERT] CRITICAL ESCALATION: Notifying Human Support Team Manager!")
                
            print("--- Finished Processing Message ---\n")

def run_local_triage():
    files = [f for f in os.listdir(INCOMING_DIR) if f.endswith('.txt')]
    
    if not files:
        print("No new emails found in Incoming_Emails/.")
        return

    for filename in files:
        file_path = os.path.join(INCOMING_DIR, filename)
        
        with open(file_path, "r") as f:
            email_content = f.read()
            
        unsubscribe_link = extract_unsubscribe_info_from_text(email_content)
        print(f"--- Processing: {filename} ---")
        
        customer_name = filename.replace(".txt", "")
        memory_file_path = os.path.join(MEMORY_DIR, f"{customer_name}_history.txt")
        
        is_followup = False
        fn_lower = filename.lower()
        if "followup" in fn_lower or "reply" in fn_lower or fn_lower.startswith("re_"):
            is_followup = True

        if os.path.exists(memory_file_path):
            with open(memory_file_path, "r") as mf:
                customer_history = mf.read()
            print(f"[Memory Found] This customer has contacted us before:\n{customer_history.strip()}")
            is_followup = True
        else:
            customer_history = "No prior history. This is a brand new customer."
            print("[New Customer] No prior history found.")

        # Check for image attachments matching customer_name
        image_path = None
        image_ext = None
        for ext in (".jpg", ".jpeg", ".png"):
            test_img = os.path.join(INCOMING_DIR, f"{customer_name}{ext}")
            if os.path.exists(test_img):
                image_path = test_img
                image_ext = ext
                break

        ai_output = triage_with_memory(email_content, customer_history, image_path)
        
        if ai_output:
            parts = ai_output.split("---DRAFT START---")
            classification_part = parts[0]
            draft_reply_part = parts[1] if len(parts) > 1 else "No draft generated."
            
            raw_confidence = extract_ai_field(classification_part, "CONFIDENCE")
            confidence = normalize_confidence_value(raw_confidence)
            print(f"\nAI Decision:\n{classification_part.strip()}")
            
            urgency = extract_urgency(classification_part)
            category = detect_category(classification_part, email_content)
            sentiment = extract_ai_field(classification_part, "SENTIMENT") or "Neutral"
            auditor_log = extract_ai_field(classification_part, "AUDITOR_LOG") or "N/A"
            cited_sources = extract_ai_field(classification_part, "CITED_SOURCES") or ""

            # If AI confidence is low, escalate to Query to prevent wrong automatic replies
            conf_val = 100
            if confidence and confidence != "N/A":
                try:
                    conf_val = int(confidence.replace("%", "").strip())
                except Exception:
                    conf_val = 100

            categories = load_categories_config()
            enabled_categories = [c for c in categories if c.get("enabled", True) and not c.get("archived", False)]
            cat_config = next((c for c in enabled_categories if c["name"] == category), None)

            if cat_config and cat_config.get("has_auto_reply", False) and conf_val <= 80:
                print(f"Low AI confidence ({conf_val}%) for category {category}. Overriding to Query for manual review.")
                category = "Query" if any(c["name"] == "Query" for c in enabled_categories) else enabled_categories[0]["name"]
                cat_config = next((c for c in enabled_categories if c["name"] == category), None)

            # Bulletproof check: double-check that this is not spam or subscription
            is_subscription = (
                category == "Subscription" or
                unsubscribe_link is not None or
                has_subscription_hint(email_content)
            )
            is_spam = (
                category == "Spam" or
                (has_spam_hint(email_content) and category != "Opportunities")
            )

            # Ensure subscription override takes precedence over spam
            if is_subscription and any(c["name"] == "Subscription" for c in enabled_categories):
                category = "Subscription"
            elif is_spam and any(c["name"] == "Spam" for c in enabled_categories):
                category = "Spam"

            is_escalated = "ESCALATION: Yes" in classification_part
            if "IS_FOLLOWUP: Yes" in classification_part:
                is_followup = True

            if is_followup:
                cat_config = next((c for c in enabled_categories if c["name"] == category), None)
                if cat_config and cat_config.get("escalate_on_reply", False):
                    print(f"Force escalating follow-up email for category: {category}")
                    is_escalated = True

            target_folder = get_category_directory(category)
            current_issue = next((c["label"] for c in enabled_categories if c["name"] == category), category)

            if is_escalated:
                current_issue = f"Escalated {current_issue}"

            
            if category in ("Spam", "Subscription"):
                if category == "Subscription":
                    with open(memory_file_path, "a") as mf:
                        mf.write(f"- Interaction: Logged a {current_issue}.\n")
                    print("Subscription message stored for review.")
                else:
                    print("No reply draft saved for Spam category.")
            else:
                with open(memory_file_path, "a") as mf:
                    mf.write(f"- Interaction: Logged a {current_issue}.\n")
                
                reply_filename = f"reply_{filename}"
                reply_path = os.path.join(target_folder, reply_filename)
                with open(reply_path, "w") as reply_file:
                    reply_file.write(draft_reply_part.strip())
                print(f"Saved support reply to folder: {reply_filename}")

            destination_path = os.path.join(target_folder, filename)
            destination_filename = filename
            if os.path.exists(destination_path):
                name_part, extension_part = os.path.splitext(filename)
                destination_filename = f"{name_part}_followup{extension_part}"
                destination_path = os.path.join(target_folder, destination_filename)
                
            os.rename(file_path, destination_path)
            
            # Also move image attachment if it exists
            if image_path and image_ext:
                img_dest_filename = f"{os.path.splitext(destination_filename)[0]}{image_ext}"
                img_dest_path = os.path.join(target_folder, img_dest_filename)
                try:
                    os.rename(image_path, img_dest_path)
                    print(f"Moved attachment to category directory: {img_dest_filename}")
                except Exception as e:
                    print(f"Error moving image attachment: {e}")

            subscriptions_folder = get_category_directory("Subscription")
            unsubscribe_link_for_meta = unsubscribe_link if target_folder == subscriptions_folder else None
            
            save_local_metadata(
                target_folder, 
                destination_filename, 
                category, 
                urgency, 
                confidence, 
                unsubscribe_link=unsubscribe_link_for_meta,
                escalated=is_escalated,
                is_followup=is_followup,
                sentiment=sentiment,
                auditor_log=auditor_log,
                cited_sources=cited_sources,
                has_attachment=(image_path is not None)
            )
            print(f"Saved metadata for {destination_filename}")

            # Trigger webhooks for Slack/Discord alerts
            send_webhook_notifications(f"Local Support Request: {customer_name}", customer_name + "@example.com", category, email_content[:200], is_escalated)

            # Log local triage to history file
            import datetime
            log_entry = {
                "sender": customer_name + "@example.com",
                "subject": f"Local Support Request: {customer_name}",
                "category": category,
                "urgency": urgency,
                "draft_reply": draft_reply_part,
                "date": datetime.datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M:%S %z"),
                "body_content": email_content,
                "confidence": confidence,
                "thread_id": "local",
                "message_id": "local_" + customer_name,
                "unsubscribe_link": unsubscribe_link_for_meta,
                "query_response_sent": False,
                "escalated": is_escalated,
                "is_followup": is_followup,
                "sentiment": sentiment,
                "auditor_log": auditor_log
            }
            history = []
            if os.path.exists(TRIAGE_HISTORY_FILE):
                try:
                    with open(TRIAGE_HISTORY_FILE, "r") as f:
                        history = json.load(f)
                except Exception:
                    pass
            history.append(log_entry)
            try:
                with open(TRIAGE_HISTORY_FILE, "w") as f:
                    json.dump(history, f, indent=2)
            except Exception as e:
                print(f"Error logging local triage: {e}")
            print("--- Finished Processing ---\n")

def main():
    creds = load_google_creds()
    if creds and "refresh_token" in creds:
        run_gmail_triage(creds)
    else:
        run_local_triage()

if __name__ == "__main__":
    main()

PROVIDER_CONFIG_FILE = os.path.join(BASE_DIR, "email_providers.json")

def load_email_providers():
    if os.path.exists(PROVIDER_CONFIG_FILE):
        try:
            with open(PROVIDER_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active_provider": "Gmail", "microsoft": {}, "imap_smtp": {}}

def save_email_providers(data):
    try:
        with open(PROVIDER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving providers: {e}")

def test_imap_smtp_connection(imap_host, imap_port, smtp_host, smtp_port, username, password):
    try:
        mail = imaplib.IMAP4_SSL(imap_host, int(imap_port))
        mail.login(username, password)
        mail.logout()
        
        server = smtplib.SMTP(smtp_host, int(smtp_port), timeout=10)
        server.starttls()
        server.login(username, password)
        server.quit()
        return True, "SSL/TLS Authorized Successfully!"
    except Exception as e:
        return False, str(e)
