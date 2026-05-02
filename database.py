import sqlite3
from datetime import datetime
import os

DB_NAME = "lost_found.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT,
            report_type TEXT NOT NULL,
            reporter_name TEXT,
            reporter_nic TEXT,
            reporter_phone TEXT,
            reporter_address TEXT,
            item_type TEXT,
            brand TEXT,
            description TEXT,
            color TEXT,
            contents TEXT,
            bus_route TEXT,
            location TEXT,
            incident_time TEXT,
            handover_location TEXT,
            handover_type TEXT,
            contact_info TEXT,
            transport_type TEXT,
            identity_proof TEXT,
            photo_path TEXT,
            ai_description TEXT,
            submitted_at TEXT,
            status TEXT DEFAULT 'active',
            matched_with INTEGER
        )
    """)

    # Safely add any new columns to existing databases
    new_cols = [
        "ticket_id TEXT", "transport_type TEXT", "identity_proof TEXT",
        "mobile TEXT", "reporter_name TEXT", "reporter_phone TEXT",
        "reporter_nic TEXT", "reporter_address TEXT", "photo_path TEXT",
        "brand TEXT"
    ]
    for col in new_cols:
        try:
            cursor.execute(f"ALTER TABLE reports ADD COLUMN {col}")
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lost_report_id INTEGER,
            found_report_id INTEGER,
            confidence_score REAL,
            match_explanation TEXT,
            matched_at TEXT,
            FOREIGN KEY (lost_report_id) REFERENCES reports(id),
            FOREIGN KEY (found_report_id) REFERENCES reports(id)
        )
    """)

    conn.commit()
    conn.close()

    # Create photos directory if it doesn't exist
    os.makedirs("photos", exist_ok=True)

def save_report(data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (
            ticket_id, report_type, reporter_name, reporter_nic, reporter_phone, reporter_address,
            item_type, brand, description, color, contents,
            transport_type, bus_route, location, incident_time,
            handover_location, handover_type, contact_info,
            identity_proof, photo_path, ai_description, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("ticket_id"),
        data.get("report_type"),
        data.get("reporter_name"),
        data.get("reporter_nic"),
        data.get("reporter_phone"),
        data.get("reporter_address"),
        data.get("item_type"),
        data.get("brand"),
        data.get("description"),
        data.get("color"),
        data.get("contents"),
        data.get("transport_type"),
        data.get("bus_route"),
        data.get("location"),
        data.get("incident_time"),
        data.get("handover_location"),
        data.get("handover_type"),
        data.get("contact_info"),
        data.get("identity_proof"),
        data.get("photo_path"),
        data.get("ai_description"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id

def save_photo_path(report_id: int, photo_path: str):
    """Save the photo file path to the report after the photo is stored on disk."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reports SET photo_path = ? WHERE id = ?", (photo_path, report_id))
    conn.commit()
    conn.close()

def get_reports_by_type(report_type: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM reports
        WHERE report_type = ? AND status = 'active'
        ORDER BY submitted_at DESC
    """, (report_type,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_match(lost_id: int, found_id: int, score: float, explanation: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM matches WHERE lost_report_id = ? AND found_report_id = ?
    """, (lost_id, found_id))
    if cursor.fetchone():
        conn.close()
        return

    cursor.execute("""
        INSERT INTO matches (lost_report_id, found_report_id, confidence_score, match_explanation, matched_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        lost_id, found_id, score, explanation,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    cursor.execute("UPDATE reports SET status = 'matched', matched_with = ? WHERE id = ?", (found_id, lost_id))
    cursor.execute("UPDATE reports SET status = 'matched', matched_with = ? WHERE id = ?", (lost_id, found_id))

    conn.commit()
    conn.close()

def get_all_matches() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*,
            l.item_type as lost_item, l.description as lost_desc,
            l.bus_route as lost_route, l.contact_info as lost_contact,
            l.reporter_name as lost_name, l.reporter_phone as lost_phone,
            f.item_type as found_item, f.description as found_desc,
            f.bus_route as found_route, f.handover_location, f.handover_type,
            f.contact_info as found_contact,
            f.reporter_name as found_name, f.reporter_phone as found_phone
        FROM matches m
        JOIN reports l ON m.lost_report_id = l.id
        JOIN reports f ON m.found_report_id = f.id
        ORDER BY m.matched_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_match_by_ticket(ticket_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*,
            l.item_type as lost_item, l.color as lost_color,
            l.bus_route as lost_route, l.contents as lost_contents,
            l.incident_time as lost_time, l.ticket_id as lost_ticket,
            l.reporter_name as lost_name, l.reporter_phone as lost_phone,
            l.ai_description as lost_ai_desc,
            l.photo_path as lost_photo_path,
            f.item_type as found_item, f.color as found_color,
            f.bus_route as found_route, f.contents as found_contents,
            f.incident_time as found_time, f.ticket_id as found_ticket,
            f.handover_location, f.contact_info as found_contact,
            f.reporter_name as found_name, f.reporter_phone as found_phone,
            f.ai_description as found_ai_desc,
            f.photo_path as found_photo_path
        FROM matches m
        JOIN reports l ON m.lost_report_id = l.id
        JOIN reports f ON m.found_report_id = f.id
        WHERE UPPER(l.ticket_id) = UPPER(?) OR UPPER(f.ticket_id) = UPPER(?)
        ORDER BY m.matched_at DESC
    """, (ticket_id, ticket_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_report_by_nic(nic: str) -> dict:
    """Get a report by NIC number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reports WHERE reporter_nic = ? ORDER BY submitted_at DESC LIMIT 1",
        (nic.strip(),)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_match_by_nic(nic: str) -> list:
    """Get matches for a report found by NIC number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*,
            l.item_type as lost_item, l.color as lost_color,
            l.bus_route as lost_route, l.contents as lost_contents,
            l.incident_time as lost_time, l.ticket_id as lost_ticket,
            l.reporter_name as lost_name, l.reporter_phone as lost_phone,
            l.ai_description as lost_ai_desc,
            l.photo_path as lost_photo_path,
            f.item_type as found_item, f.color as found_color,
            f.bus_route as found_route, f.contents as found_contents,
            f.incident_time as found_time, f.ticket_id as found_ticket,
            f.handover_location, f.contact_info as found_contact,
            f.reporter_name as found_name, f.reporter_phone as found_phone,
            f.ai_description as found_ai_desc,
            f.photo_path as found_photo_path
        FROM matches m
        JOIN reports l ON m.lost_report_id = l.id
        JOIN reports f ON m.found_report_id = f.id
        WHERE l.reporter_nic = ? OR f.reporter_nic = ?
        ORDER BY m.matched_at DESC
    """, (nic.strip(), nic.strip()))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_ticket_to_report(report_id: int, ticket_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reports SET ticket_id = ? WHERE id = ?", (ticket_id, report_id))
    conn.commit()
    conn.close()

def get_report_by_ticket(ticket_id: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE UPPER(ticket_id) = UPPER(?)", (ticket_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reports")
    total_reports = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM matches")
    total_matches = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'matched'")
    total_recovered = cursor.fetchone()[0]
    conn.close()
    return {
        "total_reports": total_reports,
        "total_matches": total_matches,
        "total_recovered": total_recovered
    }

if __name__ == "__main__":
    create_tables()
    print("Database created successfully!")