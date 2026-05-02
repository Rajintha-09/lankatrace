import streamlit as st
from database import create_tables, get_stats

create_tables()

st.set_page_config(
    page_title="LankaTrace",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    html, body, .main, .block-container,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], section.main {
        background-color: #03030A !important;
        color: #E2E8F0 !important;
        max-width: 100% !important;
    }
    .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 100% !important;
    }
    [data-testid="stSidebar"], [data-testid="collapsedControl"],
    [data-testid="stSidebarNav"], section[data-testid="stSidebar"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden !important; }

    /* Enter button */
    .enter-btn div.stButton > button {
        background: linear-gradient(135deg, #1a56db, #7e3af2) !important;
        border: none !important; border-radius: 50px !important;
        color: #fff !important; font-size: 1rem !important;
        font-weight: 700 !important; padding: 0.75rem 0 !important;
        width: 100% !important;
        box-shadow: 0 6px 24px rgba(99,102,241,0.4) !important;
        transition: all 0.2s !important;
    }
    .enter-btn div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 32px rgba(99,102,241,0.6) !important;
    }
    .enter-btn div.stButton > button p { color:#fff !important; font-size:1rem !important; font-weight:700 !important; }

    /* Nav buttons */
    .btn-red div.stButton > button {
        background: rgba(239,68,68,0.07) !important;
        border: 1px solid rgba(239,68,68,0.25) !important;
        color: #FCA5A5 !important; border-radius: 12px !important;
        font-size: 0.9rem !important; font-weight: 700 !important;
        padding: 0.75rem 1rem !important; width: 100% !important;
        text-align: left !important; margin-bottom: 0.5rem !important;
        transition: all 0.15s !important;
    }
    .btn-red div.stButton > button:hover {
        background: rgba(239,68,68,0.14) !important;
        border-color: #F87171 !important; transform: translateX(4px) !important;
    }
    .btn-grn div.stButton > button {
        background: rgba(34,197,94,0.07) !important;
        border: 1px solid rgba(34,197,94,0.25) !important;
        color: #86EFAC !important; border-radius: 12px !important;
        font-size: 0.9rem !important; font-weight: 700 !important;
        padding: 0.75rem 1rem !important; width: 100% !important;
        text-align: left !important; margin-bottom: 0.5rem !important;
        transition: all 0.15s !important;
    }
    .btn-grn div.stButton > button:hover {
        background: rgba(34,197,94,0.14) !important;
        border-color: #4ADE80 !important; transform: translateX(4px) !important;
    }
    .btn-ylw div.stButton > button {
        background: rgba(234,179,8,0.07) !important;
        border: 1px solid rgba(234,179,8,0.25) !important;
        color: #FDE68A !important; border-radius: 12px !important;
        font-size: 0.9rem !important; font-weight: 700 !important;
        padding: 0.75rem 1rem !important; width: 100% !important;
        text-align: left !important; margin-bottom: 0.5rem !important;
        transition: all 0.15s !important;
    }
    .btn-ylw div.stButton > button:hover {
        background: rgba(234,179,8,0.14) !important;
        border-color: #FBBF24 !important; transform: translateX(4px) !important;
    }
    .btn-red div.stButton > button p,
    .btn-grn div.stButton > button p,
    .btn-ylw div.stButton > button p { font-size:0.9rem !important; font-weight:700 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #0D0D1A; border-radius: 10px;
        padding: 3px; gap: 3px; border: 1px solid #1E1E35;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #64748B;
        border-radius: 7px; padding: 0.35rem 1rem;
        font-weight: 600; font-size: 0.82rem;
    }
    .stTabs [aria-selected="true"] { background: #1a2540 !important; color: #60a5fa !important; }

    .dot { display:inline-block; width:7px; height:7px; background:#22C55E;
        border-radius:50%; margin-right:7px;
        box-shadow:0 0 6px rgba(34,197,94,.7); vertical-align:middle; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "home"
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

def go_to(p):
    st.session_state.page = p
    st.rerun()

if st.session_state.page == "lost":
    st.switch_page("pages/1_report_lost.py")
elif st.session_state.page == "found":
    st.switch_page("pages/2_report_found.py")
elif st.session_state.page == "myreports":
    st.switch_page("pages/3_my_reports.py")

# ══════════════════════════════════════════
# SPLASH
# ══════════════════════════════════════════
if not st.session_state.splash_done:

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    _, mc, _ = st.columns([3, 1, 3])
    with mc:
        st.markdown("<div style='text-align:center;font-size:4rem;line-height:1;'>🚌</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:0.75rem;font-weight:700;letter-spacing:7px;color:#6366f1;margin:0;'>WELCOME TO</p>", unsafe_allow_html=True)
    st.markdown("""
    <h1 style='text-align:center;font-size:4.5rem;font-weight:900;letter-spacing:-3px;margin:0.15rem 0 0.4rem;
        background:linear-gradient(135deg,#60a5fa,#a78bfa,#34d399);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.05;'>
        LankaTrace
    </h1>
    """, unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:1rem;color:#64748B;margin:0 0 0.3rem;'>AI-Powered Lost &amp; Found &nbsp;·&nbsp; Sri Lanka Public Transport</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:0.85rem;color:#334155;margin:0 0 2rem;'>Lost something on a bus or train? Found something left behind?<br>LankaTrace uses AI to match reports automatically.</p>", unsafe_allow_html=True)

    # 4 cards — compact
    col_a, col_b, col_c, col_d = st.columns(4, gap="small")
    cards = [
        ("😔", "#ef4444", "Lost Something?", "Report via AI chat. Upload a photo — AI describes it and asks smart questions."),
        ("😊", "#22c55e", "Found Something?", "Report what you found. System instantly checks all lost reports for a match."),
        ("🤖", "#818cf8", "AI Matching",      "Semantic AI compares by meaning — not keywords. Get a confidence score."),
        ("🔔", "#f59e0b", "Track Report",     "Use your Tracking ID to check if your item was found and see contact details."),
    ]
    for col, (icon, color, title, desc) in zip([col_a, col_b, col_c, col_d], cards):
        with col:
            st.markdown(f"""
            <div style='background:#0D0D1A;border:1px solid #1E1E35;border-top:3px solid {color};
                border-radius:14px;padding:1.1rem 1rem;'>
                <div style='font-size:1.6rem;margin-bottom:0.5rem;'>{icon}</div>
                <div style='color:#F1F5F9;font-size:0.88rem;font-weight:700;margin-bottom:0.35rem;'>{title}</div>
                <div style='color:#94A3B8;font-size:0.78rem;line-height:1.6;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Pills
    _, pm, _ = st.columns([1, 4, 1])
    with pm:
        st.markdown("""
        <div style='display:flex;flex-wrap:wrap;gap:0.4rem;justify-content:center;'>
            <span style='background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.2);color:#60a5fa;padding:0.22rem 0.75rem;border-radius:20px;font-size:0.75rem;font-weight:600;'>🇱🇰 Sri Lanka</span>
            <span style='background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.2);color:#60a5fa;padding:0.22rem 0.75rem;border-radius:20px;font-size:0.75rem;font-weight:600;'>🚌 Bus &amp; Rail</span>
            <span style='background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.2);color:#34d399;padding:0.22rem 0.75rem;border-radius:20px;font-size:0.75rem;font-weight:600;'>🤖 Groq AI + LLaMA</span>
            <span style='background:rgba(167,139,250,0.1);border:1px solid rgba(167,139,250,0.2);color:#a78bfa;padding:0.22rem 0.75rem;border-radius:20px;font-size:0.75rem;font-weight:600;'>🧠 Semantic Matching</span>
            <span style='background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.2);color:#fbbf24;padding:0.22rem 0.75rem;border-radius:20px;font-size:0.75rem;font-weight:600;'>🔒 Privacy Friendly</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    _, btn_c, _ = st.columns([2, 1, 2])
    with btn_c:
        st.markdown('<div class="enter-btn">', unsafe_allow_html=True)
        if st.button("🚀  Enter LankaTrace", use_container_width=True, key="enter"):
            st.session_state.splash_done = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<p style='text-align:center;color:#1E293B;font-size:0.72rem;margin-top:0.8rem;'>Free · No account needed · Built for Sri Lanka</p>", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════
_s = get_stats()

# Header
st.markdown(f"""
<div style='display:flex;align-items:center;gap:0.8rem;border-bottom:1px solid #1E1E35;
    padding-bottom:1rem;margin-bottom:1.4rem;'>
    <span style='font-size:1.8rem;'>🚌</span>
    <div>
        <div style='font-size:1.4rem;font-weight:900;color:#F1F5F9;letter-spacing:-0.5px;'>LankaTrace</div>
        <div style='font-size:0.76rem;color:#475569;margin-top:1px;'>AI-Powered Lost &amp; Found · Sri Lanka Public Transport</div>
    </div>
    <span style='margin-left:auto;background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.2);
        color:#60a5fa;padding:0.22rem 0.7rem;border-radius:20px;font-size:0.74rem;font-weight:600;'>🇱🇰 Sri Lanka</span>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    # Stats
    s1, s2, s3 = st.columns(3, gap="small")
    for col, num, label, color in [
        (s1, _s['total_reports'],   "Reports",   "#60a5fa"),
        (s2, _s['total_matches'],   "Matched",   "#34d399"),
        (s3, _s['total_recovered'], "Recovered", "#fbbf24"),
    ]:
        with col:
            st.markdown(f"""
            <div style='background:#0D0D1A;border:1px solid #1E1E35;border-radius:12px;
                padding:0.75rem 0.5rem;text-align:center;'>
                <div style='font-size:1.7rem;font-weight:900;color:{color};line-height:1;'>{num}</div>
                <div style='font-size:0.63rem;color:#475569;text-transform:uppercase;
                    letter-spacing:1px;margin-top:4px;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.68rem;color:#475569;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:0.6rem;'>Quick Actions</p>", unsafe_allow_html=True)

    st.markdown('<div class="btn-red">', unsafe_allow_html=True)
    if st.button("😔  I Lost Something  →", use_container_width=True, key="btn_lost"):
        go_to("lost")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="btn-grn">', unsafe_allow_html=True)
    if st.button("😊  I Found Something  →", use_container_width=True, key="btn_found"):
        go_to("found")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="btn-ylw">', unsafe_allow_html=True)
    if st.button("🔔  Check My Report  →", use_container_width=True, key="btn_check"):
        go_to("myreports")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.12);
        border-radius:10px;padding:0.75rem 0.9rem;'>
        <p style='color:#F87171;font-size:0.68rem;font-weight:700;margin:0 0 0.3rem;
            text-transform:uppercase;letter-spacing:1px;'>⚠ Disclaimer</p>
        <p style='color:#7F1D1D;font-size:0.75rem;margin:0;line-height:1.7;'>
            LankaTrace is a free community platform. We do not handle physical items,
            guarantee recovery, or take responsibility for disputes.
            All matches are AI suggestions — verify before collection.
        </p>
    </div>
    """, unsafe_allow_html=True)

with right:
    tab1, tab2 = st.tabs(["❓  How It Works", "🟢  System Status"])

    with tab1:
        entries = [
            ("#F87171", "😔", "I lost something on a bus or train",
             "Click <strong style='color:#E2E8F0'>I Lost Something</strong> → Upload a photo or describe your item → Answer a few smart questions about the route, location and time → Get your <strong style='color:#60a5fa'>Tracking ID</strong> at the end and save it."),
            ("#4ADE80", "😊", "I found something on a bus or train",
             "Click <strong style='color:#E2E8F0'>I Found Something</strong> → Upload a photo or describe it → System automatically checks all lost reports for a match — the owner will contact you directly."),
            ("#FBBF24", "🔔", "How to check if my item was found",
             "Click <strong style='color:#E2E8F0'>Check My Report</strong> → Enter your Tracking ID (e.g. LT-ABC123) → If a match is found you will see confidence %, AI explanation, and the other person's contact details."),
            ("#A78BFA", "🤖", "How does the AI matching work?",
             "LankaTrace uses <strong style='color:#E2E8F0'>Sentence Transformers</strong> to compare reports by meaning — not just keywords. Then <strong style='color:#E2E8F0'>LLaMA 3 via Groq</strong> explains the match in plain English with a confidence percentage."),
        ]
        for color, icon, title, desc in entries:
            st.markdown(f"""
            <div style='background:#0D0D1A;border:1px solid #1E1E35;border-left:3px solid {color};
                border-radius:10px;padding:0.85rem 1rem;margin-bottom:0.5rem;'>
                <p style='color:{color};font-size:0.87rem;font-weight:700;margin:0 0 0.3rem;'>{icon} {title}</p>
                <p style='color:#94A3B8;font-size:0.8rem;margin:0;line-height:1.75;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div style='background:#0D0D1A;border:1px solid #1E1E35;border-radius:12px;padding:1.1rem 1.3rem;'>
            <p style='color:#22C55E;font-size:0.9rem;font-weight:700;margin:0 0 0.8rem;'>● All Systems Operational</p>
            <div style='color:#94A3B8;font-size:0.83rem;margin-bottom:0.55rem;'><span class='dot'></span>AI Agent — Memory &amp; Reasoning Active</div>
            <div style='color:#94A3B8;font-size:0.83rem;margin-bottom:0.55rem;'><span class='dot'></span>Matching Engine — Semantic + Rule-based</div>
            <div style='color:#94A3B8;font-size:0.83rem;margin-bottom:0.55rem;'><span class='dot'></span>Vision Model — LLaMA 4 Scout</div>
            <div style='color:#94A3B8;font-size:0.83rem;'><span class='dot'></span>SQLite Database — Connected</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='border-top:1px solid #1E1E35;padding-top:0.8rem;display:flex;justify-content:space-between;'>
    <span style='color:#334155;font-size:0.72rem;'>🔒 Privacy · 🤖 Groq AI · 🚌 Bus &amp; Rail</span>
    <span style='color:#334155;font-size:0.72rem;'>v1.0 · LankaTrace 🇱🇰</span>
</div>
""", unsafe_allow_html=True)