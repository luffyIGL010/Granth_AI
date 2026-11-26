
from memory import extract_memories

USER_ID = "user_001"

conversation = """
मेरा नाम सौरव है।
मुझे Python programming पसंद है।
मैंने B.Tech AI & ML किया है।
मेरा लक्ष्य एक अच्छा Software Developer बनना है।
"""

result = extract_memories(USER_ID, conversation)

print("Success:", result["success"])
print("Saved Count:", result["saved_count"])

print("\nExtracted Memories:")

for item in result["memories"]:
    print(item["memory"], "|", item["category"])
