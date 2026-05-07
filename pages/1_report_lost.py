import streamlit as st
from agent import run_agent_turn, AgentMemory, agent_decide_next_field
from database import save_ticket_to_report, save_photo_path
import random, string
from PIL import Image
import io, os, uuid

st.set_page_config(page_title="Report Lost Item", page_icon="😔", layout="centered", initial_sidebar_state="collapsed")

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
        background: linear-gradient(135deg, #3D0000 0%, #1A0000 100%);
        border: 1px solid #F87171; border-radius: 14px;
        padding: 1.2rem 1.5rem; margin-bottom: 1rem;
    }
    .report-header h2 { color: #FFFFFF !important; margin: 0; font-size: 1.5rem; }
    .report-header p { color: #FCA5A5; margin: 0.3rem 0 0 0; font-size: 0.88rem; }

    .memory-panel {
        background: linear-gradient(135deg, #060D1F 0%, #0A1628 100%);
        border: 1px solid #1E3A5F; border-radius: 14px;
        padding: 1rem 1.2rem; margin-bottom: 1rem;
    }
    .memory-header { color: #4F9EF8; font-weight: 700; font-size: 0.8rem;
        text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.8rem; }
    .memory-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem 1rem; }
    .memory-item { display: flex; flex-direction: column; gap: 1px; }
    .memory-key { color: #4F9EF8; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
    .memory-val {
        color: #E2E8F0; font-size: 0.85rem; font-weight: 500;
        background: rgba(255,255,255,0.04); border-radius: 6px;
        padding: 2px 8px; border-left: 2px solid #1E3A5F;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }

    .chat-wrap { display: flex; flex-direction: column; gap: 0.7rem; margin-bottom: 1rem; }
    .bubble-row-agent { display: flex; justify-content: flex-start; align-items: flex-end; gap: 0.5rem; }
    .bubble-row-user  { display: flex; justify-content: flex-end;  align-items: flex-end; gap: 0.5rem; }
    .bubble-agent {
        background: #0F2044; border: 1px solid #1E3A5F;
        border-radius: 18px 18px 18px 4px;
        color: #BFDBFE; padding: 0.8rem 1rem;
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
    .progress-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,#F87171,#FBBF24,#4ADE80); }
    .progress-label { color:#475569; font-size:0.75rem; margin-bottom:0.3rem; display:flex; justify-content:space-between; }

    .ticket-box {
        background: #111111; border: 2px solid #4F9EF8;
        border-radius: 16px; padding: 2rem; text-align: center; margin-top: 1rem;
    }
    .ticket-id { font-size: 2.2rem; font-weight: 900; color: #4F9EF8; letter-spacing: 5px; font-family: monospace; }

    div.stButton > button {
        background-color: #111111 !important; color: #FFFFFF !important;
        border: 1px solid #2A2A2A !important; border-radius: 10px !important; font-weight: 700 !important;
    }
    div.stButton > button:hover { background-color: #0A1628 !important; border-color: #4F9EF8 !important; }
    hr { border-color: #1E1E1E !important; }

    .photo-panel {
        background: #060D1F; border: 1px solid #1E3A5F;
        border-radius: 14px; padding: 1rem 1.2rem; margin: 0.5rem 0;
    }
    .photo-panel-title { color: #4F9EF8; font-weight: 700; font-size: 0.8rem;
        text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 0.6rem; }
    .photo-desc { color: #E2E8F0; font-size: 0.88rem; line-height: 1.6; }

    .stTextInput > div > div > input {
        background: #0A0A1A !important; border: 1px solid #1E3A5F !important;
        color: #E2E8F0 !important; border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Back button ──────────────────────────────────────────────
col_back, _ = st.columns([1, 4])
with col_back:
    if st.button("← Home", key="back"):
        for k in ["lost_memory","lost_done","lost_started","lost_ticket","lost_ticket_saved",
                  "lost_photo_asked","lost_editing","lost_image_bytes","lost_photo_path"]:
            st.session_state.pop(k, None)
        st.session_state.page = "home"
        st.switch_page("app.py")

st.markdown("""
<div class="report-header">
    <h2>😔 Report Lost Item</h2>
    <p>Our AI agent will guide you step by step</p>
</div>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────
def save_photo_to_disk(image_bytes: bytes) -> str:
    os.makedirs("photos", exist_ok=True)
    filename = f"lost_{uuid.uuid4().hex[:10]}.jpg"
    path = os.path.join("photos", filename)
    img = Image.open(io.BytesIO(image_bytes))
    img.convert("RGB").save(path, format="JPEG", quality=90)
    return path

def clear_edit_widget_cache():
    """Remove stale text_input widget keys so the edit form always loads fresh values."""
    for field in FIELD_LABELS:
        st.session_state.pop(f"edit_{field}_lost", None)

# ── Session init ─────────────────────────────────────────────
for k, v in [("lost_memory", AgentMemory()), ("lost_done", False), ("lost_started", False),
              ("lost_ticket", None), ("lost_ticket_saved", False),
              ("lost_photo_asked", False), ("lost_editing", False),
              ("lost_photo_path", None), ("lost_image_bytes", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

memory: AgentMemory = st.session_state.lost_memory

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
    "identity_proof":   ("🔐", "Proof"),
    "brand":            ("🏷️", "Brand"),
    "contents":         ("📦", "Contents"),
    "ai_description":   ("📷", "Photo Analysis"),
}

# ── Memory Panel ─────────────────────────────────────────────
def render_memory_panel(memory, show_edit=False):
    visible = {k: v for k, v in memory.data.items() if not k.startswith("_") and k in FIELD_LABELS}
    if not visible:
        return

    _all = ["reporter_name","reporter_nic","reporter_phone","reporter_address",
            "item_type","color","transport_type","bus_route","location","incident_time"]
    _pct = int(sum(1 for f in _all if memory.data.get(f)) / len(_all) * 100)
    step_labels = {1:"Your Details", 2:"Item Info", 3:"Where & When", 4:"Identity Proof", 5:"Matching"}
    current_label = step_labels.get(memory.current_step, "In Progress")

    st.markdown(f"""
    <div class="progress-label">
        <span>🧠 Agent Memory — Step {memory.current_step}/5: {current_label}</span>
        <span>{_pct}% complete</span>
    </div>
    <div class="progress-wrap"><div class="progress-fill" style="width:{_pct}%"></div></div>
    """, unsafe_allow_html=True)

    ai_desc_val = visible.pop("ai_description", None)
    items_html = ""
    for k, v in visible.items():
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
        if st.button("✏️ Edit details", key="edit_btn_lost"):
            # Clear the loaded flag so edit form pre-populates with current memory
            st.session_state.pop("_lost_edit_loaded", None)
            st.session_state.lost_editing = True
            st.rerun()

# ── Edit Form ────────────────────────────────────────────────
def render_edit_form(memory):
    st.markdown("#### ✏️ Edit your details")
    st.caption("Correct any mistakes below, then click Save.")

    editable_fields = [k for k in FIELD_LABELS if k in memory.data and k != "ai_description"]

    # CRITICAL FIX: Only pre-populate keys when the edit session is BRAND NEW.
    # If we overwrite on every rerun, user's typed text gets wiped on each keystroke.
    # We use a separate "loaded" flag that is set once and cleared on save/cancel.
    if not st.session_state.get("_lost_edit_loaded"):
        for field in editable_fields:
            st.session_state[f"ef_lost_{field}"] = memory.data.get(field, "")
        st.session_state["_lost_edit_loaded"] = True

    updated = {}
    for field in editable_fields:
        icon, label = FIELD_LABELS[field]
        updated[field] = st.text_input(f"{icon} {label}", key=f"ef_lost_{field}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save changes", use_container_width=True, key="save_edit_lost"):
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

            st.session_state.pop("_lost_edit_loaded", None)
            for field in editable_fields:
                st.session_state.pop(f"ef_lost_{field}", None)
            st.session_state.lost_memory = memory
            st.session_state.lost_editing = False
            st.rerun()
    with col2:
        if st.button("✖ Cancel", use_container_width=True, key="cancel_edit_lost"):
            st.session_state.pop("_lost_edit_loaded", None)
            for field in editable_fields:
                st.session_state.pop(f"ef_lost_{field}", None)
            st.session_state.lost_editing = False
            st.rerun()

# ── Chat renderer ────────────────────────────────────────────
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

# ══════════════════════════════════════════════════════════════
# EDIT MODE — full page, replaces everything else
# ══════════════════════════════════════════════════════════════
if st.session_state.lost_editing:
    render_edit_form(memory)
    st.stop()

# ── Memory panel ─────────────────────────────────────────────
if st.session_state.lost_started and not st.session_state.lost_done:
    render_memory_panel(memory, show_edit=True)

# ── Photo thumbnail ──────────────────────────────────────────
if st.session_state.get("lost_image_bytes") and not st.session_state.lost_done:
    col_space, col_img = st.columns([2, 1])
    with col_img:
        try:
            img = Image.open(io.BytesIO(st.session_state.lost_image_bytes))
            st.image(img, caption="📷 Your photo", use_container_width=True)
        except Exception:
            pass

# ── Chat history ─────────────────────────────────────────────
render_chat(memory)

# ══════════════════════════════════════════════════════════════
# MAIN FLOW
# ══════════════════════════════════════════════════════════════
if not st.session_state.lost_done:
    if not st.session_state.lost_started:
        if st.button("🚀 Start Reporting", type="primary", use_container_width=True):
            st.session_state.lost_started = True
            reply, memory, done = run_agent_turn("lost", memory)
            st.session_state.lost_memory = memory
            st.session_state.lost_done = done
            st.rerun()
    else:
        # ── PHOTO BUG FIX ─────────────────────────────────────────────────────────
        # Previously used a manual list of base_fields to check if all questions
        # were answered. This was unreliable — if any field was stored as
        # "not remembered", or item extras (brand/contents) were still pending,
        # the condition silently failed and the uploader NEVER appeared.
        #
        # Fix: ask the agent itself — agent_decide_next_field returns None only
        # when it genuinely has no more questions left to ask. That is the exact
        # moment to show the photo uploader.
        # ─────────────────────────────────────────────────────────────────────────
        next_q = agent_decide_next_field("lost", memory)
        identity_done = bool(memory.data.get("identity_proof"))
        all_questions_done = (next_q is None) or (next_q == "identity_proof" and identity_done)
        photo_pending = (
            all_questions_done
            and not memory.data.get("ai_description")
            and not memory.data.get("_photo_skipped")
            and memory.data.get("identity_proof")  # only show photo step after identity proof is collected
        )

        if photo_pending:
            # Add agent photo request bubble only once
            if not st.session_state.lost_photo_asked:
                # Clear any stale file uploader state so widget renders fresh
                st.session_state.pop("lost_photo", None)
                st.session_state.lost_photo_asked = True
                memory.add_message(
                    "assistant",
                    "📷 Last step — do you have a photo of your lost item?\n"
                    "A photo makes it much easier to find a match! (Optional)"
                )
                st.session_state.lost_memory = memory
                st.rerun()

            uploaded = st.file_uploader(
                "Choose a photo (JPG, PNG, WEBP)",
                type=["jpg", "jpeg", "png", "webp"],
                key="lost_photo",
                label_visibility="visible"
            )

            col_skip, _ = st.columns([1, 3])
            with col_skip:
                if st.button("Skip → No photo", key="skip_photo"):
                    memory.data["_photo_skipped"] = True
                    memory.add_message("user", "No photo — skipping")
                    st.session_state.lost_memory = memory
                    reply, memory, done = run_agent_turn("lost", memory)
                    st.session_state.lost_memory = memory
                    st.session_state.lost_done = done
                    st.rerun()

            if uploaded:
                image_bytes = uploaded.read()
                st.session_state.lost_image_bytes = image_bytes
                photo_path = save_photo_to_disk(image_bytes)
                st.session_state.lost_photo_path = photo_path
                memory.update("photo_path", photo_path)
                memory.add_message("user", "📷 Photo uploaded")
                with st.spinner("🤖 Analyzing your photo..."):
                    reply, memory, done = run_agent_turn("lost", memory, image_bytes=image_bytes)
                st.session_state.lost_memory = memory
                st.session_state.lost_done = done
                st.rerun()

        else:
            if prompt := st.chat_input("Type your answer here..."):
                with st.spinner("🤖 Thinking..."):
                    reply, memory, done = run_agent_turn("lost", memory, user_message=prompt)
                st.session_state.lost_memory = memory
                st.session_state.lost_done = done
                st.rerun()

# ══════════════════════════════════════════════════════════════
# DONE — Ticket + Summary
# ══════════════════════════════════════════════════════════════
else:
    if not st.session_state.lost_ticket:
        st.session_state.lost_ticket = "LT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    if not st.session_state.lost_ticket_saved:
        if memory._report_id:
            save_ticket_to_report(memory._report_id, st.session_state.lost_ticket)
            if st.session_state.get("lost_photo_path"):
                save_photo_path(memory._report_id, st.session_state.lost_photo_path)
            st.session_state.lost_ticket_saved = True

    st.success("✅ Report submitted successfully!")

    if st.session_state.get("lost_image_bytes"):
        col_img, col_desc = st.columns([1, 2])
        with col_img:
            try:
                img = Image.open(io.BytesIO(st.session_state.lost_image_bytes))
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

    st.markdown(f"""
    <div class="ticket-box">
        <p style="color:#64748B;font-size:0.8rem;text-transform:uppercase;letter-spacing:2px;">Your Tracking ID</p>
        <div class="ticket-id">{st.session_state.lost_ticket}</div>
        <p style="color:#94A3B8;margin-top:1rem;font-size:0.88rem;">
            <strong style="color:#F1F5F9;">📋 Copy and save this ID!</strong><br><br>
            To check if your item was found, click<br>
            <strong style="color:#FBBF24;">Check My Report</strong> on the home page<br>
            and enter this ID <strong>or your NIC number</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    clean = {k: v for k, v in memory.data.items() if not k.startswith("_")}
    if clean:
        ai_desc_final = clean.pop("ai_description", None)
        items_html = ""
        for k, v in clean.items():
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
            for k in ["lost_memory","lost_done","lost_started","lost_ticket","lost_ticket_saved",
                      "lost_photo_asked","lost_editing","lost_image_bytes","lost_photo_path"]:
                st.session_state.pop(k, None)
            st.session_state.page = "home"
            st.switch_page("app.py")
    with col2:
        if st.button("🔄 New Report", use_container_width=True):
            for k in ["lost_memory","lost_done","lost_started","lost_ticket","lost_ticket_saved",
                      "lost_photo_asked","lost_editing","lost_image_bytes","lost_photo_path"]:
                st.session_state.pop(k, None)
            st.rerun()
