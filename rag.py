
import json
import hashlib
import re

from pathlib import Path

import chromadb
import ollama

from sentence_transformers import SentenceTransformer

from processor import (
    get_all_books,
    extract_pdf
)


# Configuration

LLM_MODEL = "llama3.2:latest"
EMBEDDING_MODEL = "BAAI/bge-m3"

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "granth_books"

MANIFEST_FILE = Path("index_manifest.json")

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

TOP_K = 8
MIN_SIMILARITY = 0.35
BATCH_SIZE = 16


# Load embedding model once

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


# ChromaDB setup

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def load_manifest():
    if not MANIFEST_FILE.exists():
        return {}

    try:
        with open(
            MANIFEST_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_manifest(manifest):
    with open(
        MANIFEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            manifest,
            file,
            indent=4,
            ensure_ascii=False
        )


def split_long_text(text):
    words = text.split()

    chunks = []

    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1

        if (
            current_length + word_length > CHUNK_SIZE
            and current_chunk
        ):
            chunks.append(" ".join(current_chunk))

            overlap_words = []
            overlap_length = 0

            for old_word in reversed(current_chunk):
                if overlap_length + len(old_word) + 1 > CHUNK_OVERLAP:
                    break

                overlap_words.insert(0, old_word)
                overlap_length += len(old_word) + 1

            current_chunk = overlap_words
            current_length = overlap_length

        current_chunk.append(word)
        current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def create_chunks(pages, book_name):
    chunks = []

    for page_number, text in pages.items():
        if not text.strip():
            continue

        page_chunks = split_long_text(text)

        for chunk_number, chunk in enumerate(page_chunks):
            chunks.append({
                "text": chunk,
                "metadata": {
                    "source_type": "pdf",
                    "book_name": book_name,
                    "page": int(page_number),
                    "chunk": chunk_number
                }
            })

    return chunks


def index_book(file_path):
    manifest = load_manifest()

    pages, file_hash = extract_pdf(file_path)

    if manifest.get(file_path.name) == file_hash:
        print(f"Already indexed: {file_path.name}")
        return

    print(f"\nCreating chunks for {file_path.name}...")

    chunks = create_chunks(
        pages,
        file_path.name
    )

    if not chunks:
        print("No readable text found. Skipping indexing.")
        return

    print(f"Total chunks: {len(chunks)}")

    # Remove old records for this book if it changed.
    old_records = collection.get(
        where={"book_name": file_path.name},
        include=[]
    )

    if old_records["ids"]:
        collection.delete(ids=old_records["ids"])

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        texts = [
            item["text"] for item in batch
        ]

        embeddings = embedding_model.encode(
            texts,
            normalize_embeddings=True
        ).tolist()

        ids = []
        metadatas = []

        for item in batch:
            metadata = item["metadata"]

            unique_string = (
                f"{file_hash}_"
                f"{metadata['page']}_"
                f"{metadata['chunk']}"
            )

            chunk_id = hashlib.sha256(
                unique_string.encode()
            ).hexdigest()

            ids.append(chunk_id)
            metadatas.append(metadata)

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(
            f"Indexed {min(start + BATCH_SIZE, len(chunks))}"
            f"/{len(chunks)} chunks"
        )

    manifest[file_path.name] = file_hash
    save_manifest(manifest)

    print(f"Successfully indexed: {file_path.name}")


def index_all_books():
    books = get_all_books()

    if not books:
        print("\nNo PDF books found in documents/.")
        return

    for book in books:
        index_book(book)


def retrieve_context(question):
    query_embedding = embedding_model.encode(
        [question],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=TOP_K,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    contexts = []

    if not results["documents"]:
        return contexts

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    print("\nRetrieval results:")

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        similarity = 1 - distance

        print(
            f"Similarity: {similarity:.3f} | "
            f"Page: {metadata['page']} | "
            f"Book: {metadata['book_name']}"
        )

        if similarity < MIN_SIMILARITY:
            continue

        contexts.append({
            "text": document,
            "metadata": metadata,
            "similarity": similarity
        })

    return contexts



def generate_answer(question, contexts):

    if not contexts:
        return "यह जानकारी अपलोड की गई पुस्तकों में नहीं मिली।"

    context_parts = []

    for index, item in enumerate(contexts, start=1):
        metadata = item["metadata"]

        context_parts.append(
            f"""
[Passage {index}]
Book: {metadata.get('book_name', 'Unknown')}
Page: {metadata.get('page', 'Unknown')}
Content:
{item['text']}
"""
        )

    context_text = "\n".join(context_parts)

    system_prompt = """
You are Granth AI, a book-based question answering assistant.

STRICT INSTRUCTIONS:

1. Answer ONLY using the provided book passages.
2. Never use outside knowledge or assumptions.
3. Never invent facts, names, dates, quotations or page numbers.
4. First check whether the passages contain the answer.
5. If the answer is not clearly available, reply exactly:
   यह जानकारी अपलोड की गई पुस्तकों में नहीं मिली।
6. If the question is in Hindi, answer in natural and simple Hindi.
7. If the question is in English, answer in English.
8. Do not translate Hindi names incorrectly.
9. Do not provide internal reasoning or thinking.
10. Do not write phrases like:
    "Let me think", "I need to check", "The user is asking".
11. Give only the final answer.
12. Mention the source book and page number when supported by context.

ANSWER FORMAT:

उत्तर: [Direct and concise answer]

स्रोत: [Book name], पृष्ठ [Page number]

If the information is unavailable, return only:
यह जानकारी अपलोड की गई पुस्तकों में नहीं मिली।
"""

    user_prompt = f"""
नीचे पुस्तक से प्राप्त अंश दिए गए हैं।

पुस्तक के अंश:
{context_text}

प्रश्न:
{question}

निर्देश:
पुस्तक के अंशों को ध्यान से पढ़कर केवल अंतिम उत्तर दो।
यदि उत्तर अंशों में मौजूद नहीं है, तो निर्धारित fallback उत्तर दो।
"""

    try:

        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            think=False,
            options={
                "temperature": 0,
                "num_predict": 300
            }
        )

        message = response.get("message", {})

        answer = message.get("content", "").strip()

        if not answer:
            print("Ollama returned an empty response.")
            print("Debug response:", response)

            return "माफ़ कीजिए, उत्तर generate नहीं हो पाया।"

        return answer

    except Exception as error:

        print(f"Ollama error: {error}")

        return (
            "माफ़ कीजिए, स्थानीय AI मॉडल से "
            "उत्तर प्राप्त नहीं हो पाया।"
        )


def ask_question(question):
    contexts = retrieve_context(question)

    answer = generate_answer(
        question,
        contexts
    )

    print("\n" + "=" * 55)
    print("GRANTH AI ANSWER")
    print("=" * 55)

    print(answer)

    if contexts:
        print("\nSOURCES:")

        seen = set()

        for item in contexts:
            metadata = item["metadata"]

            source = (
                metadata["book_name"],
                metadata["page"]
            )

            if source in seen:
                continue

            seen.add(source)

            print(
                f"- {metadata['book_name']} "
                f"| Page {metadata['page']}"
            )

    print("=" * 55)
