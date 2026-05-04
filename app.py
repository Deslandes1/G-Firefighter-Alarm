import streamlit as st
import streamlit.components.v1 as components
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

st.set_page_config(
    page_title="G-Firefighter Alarm",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- CSS (all text white, buttons readable) ----------
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
    /* Make all normal text white */
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
    /* Make button text white and background dark */
    .stButton button {
        color: white !important;
        background-color: #2a5298 !important;
        border: none !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        background-color: #1e3c72 !important;
    }
    /* Make expander header and content white */
    .streamlit-expanderHeader {
        color: white !important;
        background-color: rgba(0,0,0,0.3) !important;
        border-radius: 10px;
    }
    .streamlit-expanderContent {
        color: white !important;
    }
    /* Ensure warning/info boxes also have readable text */
    .stAlert {
        color: white !important;
        background-color: rgba(0,0,0,0.7) !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- LOGIN STATE ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "email_config" not in st.session_state:
    st.session_state.email_config = None
if "email_sent_flag" not in st.session_state:
    st.session_state.email_sent_flag = False

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

# ---------- EMAIL SENDER ----------
def send_alert_email():
    if st.session_state.email_config is None:
        return False, "Email not configured"
    try:
        msg = MIMEMultipart()
        msg["From"] = st.session_state.email_config["sender"]
        msg["To"] = st.session_state.email_config["recipient"]
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
        server.login(st.session_state.email_config["sender"], st.session_state.email_config["password"])
        server.send_message(msg)
        server.quit()
        return True, "Email sent"
    except Exception as e:
        return False, str(e)

# ---------- MAIN APP ----------
def main_app():
    st.markdown('<div style="display: flex; align-items: center; justify-content: center;"><span class="logo-small">🚒</span><span class="logo-small">G‑Firefighter Alarm</span><span class="logo-small">🔥</span></div>', unsafe_allow_html=True)
    st.title("🔥 Live Fire Detection")
    st.markdown("**Camera feed** – we analyze for flames. Alarm + Email on detection.")

    # Logout button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.email_sent_flag = False
        st.rerun()

    st.markdown("---")

    # Email configuration section
    with st.expander("📧 Configure Email Alerts (required for email notifications)"):
        sender = st.text_input("Your Gmail Address")
        app_password = st.text_input("Gmail App Password", type="password")
        recipient = st.text_input("House Owner's Email Address")
        if st.button("Save Email Settings"):
            if sender and app_password and recipient:
                st.session_state.email_config = {
                    "sender": sender,
                    "password": app_password,
                    "recipient": recipient
                }
                st.success("Email settings saved.")
            else:
                st.error("All fields required.")

    # Check for fire detection trigger from JavaScript (via query param)
    query_params = st.query_params
    if query_params.get("fire_detected") == "1":
        if not st.session_state.email_sent_flag:
            success, msg = send_alert_email()
            if success:
                st.success("Alert email sent to house owner.")
                st.session_state.email_sent_flag = True
            else:
                st.error(f"Failed to send email: {msg}")
        # Clear the query param to prevent repeated sending
        st.query_params.clear()

    st.markdown("### 🎥 Camera Detection")

    # Build HTML/JS component (camera, detection, alarm)
    camera_html = """
    <div id="camera-container" style="text-align: center;">
        <video id="video" width="100%" autoplay muted style="border-radius: 20px; border: 2px solid #ff6b6b;"></video>
        <canvas id="canvas" style="display: none;"></canvas>
        <div id="status" style="margin-top: 1rem; padding: 0.5rem; border-radius: 20px; background: rgba(0,0,0,0.7); color: white;"></div>
        <button id="startBtn" style="margin-top: 1rem; padding: 0.5rem 1.5rem; background-color: #ff4b4b; border: none; border-radius: 30px; color: white; font-weight: bold;">Start Detection</button>
        <button id="stopBtn" style="margin-top: 1rem; margin-left: 1rem; padding: 0.5rem 1.5rem; background-color: #555; border: none; border-radius: 30px; color: white; font-weight: bold;">Stop Detection</button>
        <button id="stopAlarmBtn" style="margin-top: 1rem; margin-left: 1rem; padding: 0.5rem 1.5rem; background-color: #ff9800; border: none; border-radius: 30px; color: black; font-weight: bold;">Stop Alarm Sound</button>
    </div>
    <script>
        (function() {
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const statusDiv = document.getElementById('status');
            let stream = null;
            let detectionInterval = null;
            let alarmPlaying = false;
            let audioCtx = null;
            let oscillator = null;
            let gain = null;

            function playAlarm() {
                if (alarmPlaying) return;
                try {
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
                    if (audioCtx.state === 'suspended') {
                        audioCtx.resume();
                    }
                } catch(e) { console.error("Audio error", e); }
            }

            function stopAlarm() {
                if (oscillator) {
                    try { oscillator.stop(); oscillator.disconnect(); } catch(e) {}
                    oscillator = null;
                }
                if (audioCtx) {
                    audioCtx.close().catch(console.error);
                    audioCtx = null;
                }
                alarmPlaying = false;
            }

            function detectFire(frameData, width, height) {
                let firePixels = 0;
                for (let i = 0; i < frameData.data.length; i += 4) {
                    let r = frameData.data[i];
                    let g = frameData.data[i+1];
                    let b = frameData.data[i+2];
                    let rr = r/255, gg = g/255, bb = b/255;
                    let max = Math.max(rr, gg, bb);
                    let min = Math.min(rr, gg, bb);
                    let h, s, v;
                    v = max;
                    let delta = max - min;
                    if (max === 0) s = 0;
                    else s = delta / max;
                    if (delta === 0) h = 0;
                    else {
                        if (max === rr) h = 60 * (((gg - bb)/delta) % 6);
                        else if (max === gg) h = 60 * (((bb - rr)/delta) + 2);
                        else h = 60 * (((rr - gg)/delta) + 4);
                    }
                    if (h < 0) h += 360;
                    if ((h <= 25 || h >= 335) && s > 0.4 && v > 0.5) {
                        firePixels++;
                    }
                }
                let ratio = firePixels / (width * height);
                return { fire: ratio > 0.01, ratio: ratio };
            }

            let lastEmailTriggerTime = 0;
            function captureAndAnalyze() {
                if (!video.videoWidth || !video.videoHeight) return;
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const frameData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const result = detectFire(frameData, canvas.width, canvas.height);
                if (result.fire) {
                    statusDiv.innerHTML = '<span style="color: #ff4b4b; font-weight: bold;">🔥 FIRE DETECTED! Alarm sounding. 🔥</span>';
                    playAlarm();
                    const now = Date.now();
                    if (now - lastEmailTriggerTime > 30000) {
                        lastEmailTriggerTime = now;
                        fetch(window.location.href + '?fire_detected=1', { method: 'POST' })
                            .catch(e => console.warn("Email trigger failed", e));
                    }
                } else {
                    statusDiv.innerHTML = '<span style="color: #2e7d32;">✅ No fire detected. (Fire ratio: ' + (result.ratio*100).toFixed(2) + '%)</span>';
                    if (alarmPlaying) stopAlarm();
                }
            }

            function startDetection() {
                if (detectionInterval) clearInterval(detectionInterval);
                detectionInterval = setInterval(captureAndAnalyze, 500);
                statusDiv.innerHTML = "Detection active...";
            }

            function stopDetection() {
                if (detectionInterval) {
                    clearInterval(detectionInterval);
                    detectionInterval = null;
                }
                stopAlarm();
                statusDiv.innerHTML = "Detection stopped.";
            }

            document.getElementById('startBtn').onclick = () => {
                if (!stream) {
                    navigator.mediaDevices.getUserMedia({ video: true })
                        .then(s => {
                            stream = s;
                            video.srcObject = stream;
                            video.play();
                            startDetection();
                        })
                        .catch(err => {
                            statusDiv.innerHTML = "Camera error: " + err.message;
                            console.error(err);
                        });
                } else {
                    startDetection();
                }
            };
            document.getElementById('stopBtn').onclick = () => {
                stopDetection();
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    stream = null;
                    video.srcObject = null;
                }
            };
            document.getElementById('stopAlarmBtn').onclick = () => {
                stopAlarm();
            };
        })();
    </script>
    """
    components.html(camera_html, height=550)

    st.markdown("---")
    st.caption("G‑Firefighter Alarm – Protecting your home 24/7")

# ---------- ROUTING ----------
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
