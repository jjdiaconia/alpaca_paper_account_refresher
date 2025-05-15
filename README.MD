README.TXT

\===============================================================================
ALPACA PAPER‐ACCOUNT REFRESHER
------------------------------

This package provides two scripts:

1. record\_auth\_state.py
   – Opens a headed browser for you to log in to Alpaca
   – Saves your cookies & local storage to auth\_state.json

2. refresh\_three\_paper\_accounts.py
   – Uses auth\_state.json to authenticate
   – Deletes and recreates N dummy paper accounts (“DUMMY\_PAPER\_1”, …)
   – Generates new access keys and validates them
   – Prints out a BLOCK of PAPER#\_API\_KEY/SECRET constants for your constants.py

\===============================================================================
PREREQUISITES
-------------

• Python 3.8 or later
• pip
• Node.js (for Playwright)

\===============================================================================
INSTALLATION
------------

1. Create (and activate) a virtual environment (optional but recommended):
   python3 -m venv .venv
   source .venv/bin/activate

2. Install Python dependencies:
   pip install playwright requests alpaca-py

3. Install Playwright browsers:
   playwright install

\===============================================================================

1. RECORD YOUR AUTH STATE

---

Run the login recorder to capture your session cookies & CSRF token:

python record\_auth\_state.py

• A headed Chromium window will open at
[https://app.alpaca.markets/login](https://app.alpaca.markets/login)
• Log in manually.
• Once you see the dashboard, auth\_state.json will be saved.
• If you take longer than 300 s, the script will exit without saving.

\===============================================================================
2\) REFRESH PAPER ACCOUNTS
--------------------------

Ensure auth\_state.json is present, then run:

# default creates 3 slots with \$1 000 000 each:

python refresh\_three\_paper\_accounts.py

You can override with environment variables:
NUM\_SLOTS=3          # number of “DUMMY\_PAPER\_N” accounts to refresh
STARTING\_CASH=500000 # starting cash balance for each

Example:

NUM\_SLOTS=3 STARTING\_CASH=1000000 python refresh\_three\_paper\_accounts.py

The script will:
• Delete any existing “DUMMY\_PAPER\_1”…“DUMMY\_PAPER\_N” accounts
• Create fresh ones, generate new access keys
• Validate each key via alpaca-py’s TradingClient
• Print at the end:

```
 # ─── Copy these into your constants.py ─────────────
 PAPER1_API_KEY    = "PK…"
 PAPER1_API_SECRET = "…"
 PAPER2_API_KEY    = "PK…"
 PAPER2_API_SECRET = "…"
 PAPER3_API_KEY    = "PK…"
 PAPER3_API_SECRET = "…"
```

Copy those lines into your constants.py and restart your application.

\===============================================================================
TROUBLESHOOTING
---------------

• “auth\_state.json not found” → run record\_auth\_state.py first.
• CSRF errors → your auth\_state.json may have expired; re‐run the recorder.
• Playwright/browser issues → ensure `playwright install` completed.

\===============================================================================
LICENSE & SUPPORT
-----------------

# This is provided as‐is. For questions, see the project README or raise an issue.
