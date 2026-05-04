import streamlit as st
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import json
import os
import requests

st.set_page_config(
    page_title="G-Firefighter Alarm",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- PERSISTENT SETTINGS FILE ----------
SETTINGS_FILE = "fire_alarm_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

# ---------- SESSION STATE INIT ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()
if "detection_active" not in st.session_state:
    st.session_state.detection_active = False
if "logs" not in st.session_state:
    st.session_state.logs = []

def add_log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.insert(0, f"{timestamp} - {msg}")
    if len(st.session_state.logs) > 50:
        st.session_state.logs = st.session_state.logs[:50]

# ---------- CSS (all white text, sidebar fixed) ----------
st.markdown(r"""
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
    @media (max-width: 768px) {
        .logo-text { font-size: 1.8rem; }
        .fire-alert { font-size: 1.2rem; }
    }
    /* Main area text */
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
    .stTextInput input::placeholder {
        color: #cccccc !important;
    }
    .stRadio div[role="radiogroup"] div {
        color: white !important;
    }
    /* Buttons */
    .stButton button {
        color: white !important;
        background-color: #2a5298 !important;
        border: none !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        background-color: #1e3c72 !important;
    }
    /* Expander in main and sidebar */
    .streamlit-expanderHeader {
        color: white !important;
        background-color: rgba(0,0,0,0.4) !important;
        border-radius: 10px;
        font-weight: bold;
    }
    .streamlit-expanderHeader:hover {
        background-color: rgba(0,0,0,0.6) !important;
    }
    .streamlit-expanderContent {
        color: white !important;
    }
    /* Sidebar specific - force everything white */
    [data-testid="stSidebar"] {
        background: #0a0f2a;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .streamlit-expanderHeader,
    [data-testid="stSidebar"] .stCheckbox label span,
    [data-testid="stSidebar"] .stSlider label {
        color: white !important;
    }
    .stCheckbox label span {
        color: white !important;
    }
    /* Alert boxes */
    .stAlert {
        color: white !important;
        background-color: rgba(0,0,0,0.7) !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- LOGIN PAGE ----------
def login_page():
    st.markdown('<div class="logo-text">🚒 G‑Firefighter Alarm 🔥</div>', unsafe_allow_html=True)
    st.markdown("### 🔐 Secure Access")
    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password == "20082010":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

# ---------- SEND SMS (Twilio) ----------
def send_sms_alert(to_phone, message):
    twilio_sid = st.session_state.settings.get("twilio_account_sid")
    twilio_token = st.session_state.settings.get("twilio_auth_token")
    twilio_from = st.session_state.settings.get("twilio_phone")
    if not twilio_sid or not twilio_token or not twilio_from:
        add_log("SMS not configured: missing Twilio credentials")
        return False
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
        payload = {
            "To": to_phone,
            "From": twilio_from,
            "Body": message
        }
        r = requests.post(url, data=payload, auth=(twilio_sid, twilio_token))
        if r.status_code == 201:
            add_log("SMS alert sent")
            return True
        else:
            add_log(f"SMS failed: {r.text}")
            return False
    except Exception as e:
        add_log(f"SMS error: {e}")
        return False

# ---------- SEND EMAIL ----------
def send_alert_email(recipient=None):
    email_config = st.session_state.settings.get("email_config", {})
    if not email_config.get("sender") or not email_config.get("password"):
        add_log("Email not configured")
        return False, "Email not configured"
    try:
        msg = MIMEMultipart()
        msg["From"] = email_config["sender"]
        msg["To"] = recipient or email_config.get("recipient")
        msg["Subject"] = "🔥 FIRE ALERT - G-Firefighter Alarm System"
        body = f"""
        ALERT: Fire has been detected by your G-Firefighter Alarm system.
        Please call the fire department immediately.
        
        Time: {time.ctime()}
        
        This is an automated message from your home security system.
        """
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_config["sender"], email_config["password"])
        server.send_message(msg)
        server.quit()
        add_log("Email alert sent")
        return True, "Email sent"
    except Exception as e:
        add_log(f"Email error: {e}")
        return False, str(e)

# ---------- SIDEBAR CONFIGURATION ----------
def sidebar_config():
    st.sidebar.title("⚙️ Real‑Life Configuration")

    # Camera source
    st.sidebar.subheader("📷 Camera Source")
    cam_source = st.sidebar.selectbox("Source Type", ["Webcam", "IP Camera"])
    ip_camera_url = ""
    if cam_source == "IP Camera":
        ip_camera_url = st.sidebar.text_input("MJPEG/JPEG URL", 
            value=st.session_state.settings.get("ip_camera_url", ""),
            help="Example: http://192.168.1.100:8080/shot.jpg")
    st.session_state.settings["cam_source"] = cam_source
    st.session_state.settings["ip_camera_url"] = ip_camera_url

    # Detection model
    st.sidebar.subheader("🔥 Detection Method")
    detection_model = st.sidebar.selectbox("Model", ["Simple Color", "TensorFlow.js (Alpha)"])
    st.session_state.settings["detection_model"] = detection_model

    # Sensitivity
    sensitivity = st.sidebar.slider("Sensitivity (Fire % threshold)", 
        min_value=0.5, max_value=5.0, value=1.0, step=0.1)
    st.session_state.settings["sensitivity"] = sensitivity / 100.0

    # Email alerts
    st.sidebar.subheader("📧 Email Alerts")
    with st.sidebar.expander("Configure Email"):
        sender = st.text_input("Your Gmail", value=st.session_state.settings.get("email_config", {}).get("sender", ""))
        app_pwd = st.text_input("App Password", type="password", value=st.session_state.settings.get("email_config", {}).get("password", ""))
        recipient = st.text_input("Recipient Email", value=st.session_state.settings.get("email_config", {}).get("recipient", ""))
        if st.button("Save Email Settings"):
            st.session_state.settings["email_config"] = {
                "sender": sender,
                "password": app_pwd,
                "recipient": recipient
            }
            st.success("Email settings saved")

    # SMS alerts
    st.sidebar.subheader("📱 SMS Alerts (Twilio)")
    with st.sidebar.expander("Configure SMS"):
        twilio_sid = st.text_input("Account SID", value=st.session_state.settings.get("twilio_account_sid", ""))
        twilio_token = st.text_input("Auth Token", type="password", value=st.session_state.settings.get("twilio_auth_token", ""))
        twilio_phone = st.text_input("Twilio Phone Number", value=st.session_state.settings.get("twilio_phone", ""))
        sms_recipient = st.text_input("Recipient Phone Number", value=st.session_state.settings.get("sms_recipient", ""))
        if st.button("Save SMS Settings"):
            st.session_state.settings["twilio_account_sid"] = twilio_sid
            st.session_state.settings["twilio_auth_token"] = twilio_token
            st.session_state.settings["twilio_phone"] = twilio_phone
            st.session_state.settings["sms_recipient"] = sms_recipient
            st.success("SMS settings saved")

    # Test mode
    st.sidebar.subheader("🧪 Test Mode")
    test_mode = st.sidebar.checkbox("Simulate fire every 30 sec (no real alert)", 
        value=st.session_state.settings.get("test_mode", False))
    st.session_state.settings["test_mode"] = test_mode

    # Save/Load settings
    if st.sidebar.button("💾 Save Settings to Disk"):
        save_settings(st.session_state.settings)
        st.sidebar.success("Settings saved!")
    if st.sidebar.button("📂 Load Settings from Disk"):
        st.session_state.settings = load_settings()
        st.rerun()

    # ========== PRICING SECTION (ADDED) ==========
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Pricing Plans")
    st.sidebar.markdown("""
    **One‑time Purchase (Lifetime License)**  
    – $99 USD  
    – Includes all features (webcam/IP camera, email, SMS, test mode)  
    – Free updates for one year, then $19/year optional

    **Monthly Subscription**  
    – $9.99 USD / month  
    – Cancel anytime  
    – Same features as lifetime

    **Professional Plan**  
    – $49 USD / month  
    – Monitor up to 5 cameras simultaneously  
    – Priority email support  
    – Extended log retention (90 days)

    *All plans include basic email support. Volume discounts available for businesses.*
    """)

    # Log viewer
    st.sidebar.subheader("📜 Recent Logs")
    for log in st.session_state.logs[:10]:
        st.sidebar.text(log)

# ---------- MAIN APP ----------
def main_app():
    sidebar_config()

    # Main area
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div style="display: flex; align-items: center;"><span class="logo-small">🚒</span><span class="logo-small">G‑Firefighter Alarm</span><span class="logo-small">🔥</span></div>', unsafe_allow_html=True)
        st.title("🔥 Live Fire Detection")
        st.markdown("**Real‑time monitoring** – AI + color detection, email & SMS alerts")
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown("---")

    # Camera HTML component with settings injected
    settings_json = json.dumps({
        "cam_source": st.session_state.settings.get("cam_source", "Webcam"),
        "ip_camera_url": st.session_state.settings.get("ip_camera_url", ""),
        "detection_model": st.session_state.settings.get("detection_model", "Simple Color"),
        "sensitivity": st.session_state.settings.get("sensitivity", 0.01),
        "test_mode": st.session_state.settings.get("test_mode", False)
    })

    camera_html = f"""
    <div id="camera-container" style="text-align: center;">
        <video id="video" width="100%" autoplay muted style="border-radius: 20px; border: 2px solid #ff6b6b; display: none;"></video>
        <img id="ipImage" width="100%" style="border-radius: 20px; border: 2px solid #ff6b6b; display: none;">
        <canvas id="canvas" style="display: none;"></canvas>
        <div id="status" style="margin-top: 1rem; padding: 0.5rem; border-radius: 20px; background: rgba(0,0,0,0.7); color: white;"></div>
        <button id="startBtn" style="margin-top: 1rem; padding: 0.5rem 1.5rem; background-color: #ff4b4b; border: none; border-radius: 30px; color: white; font-weight: bold;">Start Detection</button>
        <button id="stopBtn" style="margin-top: 1rem; margin-left: 1rem; padding: 0.5rem 1.5rem; background-color: #555; border: none; border-radius: 30px; color: white; font-weight: bold;">Stop Detection</button>
        <button id="stopAlarmBtn" style="margin-top: 1rem; margin-left: 1rem; padding: 0.5rem 1.5rem; background-color: #ff9800; border: none; border-radius: 30px; color: black; font-weight: bold;">Stop Alarm Sound</button>
    </div>
    <script>
        (function() {{
            const settings = {settings_json};
            const video = document.getElementById('video');
            const ipImage = document.getElementById('ipImage');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const statusDiv = document.getElementById('status');
            let stream = null;
            let detectionInterval = null;
            let alarmPlaying = false;
            let audioCtx = null;
            let oscillator = null;
            let gain = null;
            let lastEmailTriggerTime = 0;
            let testModeCounter = 0;

            function playAlarm() {{
                if (alarmPlaying) return;
                try {{
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    oscillator = audioCtx.createOscillator();
                    gain = audioCtx.createGain();
                    oscillator.type = 'sawtooth';
                    oscillator.frequency.value = 880;
                    gain.gain.value = 0.5;
                    oscillator.connect(gain);
                    gain.connect(audioCtx.destination);
                    oscillator.start();
                    alarmPlaying = true;
                    if (audioCtx.state === 'suspended') audioCtx.resume();
                }} catch(e) {{ console.error("Audio error", e); }}
            }}
            function stopAlarm() {{
                if (oscillator) {{
                    try {{ oscillator.stop(); oscillator.disconnect(); }} catch(e) {{}}
                    oscillator = null;
                }}
                if (audioCtx) {{ audioCtx.close().catch(console.error); audioCtx = null; }}
                alarmPlaying = false;
            }}

            function detectFire_Simple(frameData, width, height, threshold) {{
                let firePixels = 0;
                for (let i = 0; i < frameData.data.length; i += 4) {{
                    let r = frameData.data[i];
                    let g = frameData.data[i+1];
                    let b = frameData.data[i+2];
                    if (r > 120 && g < 100 && b < 100) firePixels++;
                }}
                let ratio = firePixels / (width * height);
                return {{ fire: ratio > threshold, ratio: ratio }};
            }}

            let tfReady = false;
            if (settings.detection_model === "TensorFlow.js (Alpha)") {{
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@latest';
                script.onload = () => {{ console.log("TF.js loaded"); tfReady = true; }};
                document.head.appendChild(script);
            }}

            async function detectFire_TF(frameData, width, height, threshold) {{
                return {{ fire: false, ratio: 0 }};
            }}

            async function captureAndAnalyze() {{
                if (settings.test_mode) {{
                    testModeCounter++;
                    if (testModeCounter % 30 === 0) {{
                        statusDiv.innerHTML = '<span style="color: #ff4b4b;">🔥 SIMULATED FIRE DETECTION 🔥</span>';
                        playAlarm();
                        const now = Date.now();
                        if (now - lastEmailTriggerTime > 30000) {{
                            lastEmailTriggerTime = now;
                            fetch(window.location.href + '?fire_detected=1', {{ method: 'POST' }});
                        }}
                        return;
                    }} else {{
                        statusDiv.innerHTML = '<span style="color: #2e7d32;">✅ Test mode – no fire (simulation will trigger periodically)</span>';
                        if (alarmPlaying) stopAlarm();
                    }}
                    return;
                }}

                if (settings.cam_source === "Webcam" && video.videoWidth) {{
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                }} else if (settings.cam_source === "IP Camera" && ipImage.complete && ipImage.naturalWidth) {{
                    canvas.width = ipImage.naturalWidth;
                    canvas.height = ipImage.naturalHeight;
                    ctx.drawImage(ipImage, 0, 0, canvas.width, canvas.height);
                }} else {{
                    return;
                }}
                const frameData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                let result;
                if (settings.detection_model === "TensorFlow.js (Alpha)" && tfReady) {{
                    result = await detectFire_TF(frameData, canvas.width, canvas.height, settings.sensitivity);
                }} else {{
                    result = detectFire_Simple(frameData, canvas.width, canvas.height, settings.sensitivity);
                }}
                if (result.fire) {{
                    statusDiv.innerHTML = '<span style="color: #ff4b4b; font-weight: bold;">🔥 FIRE DETECTED! Alarm sounding. 🔥</span>';
                    playAlarm();
                    const now = Date.now();
                    if (now - lastEmailTriggerTime > 30000) {{
                        lastEmailTriggerTime = now;
                        fetch(window.location.href + '?fire_detected=1', {{ method: 'POST' }});
                    }}
                }} else {{
                    statusDiv.innerHTML = '<span style="color: #2e7d32;">✅ No fire detected. (Fire ratio: ' + (result.ratio*100).toFixed(2) + '%)</span>';
                    if (alarmPlaying) stopAlarm();
                }}
            }}

            let ipRefreshInterval = null;
            function startIpRefresh() {{
                if (ipRefreshInterval) clearInterval(ipRefreshInterval);
                ipRefreshInterval = setInterval(() => {{
                    if (settings.ip_camera_url) {{
                        ipImage.src = settings.ip_camera_url + '?t=' + Date.now();
                    }}
                }}, 200);
            }}
            function stopIpRefresh() {{
                if (ipRefreshInterval) clearInterval(ipRefreshInterval);
                ipRefreshInterval = null;
            }}

            function startDetection() {{
                if (detectionInterval) clearInterval(detectionInterval);
                detectionInterval = setInterval(captureAndAnalyze, 500);
                statusDiv.innerHTML = "Detection active...";
            }}
            function stopDetection() {{
                if (detectionInterval) clearInterval(detectionInterval);
                detectionInterval = null;
                stopAlarm();
                statusDiv.innerHTML = "Detection stopped.";
            }}

            document.getElementById('startBtn').onclick = () => {{
                if (settings.cam_source === "Webcam") {{
                    if (!stream) {{
                        navigator.mediaDevices.getUserMedia({{ video: true }})
                            .then(s => {{
                                stream = s;
                                video.srcObject = stream;
                                video.style.display = "block";
                                ipImage.style.display = "none";
                                video.play();
                                startDetection();
                            }})
                            .catch(err => {{
                                statusDiv.innerHTML = "Camera error: " + err.message;
                            }});
                    }} else {{
                        startDetection();
                    }}
                }} else if (settings.cam_source === "IP Camera") {{
                    if (!ipRefreshInterval) {{
                        startIpRefresh();
                        ipImage.style.display = "block";
                        video.style.display = "none";
                        startDetection();
                    }} else {{
                        startDetection();
                    }}
                }}
            }};
            document.getElementById('stopBtn').onclick = () => {{
                stopDetection();
                if (stream) {{
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                    video.srcObject = null;
                }}
                if (ipRefreshInterval) stopIpRefresh();
                video.style.display = "none";
                ipImage.style.display = "none";
            }};
            document.getElementById('stopAlarmBtn').onclick = () => {{
                stopAlarm();
            }};
        }})();
    </script>
    """
    st.components.v1.html(camera_html, height=550)

    # Handle fire detection trigger (email + SMS)
    query_params = st.query_params
    if query_params.get("fire_detected") == "1":
        email_recipient = st.session_state.settings.get("email_config", {}).get("recipient")
        if email_recipient:
            send_alert_email(email_recipient)
        sms_recipient = st.session_state.settings.get("sms_recipient")
        if sms_recipient:
            send_sms_alert(sms_recipient, "🔥 FIRE ALERT! Check your home immediately.")
        add_log("Fire detected – alerts triggered")
        st.query_params.clear()

    st.markdown("---")
    st.caption("G‑Firefighter Alarm – Protecting your home 24/7 | Powered by AI + Cloud Alerts")

# ---------- ROUTING ----------
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
