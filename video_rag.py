
import json
import re
from pathlib import Path

import chromadb
import ollama

# Reuse the embedding model loaded by PDF RAG
from rag import embedding_model


# ==========================================
# CONFIGURATION
# ==========================================

LLM_MODEL = "llama3.2:latest"
EMBEDDING_MODEL = "BAAI/bge-m3"

TRANSCRIPT_DIR = Path("videos/transcripts")
CHROMA_DIR = "chroma_db"

COLLECTION_NAME = "granth_videos_v2"

CHUNK_SIZE = 450
TOP_K = 6
BATCH_SIZE = 32


# ==========================================
# INITIALIZATION
# ==========================================

print("\nLoading Granth AI Video RAG...")

print("Using shared embedding model from PDF RAG...")

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(path=CHROMA_DIR)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

print("Video RAG initialized successfully!")


# ==========================================
# TIMESTAMP FUNCTIONS
# ==========================================

def format_timestamp(seconds):

    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def create_timestamp_url(video_url, seconds):

    separator = "&" if "?" in video_url else "?"

    return f"{video_url}{separator}t={int(seconds)}s"


# ==========================================
# TRANSCRIPT CHUNKING
# ==========================================

def create_video_chunks(video):

    segments = video.get("segments", [])

    chunks = []
    current_segments = []
    current_length = 0

    for segment in segments:

        text = segment.get("text", "").strip()

        if not text:
            continue

        start = float(segment.get("start", 0))
        duration = float(segment.get("duration", 0))

        current_segments.append({
            "text": text,
            "start": start,
            "end": start + duration
        })

        current_length += len(text)

        if current_length >= CHUNK_SIZE:

            chunks.append({
                "text": " ".join(
                    item["text"] for item in current_segments
                ),
                "start": current_segments[0]["start"],
                "end": current_segments[-1]["end"]
            })

            # Overlap: retain last two segments
            current_segments = current_segments[-2:]

            current_length = sum(
                len(item["text"])
                for item in current_segments
            )

    if current_segments:

        chunks.append({
            "text": " ".join(
                item["text"] for item in current_segments
            ),
            "start": current_segments[0]["start"],
            "end": current_segments[-1]["end"]
        })

    return chunks


# ==========================================
# INDEX VIDEO
# ==========================================

def index_video(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        video = json.load(file)

    video_id = video["video_id"]

    chunks = create_video_chunks(video)

    if not chunks:

        print("No transcript content found.")
        return

    # Skip videos already indexed
    existing = collection.get(
        where={"video_id": video_id},
        limit=1
    )

    if existing["ids"]:

        print(f"\nAlready indexed: {video['title']}")
        return

    print(f"\nIndexing: {video['title']}")
    print(f"Total chunks: {len(chunks)}")

    for batch_start in range(0, len(chunks), BATCH_SIZE):

        batch = chunks[
            batch_start:batch_start + BATCH_SIZE
        ]

        texts = [item["text"] for item in batch]

        embeddings = embedding_model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        ids = []
        metadatas = []

        for offset, chunk in enumerate(batch):

            chunk_number = batch_start + offset

            ids.append(f"{video_id}_{chunk_number}")

            metadatas.append({
                "video_id": video_id,
                "video_title": video["title"],
                "video_url": video["url"],
                "language": video.get("language", "Unknown"),
                "start": float(chunk["start"]),
                "end": float(chunk["end"])
            })

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(
            f"Indexed {min(batch_start + BATCH_SIZE, len(chunks))}"
            f"/{len(chunks)} chunks"
        )

    print("\nVideo indexed successfully!")


# ==========================================
# INDEX ALL SAVED VIDEOS
# ==========================================

def index_all_videos():

    TRANSCRIPT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    files = sorted(TRANSCRIPT_DIR.glob("*.json"))

    if not files:

        print("\nNo saved video transcripts found.")
        return

    print(f"\nFound {len(files)} video transcript(s).")

    for file_path in files:

        try:

            index_video(file_path)

        except Exception as error:

            print(
                f"Indexing error in {file_path.name}: {error}"
            )

    print(
        f"\nTotal indexed chunks: {collection.count()}"
    )


# ==========================================
# TEXT PROCESSING
# ==========================================

def tokenize(text):

    return set(
        re.findall(
            r"[^\W_]+",
            text.lower(),
            flags=re.UNICODE
        )
    )


STOPWORDS = {
    "कौन", "क्या", "कैसे", "कब", "कहाँ",
    "है", "हैं", "था", "थे", "की", "का",
    "के", "में", "से", "को", "और", "तो",
    "पर", "इस", "उस", "यह", "वह", "बताओ",
    "बताइए", "समझाओ", "समझाइए",
    "the", "what", "who", "when", "where",
    "how", "is", "are", "was", "were",
    "a", "an", "of", "in", "on", "to",
    "and", "about", "does", "did"
}


def get_question_keywords(question):

    return {
        word
        for word in tokenize(question)
        if word not in STOPWORDS and len(word) > 1
    }


# ==========================================
# RETRIEVE RELEVANT TRANSCRIPT
# ==========================================

def retrieve_video_context(question):

    if collection.count() == 0:
        return []

    query_embedding = embedding_model.encode(
        [question],
        normalize_embeddings=True
    )

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=min(12, collection.count()),
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    candidates = {}

    if results["documents"]:

        for document, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):

            key = (
                metadata["video_id"]
                + "_"
                + str(metadata["start"])
            )

            candidates[key] = {
                "text": document,
                "metadata": metadata,
                "semantic_score": max(
                    0,
                    1 - float(distance)
                ),
                "keyword_score": 0
            }

    # Keyword matching
    all_records = collection.get(
        include=["documents", "metadatas"]
    )

    keywords = get_question_keywords(question)

    if keywords:

        for document, metadata in zip(
            all_records["documents"],
            all_records["metadatas"]
        ):

            matched = keywords.intersection(
                tokenize(document)
            )

            if not matched:
                continue

            key = (
                metadata["video_id"]
                + "_"
                + str(metadata["start"])
            )

            score = len(matched) / len(keywords)

            if key in candidates:

                candidates[key]["keyword_score"] = score

            else:

                candidates[key] = {
                    "text": document,
                    "metadata": metadata,
                    "semantic_score": 0,
                    "keyword_score": score
                }

    ranked = []

    for item in candidates.values():

        item["final_score"] = (
            0.55 * item["semantic_score"]
            + 0.45 * item["keyword_score"]
        )

        ranked.append(item)

    ranked.sort(
        key=lambda item: item["final_score"],
        reverse=True
    )

    return ranked[:TOP_K]


# ==========================================
# GENERATE ANSWER
# ==========================================

def generate_video_answer(question, contexts):

    if not contexts:

        return (
            "इस वीडियो के transcript में "
            "इस प्रश्न का उत्तर नहीं मिला।"
        )

    context_text = ""

    for index, item in enumerate(contexts, start=1):

        metadata = item["metadata"]

        context_text += f"""
[Source {index}]
Timestamp: {format_timestamp(metadata['start'])}
Transcript: {item['text']}
"""

    prompt = f"""
You are Granth AI.

Your job is to answer questions using only the
provided video transcript.

STRICT INSTRUCTIONS:

1. Answer the exact question directly.
2. First sentence must contain the answer.
3. Use the same language as the question.
4. For simple questions, give a short answer.
5. Do not give unnecessary explanations.
6. Never invent information.
7. If the transcript does not support an answer,
   clearly say that the answer is not available.
8. Do not confuse the speaker's words with your own assumptions.

Example:
Question: बुद्धि किसने मांगी?
If the transcript supports it, answer:
भगवान ने बुद्धि मांगी है।

TRANSCRIPT:

{context_text}

QUESTION:

{question}

DIRECT ANSWER:
"""

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
            "temperature": 0,
            "num_predict": 400
        }
    )

    answer = response["message"].get(
        "content", ""
    ).strip()

    if not answer:

        raise RuntimeError(
            "Ollama returned an empty answer."
        )

    return answer


# ==========================================
# ASK QUESTION
# ==========================================

def ask_video_question(question):

    if collection.count() == 0:

        print("\nNo videos indexed.")
        return

    print("\nSearching video transcript...")

    contexts = retrieve_video_context(question)

    if not contexts:

        print("\nNo relevant transcript found.")
        return

    print("Generating answer...")

    answer = generate_video_answer(
        question,
        contexts
    )

    print("\n" + "=" * 55)
    print("GRANTH AI ANSWER")
    print("=" * 55)

    print(answer)

    print("\n" + "=" * 55)
    print("VIDEO SOURCES")
    print("=" * 55)

    seen = set()

    for index, item in enumerate(contexts, start=1):

        metadata = item["metadata"]

        timestamp = format_timestamp(
            metadata["start"]
        )

        url = create_timestamp_url(
            metadata["video_url"],
            metadata["start"]
        )

        key = (
            metadata["video_id"],
            timestamp
        )

        if key in seen:
            continue

        seen.add(key)

        print(f"\nSource: {index}")
        print(f"Video: {metadata['video_title']}")
        print(f"Timestamp: {timestamp}")
        print(f"Watch: {url}")
