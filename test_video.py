
from video_processor import process_video, list_saved_videos

def main():
    print("\n" + "=" * 45)
    print("          GRANTH AI VIDEO DOWNLOADER")
    print("=" * 45)

    while True:
        print("\n1. Add new YouTube video")
        print("2. View saved videos")
        print("3. Exit")

        choice = input("\nChoose option: ").strip()

        if choice == "1":
            video_url = input("\nPaste YouTube URL: ").strip()

            if not video_url:
                print("Please enter a valid URL.")
                continue

            result = process_video(video_url)

            if result:
                print("\nVideo transcript is ready!")
                print(f"Title: {result['title']}")
                print(f"Video ID: {result['video_id']}")

        elif choice == "2":
            list_saved_videos()

        elif choice == "3":
            print("\nThank you for using Granth AI!")
            break

        else:
            print("\nInvalid choice. Try again.")


if __name__ == "__main__":
    main()
