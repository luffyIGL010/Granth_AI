
from video_rag import (
    index_all_videos,
    ask_video_question
)


def main():

    print("\n")
    print("=" * 55)
    print("              GRANTH AI")
    print("           VIDEO QUESTION ANSWER")
    print("=" * 55)

    # Automatically index saved transcripts
    index_all_videos()

    while True:

        print("\nAsk a question about your video.")
        print("Type 'exit' to quit.")

        question = input("\nYour question: ").strip()

        if question.lower() == "exit":

            print("\nThank you for using Granth AI!")
            break

        if not question:
            continue

        try:

            ask_video_question(question)

        except Exception as error:

            print(f"\nError: {error}")


if __name__ == "__main__":
    main()
