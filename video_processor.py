
import json
import re

from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen

from youtube_transcript_api import YouTubeTranscriptApi


VIDEO_DIR = Path("videos")
TRANSCRIPT_DIR = VIDEO_DIR / "transcripts"

TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)



def extract_video_id(url):
    """Extract an 11-character YouTube video ID."""

    parsed = urlparse(url.strip())

    host = parsed.netloc.lower().split(":")[0]
    video_id = None

    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]

        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                video_id = parts[1]

    elif host in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.strip("/").split("/")[0]

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Invalid YouTube URL or video ID.")

    return video_id


def get_video_title(video_id):
    """Try to retrieve the public YouTube video title."""

    url = (
        "https://www.youtube.com/oembed"
        f"?url=https://www.youtube.com/watch?v={video_id}"
        "&format=json"
    )

    try:
        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data.get("title", video_id)

    except Exception:
        return video_id


def get_transcript(video_id):
    """
    Prefer Hindi captions, then English.
    If neither exists, use the first available language.
    """

    api = YouTubeTranscriptApi()

    transcript_list = api.list(video_id)

    available_tracks = list(transcript_list)

    if not available_tracks:
        raise RuntimeError("No captions are available for this video.")

    selected_track = None

    # Prefer Hindi first.
    for language_code in ["hi", "en"]:
        for track in available_tracks:
            if track.language_code == language_code:
                selected_track = track
                break

        if selected_track:
            break

    # Fall back to the video's first available caption language.
    if selected_track is None:
        selected_track = available_tracks[0]

    fetched = selected_track.fetch()

    segments = fetched.to_raw_data()

    if not segments:
        raise RuntimeError("The transcript is empty.")

    return {
        "language": fetched.language,
        "language_code": fetched.language_code,
        "is_generated": fetched.is_generated,
        "segments": segments
    }


def save_transcript(video_id, video_url, title, transcript):
    """Save transcript and timestamp information as JSON."""

    output_file = TRANSCRIPT_DIR / f"{video_id}.json"

    data = {
        "video_id": video_id,
        "title": title,
        "url": video_url,
        "language": transcript["language"],
        "language_code": transcript["language_code"],
        "is_generated": transcript["is_generated"],
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "segments": transcript["segments"]
    }

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_file


def process_video(video_url):
    """Complete video transcript extraction workflow."""

    try:
        video_id = extract_video_id(video_url)

        output_file = TRANSCRIPT_DIR / f"{video_id}.json"

        # Reuse previously extracted transcript.
        if output_file.exists():
            print("\nTranscript already exists.")
            print("Loading saved transcript...")

            with open(output_file, "r", encoding="utf-8") as file:
                return json.load(file)

        print("\nExtracting video information...")

        title = get_video_title(video_id)

        print(f"Video: {title}")
        print("\nFetching available captions...")

        transcript = get_transcript(video_id)

        print(f"Language: {transcript['language']}")
        print(f"Segments: {len(transcript['segments'])}")

        saved_file = save_transcript(
            video_id,
            video_url,
            title,
            transcript
        )

        print("\nTranscript saved successfully!")
        print(f"Location: {saved_file}")

        return {
            "video_id": video_id,
            "title": title,
            "url": video_url,
            "language": transcript["language"],
            "language_code": transcript["language_code"],
            "is_generated": transcript["is_generated"],
            "segments": transcript["segments"]
        }

    except Exception as error:
        print(f"\nTranscript extraction failed: {error}")
        return None


def list_saved_videos():
    """Display previously saved transcripts."""

    files = list(TRANSCRIPT_DIR.glob("*.json"))

    if not files:
        print("\nNo video transcripts found.")
        return

    print("\nSaved Videos:")

    for index, file in enumerate(files, start=1):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(
                f"{index}. {data['title']} "
                f"| Language: {data['language']}"
            )

        except (json.JSONDecodeError, OSError, KeyError):
            print(f"{index}. {file.name} (could not read metadata)")
