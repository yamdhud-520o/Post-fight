import streamlit as st
import time
import threading
import gc
import json
import os
import uuid
from pathlib import Path
from collections import deque
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

st.set_page_config(
    page_title="FB Comment Tool",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

KEEP_ALIVE_JS = """
<script>
    setInterval(function() { fetch(window.location.href, {method: 'HEAD'}).catch(function(){}); }, 25000);
    setInterval(function() { document.dispatchEvent(new MouseEvent('mousemove', {bubbles: true, clientX: 100, clientY: 100})); }, 60000);
</script>
"""

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    * { font-family: 'Poppins', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0033 50%, #0a0a0a 100%);
        position: relative;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 50%, rgba(0, 255, 255, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 0, 255, 0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }
    
    .main .block-container {
        background: rgba(0, 0, 0, 0.65);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(0, 255, 255, 0.3);
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.1);
        position: relative;
        z-index: 1;
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(255, 0, 255, 0.1));
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0, 255, 255, 0.4);
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        animation: glowPulse 2s ease-in-out infinite;
    }
    
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.2); border-color: rgba(0, 255, 255, 0.4); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 255, 0.4); border-color: rgba(0, 255, 255, 0.7); }
    }
    
    .main-header h1 {
        background: linear-gradient(135deg, #00ffff, #ff00ff, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 200% 200%;
        animation: gradientShift 3s ease infinite;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #00ffff, #ff00ff);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 700;
        width: 100%;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 12px;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgba(0, 255, 255, 0.6);
        background: linear-gradient(135deg, #ff00ff, #00ffff);
    }
    
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea, 
    .stNumberInput>div>div>input {
        background: rgba(0, 0, 0, 0.7);
        border: 1px solid rgba(0, 255, 255, 0.4);
        border-radius: 10px;
        color: #00ffcc;
        padding: 0.7rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus, 
    .stNumberInput>div>div>input:focus {
        border-color: #ff00ff;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.3);
        outline: none;
    }
    
    label {
        color: #00ffff !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    }
    
    .console-box {
        background: rgba(0, 0, 0, 0.85);
        border: 1px solid rgba(0, 255, 255, 0.6);
        border-radius: 12px;
        padding: 12px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        color: #00ffcc;
        max-height: 200px;
        overflow-y: auto;
        min-height: 100px;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
    }
    
    .log-line {
        padding: 4px 8px;
        border-left: 3px solid #00ffff;
        margin: 4px 0;
        background: rgba(0, 255, 255, 0.05);
        color: #00ffcc;
    }
    
    .status-running {
        background: linear-gradient(135deg, #00ff88, #00ffff);
        padding: 10px;
        border-radius: 10px;
        color: #000;
        text-align: center;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        animation: pulse 1s ease-in-out infinite;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }
    
    .status-stopped {
        background: linear-gradient(135deg, #ff0066, #ff00ff);
        padding: 10px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        box-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; transform: scale(0.98); }
    }
    
    [data-testid="stMetricValue"] {
        color: #00ffff;
        font-weight: 800;
        font-size: 2rem;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: #ff00ff !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .active-sessions {
        background: rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(0, 255, 255, 0.4);
        border-radius: 12px;
        padding: 15px;
        margin-top: 20px;
        backdrop-filter: blur(5px);
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #00ffff, #ff00ff);
        border-radius: 10px;
    }
    
    hr {
        border-color: rgba(0, 255, 255, 0.3);
    }
    
    code {
        color: #00ffff !important;
        background: rgba(0, 0, 0, 0.6) !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        border: 1px solid rgba(0, 255, 255, 0.3);
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)
st.markdown(KEEP_ALIVE_JS, unsafe_allow_html=True)

SESSIONS_FILE = "sessions_registry.json"
LOGS_DIR = "session_logs"
MAX_LOGS = 30

os.makedirs(LOGS_DIR, exist_ok=True)

class Session:
    __slots__ = ['id', 'running', 'count', 'logs', 'idx', 'driver', 'start_time']
    def __init__(self, sid):
        self.id = sid
        self.running = False
        self.count = 0
        self.logs = deque(maxlen=MAX_LOGS)
        self.idx = 0
        self.driver = None
        self.start_time = None
    
    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        log_entry = f"[{ts}] {msg}"
        self.logs.append(log_entry)
        try:
            with open(f"{LOGS_DIR}/{self.id}.log", "a") as f:
                f.write(log_entry + "\n")
        except:
            pass

@st.cache_resource
def get_session_manager():
    return SessionManager()

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
        self._load_registry()
    
    def _load_registry(self):
        if os.path.exists(SESSIONS_FILE):
            try:
                with open(SESSIONS_FILE, 'r') as f:
                    data = json.load(f)
                    for sid, info in data.items():
                        if sid not in self.sessions:
                            s = Session(sid)
                            s.count = info.get('count', 0)
                            s.running = False
                            s.start_time = info.get('start_time')
                            self.sessions[sid] = s
            except:
                pass
    
    def _save_registry(self):
        try:
            data = {}
            for sid, s in self.sessions.items():
                data[sid] = {
                    'count': s.count,
                    'running': s.running,
                    'start_time': s.start_time
                }
            with open(SESSIONS_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def create_session(self):
        with self.lock:
            sid = uuid.uuid4().hex[:8].upper()
            s = Session(sid)
            self.sessions[sid] = s
            self._save_registry()
            return s
    
    def get_session(self, sid):
        return self.sessions.get(sid)
    
    def get_all_sessions(self):
        return list(self.sessions.values())
    
    def get_active_sessions(self):
        return [s for s in self.sessions.values() if s.running]
    
    def stop_session(self, sid):
        s = self.sessions.get(sid)
        if s:
            s.running = False
            if s.driver:
                try:
                    s.driver.quit()
                except:
                    pass
                s.driver = None
            self._save_registry()
    
    def get_logs(self, sid, limit=30):
        log_file = f"{LOGS_DIR}/{sid}.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    return lines[-limit:]
            except:
                pass
        s = self.sessions.get(sid)
        if s:
            return list(s.logs)[-limit:]
        return []
    
    def update_count(self, sid, count):
        s = self.sessions.get(sid)
        if s:
            s.count = count
            self._save_registry()
    
    def cleanup_stopped(self):
        with self.lock:
            to_remove = [sid for sid, s in self.sessions.items() if not s.running and s.count == 0]
            for sid in to_remove:
                del self.sessions[sid]
                try:
                    os.remove(f"{LOGS_DIR}/{sid}.log")
                except:
                    pass
            self._save_registry()

manager = get_session_manager()

def setup_browser(session):
    session.log('Setting up Chrome browser...')
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-setuid-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    for p in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']:
        if Path(p).exists():
            opts.binary_location = p
            session.log(f'Found Chromium: {p}')
            break
    
    drv_path = None
    for d in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver']:
        if Path(d).exists():
            drv_path = d
            break
    
    from selenium.webdriver.chrome.service import Service
    if drv_path:
        svc = Service(executable_path=drv_path)
        driver = webdriver.Chrome(service=svc, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
    
    driver.set_window_size(1920, 1080)
    session.log('Browser ready!')
    return driver

def find_comment_input(driver, session):
    session.log('Finding comment input...')
    time.sleep(10)
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except:
        pass
    
    selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="comment" i][contenteditable="true"]',
        'div[aria-label*="Comment" i][contenteditable="true"]',
        'div[aria-label*="Write a comment" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        '[contenteditable="true"]'
    ]
    
    for idx, selector in enumerate(selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' || 
                               arguments[0].tagName === 'TEXTAREA' || 
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    if is_editable:
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        session.log(f'Found input with selector #{idx+1}')
                        return element
                except:
                    continue
        except:
            continue
    return None

def run_session(session, post_id, cookies, comments_list, prefix, delay):
    retries = 0
    driver = None
    
    while session.running and retries < 5:
        try:
            if driver is None:
                driver = setup_browser(session)
                session.driver = driver
            
            session.log('Navigating to Facebook...')
            driver.get('https://www.facebook.com/')
            time.sleep(8)
            
            if cookies:
                session.log('Adding cookies...')
                for c in cookies.split(';'):
                    c = c.strip()
                    if c and '=' in c:
                        i = c.find('=')
                        try:
                            driver.add_cookie({'name': c[:i].strip(), 'value': c[i+1:].strip(), 'domain': '.facebook.com', 'path': '/'})
                        except:
                            pass
            
            session.log(f'Opening post...')
            if post_id.startswith('http'):
                driver.get(post_id)
            else:
                driver.get(f'https://www.facebook.com/{post_id}')
            
            time.sleep(15)
            session.log('ID Online - Browser Active!')
            
            while session.running:
                try:
                    comment_input = find_comment_input(driver, session)
                    
                    if not comment_input:
                        session.log('Comment input not found, refreshing...')
                        driver.refresh()
                        time.sleep(10)
                        continue
                    
                    base_comment = comments_list[session.idx % len(comments_list)]
                    session.idx += 1
                    
                    comment_to_send = f"{prefix} {base_comment}" if prefix else base_comment
                    
                    session.log(f'Typing: {comment_to_send[:25]}...')
                    
                    driver.execute_script("""
                        const element = arguments[0];
                        const message = arguments[1];
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.focus();
                        element.click();
                        if (element.tagName === 'DIV') {
                            element.textContent = message;
                            element.innerHTML = message;
                        } else {
                            element.value = message;
                        }
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                        element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                    """, comment_input, comment_to_send)
                    
                    time.sleep(1)
                    
                    session.log('Sending...')
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        const events = [
                            new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                        ];
                        events.forEach(event => element.dispatchEvent(event));
                    """, comment_input)
                    
                    time.sleep(1)
                    session.count += 1
                    manager.update_count(session.id, session.count)
                    session.log(f'Comment #{session.count} sent!')
                    retries = 0
                    
                    session.log(f'Waiting {delay}s...')
                    for _ in range(delay):
                        if not session.running:
                            break
                        time.sleep(1)
                    
                    if session.count % 3 == 0:
                        gc.collect()
                        
                except Exception as e:
                    err = str(e)[:50]
                    session.log(f'Error: {err}')
                    if 'session' in err.lower() or 'disconnect' in err.lower():
                        session.log('Restarting browser...')
                        try: driver.quit()
                        except: pass
                        driver = None
                        retries += 1
                        time.sleep(3)
                        break
                    time.sleep(5)
                    
        except Exception as e:
            session.log(f'Fatal: {str(e)[:50]}')
            retries += 1
            try: driver.quit()
            except: pass
            driver = None
            time.sleep(5)
    
    session.running = False
    session.log('Stopped.')
    manager._save_registry()
    if driver:
        try: driver.quit()
        except: pass
    gc.collect()

def start_session(session, post_id, cookies, comments, prefix, delay):
    session.running = True
    session.logs = deque(maxlen=MAX_LOGS)
    session.count = 0
    session.idx = 0
    session.start_time = time.strftime("%H:%M:%S")
    
    try:
        open(f"{LOGS_DIR}/{session.id}.log", 'w').close()
    except:
        pass
    
    session.log(f'Session {session.id} starting...')
    manager._save_registry()
    
    comments_list = [c.strip() for c in comments.split('\n') if c.strip()] or ['Nice post!']
    threading.Thread(target=run_session, args=(session, post_id, cookies, comments_list, prefix, delay), daemon=True).start()

st.markdown('<div class="main-header"><h1>FB Comment Tool</h1></div>', unsafe_allow_html=True)

all_sessions = manager.get_all_sessions()
active_sessions = manager.get_active_sessions()
total_comments = sum(s.count for s in all_sessions)

col1, col2, col3 = st.columns(3)
col1.metric("Total Comments", total_comments)
col2.metric("Active Sessions", len(active_sessions))
with col3:
    if st.button("+ New Session"):
        manager.create_session()
        st.rerun()

if 'view_session' not in st.session_state:
    st.session_state.view_session = None

st.markdown("---")

if st.session_state.view_session:
    sid = st.session_state.view_session
    session = manager.get_session(sid)
    
    st.markdown(f"### Viewing Session: `{sid}`")
    
    if session:
        if session.running:
            st.markdown(f'<div class="status-running">RUNNING - {session.count} comments</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-stopped">STOPPED</div>', unsafe_allow_html=True)
        
        logs = manager.get_logs(sid, 25)
        if logs:
            logs_html = '<div class="console-box">'
            for log in logs:
                logs_html += f'<div class="log-line">{log.strip()}</div>'
            logs_html += '</div>'
            st.markdown(logs_html, unsafe_allow_html=True)
        else:
            st.markdown('<div class="console-box">No logs yet</div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("STOP Session", disabled=not session.running):
                manager.stop_session(sid)
                st.rerun()
        with c2:
            if st.button("Refresh Logs"):
                st.rerun()
        with c3:
            if st.button("Back"):
                st.session_state.view_session = None
                st.rerun()
    else:
        st.error("Session not found")
        if st.button("Back"):
            st.session_state.view_session = None
            st.rerun()

else:
    st.markdown("### Start New Automation")
    
    c1, c2 = st.columns(2)
    with c1:
        post_id = st.text_input("Post ID/URL", placeholder="https://facebook.com/...")
        prefix = st.text_input("Prefix (optional)", placeholder="@username")
        delay = st.number_input("Delay (seconds)", 10, 3600, 30)
    with c2:
        cookies = st.text_area("Cookies", height=100, placeholder="Paste cookies here...")
    
    uploaded = st.file_uploader("Upload Comments TXT", type=['txt'])
    if uploaded:
        comments = uploaded.read().decode('utf-8')
    else:
        comments = st.text_area("Comments (one per line)", height=70, placeholder="Nice!\nGreat post!")
    
    if st.button("START NEW SESSION", use_container_width=True):
        if not cookies:
            st.error("Add cookies!")
        elif not post_id:
            st.error("Add Post ID!")
        elif not comments:
            st.error("Add comments!")
        else:
            new_session = manager.create_session()
            start_session(new_session, post_id, cookies, comments, prefix, delay)
            st.success(f"Session Started! ID: {new_session.id}")
            time.sleep(1)
            st.rerun()

st.markdown("---")
st.markdown("### Active Sessions")

active = manager.get_active_sessions()
stopped = [s for s in all_sessions if not s.running and s.count > 0]

if active:
    st.markdown('<div class="active-sessions">', unsafe_allow_html=True)
    for s in active:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.code(s.id, language=None)
        with col2:
            st.write(f"Comments: {s.count}")
        with col3:
            if st.button("View", key=f"view_{s.id}"):
                st.session_state.view_session = s.id
                st.rerun()
        with col4:
            if st.button("Stop", key=f"stop_{s.id}"):
                manager.stop_session(s.id)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No active sessions")

if stopped:
    with st.expander("Stopped Sessions"):
        for s in stopped[-5:]:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.code(s.id, language=None)
            with col2:
                st.write(f"Comments: {s.count}")
            with col3:
                if st.button("Logs", key=f"logs_{s.id}"):
                    st.session_state.view_session = s.id
                    st.rerun()

st.markdown("---")
st.markdown("### Session ID Lookup")
lookup_id = st.text_input("Enter Session ID to view:", placeholder="XXXXXXXX")
if lookup_id and st.button("Find Session"):
    if manager.get_session(lookup_id.upper()):
        st.session_state.view_session = lookup_id.upper()
        st.rerun()
    else:
        st.error("Session not found")
