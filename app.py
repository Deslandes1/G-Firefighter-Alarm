import streamlit as st
import cv2
import numpy as np
from PIL import Image
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

# ---------- CSS (using raw string to avoid comment issues) ----------
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
</style>
""", unsafe_allow_html=True)

# ---------- LOGIN STATE ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "detection_active" not in st.session_state:
    st.session_state.detection_active = False
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False
if "alarm_playing" not in st.session_state:
    st.session_state.alarm_playing = False

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

# ---------- EMAIL ALERT FUNCTION ----------
def send_alert_email():
    if "email_config" not in st.session_state:
        st.session_state.email_config = None

    if st.session_state.email_config is None:
        st.warning("⚠️ To send an email alert, please enter your email credentials below. They will not be saved permanently.")
        sender_email = st.text_input("Your Email (Gmail recommended)")
        sender_password = st.text_input("App Password (for Gmail)", type="password")
        recipient_email = st.text_input("House Owner's Email")
        if st.button("Save Email Settings"):
            if sender_email and sender_password and recipient_email:
                st.session_state.email_config = {
                    "sender": sender_email,
                    "password": sender_password,
                    "recipient": recipient_email
                }
                st.success("Settings saved. Detection will now send emails.")
                st.rerun()
            else:
                st.error("All fields required.")
        return False
    else:
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
            return True
        except Exception as e:
            st.error(f"Failed to send email: {e}")
            return False

# ---------- FIRE DETECTION FUNCTION ----------
def detect_fire(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    lower_orange = np.array([10, 100, 100])
    upper_orange = np.array([25, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask3 = cv2.inRange(hsv, lower_orange, upper_orange)
    mask = cv2.bitwise_or(mask1, mask2)
    mask = cv2.bitwise_or(mask, mask3)
    
    fire_pixels = np.sum(mask > 0)
    total_pixels = frame.shape[0] * frame.shape[1]
    fire_ratio = fire_pixels / total_pixels
    return fire_ratio > 0.01, fire_ratio

# ---------- JAVASCRIPT ALARM ----------
def get_alarm_js(action):
    if action == "start":
        return """
        <script>
            if (typeof window.alarmOscillator === 'undefined' || window.alarmOscillator === null) {
                try {
                    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    const oscillator = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    oscillator.type = 'sawtooth';
                    oscillator.frequency.value = 880;
                    gain.gain.value = 0.5;
                    oscillator.connect(gain);
                    gain.connect(audioCtx.destination);
                    oscillator.start();
                    window.alarmOscillator = oscillator;
                    window.alarmGain = gain;
                    window.alarmCtx = audioCtx;
                    if (audioCtx.state === 'suspended') {
                        audioCtx.resume();
                    }
                } catch(e) { console.error("Web Audio not supported", e); }
            }
        </script>
        """
    else:
        return """
        <script>
            if (window.alarmOscillator) {
                try {
                    window.alarmOscillator.stop();
                    window.alarmOscillator.disconnect();
                } catch(e) {}
                window.alarmOscillator = null;
            }
            if (window.alarmCtx) {
                window.alarmCtx.close().catch(console.error);
                window.alarmCtx = null;
            }
        </script>
        """

# ---------- MAIN APP ----------
def main_app():
    st.markdown('<div style="display: flex; align-items: center; justify-content: center;"><span class="logo-small">🚒</span><span class="logo-small">G‑Firefighter Alarm</span><span class="logo-small">🔥</span></div>', unsafe_allow_html=True)
    st.title("🔥 Live Fire Detection")
    st.markdown("**Camera or image upload** – we analyze for flames. Alarm + Email on detection.")

    if st.button("Logout"):
        st.components.v1.html(get_alarm_js("stop"), height=0)
        st.session_state.authenticated = False
        st.session_state.detection_active = False
        st.session_state.email_sent = False
        st.session_state.alarm_playing = False
        st.rerun()

    st.markdown("---")

    source = st.radio("Select input source:", ["Camera (Webcam)", "Upload Image"])
    frame_placeholder = st.empty()
    status_placeholder = st.empty()

    if st.button("🔊 Stop Alarm Now", key="stop_alarm_btn"):
        st.components.v1.html(get_alarm_js("stop"), height=0)
        st.session_state.alarm_playing = False
        st.success("Alarm silenced.")

    if source == "Camera (Webcam)":
        if st.button("Start Detection"):
            st.session_state.detection_active = True
            st.session_state.email_sent = False
            st.session_state.alarm_playing = False
            st.components.v1.html(get_alarm_js("stop"), height=0)
        if st.button("Stop Detection"):
            st.session_state.detection_active = False
            st.components.v1.html(get_alarm_js("stop"), height=0)
            st.session_state.alarm_playing = False
            st.rerun()

        if st.session_state.detection_active:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                st.error("Cannot access webcam. Please allow permissions.")
                st.session_state.detection_active = False
            else:
                st.info("Detection running... looking for fire. Alarm will sound if fire detected.")
                while st.session_state.detection_active:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frame = cv2.flip(frame, 1)
                    fire_detected, ratio = detect_fire(frame)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                    if fire_detected and not st.session_state.alarm_playing:
                        st.components.v1.html(get_alarm_js("start"), height=0)
                        st.session_state.alarm_playing = True
                    elif not fire_detected and st.session_state.alarm_playing:
                        st.components.v1.html(get_alarm_js("stop"), height=0)
                        st.session_state.alarm_playing = False

                    if fire_detected and not st.session_state.email_sent:
                        status_placeholder.markdown('<div class="fire-alert">🔥🔥 FIRE DETECTED! Sending alert & alarm sounding... 🔥🔥</div>', unsafe_allow_html=True)
                        if send_alert_email():
                            st.session_state.email_sent = True
                            status_placeholder.markdown('<div class="fire-alert">🚨 ALERT SENT! Fire department notified. Alarm active. 🚨</div>', unsafe_allow_html=True)
                        else:
                            status_placeholder.error("Email sending failed.")
                    elif fire_detected and st.session_state.email_sent:
                        status_placeholder.markdown('<div class="fire-alert">🔥 FIRE STILL PRESENT – Alarm sounding. Alert already sent. 🔥</div>', unsafe_allow_html=True)
                    else:
                        status_placeholder.markdown(f'<div class="status-safe">✅ No fire detected. (Fire ratio: {ratio:.2%})</div>', unsafe_allow_html=True)
                    
                    time.sleep(0.1)
                cap.release()
                st.components.v1.html(get_alarm_js("stop"), height=0)
                st.session_state.detection_active = False
                st.rerun()

    else:
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            frame = np.array(image)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            fire_detected, ratio = detect_fire(frame_bgr)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            if fire_detected:
                st.markdown('<div class="fire-alert">🔥 FIRE DETECTED in this image! 🔥</div>', unsafe_allow_html=True)
                st.components.v1.html(get_alarm_js("start"), height=0)
                if st.button("Send Emergency Email"):
                    if send_alert_email():
                        st.success("Alert email sent to house owner!")
                    else:
                        st.error("Email configuration required.")
                if st.button("Stop Alarm"):
                    st.components.v1.html(get_alarm_js("stop"), height=0)
            else:
                st.markdown(f'<div class="status-safe">✅ No fire detected (fire ratio: {ratio:.2%})</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("G‑Firefighter Alarm – Protecting your home 24/7")

# ---------- ROUTING ----------
if not st.session_state.authenticated:
    login_page()
else:
    main_app()
