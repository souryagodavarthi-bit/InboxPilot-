
## How to Run Locally

1. Clone the repository.
2. Copy the `.env.example` file and rename it to `.env`.
3. Obtain your own Google Cloud Service Account credentials JSON.
4. copy googlecreds_example.json and rename googlecreds.json file and place keys.
4. Place the JSON file in the project root.
5. Run the installation and start commands...

Streamli UI link - https://inboxpilotplus.streamlit.app/
This link will only work with the credetials obatained as per above steps however the credentials cannot be pushed through GitHub.


Here is the revised, professional README.md with the color scheme updated to reflect the light blue branding.

InboxPilot+ Control Panel
InboxPilot+ is an automated email management and triage platform designed to optimize customer support workflows. By intercepting incoming communications, the application dynamically categorizes messages, evaluates customer sentiment, handles secure authentication, and manages autonomous workflow responses through a centralized, high-performance interface styled in a clean light blue theme.

Core Features
Dynamic Triage Engine: Automatically parses and routes incoming emails into dedicated operational categories including Refund Requests, Bug Reports, Delay Complaints, Queries, Opportunities, Subscriptions, and Spam.

Sentiment Identification: Evaluates the emotional urgency of incoming customer communications (e.g., Angry, Frustrated, Neutral, Positive) to escalate high-risk interactions immediately.

Granular Rule Management: Provides comprehensive controls to toggle global auto-triage, modify auto-reply behaviors, and configure specific escalation protocols per category.

Secure Data Governance: Integrates native Google OAuth2 workflows for secure email access alongside a comprehensive, automated file-exclusion system to protect sensitive customer data and local operational records.

Light Blue Theme Architecture: Implements a streamlined rendering engine conforming to minimalist Material Design specifications, using a custom light blue aesthetic for clear data visualization.

Repository Architecture
The core application structure operates via the following baseline deployment logic:

Plaintext
├── app.py                      # Core control panel interface and runtime lifecycle
├── accounts.json               # Local credential persistence layer (Git ignored)
├── google_creds.json           # Google OAuth application credentials (Git ignored)
├── business_profile.json       # User environment configuration and state (Git ignored)
├── categories_config.json      # Dynamic triage classification schemas (Git ignored)
├── Customer_Memory/            # Historical interaction database logs (Git ignored)
└── Incoming_Emails/            # Raw email stream ingress directory (Git ignored)
Installation and Deployment
Prerequisites
Python 3.8 or higher

Google Cloud Platform Console developer account with Gmail API enablement

Dependencies
Install the required core packages using the package installer for Python:

Bash
pip install streamlit requests
Initial Configuration
Secure your Google OAuth 2.0 client credentials from the Google Cloud Console.

Initialize a local file named google_creds.json in the root directory matching the following structure:

JSON
{
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8501/"
}
Execute the Streamlit runtime command to initialize the interface:

Bash
streamlit run app.py
Data Privacy and Security
This repository enforces strict operational boundaries between application logic and private data. The underlying Git configuration explicitly isolates customer interactions, local operational profiles, and security tokens.

The following files and directories are programmatically restricted from remote deployment to maintain compliance and prevent data leaks:

Dynamic data directories (Customer_Memory/, Incoming_Emails/)

Generated triage routing targets (Refund_Requests/, Bug_Reports/, etc.)

Local authentication profiles, dynamic system preferences, and runtime key assets