import streamlit as st
from agent import run_agent_turn, AgentMemory, agent_decide_next_field
from database import save_ticket_to_report, save_photo_path
import random, string
from PIL import Image
import io, os, uuid

st.set_page_config(page_title="Report Found Item", page_icon="😊", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    html, body, .main, .block-container, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], section.main {
        background-color: #000000 !important; color: #F1F5F9 !important;
    }
    [data-testid="stSidebar"], [data-testid="collapsedControl"],
    [data-testid="stSidebarNav"], section[data-testid="stSidebar"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden !important; }

    .report-header {
        background: linear-gradient(135deg, #052E16 0%, #000000 100%);
        border: 1px solid #4ADE80; border-radius: 14px;
        padding: 1.2rem 1.5rem; margin-bottom: 1rem;
    }
    .report-header h2 { color: #FFFFFF !important; margin: 0; font-size: 1.5rem; }
    .report-header p { color: #86EFAC; margin: 0.3rem 0 0 0; font-size: 0.88rem; }

    .memory-panel {
        background: linear-gradient(135deg, #060F08 0%, #030A04 100%);
        border: 1px solid #1A3A1F; border-radius: 14px;
        padding: 1rem 1.2rem; margin-bottom: 1rem;
    }
    .memory-header { color: #4ADE80; font-weight: 700; font-size: 0.8rem;
        text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.8rem; }
    .memory-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem 1rem; }
    .memory-item { display: flex; flex-direction: column; gap: 1px; }
    .memory-key { color: #4ADE80; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
    .memory-val {
        color: #E2E8F0; font-size: 0.85rem; font-weight: 500;
        background: rgba(255,255,255,0.04); border-radius: 6px;
        padding: 2px 8px; border-left: 2px solid #166534;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }

    .chat-wrap { display: flex; flex-direction: column; gap: 0.7rem; margin-bottom: 1rem; }
    .bubble-row-agent { display: flex; justify-content: flex-start; align-items: flex-end; gap: 0.5rem; }
    .bubble-row-user  { display: flex; justify-content: flex-end;  align-items: flex-end; gap: 0.5rem; }
    .bubble-agent {
        background: #052E16; border: 1px solid #166534;
        border-radius: 18px 18px 18px 4px;
        color: #86EFAC; padding: 0.8rem 1rem;
        max-width: 78%; font-size: 0.93rem; line-height: 1.6;
    }
    .bubble-user {
        background: #1A1A2E; border: 1px solid #2A2A4A;
        border-radius: 18px 18px 4px 18px;
        color: #E2E8F0; padding: 0.8rem 1rem;
        max-width: 78%; font-size: 0.93rem; line-height: 1.6;
    }
    .avatar { font-size: 1.3rem; line-height: 1; }

    .progress-wrap { background:#111; border-radius:99px; height:5px; margin-bottom:0.8rem; overflow:hidden; }
    .progress-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,#4ADE80,#4F9EF8); }
    .progress-label { color:#475569; font-size:0.75rem; margin-bottom:0.3rem; display:flex; justify-content:space-between; }

    .ticket-box {
        background: #111111; border: 2px solid #4ADE80;
        border-radius: 16px; padding: 2rem; text-align: center; margin-top: 1rem;
    }
    .ticket-id { font-size: 2.2rem; font-weight: 900; color: #4ADE80; letter-spacing: 5px; font-family: monospace; }

    div.stButton > button {
        background-color: #111111 !important; color: #FFFFFF !important;
        border: 1px solid #2A2A2A !important; border-radius: 10px !important; font-weight: 700 !important;
    }
    div.stButton > button:hover { background-color: #052E16 !important; border-color: #4ADE80 !important; }
    hr { border-color: #1E1E1E !important; }
    .stTextInput > div > div > input {
        background: #0A0A0A !important; border: 1px solid #166534 !important;
        color: #E2E8F0 !important; border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] {
        background: #060F08 !important; border: 2px dashed #166534 !important;
        border-radius: 12px !important; padding: 1rem !important;
    }
    .photo-panel {
        background: #060F08; border: 1px solid #166534;
        border-radius: 14px; padding: 1rem 1.2rem; margin: 1rem 0;
    }
    .photo-panel-title { color: #4ADE80; font-weight: 700; font-size: 0.8rem;
        text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.6rem; }
    .photo-desc { color: #E2E8F0; font-size: 0.88rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ── Back button ──────────────────────────────────────────────
col_back, _ = st.columns([1, 4])
with col_back:
    if st.button("← Home", key="back"):
        for k in ["found_memory","found_done","found_started","found_ticket","found_ticket_saved",
                  "found_photo_done","found_editing","found_image_bytes","found_photo_path"]:
            st.session_state.pop(k, None)
        st.session_state.page = "home"
        st.switch_page("app.py")

st.markdown("""
<div class="report-header">
    <h2>😊 Report Found Item</h2>
    <p>Help return this item to its owner</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(135deg,#052E16 0%,#071A0E 100%);border:1px solid #4ADE80;
    border-radius:14px;padding:1rem 1.5rem;margin-bottom:1rem;text-align:center;">
    <p style="font-size:1.6rem;margin:0;">🙏</p>
    <p style="color:#4ADE80;font-size:0.95rem;font-weight:800;margin:0.3rem 0 0.2rem 0;">Thank you for your kindness!</p>
    <p style="color:#86EFAC;font-size:0.83rem;margin:0;">Because of people like you, lost items find their way home. 💚</p>
</div>
""", unsafe_allow_html=True)

# ── Session init ─────────────────────────────────────────────
for k, v in [("found_memory", AgentMemory()), ("found_done", False), ("found_started", False),
              ("found_ticket", None), ("found_ticket_saved", False),
              ("found_photo_done", False), ("found_editing", False),
              ("found_image_bytes", None), ("found_photo_path", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

memory: AgentMemory = st.session_state.found_memory

FIELD_LABELS = {
    "reporter_name":    ("👤", "Name"),
    "reporter_nic":     ("🪪", "NIC"),
    "reporter_phone":   ("📞", "Phone"),
    "reporter_address": ("📍", "Address"),
    "item_type":        ("🏷️", "Item Type"),
    "color":            ("🎨", "Color"),
    "transport_type":   ("🚌", "Transport"),
    "bus_route":        ("🛣️", "Route"),
    "location":         ("📌", "Location"),
    "incident_time":    ("🕐", "Time"),
    "brand":            ("🏷️", "Brand"),
    "contents":         ("📦", "Contents"),
    "ai_description":   ("📷", "Photo Analysis"),
}

# ── Save photo to disk ───────────────────────────────────────
def save_photo_to_disk(image_bytes: bytes) -> str:
    os.makedirs("photos", exist_ok=True)
    filename = f"found_{uuid.uuid4().hex[:10]}.jpg"
    path = os.path.join("photos", filename)
    img = Image.open(io.BytesIO(image_bytes))
    img.convert("RGB").save(path, format="JPEG", quality=90)
    return path

def clear_edit_widget_cache():
    for field in FIELD_LABELS:
        st.session_state.pop(f"edit_{field}_found", None)

# ── Memory Panel ─────────────────────────────────────────────
def render_memory_panel(memory, show_edit=False):
    visible = {k: v for k, v in memory.data.items() if not k.startswith("_") and k in FIELD_LABELS}
    if not visible:
        return

    _all = ["reporter_name","reporter_phone","item_type","color","transport_type","location","incident_time"]
    _pct = int(sum(1 for f in _all if memory.data.get(f) and memory.data.get(f) != "not specified") / len(_all) * 100)
    step_labels = {1:"Your Details", 2:"Item Info", 3:"Where & When", 5:"Matching"}
    current_label = step_labels.get(memory.current_step, "In Progress")

    st.markdown(f"""
    <div class="progress-label">
        <span>🧠 Agent Memory — Step {memory.current_step}/4: {current_label}</span>
        <span>{_pct}% complete</span>
    </div>
    <div class="progress-wrap"><div class="progress-fill" style="width:{_pct}%"></div></div>
    """, unsafe_allow_html=True)

    ai_desc_val = visible.pop("ai_description", None)
    items_html = ""
    for k, v in visible.items():
        if str(v) in ("not provided", "not specified"):
            continue
        icon, label = FIELD_LABELS.get(k, ("•", k))
        val_str = str(v)[:40] + ("…" if len(str(v)) > 40 else "")
        items_html += f"""<div class="memory-item">
            <span class="memory-key">{icon} {label}</span>
            <span class="memory-val">{val_str}</span>
        </div>"""

    ai_html = ""
    if ai_desc_val:
        ai_html = f"""<div style="grid-column:1/-1;margin-top:0.4rem;">
            <span class="memory-key">📷 Photo Analysis</span>
            <div class="memory-val" style="white-space:normal;overflow:visible;text-overflow:unset;margin-top:2px;">{str(ai_desc_val)}</div>
        </div>"""

    st.markdown(f"""
    <div class="memory-panel">
        <div class="memory-header">🧠 Agent Memory</div>
        <div class="memory-grid">{items_html}{ai_html}</div>
    </div>
    """, unsafe_allow_html=True)

    if show_edit:
        if st.button("✏️ Edit details", key="edit_btn_found"):
            # Clear the loaded flag so edit form pre-populates with current memory
            st.session_state.pop("_found_edit_loaded", None)
            st.session_state.found_editing = True
            st.rerun()

# ── Edit Form ────────────────────────────────────────────────
def render_edit_form(memory):
    st.markdown("#### ✏️ Edit your details")
    st.caption("Correct any mistakes below, then click Save.")

    editable_fields = [k for k in FIELD_LABELS if k in memory.data and k != "ai_description"]

    # CRITICAL FIX: Only pre-populate keys when the edit session is BRAND NEW.
    # If we overwrite on every rerun, user's typed text gets wiped on each keystroke.
    if not st.session_state.get("_found_edit_loaded"):
        for field in editable_fields:
            st.session_state[f"ef_found_{field}"] = memory.data.get(field, "")
        st.session_state["_found_edit_loaded"] = True

    updated = {}
    for field in editable_fields:
        icon, label = FIELD_LABELS[field]
        updated[field] = st.text_input(f"{icon} {label}", key=f"ef_found_{field}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save changes", use_container_width=True, key="save_edit_found"):
            # Capture old values BEFORE touching memory.data
            old_values = {}
            for field in editable_fields:
                old_values[field] = memory.data.get(field, "")

            # Update memory with new values
            for field, val in updated.items():
                if val.strip():
                    memory.data[field] = val.strip()

            # Replace old values in chat history with new values
            for field in editable_fields:
                old_val = old_values[field]
                new_val = updated.get(field, "").strip()
                if old_val and new_val and old_val != new_val:
                    for msg in memory.history:
                        if msg["role"] == "user" and old_val in msg["content"]:
                            msg["content"] = msg["content"].replace(old_val, new_val)
                            break

            st.session_state.pop("_found_edit_loaded", None)
            for field in editable_fields:
                st.session_state.pop(f"ef_found_{field}", None)
            st.session_state.found_memory = memory
            st.session_state.found_editing = False
            st.rerun()
    with col2:
        if st.button("✖ Cancel", use_container_width=True, key="cancel_edit_found"):
            st.session_state.pop("_found_edit_loaded", None)
            for field in editable_fields:
                st.session_state.pop(f"ef_found_{field}", None)
            st.session_state.found_editing = False
            st.rerun()


# ── Chat Renderer ─────────────────────────────────────────────
def render_chat(memory):
    chat_html = '<div class="chat-wrap">'
    for msg in memory.history:
        if msg["role"] == "assistant":
            content = msg["content"].replace("\n", "<br>")
            chat_html += f'<div class="bubble-row-agent"><span class="avatar">🤖</span><div class="bubble-agent">{content}</div></div>'
        elif msg["role"] == "user":
            content = msg["content"].replace("\n", "<br>")
            chat_html += f'<div class="bubble-row-user"><div class="bubble-user">{content}</div><span class="avatar">🧑</span></div>'
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # Photo is shown once at the top (see below), not here inside chat

# ── EDIT MODE ────────────────────────────────────────────────
if st.session_state.found_editing:
    render_edit_form(memory)
    st.stop()

# ── Memory panel (during chat) ───────────────────────────────
if st.session_state.found_started and not st.session_state.found_done:
    render_memory_panel(memory, show_edit=True)

# ── FIX 5: Show uploaded photo ONCE at the top (not repeated per question) ──
if st.session_state.found_photo_done and st.session_state.get("found_image_bytes"):
    col_space, col_img = st.columns([2, 1])
    with col_img:
        try:
            img = Image.open(io.BytesIO(st.session_state.found_image_bytes))
            st.image(img, caption="📷 Your uploaded photo", use_container_width=True)
        except Exception:
            pass

# ── Chat history ─────────────────────────────────────────────
render_chat(memory)

# ══════════════════════════════════════════════════════════════
# MAIN FLOW
# ══════════════════════════════════════════════════════════════
if not st.session_state.found_done:

    if not st.session_state.found_started:
        # ── Start button ─────────────────────────────────────
        if st.button("🚀 Start Reporting", type="primary", use_container_width=True):
            st.session_state.found_started = True
            memory.add_message(
                "assistant",
                "👋 Hi! Since you have the item with you, let's start with a photo.\n"
                "📷 Please upload a clear photo of the item below — this helps the owner identify it "
                "and improves our AI matching accuracy."
            )
            st.session_state.found_memory = memory
            st.rerun()

    elif not st.session_state.found_photo_done:
        # ── Photo upload — appears right after agent's first bubble ──────────
        uploaded = st.file_uploader(
            "📷 Upload photo of the found item",
            type=["jpg", "jpeg", "png", "webp"],
            key="found_photo",
            help="Upload a clear photo of the item you found"
        )

        if uploaded:
            image_bytes = uploaded.read()
            st.session_state.found_image_bytes = image_bytes

            # Save to disk so it can be shown on the Check Report page later
            photo_path = save_photo_to_disk(image_bytes)
            st.session_state.found_photo_path = photo_path
            memory.update("photo_path", photo_path)

            st.session_state.found_photo_done = True

            with st.spinner("🤖 Analyzing the item..."):
                reply, memory, done = run_agent_turn("found", memory, image_bytes=image_bytes)

            st.session_state.found_memory = memory
            st.session_state.found_done = done
            st.rerun()

    else:
        # ── Normal Q&A chat ──────────────────────────────────
        if prompt := st.chat_input("Type your answer here..."):
            with st.spinner("🤖 Thinking..."):
                reply, memory, done = run_agent_turn("found", memory, user_message=prompt)
            st.session_state.found_memory = memory
            st.session_state.found_done = done
            st.rerun()

# ══════════════════════════════════════════════════════════════
# DONE — Ticket + Summary
# ══════════════════════════════════════════════════════════════
else:
    if not st.session_state.found_ticket:
        st.session_state.found_ticket = "FT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    if not st.session_state.found_ticket_saved:
        if memory._report_id:
            save_ticket_to_report(memory._report_id, st.session_state.found_ticket)
            if st.session_state.found_photo_path:
                save_photo_path(memory._report_id, st.session_state.found_photo_path)
            st.session_state.found_ticket_saved = True

    st.success("✅ Report submitted! Thank you for your kindness 🙏")
    st.markdown(f"""
    <div class="ticket-box">
        <p style="color:#64748B;font-size:0.8rem;text-transform:uppercase;letter-spacing:2px;">Your Tracking ID</p>
        <div class="ticket-id">{st.session_state.found_ticket}</div>
        <p style="color:#94A3B8;margin-top:1rem;font-size:0.88rem;">
            The owner will contact you on your phone if a match is found.<br><br>
            You can also check <strong style="color:#4ADE80;">Check My Report</strong> anytime.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show uploaded photo + AI description side by side
    if st.session_state.found_image_bytes:
        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)
        col_img, col_desc = st.columns([1, 2])
        with col_img:
            try:
                img = Image.open(io.BytesIO(st.session_state.found_image_bytes))
                st.image(img, caption="📷 Your uploaded photo", use_container_width=True)
            except Exception:
                pass
        with col_desc:
            if memory.ai_description:
                st.markdown(f"""
                <div class="photo-panel">
                    <div class="photo-panel-title">📷 AI Photo Analysis</div>
                    <div class="photo-desc">{memory.ai_description}</div>
                </div>
                """, unsafe_allow_html=True)

    # Final memory summary
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    clean = {k: v for k, v in memory.data.items() if not k.startswith("_") and k != "photo_path"}
    if clean:
        ai_desc_final = clean.pop("ai_description", None)
        items_html = ""
        for k, v in clean.items():
            if str(v) in ("not provided", "not specified"):
                continue
            icon, label = FIELD_LABELS.get(k, ("•", k.replace("_", " ").title()))
            val_str = str(v)[:60] + ("…" if len(str(v)) > 60 else "")
            items_html += f"""<div class="memory-item">
                <span class="memory-key">{icon} {label}</span>
                <span class="memory-val">{val_str}</span>
            </div>"""
        ai_final_html = ""
        if ai_desc_final:
            ai_final_html = f"""<div style="grid-column:1/-1;margin-top:0.6rem;">
                <span class="memory-key">📷 Photo Analysis</span>
                <div class="memory-val" style="white-space:normal;overflow:visible;text-overflow:unset;margin-top:2px;">{str(ai_desc_final)}</div>
            </div>"""
        st.markdown(f"""
        <div class="memory-panel">
            <div class="memory-header">🧠 Agent Memory — Full Report Summary</div>
            <div class="memory-grid">{items_html}{ai_final_html}</div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            for k in ["found_memory","found_done","found_started","found_ticket","found_ticket_saved",
                      "found_photo_done","found_editing","found_image_bytes","found_photo_path"]:
                st.session_state.pop(k, None)
            st.session_state.page = "home"
            st.switch_page("app.py")
    with col2:
        if st.button("🔄 New Report", use_container_width=True):
            for k in ["found_memory","found_done","found_started","found_ticket","found_ticket_saved",
                      "found_photo_done","found_editing","found_image_bytes","found_photo_path"]:
                st.session_state.pop(k, None)
            st.rerun()