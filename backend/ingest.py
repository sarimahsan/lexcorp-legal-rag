import fitz
import pdfplumber
import re
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

PDF_PATH   = "../data/LexCorp_Law.pdf"
QDRANT_PATH = "qdrant_data"
COLLECTION  = "lexcorp"
EMBED_MODEL = "all-MiniLM-L6-v2"

# ── 1. Parse ──────────────────────────────────────────────

def extract_lexcorp(pdf_path: str) -> list:
    chunks = []
    current_part, current_section, current_section_title = "", "", ""
    current_text, current_page = "", 1

    def save():
        if current_text.strip():
            chunks.append({
                "part":          current_part,
                "section":       current_section,
                "section_title": current_section_title,
                "text":          current_text.strip(),
                "page":          current_page,
                "type":          "text"
            })

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            for table in page.extract_tables():
                if table:
                    save()
                    chunks.append({
                        "part":          current_part,
                        "section":       current_section,
                        "section_title": current_section_title,
                        "text":          table_to_text(table),
                        "page":          page_num,
                        "type":          "table"
                    })

            raw = page.extract_text()
            if not raw:
                continue

            for line in raw.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if re.match(r"^PART\s+(I{1,5}|V?I{0,3}|\d+)\s*:", line, re.IGNORECASE):
                    save()
                    current_part, current_section = line, ""
                    current_section_title, current_text = "", ""
                    current_page = page_num

                elif re.match(r"^\d+\.\d+(\.\d+)?\s+[A-Z]", line):
                    save()
                    current_section = re.match(r"^(\d+\.\d+(?:\.\d+)?)", line).group(1)
                    current_section_title = line
                    current_text, current_page = "", page_num

                elif re.match(r"^Rule\s+\d+\.\d+", line, re.IGNORECASE):
                    save()
                    current_section = line
                    current_section_title = line
                    current_text, current_page = "", page_num

                else:
                    current_text += " " + line

    save()
    return chunks


def table_to_text(table: list) -> str:
    if not table or not table[0]:
        return ""
    headers = [str(h).strip() for h in table[0] if h and str(h).strip()]
    lines = [f"Table — columns: {', '.join(headers)}"]
    for row in table[1:]:
        if not any(row):
            continue
        paired = [f"{h}: {v}" for h, v in zip(headers, row) if v and str(v).strip()]
        if paired:
            lines.append(" | ".join(paired))
    return "\n".join(lines)


# ── 2. Build embed text ───────────────────────────────────

def build_embed_text(chunk: dict) -> str:
    parts = [p for p in [chunk["part"], chunk["section_title"], chunk["text"]] if p]
    return " | ".join(parts)


# ── 3. Embed + upload ─────────────────────────────────────

def ingest(pdf_path: str = PDF_PATH):
    print("Parsing PDF...")
    chunks = extract_lexcorp(pdf_path)
    print(f"  {len(chunks)} chunks extracted")
    print(f"  Parts:    {sorted(set(c['part'] for c in chunks))}")
    print(f"  Sections: {len(set(c['section'] for c in chunks))}")
    print(f"  Tables:   {len([c for c in chunks if c['type'] == 'table'])}")

    print("\nEmbedding chunks...")
    model = SentenceTransformer(EMBED_MODEL)
    embed_texts = [build_embed_text(c) for c in chunks]
    vectors = model.encode(embed_texts, show_progress_bar=True)

    print("\nUploading to Qdrant...")
    client = QdrantClient(path=QDRANT_PATH)

    # recreate collection fresh each run
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

    points = [
        PointStruct(
            id=i,
            vector=vec.tolist(),
            payload={
                "part":          c["part"],
                "section":       c["section"],
                "section_title": c["section_title"],
                "text":          c["text"],
                "page":          c["page"],
                "type":          c["type"]
            }
        )
        for i, (c, vec) in enumerate(zip(chunks, vectors))
    ]

    client.upsert(collection_name=COLLECTION, points=points)
    print(f"\nDone. {len(points)} vectors stored in '{QDRANT_PATH}/'")


if __name__ == "__main__":
    ingest()
