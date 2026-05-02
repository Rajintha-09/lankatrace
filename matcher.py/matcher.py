from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from database import get_reports_by_type, save_match
from agent import get_item_category
from groq import Groq
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load model once and cache — avoids slow reload every time
@st.cache_resource(show_spinner=False)
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')


def build_text_summary(report: dict) -> str:
    """Build a text summary of a report for semantic matching."""
    parts = []
    for field in ["item_type", "description", "color", "contents", "ai_description",
                  "bus_route", "location", "incident_time", "transport_type"]:
        val = report.get(field)
        if val and str(val).strip():
            parts.append(f"{field}: {val}")
    return ". ".join(parts)


def get_similarity_score(text1: str, text2: str) -> float:
    model = load_model()
    embeddings = model.encode([text1, text2])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return round(float(score), 4)


def hybrid_score(new_report: dict, existing: dict, base_score: float) -> float:
    """
    Hybrid scoring: semantic similarity + rule-based boosts.
    Item type, location, and route matches add bonus points.
    """
    score = base_score

    # Item type exact match boost
    if new_report.get("item_type") and existing.get("item_type"):
        if new_report["item_type"].lower() == existing["item_type"].lower():
            score += 0.15

    # Location partial match boost
    if new_report.get("location") and existing.get("location"):
        if new_report["location"].lower() in existing["location"].lower():
            score += 0.10

    # Route match boost
    if new_report.get("bus_route") and existing.get("bus_route"):
        if new_report["bus_route"] == existing["bus_route"]:
            score += 0.10

    return min(score, 1.0)


def get_ai_explanation(lost_summary: str, found_summary: str, score: float) -> str:
    prompt = f"""
You are an assistant helping match lost and found items on Sri Lanka public transport.

Lost item report:
{lost_summary}

Found item report:
{found_summary}

Match score: {score:.0%}

Explain in 2-3 sentences why these items might or might not match.
Mention specific details like color, route, location, or time.
Keep it simple and clear.
"""
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    ).choices[0].message.content.strip()


def run_matching(new_report: dict) -> list:
    results = []

    try:
        opposite_type = "found" if new_report["report_type"] == "lost" else "lost"
        opposite_reports = get_reports_by_type(opposite_type)
    except Exception:
        return []

    new_cat = get_item_category(new_report.get("item_type", ""))
    new_summary = build_text_summary(new_report)

    for report in opposite_reports:
        try:
            # Strict same-item-category matching
            existing_cat = get_item_category(report.get("item_type", ""))
            if new_cat != "other" and existing_cat != "other" and new_cat != existing_cat:
                continue

            existing_summary = build_text_summary(report)
            base_score = get_similarity_score(new_summary, existing_summary)
            final_score = hybrid_score(new_report, report, base_score)

            if final_score >= 0.55:
                explanation = get_ai_explanation(new_summary, existing_summary, final_score)

                # Correctly assign lost/found IDs
                if new_report["report_type"] == "lost":
                    lost_id = new_report["id"]
                    found_id = report["id"]
                else:
                    lost_id = report["id"]
                    found_id = new_report["id"]

                save_match(lost_id, found_id, final_score, explanation)

                results.append({
                    "matched_report": report,
                    "score": final_score,
                    "explanation": explanation
                })

        except Exception:
            continue

    return sorted(results, key=lambda x: x["score"], reverse=True)