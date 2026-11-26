
import uuid

from chat import chat_reply, reset_chat


def new_session():
    return str(uuid.uuid4())


def main():

    SESSION = new_session()

    print("\n" + "=" * 50)
    print("   GRANTH MITRA CHAT TEST")
    print("=" * 50)
    print("Type karo, ya suggestion ka number (1/2/3) dabao.")
    print("'new' = nayi chat, 'exit' = band\n")

    print(f"Session ID: {SESSION}\n")

    suggestions = []

    while True:

        text = input("Tum: ").strip()

        if not text:
            continue

        if text.lower() == "exit":
            break

        if text.lower() == "new":

            reset_chat(SESSION)

            SESSION = new_session()

            suggestions = []

            print("\n(nayi chat shuru)\n")
            print(f"New Session ID: {SESSION}\n")

            continue

        # Suggestion number
        if text in ("1", "2", "3") and suggestions:

            index = int(text) - 1

            if index < len(suggestions):

                text = suggestions[index]

                print(f"Tum (chip): {text}")

        reply, suggestions = chat_reply(
            SESSION,
            text
        )

        print(f"\nMitra: {reply}\n")

        for i, suggestion in enumerate(
            suggestions,
            start=1
        ):
            print(f"  [{i}] {suggestion}")

        print()


if __name__ == "__main__":
    main()
