
# from database import (
#     save_memory,
#     get_user_memories,
#     update_memory,
#     delete_memory
# )

# USER_ID = "user_001"

# # Save memories
# save_memory(
#     USER_ID,
#     "My name is Saurav",
#     "personal"
# )

# save_memory(
#     USER_ID,
#     "I like Python programming",
#     "preference"
# )

# # Update existing memory (ID 1)
# result = update_memory(
#     1,
#     USER_ID,
#     "My name is Saurav Rauthan",
#     "personal"
# )

# print("Memory updated:", result)

# # Retrieve memories
# print("\nAll Memories:")

# memories = get_user_memories(USER_ID)

# for item in memories:
#     print(item)


# # Delete memory with ID 3
# result = delete_memory(3, USER_ID)

# print("\nMemory deleted:", result)

# print("\nRemaining Memories:")

# for item in get_user_memories(USER_ID):
#     print(item)




from database import save_memory, get_user_memories

USER_ID = "user_001"

first = save_memory(
    USER_ID,
    "I like Python programming",
    "preference"
)

second = save_memory(
    USER_ID,
    "I like Python programming",
    "preference"
)

print("First ID:", first)
print("Second ID:", second)

print("\nAll Memories:")
for item in get_user_memories(USER_ID):
    print(item)