
from pathlib import Path

import ollama

from rag import (
    index_all_books,
    ask_question,
    collection,
    LLM_MODEL
)


def check_ollama():
    try:
        ollama.show(LLM_MODEL)
        print("Ollama model is available.")
        return True

    except Exception:
        print(
            f"\nModel {LLM_MODEL} is not available."
        )
        print(
            f"Run: ollama pull {LLM_MODEL}"
        )
        return False


def show_books():
    books = collection.get(
        include=["metadatas"]
    )

    if not books["metadatas"]:
        print("\nNo indexed books found.")
        return

    unique_books = sorted({
        metadata["book_name"]
        for metadata in books["metadatas"]
    })

    print("\nIndexed Books:")

    for number, book in enumerate(
        unique_books,
        start=1
    ):
        print(f"{number}. {book}")


def main():
    print("\n")
    print("=" * 55)
    print("                 GRANTH AI")
    print("          Your Personal Book Assistant")
    print("=" * 55)

    if not check_ollama():
        return

    Path("documents").mkdir(exist_ok=True)

    print("\nChecking PDF books and indexing...")

    index_all_books()

    while True:
        print("\n")
        print("1. Ask a Question")
        print("2. List Indexed Books")
        print("3. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            question = input(
                "\nAsk Granth AI: "
            ).strip()

            if not question:
                print("Please enter a question.")
                continue

            ask_question(question)

        elif choice == "2":
            show_books()

        elif choice == "3":
            print("\nThank you for using Granth AI!")
            break

        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
