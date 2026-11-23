from chat import chat_reply, reset_chat

SESSION = "test-user"


def main():
    print("\n" + "=" * 50)
    print("   GRANTH MITRA CHAT TEST")
    print("=" * 50)
    print("Type karo, ya suggestion ka number (1/2/3) dabao.")
    print("'new' = nayi chat, 'exit' = band\n")

    suggestions = []

    while True:
        text = input("Tum: ").strip()

        if not text:
            continue

        if text.lower() == "exit":
            break

        if text.lower() == "new":
            reset_chat(SESSION)
            suggestions = []
            print("\n(nayi chat shuru)\n")
            continue

        # number dabane par suggestion bhej do (chip tap jaisa)
        if text in ("1", "2", "3") and suggestions:
            index = int(text) - 1
            if index < len(suggestions):
                text = suggestions[index]
                print(f"Tum (chip): {text}")

        reply, suggestions = chat_reply(SESSION, text)

        print(f"\nMitra: {reply}\n")

        for i, s in enumerate(suggestions, start=1):
            print(f"  [{i}] {s}")

        print()


if __name__ == "__main__":
    main()