import streamlit as st
from database import (get_match_by_ticket, get_report_by_ticket,
                      get_report_by_nic, get_match_by_nic, get_connection)
from PIL import Image
import os

st.set_page_config(page_title="Check Your Report", page_icon="🔔", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    html, body, .main, .block-container, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], section.main {
        background-color: #000000 !important; color: #F1F5F9 !important;
    }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu, footer, header { visibility: hidden; }

    .page-header {
        background: linear-gradient(135deg, #3D1A00 0%, #000000 100%);
        border: 1px solid #FBBF24; border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem;
    }
    .page-header h2 { color: #FFFFFF !important; margin: 0; font-size: 1.6rem; }
    .page-header p { color: #FDE68A; margin: 0.3rem 0 0 0; font-size: 0.9rem; }

    .match-card {
        background: #111111; border: 1px solid #1E1E1E;
        border-top: 4px solid #4ADE80; border-radius: 16px; padding: 1.5rem; margin-top: 1rem;
    }
    .report-box {
        background: #000000; border: 1px solid #1E1E1E; border-radius: 10px; padding: 1rem;
    }
    .stTextInput input {
        background: #111111 !important; color: #F1F5F9 !important;
        border: 1px solid #1E1E1E !important; border-radius: 10px !important; font-size: 1rem !important;
    }
    .stButton button { border-radius: 10px !important; font-weight: 600 !important; }

    .photo-section {
        background: #0A0A0A; border: 1px solid #1E1E1E; border-radius: 12px;
        padding: 1rem; margin-top: 0.8rem;
    }
    .photo-label { color: #475569; font-size: 0.75rem; text-transform: uppercase;
        letter-spacing: 1px; margin-bottom: 0.5rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

col_back, _ = st.columns([1, 4])
with col_back:
    if st.button("← Home"):
        st.session_state.page = "home"
        st.switch_page("app.py")

st.markdown("""
<div class="page-header">
    <h2>🔔 Check Your Report</h2>
    <p>Enter your Tracking ID or NIC number to check your match status</p>
</div>
""", unsafe_allow_html=True)

st.markdown("**How would you like to search?**")
search_method = st.radio(
    "Search by",
    ["🎫 Tracking ID (e.g. LT-ABC123)", "🪪 NIC Number"],
    label_visibility="collapsed",
    horizontal=True
)

col1, col2 = st.columns([3, 1])
with col1:
    if "Tracking ID" in search_method:
        search_input = st.text_input("Tracking ID", placeholder="e.g. LT-ABC123 or FT-XYZ789", label_visibility="collapsed")
    else:
        search_input = st.text_input("NIC Number", placeholder="e.g. 199512345678 or 950123456V", label_visibility="collapsed")
with col2:
    check = st.button("🔍 Check", type="primary", use_container_width=True)

if check and search_input:
    raw_input = search_input.strip()
    search_input_upper = raw_input.upper()
    st.markdown("---")

    # ── FIX 6: Smart search — auto-detect ticket ID even if NIC is selected ──
    # If input looks like LT-XXXXXX or FT-XXXXXX, always search as ticket ID
    looks_like_ticket = (
        search_input_upper.startswith("LT-") or
        search_input_upper.startswith("FT-")
    )

    report = None
    matches = []
    is_lost_person = True

    if looks_like_ticket:
        # Always treat as ticket ID regardless of radio selection
        report = get_report_by_ticket(search_input_upper)
        matches = get_match_by_ticket(search_input_upper) if report else []
        is_lost_person = search_input_upper.startswith("LT-")
        search_mode_used = "ticket"
    elif "Tracking ID" in search_method:
        report = get_report_by_ticket(search_input_upper)
        matches = get_match_by_ticket(search_input_upper) if report else []
        is_lost_person = search_input_upper.startswith("LT-")
        search_mode_used = "ticket"
    else:
        report = get_report_by_nic(raw_input)
        matches = get_match_by_nic(raw_input) if report else []
        is_lost_person = report.get("report_type") == "lost" if report else True
        search_mode_used = "nic"

    if not report:
        st.error("❌ No report found. Please check your Tracking ID and try again.")
        st.info("💡 Your Tracking ID looks like **LT-ABC123** (lost) or **FT-ABC123** (found). Check the exact ID you received when you submitted your report.")
    else:
        if not matches:
            st.warning("⏳ No match found yet for your report.")
            st.info("Our AI checks for matches automatically whenever a new report is submitted. Please check back later!")

            st.markdown("**Your Report Details:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"🏷️ Item: **{report.get('item_type') or 'N/A'}**")
                st.write(f"🎨 Color: {report.get('color') or 'N/A'}")
                st.write(f"🚌 Route: {report.get('bus_route') or 'N/A'}")
            with col_b:
                st.write(f"📍 Location: {report.get('location') or 'N/A'}")
                st.write(f"🕐 Time: {report.get('incident_time') or 'N/A'}")
                st.write(f"📅 Submitted: {report.get('submitted_at','')[:10] or 'N/A'}")

            # FIX 4: Show full photo description
            if report.get("ai_description"):
                st.markdown("---")
                st.markdown("**📷 Photo Analysis from your report:**")
                st.markdown(f'<div style="background:#0F2044;border:1px solid #1E3A5F;border-radius:10px;padding:0.8rem 1rem;color:#BFDBFE;font-size:0.88rem;line-height:1.7;">{report["ai_description"]}</div>', unsafe_allow_html=True)

        else:
            st.success("🎉 A match has been found for your report!")

            for m in matches:
                m = dict(m)
                score_pct = int(m["confidence_score"] * 100)

                if score_pct >= 80:
                    _sc = "#4ADE80"; _sb = "#052E16"; _sbo = "#166534"; _sl = "High Match"
                elif score_pct >= 70:
                    _sc = "#FBBF24"; _sb = "#3D1A00"; _sbo = "#92400E"; _sl = "Good Match"
                else:
                    _sc = "#F87171"; _sb = "#3D0000"; _sbo = "#991B1B"; _sl = "Possible Match"

                st.markdown('<div class="match-card">', unsafe_allow_html=True)
                st.markdown(f'<div style="text-align:center;margin-bottom:1rem;"><span style="background:{_sb};color:{_sc};border:1px solid {_sbo};padding:0.5rem 1.5rem;border-radius:20px;font-weight:700;font-size:1.3rem;display:inline-block;">{score_pct}% — {_sl}</span></div>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="report-box">', unsafe_allow_html=True)
                    st.markdown("**😔 Lost Item**")
                    st.write(f"🏷️ {m.get('lost_item') or 'N/A'}")
                    st.write(f"🎨 {m.get('lost_color') or 'N/A'}")
                    st.write(f"📦 {m.get('lost_contents') or 'N/A'}")
                    st.write(f"🚌 {m.get('lost_route') or 'N/A'}")
                    st.write(f"🕐 {m.get('lost_time') or 'N/A'}")
                    if m.get("lost_name"):
                        st.write(f"👤 **{m['lost_name']}**")
                    if m.get("lost_phone"):
                        st.write(f"📞 **{m['lost_phone']}**")
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown('<div class="report-box">', unsafe_allow_html=True)
                    st.markdown("**😊 Found Item**")
                    st.write(f"🏷️ {m.get('found_item') or 'N/A'}")
                    st.write(f"🎨 {m.get('found_color') or 'N/A'}")
                    st.write(f"📦 {m.get('found_contents') or 'N/A'}")
                    st.write(f"🚌 {m.get('found_route') or 'N/A'}")
                    st.write(f"🕐 {m.get('found_time') or 'N/A'}")
                    if m.get("found_name"):
                        st.write(f"👤 **{m['found_name']}**")
                    if m.get("found_phone"):
                        st.write(f"📞 **{m['found_phone']}**")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Show actual photos + AI descriptions
                lost_ai   = m.get("lost_ai_desc")
                found_ai  = m.get("found_ai_desc")
                lost_photo  = m.get("lost_photo_path")
                found_photo = m.get("found_photo_path")

                if lost_ai or found_ai or lost_photo or found_photo:
                    st.markdown("---")
                    st.markdown("**📷 Photo Analysis**")
                    pcol1, pcol2 = st.columns(2)

                    with pcol1:
                        st.markdown('<div class="photo-section">', unsafe_allow_html=True)
                        st.markdown('<p class="photo-label">😔 Lost Item</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        # Show actual image if it exists on disk
                        if lost_photo and os.path.exists(lost_photo):
                            st.image(lost_photo, caption="Lost item photo", use_container_width=True)
                        if lost_ai:
                            st.markdown(f'<p style="color:#94A3B8;font-size:0.84rem;line-height:1.6;margin:0.4rem 0 0 0;">{lost_ai}</p>', unsafe_allow_html=True)
                        elif not lost_photo:
                            st.markdown('<p style="color:#475569;font-size:0.82rem;">No photo uploaded</p>', unsafe_allow_html=True)

                    with pcol2:
                        st.markdown('<div class="photo-section">', unsafe_allow_html=True)
                        st.markdown('<p class="photo-label">😊 Found Item</p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        # Show actual image if it exists on disk
                        if found_photo and os.path.exists(found_photo):
                            st.image(found_photo, caption="Found item photo", use_container_width=True)
                        if found_ai:
                            st.markdown(f'<p style="color:#94A3B8;font-size:0.84rem;line-height:1.6;margin:0.4rem 0 0 0;">{found_ai}</p>', unsafe_allow_html=True)
                        elif not found_photo:
                            st.markdown('<p style="color:#475569;font-size:0.82rem;">No photo uploaded</p>', unsafe_allow_html=True)

                st.markdown("")
                st.markdown("**🤖 Why AI thinks this is a match**")
                st.info(m["match_explanation"])

                # Contact section
                st.markdown("**📞 Contact Details**")
                if is_lost_person:
                    if m.get("found_phone") and m.get("found_phone") not in ["no", "unknown"]:
                        st.success(f"Call the finder **{m.get('found_name','Finder')}** at: **{m['found_phone']}**")
                    else:
                        st.info("Finder contact not available. They may reach out to you.")
                else:
                    if m.get("lost_phone") and m.get("lost_phone") not in ["no", "unknown"]:
                        st.success(f"Call the owner **{m.get('lost_name','Owner')}** at: **{m['lost_phone']}**")
                    else:
                        st.info("Owner contact not available. They will reach out to you.")

                # Identity proof (lost person only)
                if is_lost_person:
                    conn2 = get_connection()
                    cursor2 = conn2.cursor()
                    if search_mode_used == "ticket":
                        cursor2.execute("SELECT identity_proof FROM reports WHERE ticket_id = ?", (search_input_upper,))
                    else:
                        cursor2.execute("SELECT identity_proof FROM reports WHERE reporter_nic = ? ORDER BY submitted_at DESC LIMIT 1", (raw_input,))
                    row2 = cursor2.fetchone()
                    conn2.close()
                    if row2 and row2[0] and row2[0] not in ["unknown", "no", None]:
                        st.markdown("**🔐 Your Identity Verification Note**")
                        st.warning(f"When meeting the finder, mention this to prove ownership: **{row2[0]}**")

                st.markdown(f'<p style="color:#374151;font-size:0.8rem;text-align:right;margin-top:0.8rem;">Matched at: {m["matched_at"]}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif check and not search_input:
    st.warning("Please enter your Tracking ID or NIC number first.")