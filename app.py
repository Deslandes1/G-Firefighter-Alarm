<style>
    .stApp {
        background: linear-gradient(135deg, #1e2a3a, #0f172a);
    }
    .logo-text {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        font-family: 'Courier New', monospace;
        color: #ff6b6b;
        text-shadow: 2px 2px 4px #000000;
        margin-bottom: 1rem;
    }
    .logo-small {
        font-size: 1.8rem;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        color: #ff6b6b;
        display: inline-block;
        margin-right: 10px;
    }
    .fire-alert {
        background-color: #ff4b4b;
        padding: 1rem;
        border-radius: 20px;
        text-align: center;
        font-weight: bold;
        font-size: 1.5rem;
        animation: blink 1s infinite;
        color: white !important;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .status-safe {
        background-color: #2e7d32;
        padding: 0.8rem;
        border-radius: 20px;
        text-align: center;
        font-weight: bold;
        color: white !important;
    }
    .stop-alarm-btn {
        background-color: #ff9800;
        color: black;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 30px;
        border: none;
        margin-top: 10px;
    }
    @media (max-width: 768px) {
        .logo-text { font-size: 1.8rem; }
        .fire-alert { font-size: 1.2rem; }
    }
    /* NEW: Make all default text white */
    .stMarkdown, .stRadio label, .stTextInput label, .stButton button p, .stCaption {
        color: white !important;
    }
    h1, h2, h3, .stHeading {
        color: white !important;
    }
    .stRadio div[role="radiogroup"] label {
        color: white !important;
    }
    .stFileUploader label {
        color: white !important;
    }
    footer .stCaption, .stCaption {
        color: white !important;
    }
    /* Ensure placeholder text is also visible */
    .stTextInput input::placeholder {
        color: #cccccc !important;
    }
    /* Keep radio button circles visible */
    .stRadio div[role="radiogroup"] div {
        color: white !important;
    }
</style>
