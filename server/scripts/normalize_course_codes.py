import os
import re
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient

def normalize_course_code(code_raw):
    """Normalize a single course code (e.g. 'CT 101' -> 'CT101')."""
    return re.sub(r"[\s\-]", "", str(code_raw)).upper()

def main():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = os.getenv("QDRANT_COLLECTION", "aura_documents")
    
    print(f"Connecting to Qdrant at {qdrant_url}...")
    try:
        client = QdrantClient(url=qdrant_url)
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        sys.exit(1)
        
    print(f"Scrolling points in collection: {collection_name}")
    
    has_more = True
    next_page_offset = None
    updated_count = 0
    total_processed = 0
    
    while has_more:
        # scroll returns (points, next_page_offset)
        points, next_page_offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=next_page_offset,
            with_payload=True,
            with_vectors=False
        )
        
        for point in points:
            total_processed += 1
            payload = point.payload
            
            if not payload or "course_code" not in payload:
                continue
                
            course_code_raw = payload["course_code"]
            if not course_code_raw:
                continue
                
            needs_update = False
            if isinstance(course_code_raw, list):
                new_codes = []
                for c in course_code_raw:
                    norm = normalize_course_code(c)
                    if norm != c:
                        needs_update = True
                    new_codes.append(norm)
                new_val = new_codes
            else:
                new_val = normalize_course_code(course_code_raw)
                if new_val != course_code_raw:
                    needs_update = True
                    
            if needs_update:
                # Update the payload for this point
                client.set_payload(
                    collection_name=collection_name,
                    payload={"course_code": new_val},
                    points=[point.id]
                )
                updated_count += 1
                print(f"Updated point {point.id}: {course_code_raw} -> {new_val}")
                
        if next_page_offset is None:
            has_more = False

    print(f"Finished! Processed {total_processed} points, updated {updated_count} points.")

if __name__ == "__main__":
    main()
