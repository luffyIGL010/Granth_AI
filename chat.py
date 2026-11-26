# import json

# import ollama
# from pydantic import BaseModel

# LLM_MODEL = "llama3.2:latest"

# KEEP_RECENT = 16        # itne latest messages poore bheje jayenge
# SUMMARIZE_AFTER = 24    # isse zyada ho to purane ka summary banega
# MAX_SESSIONS = 500


# class ChatOutput(BaseModel):
#     reply: str
#     suggestions: list[str]


# SYSTEM_PROMPT = """
# तुम "ग्रंथ मित्र" हो। तुम कोई मशीन नहीं, एक करीबी, समझदार दोस्त की तरह बात करते हो।

# बात करने का तरीका:
# 1. बोलचाल की सरल हिंदी में बात करो, जैसे दोस्त फ़ोन पर करता है। यूज़र English या Hinglish में लिखे तो उसी में जवाब दो।
# 2. सबसे पहले यूज़र की भावना पकड़ो। "मुझे खेद है कि आपको ऐसा लगा" जैसी रटी-रटाई लाइनें मत बोलो।
# 3. जवाब 2 से 4 वाक्य का हो। लिस्ट, bullet points, हेडिंग बिल्कुल नहीं।
# 4. बातचीत कभी अपने आप खत्म मत करो। हर जवाब के अंत में एक ही सवाल पूछो जो यूज़र की ताज़ा बात से जुड़ा हो।
# 5. यूज़र ने जो अभी बताया, उसी धागे को आगे बढ़ाओ। विषय अपने आप मत बदलो।
#    बातचीत का क्रम: (क) बात समझो -> (ख) कारण या असर पूछो -> (ग) हल्का-सा सुझाव बातचीत में बुनो -> (घ) बाद में हालचाल पूछो कि सुझाव से कुछ फ़र्क पड़ा या नहीं।
# 6. जो सवाल पहले पूछ चुके हो, उसे दोबारा मत पूछो। जो यूज़र बता चुका है, उसे याद रखो और इस्तेमाल करो।
# 7. सलाह थोपो मत। एक बार में सिर्फ़ एक छोटा सुझाव दो।
# 8. मेडिकल, कानूनी या खतरनाक सलाह मत दो। अगर यूज़र खुद को नुकसान पहुँचाने की बात करे,
#    तो प्यार से सुनो और उसे किसी भरोसेमंद इंसान या मदद-लाइन से बात करने को कहो।
# 9. जो न पता हो वो मत गढ़ो।

# सिर्फ़ इस JSON फ़ॉर्मैट में जवाब दो:
# {
#   "reply": "दोस्त जैसा जवाब",
#   "suggestions": ["जवाब 1", "जवाब 2", "जवाब 3"]
# }

# suggestions के नियम:
# - ठीक 3 हों, हर एक 2 से 6 शब्द का।
# - ये वो संभावित जवाब हैं जो यूज़र तुम्हारे अभी पूछे गए सवाल के जवाब में दे सकता है, पहले पुरुष में।
# - तीनों अलग दिशाओं में हों।

# उदाहरण:
# यूज़र: आज मेरा दिन अच्छा नहीं गया
# {"reply": "अरे, लगता है आज काफ़ी भारी दिन रहा। क्या हुआ, कुछ खास बात थी?", "suggestions": ["ऑफ़िस में दिक्कत हुई", "बस मन ठीक नहीं है", "घर पर कुछ हुआ"]}

# यूज़र: ऑफ़िस में दिक्कत हुई
# {"reply": "ओह, ऑफ़िस की टेंशन सबसे ज़्यादा थका देती है। किस तरह की दिक्कत थी, काम का दबाव या किसी से बहस?", "suggestions": ["बॉस से बहस हो गई", "काम बहुत ज़्यादा है", "टीम में झगड़ा हुआ"]}
# """

# sessions = {}


# def get_session(session_id):
#     if session_id not in sessions:
#         if len(sessions) >= MAX_SESSIONS:
#             sessions.pop(next(iter(sessions)))
#         sessions[session_id] = {"history": [], "summary": ""}
#     return sessions[session_id]


# def summarize(old_summary, old_messages):
#     text = "\n".join(
#         f"{m['role']}: {m['content']}" for m in old_messages
#     )

#     prompt = f"""
# पिछला सारांश:
# {old_summary or "कोई नहीं"}

# नई पुरानी बातचीत:
# {text}

# ऊपर की जानकारी से यूज़र के बारे में ज़रूरी बातें (नाम, परेशानी, भावनाएँ,
# क्या सुझाव दिए गए) 4-6 छोटे वाक्यों में हिंदी में लिखो। सिर्फ़ सारांश लिखो।
# """

#     try:
#         response = ollama.chat(
#             model=LLM_MODEL,
#             messages=[{"role": "user", "content": prompt}],
#             think=False,
#             options={"temperature": 0.2, "num_predict": 200}
#         )
#         return response["message"].get("content", "").strip() or old_summary
#     except Exception as error:
#         print(f"Summary error: {error}")
#         return old_summary


# def parse_output(raw):
#     try:
#         data = json.loads(raw)
#         reply = str(data.get("reply", "")).strip()
#         suggestions = [
#             str(s).strip()
#             for s in data.get("suggestions", [])
#             if str(s).strip()
#         ][:3]
#         return reply, suggestions
#     except (json.JSONDecodeError, AttributeError, TypeError):
#         return raw.strip(), []


# def chat_reply(session_id, message):
#     session = get_session(session_id)
#     history = session["history"]

#     history.append({"role": "user", "content": message})

#     system = SYSTEM_PROMPT

#     if session["summary"]:
#         system += (
#             "\n\nअब तक की बातचीत का सारांश (इसे याद रखो):\n"
#             + session["summary"]
#         )

#     response = ollama.chat(
#         model=LLM_MODEL,
#         messages=[{"role": "system", "content": system}]
#         + history[-KEEP_RECENT:],
#         format=ChatOutput.model_json_schema(),
#         think=False,
#         options={
#             "temperature": 0.8,
#             "num_predict": 350
#         }
#     )

#     raw = response["message"].get("content", "")

#     reply, suggestions = parse_output(raw)

#     if not reply:
#         reply = "माफ़ करना, मैं ठीक से समझ नहीं पाया। एक बार फिर बताओगे?"

#     if not suggestions:
#         suggestions = ["और बताता हूँ", "थोड़ा रुको", "विषय बदलते हैं"]

#     history.append({"role": "assistant", "content": reply})

#     # बातचीत लंबी हो जाए तो पुराना हिस्सा summary में बदल दो
#     if len(history) > SUMMARIZE_AFTER:
#         old = history[:-KEEP_RECENT]
#         session["summary"] = summarize(session["summary"], old)
#         session["history"] = history[-KEEP_RECENT:]

#     return reply, suggestions


# def reset_chat(session_id):
#     sessions.pop(session_id, None)





import json

import ollama
from pydantic import BaseModel

from database import (
    create_conversation,
    get_conversation,
    get_messages,
    save_message,
    update_summary
)
from database import get_user_memories
from memory import extract_memories
# ==========================================
# CONFIGURATION
# ==========================================

LLM_MODEL = "llama3.2:latest"

KEEP_RECENT = 16
SUMMARIZE_AFTER = 24
MAX_SESSIONS = 500


class ChatOutput(BaseModel):
    reply: str
    suggestions: list[str]


# ==========================================
# SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
तुम "ग्रंथ मित्र" हो। तुम कोई मशीन नहीं, एक करीबी, समझदार दोस्त की तरह बात करते हो।

बात करने का तरीका:
1. बोलचाल की सरल हिंदी में बात करो, जैसे दोस्त फ़ोन पर करता है। यूज़र English या Hinglish में लिखे तो उसी में जवाब दो।
2. सबसे पहले यूज़र की भावना पकड़ो। "मुझे खेद है कि आपको ऐसा लगा" जैसी रटी-रटाई लाइनें मत बोलो।
3. जवाब 2 से 4 वाक्य का हो। लिस्ट, bullet points, हेडिंग बिल्कुल नहीं।
4. बातचीत कभी अपने आप खत्म मत करो। हर जवाब के अंत में एक ही सवाल पूछो जो यूज़र की ताज़ा बात से जुड़ा हो।
5. यूज़र ने जो अभी बताया, उसी धागे को आगे बढ़ाओ। विषय अपने आप मत बदलो।
   बातचीत का क्रम: (क) बात समझो -> (ख) कारण या असर पूछो -> (ग) हल्का-सा सुझाव बातचीत में बुनो -> (घ) बाद में हालचाल पूछो कि सुझाव से कुछ फ़र्क पड़ा या नहीं।
6. जो सवाल पहले पूछ चुके हो, उसे दोबारा मत पूछो। जो यूज़र बता चुका है, उसे याद रखो और इस्तेमाल करो।
7. सलाह थोपो मत। एक बार में सिर्फ़ एक छोटा सुझाव दो।
8. मेडिकल, कानूनी या खतरनाक सलाह मत दो। अगर यूज़र खुद को नुकसान पहुँचाने की बात करे,
   तो प्यार से सुनो और उसे किसी भरोसेमंद इंसान या मदद-लाइन से बात करने को कहो।
9. जो न पता हो वो मत गढ़ो।

सिर्फ़ इस JSON फ़ॉर्मैट में जवाब दो:
{
  "reply": "दोस्त जैसा जवाब",
  "suggestions": ["जवाब 1", "जवाब 2", "जवाब 3"]
}

suggestions के नियम:
- ठीक 3 हों, हर एक 2 से 6 शब्द का।
- ये वो संभावित जवाब हैं जो यूज़र तुम्हारे अभी पूछे गए सवाल के जवाब में दे सकता है, पहले पुरुष में।
- तीनों अलग दिशाओं में हों।

उदाहरण:
यूज़र: आज मेरा दिन अच्छा नहीं गया
{"reply": "अरे, लगता है आज काफ़ी भारी दिन रहा। क्या हुआ, कुछ खास बात थी?", "suggestions": ["ऑफ़िस में दिक्कत हुई", "बस मन ठीक नहीं है", "घर पर कुछ हुआ"]}

यूज़र: ऑफ़िस में दिक्कत हुई
{"reply": "ओह, ऑफ़िस की टेंशन सबसे ज़्यादा थका देती है। किस तरह की दिक्कत थी, काम का दबाव या किसी से बहस?", "suggestions": ["बॉस से बहस हो गई", "काम बहुत ज़्यादा है", "टीम में झगड़ा हुआ"]}
"""


# ==========================================
# IN-MEMORY SESSION CACHE
# ==========================================

sessions = {}


def get_session(session_id, first_message="नई बातचीत"):

    if session_id in sessions:
        return sessions[session_id]

    if len(sessions) >= MAX_SESSIONS:
        sessions.pop(next(iter(sessions)))

    conversation = get_conversation(session_id)

    # New conversation
    if conversation is None:

        create_conversation(
            session_id,
            first_message
        )

        session = {
            "history": [],
            "summary": ""
        }

    # Restore existing conversation from SQLite
    else:

        previous_messages = get_messages(
            session_id,
            limit=KEEP_RECENT
        )

        session = {
            "history": [
                {
                    "role": message["role"],
                    "content": message["content"]
                }
                for message in previous_messages
            ],
            "summary": conversation["summary"] or ""
        }

    sessions[session_id] = session

    return session


# ==========================================
# SUMMARIZATION
# ==========================================

def summarize(old_summary, old_messages):

    text = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in old_messages
    )

    prompt = f"""
पिछला सारांश:
{old_summary or "कोई नहीं"}

नई पुरानी बातचीत:
{text}

ऊपर की जानकारी से यूज़र के बारे में ज़रूरी बातें (नाम, परेशानी, भावनाएँ,
क्या सुझाव दिए गए) 4-6 छोटे वाक्यों में हिंदी में लिखो। सिर्फ़ सारांश लिखो।
"""

    try:

        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            think=False,
            options={
                "temperature": 0.2,
                "num_predict": 200
            }
        )

        return (
            response["message"]
            .get("content", "")
            .strip() or old_summary
        )

    except Exception as error:

        print(f"Summary error: {error}")

        return old_summary


# ==========================================
# OUTPUT PARSING
# ==========================================

def parse_output(raw):

    try:

        data = json.loads(raw)

        reply = str(
            data.get("reply", "")
        ).strip()

        suggestions = [
            str(s).strip()
            for s in data.get("suggestions", [])
            if str(s).strip()
        ][:3]

        return reply, suggestions

    except (
        json.JSONDecodeError,
        AttributeError,
        TypeError
    ):

        return raw.strip(), []


# ==========================================
# MAIN CHAT FUNCTION
# ==========================================

def chat_reply(session_id, message):

    message = message.strip()

    if not message:
        raise ValueError("Message cannot be empty.")

    session = get_session(
        session_id,
        first_message=message
    )

    history = session["history"]

    # Save user message in memory
    history.append({
        "role": "user",
        "content": message
    })

    # Save user message permanently in SQLite
    save_message(
        session_id,
        "user",
        message
    )

    # Build system prompt
    system = SYSTEM_PROMPT
        # Retrieve user's personal memories
    USER_ID = "user_001"

    memories = get_user_memories(USER_ID)

    if memories:
        memory_text = "\n".join(
            f"- {item['memory']}"
            for item in memories
        )

        system += (
            "\n\nUser ki saved personal memories:\n"
            + memory_text
            + "\n\nIn memories ko relevant hone par naturally use karo. "
            "Har response mein inka zikr zaroori nahi hai. "
            "Kisi memory ko lekar assumption mat banao."
        )

    if session["summary"]:

        system += (
            "\n\nअब तक की बातचीत का सारांश (इसे याद रखो):\n"
            + session["summary"]
        )

    # Generate response
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system
            }
        ] + history[-KEEP_RECENT:],
        format=ChatOutput.model_json_schema(),
        think=False,
        options={
            "temperature": 0.8,
            "num_predict": 350
        }
    )

    raw = response["message"].get("content", "")

    reply, suggestions = parse_output(raw)

    if not reply:

        reply = (
            "माफ़ करना, मैं ठीक से समझ नहीं पाया। "
            "एक बार फिर बताओगे?"
        )

    if not suggestions:

        suggestions = [
            "और बताता हूँ",
            "थोड़ा रुको",
            "विषय बदलते हैं"
        ]

    # Save assistant response in memory
    history.append({
        "role": "assistant",
        "content": reply
    })

    # Save assistant response permanently
    save_message(
        session_id,
        "assistant",
        reply
    )


        # Automatically extract and save user memories
    USER_ID = "user_001"

    conversation_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history
    )

    extract_memories(USER_ID, conversation_text)

    # Summarize older messages
    if len(history) > SUMMARIZE_AFTER:

        old = history[:-KEEP_RECENT]

        new_summary = summarize(
            session["summary"],
            old
        )

        session["summary"] = new_summary

        # Save summary permanently
        update_summary(
            session_id,
            new_summary
        )

        # Keep only recent messages in memory
        session["history"] = history[-KEEP_RECENT:]

    return reply, suggestions


# ==========================================
# RESET SESSION CACHE
# ==========================================

def reset_chat(session_id):

    # Only clear in-memory session.
    # Database history remains محفوظ.
    sessions.pop(session_id, None)
