
import json
import ollama

from database import save_memory, get_user_memories


LLM_MODEL = "llama3.2:latest"


MEMORY_PROMPT = """
You are the personal memory extractor for Granth Mitra.

Your task is to identify important and useful facts explicitly
shared by the user in the conversation.

Extract only information useful for future conversations.

ALLOWED CATEGORIES:

1. personal
   - User's name
   - Personal details explicitly shared

2. education
   - Degree
   - College
   - Academic background

3. skills
   - Programming languages
   - Technical skills
   - Professional abilities

4. preferences
   - Interests
   - Likes and dislikes
   - Communication preferences

5. goals
   - Career goals
   - Long-term plans
   - Learning objectives

STRICT RULES:

- Never invent or assume information.
- Extract facts only from the user's messages.
- Ignore assistant messages.
- Do not save temporary questions or casual conversation.
- Do not create incomplete memories.
- Write memories in clear, natural English.
- Keep each memory short and meaningful.
- Use consistent categories from the allowed list.
- Do not save the same fact twice.
- If the user's name is Saurav, write:
  "User's name is Saurav."
- If no useful information exists, return an empty list.

Return ONLY valid JSON:

{
    "memories": [
        {
            "memory": "User's name is Saurav.",
            "category": "personal"
        }
    ]
}
"""


def extract_memories(user_id, conversation):

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": MEMORY_PROMPT
                },
                {
                    "role": "user",
                    "content": conversation
                }
            ],
            format="json"
        )

        result = json.loads(response["message"]["content"])

        extracted = result.get("memories", [])

        saved_count = 0

        for item in extracted:

            memory = item.get("memory", "").strip()
            category = item.get("category", "general").strip()

            if not memory:
                continue

            save_memory(user_id, memory, category)
            saved_count += 1

        return {
            "success": True,
            "saved_count": saved_count,
            "memories": get_user_memories(user_id)
        }

    except Exception as error:

        print(f"Memory extraction error: {error}")

        return {
            "success": False,
            "saved_count": 0,
            "memories": []
        }
