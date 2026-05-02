from groq import Groq
from dotenv import load_dotenv
import os
import json
import base64
from datetime import date
from PIL import Image
import io
from database import save_report, create_tables

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
create_tables()


# ══════════════════════════════════════════════════════════════
# 🧠 AGENT MEMORY
# ══════════════════════════════════════════════════════════════
class AgentMemory:
    def __init__(self):
        self.history = []
        self.data = {}
        self.goal = "Collect all required details to file a lost or found report, then match against existing reports."
        self.plan = [
            "Step 1: Collect reporter personal details (name, NIC, phone, address)",
            "Step 2: Collect item details (type, brand/model if applicable, color)",
            "Step 3: Collect incident details (transport, route, location, time)",
            "Step 4: For lost items — get identity proof for ownership verification",
            "Step 5: Save report and run AI semantic matching",
        ]
        self.current_step = 1
        self._last_question = None
        self._report_id = None
        self._done = False
        self.ai_description = None

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def update(self, key: str, value):
        # Accept ALL non-empty values including "not remembered"
        if value and str(value).strip() not in ["", "none"]:
            self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def context_summary(self) -> str:
        return json.dumps(self.data, indent=2)

    def __contains__(self, key):
        return key in self.data or key in ["_report_id", "_done"]


# ══════════════════════════════════════════════════════════════
# Question lists
# ══════════════════════════════════════════════════════════════
QUESTIONS_LOST = [
    # Phase 1: Personal
    "reporter_name", "reporter_nic", "reporter_phone", "reporter_address",
    # Phase 2: Item
    "item_type", "color",
    # Phase 3: Incident
    "transport_type", "bus_route", "location", "incident_time",
    # Phase 4: Proof — lost only
    "identity_proof",
]

QUESTIONS_FOUND = [
    # Phase 1: Personal
    "reporter_name", "reporter_nic", "reporter_phone", "reporter_address",
    # Phase 2: Item
    "item_type", "color",
    # Phase 3: Incident
    "transport_type", "bus_route", "location", "incident_time",
]

# Item extras — asked after item_type + color, before location questions
ITEM_EXTRA_QUESTIONS = {
    "phone":    ["brand"],
    "wallet":   ["contents"],
    "bag":      ["contents"],
    "laptop":   ["brand"],
    "umbrella": ["umbrella_type"],
    "keys":     ["keychain"],
    "id":       ["id_type", "id_name"],
}

QUESTION_PROMPTS = {
    "reporter_name":    "Let's start! What is your full name?",
    "reporter_nic":     "What is your NIC number? (e.g. 199512345678 / 950123456V)",
    "reporter_phone":   "What is your phone number? (e.g. 0771234567)",
    "reporter_address": "What is your area? (e.g. Colombo 03 / Kandy / Matara / Gampaha)",
    "item_type":        "What type of item is it? (e.g. phone, wallet, bag, laptop, umbrella, keys, ID card)",
    "color":            "What color is it? (e.g. black, blue, red, brown, white, silver)",
    "transport_type":   "Was this on a bus or a train?",
    "bus_route":        "What is the route name or direction? (e.g. Colombo-Kandy / Galle Road / Matara direction / Intercity Express / Udarata Menike)",
    "location":         "Which stop, station, or area did this happen? (e.g. Pettah bus stand / Colombo Fort / Kandy / Nugegoda)",
    "incident_time":    "When did this happen? (e.g. today morning / yesterday 3pm / 15th April at 6pm)",
    "identity_proof":   "To verify ownership when collecting — please share one detail only the real owner would know. (e.g. a card name in wallet / sticker on laptop / phone wallpaper / keychain shape)",
    "brand":            "What is the brand or model? (e.g. Samsung Galaxy A54 / iPhone 13 / Dell i5 / HP Pavilion / MacBook Air)",
    "contents":         "What was inside? (e.g. NIC / driving license / cash / bank cards / charger)",
    "umbrella_type":    "Fold-up or long handle? Any color or pattern?",
    "keychain":         "Any keychain or tag on the keys? (e.g. small teddy / car logo / red tag / no keychain)",
    "id_type":          "What type of ID? (e.g. NIC / driving license / student ID / office ID)",
    "id_name":          "Whose name is on the ID?",
}

IMAGE_ANALYSIS_TEXT = """You are helping with a lost and found system for Sri Lanka public transport.
Look at this image carefully and describe:
1. What type of item it is
2. Color and material
3. Any visible features, logos, or distinguishing marks
4. Approximate size
Keep your description clear and factual in 3-4 sentences."""


def get_item_category(item_type: str) -> str:
    if not item_type:
        return "other"
    t = item_type.lower()
    if any(w in t for w in ["phone", "mobile", "smartphone", "iphone", "samsung", "android", "redmi", "xiaomi", "oppo", "vivo", "nokia"]):
        return "phone"
    if any(w in t for w in ["wallet", "purse", "billfold"]):
        return "wallet"
    if any(w in t for w in ["bag", "backpack", "handbag", "satchel", "pouch"]):
        return "bag"
    if any(w in t for w in ["laptop", "notebook", "macbook", "computer"]):
        return "laptop"
    if any(w in t for w in ["umbrella", "brolly"]):
        return "umbrella"
    if any(w in t for w in ["key", "keys"]):
        return "keys"
    if any(w in t for w in ["id", "nic", "license", "card", "pass"]):
        return "id"
    return "other"


def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()


def image_bytes_to_base64(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    output = io.BytesIO()
    image.convert("RGB").save(output, format="JPEG", quality=90)
    return base64.b64encode(output.getvalue()).decode()


def analyze_image(image_bytes: bytes) -> str:
    try:
        img_b64 = image_bytes_to_base64(image_bytes)
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": IMAGE_ANALYSIS_TEXT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not analyze image: {str(e)}"


# ══════════════════════════════════════════════════════════════
# 🧠 AGENT PLANNING
# ══════════════════════════════════════════════════════════════
def agent_decide_next_field(report_type: str, memory: AgentMemory) -> str | None:
    base = QUESTIONS_LOST if report_type == "lost" else QUESTIONS_FOUND

    # Auto-infer transport type from conversation history
    if not memory.data.get("transport_type"):
        all_user = " ".join(m["content"] for m in memory.history if m["role"] == "user").lower()
        train_words = ["train", "rail", "railway", "udarata menike", "ruhunu kumari",
                       "intercity express", "rajarata menike", "yal devi", "denuwara menike"]
        if any(w in all_user for w in train_words):
            memory.data["transport_type"] = "train"
        elif any(w in all_user for w in ["bus", "ctb", "private bus"]):
            memory.data["transport_type"] = "bus"

    for field in base:
        if memory.data.get(field):
            continue

        # Update step display
        if field in ["reporter_name", "reporter_nic", "reporter_phone", "reporter_address"]:
            memory.current_step = 1
        elif field in ["item_type", "color"]:
            memory.current_step = 2
        elif field in ["transport_type", "bus_route", "location", "incident_time"]:
            # Before asking transport questions, check if brand/extra is needed
            category = get_item_category(memory.data.get("item_type", ""))
            item_extras = ITEM_EXTRA_QUESTIONS.get(category, [])
            for extra_field in item_extras:
                if not memory.data.get(extra_field):
                    memory.current_step = 2
                    return extra_field
            memory.current_step = 3
        elif field == "identity_proof":
            memory.current_step = 4

        return field

    # Any remaining item extras not caught above
    category = get_item_category(memory.data.get("item_type", ""))
    for field in ITEM_EXTRA_QUESTIONS.get(category, []):
        if not memory.data.get(field):
            memory.current_step = 2
            return field

    return None


def get_question_prompt(field: str, memory: AgentMemory) -> str:
    transport = memory.data.get("transport_type", "").lower()

    if field == "bus_route":
        if transport == "bus":
            return "What is the bus route or direction? (e.g. Colombo to Galle / Matara to Colombo / 138 / Kandy to Colombo / Galle Road bus)"
        elif transport == "train":
            return "Which train service? (e.g. Colombo-Kandy / Intercity Express / Udarata Menike / Ruhunu Kumari / Coastal Line)"
        return QUESTION_PROMPTS["bus_route"]

    if field == "location":
        if transport == "bus":
            return "Which bus stop or area did this happen? (e.g. Pettah bus stand / Nugegoda / Maharagama / Kandy bus stand)\nIf you can't remember exactly, just say the nearest town or area."
        elif transport == "train":
            return "Which train station or area? (e.g. Colombo Fort / Kandy / Gampaha / Matara / Moratuwa)\nIf you can't remember, say the nearest station you remember."
        return QUESTION_PROMPTS["location"] + "\nIf you can't remember exactly, just give the nearest area."

    return QUESTION_PROMPTS.get(field, f"Please tell me: {field}")


# ══════════════════════════════════════════════════════════════
# 🧠 AGENT EXTRACTION
# ══════════════════════════════════════════════════════════════
def agent_extract(field: str, user_reply: str, memory: AgentMemory) -> dict:
    reply_lower = user_reply.strip().lower()

    # Handle "I can't remember" BEFORE calling AI — accept as valid answer
    cant_remember = ["cant remember", "can't remember", "don't remember", "dont remember",
                     "not sure", "i don't know", "i dont know", "no idea", "i forgot",
                     "not remember", "cannot remember", "can not remember"]
    if any(p in reply_lower for p in cant_remember):
        return {field: "not remembered"}

    # Fast local transport detection
    if field == "transport_type":
        train_words = ["train", "rail", "railway", "udarata", "ruhunu", "intercity", "express", "yal devi"]
        if any(w in reply_lower for w in train_words):
            return {"transport_type": "train"}
        if any(w in reply_lower for w in ["bus", "ctb", "private bus"]):
            return {"transport_type": "bus"}

    if field == "incident_time":
        return {"incident_time": user_reply.strip()}

    # identity_proof — save raw reply directly
    if field == "identity_proof":
        return {"identity_proof": user_reply.strip()}

    category = get_item_category(memory.data.get("item_type", ""))
    today_str = date.today().strftime("%Y-%m-%d")

    prompt = f"""
You are an AI agent for a Sri Lanka lost & found system.

Currently asking about: {field}
User replied: "{user_reply}"
Already collected: {json.dumps(memory.data)}
Item category: {category}
Today: {today_str}

IMPORTANT RULES:
1. Always return a value for "{field}" — never skip it
2. Also extract any other visible fields from the reply to avoid asking again
3. "identity_proof" is ONLY about ownership verification — NEVER extract it automatically
4. If user says "bus 138 at Pettah" → extract transport_type=bus, bus_route=138, location=Pettah
5. For transport_type: only "bus" or "train"
6. Only extract fields where the user CLEARLY gave a value
7. For brand: store full string like "Dell i5" or "Samsung A54"
8. "contents" is ONLY for what's physically inside a bag/wallet

Available fields: reporter_name, reporter_nic, reporter_phone, reporter_address,
item_type, color, contents, transport_type, bus_route, location, incident_time,
brand, umbrella_type, keychain, id_type, id_name

Return ONLY valid JSON. No explanation. No markdown.
"""
    text = call_groq(prompt)
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(text)
        result.pop("identity_proof", None)
        return result
    except Exception:
        return {field: user_reply}


# ══════════════════════════════════════════════════════════════
# 🚀 MAIN AGENT TURN
# ══════════════════════════════════════════════════════════════
def run_agent_turn(
    report_type: str,
    memory: AgentMemory,
    user_message: str = None,
    image_bytes: bytes = None,
) -> tuple[str, AgentMemory, bool]:
    """
    One turn: process input → update memory → plan → execute
    """

    # Process image — store description and add to chat history as visible message
    if image_bytes and not memory.ai_description:
        ai_desc = analyze_image(image_bytes)
        memory.ai_description = ai_desc
        memory.data["ai_description"] = ai_desc  # store directly, bypass update() filter

        extract_prompt = f"""
From this item description, extract only what you are confident about: item_type, color, brand.
Description: {ai_desc}
Return ONLY JSON. Example: {{"item_type": "wallet", "color": "black"}}
Only include fields you are very sure about.
"""
        text = call_groq(extract_prompt)
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            extracted = json.loads(text)
            for k, v in extracted.items():
                if k in ["item_type", "color", "brand"] and not memory.data.get(k):
                    memory.update(k, v)
        except Exception:
            pass

        # Never let image overwrite personal fields (already collected from user)
        # We only block extraction, not deletion — data stays intact

        # Add the photo analysis as a visible agent message
        memory.add_message("assistant", f"📷 I analyzed your photo:\n\n{ai_desc}")

    # Process user message
    if user_message:
        memory.add_message("user", user_message)
        last_field = memory._last_question
        if last_field:
            extracted = agent_extract(last_field, user_message, memory)
            for k, v in extracted.items():
                memory.update(k, v)

    # Plan next action
    next_field = agent_decide_next_field(report_type, memory)

    if next_field:
        memory._last_question = next_field
        question = get_question_prompt(next_field, memory)
        memory.add_message("assistant", question)
        return question, memory, False

    # All collected — but wait for photo step before saving (lost reports only)
    if report_type == "lost" and not memory.data.get("ai_description") and not memory.data.get("_photo_skipped"):
        memory._last_question = None
        return "", memory, False

    # All collected — save and match
    memory.current_step = 5
    from matcher import run_matching

    report_data = dict(memory.data)
    report_data["report_type"] = report_type

    report_id = save_report(report_data)
    report_data["id"] = report_id
    memory._report_id = report_id
    memory._done = True

    matches = run_matching(report_data)

    if matches:
        best = matches[0]
        score_pct = int(best["score"] * 100)
        matched = best["matched_report"]
        explanation = best["explanation"]

        if report_type == "found":
            phone = matched.get("reporter_phone", "")
            contact_msg = (f"📞 The owner's phone: **{phone}** — please contact them to arrange the return."
                           if phone and phone not in ["no", "unknown"]
                           else "The owner will be notified and will check the **Check Your Report** page.")
        else:
            phone = matched.get("reporter_phone", "")
            contact_msg = (f"📞 You can call the finder at: **{phone}**"
                           if phone and phone not in ["no", "unknown"]
                           else "Please check the **Check Your Report** page with your Tracking ID.")

        reply = f"""Your report has been saved! ✅

🎉 Great news — a potential match was found! ({score_pct}% confidence)

{explanation}

{contact_msg}"""
    else:
        if report_type == "found":
            reply = "Your report has been saved! ✅\n\nIf the owner reports this item as lost, a match will be created automatically and they can contact you directly."
        else:
            reply = "Your report has been saved! ✅\n\nTo check if your item has been found:\n→ Go to **Check Your Report** page\n→ Enter your Tracking ID or NIC number\n→ If a match is found, you will see the finder's contact details\n\nKeep your Tracking ID safe!"

    memory.add_message("assistant", reply)
    return reply, memory, True