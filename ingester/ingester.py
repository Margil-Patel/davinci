import os
import re
from pathlib import Path
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import uuid

# === Configuration ===
VAULT_PATH = "C:/Users/Margil/Documents/MyNotes/drone"  # Your Obsidian folder
CHROMA_PATH = os.path.join("chroma_db", uuid.uuid5(uuid.NAMESPACE_DNS, VAULT_PATH).hex)
COLLECTION_NAME = "obsidian_notes"

# === Initialize ChromaDB ===
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# === Clean Obsidian Wiki-Style Links ===
def clean_obsidian(text):
    text = re.sub(r'!\[\[.*?\]\]', '', text)              # Remove embedded media
    text = re.sub(r'\[\[([^\|\]]+)\|?([^\]]*)\]\]', lambda m: m.group(2) if m.group(2) else m.group(1), text)  # [[Page|Alias]] or [[Page]]
    return text

# === Chunk and Upsert Function ===
def process_and_upsert_md(file_path):
    try:
        loader = UnstructuredMarkdownLoader(file_path)
        documents = loader.load()
        for doc in documents:
            doc.page_content = clean_obsidian(doc.page_content)
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        # Use file path and chunk index for unique IDs
        ids = [f"{os.path.relpath(file_path, VAULT_PATH)}_chunk_{i}" for i in range(len(chunks))]
        embeddings = model.encode(texts)
        collection.upsert(
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings.tolist(),
            ids=ids
        )
        print(f"✅ Ingested {len(chunks)} chunks from {file_path} into ChromaDB collection '{COLLECTION_NAME}'.")
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

# === Initial Bulk Ingestion ===
def initial_ingestion():
    """Process all existing markdown files in the vault"""
    print(f"🔍 Starting initial ingestion from {VAULT_PATH}...")
    
    if not os.path.exists(VAULT_PATH):
        print(f"❌ Vault path does not exist: {VAULT_PATH}")
        print(f"Please make sure the path exists and contains markdown files.")
        return
    
    markdown_files = []
    for root, dirs, files in os.walk(VAULT_PATH):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
    
    if not markdown_files:
        print(f"📭 No markdown files found in {VAULT_PATH}")
        print(f"Please add some .md files to your Obsidian vault.")
        return
    
    print(f"📚 Found {len(markdown_files)} markdown files. Processing...")
    
    for file_path in markdown_files:
        process_and_upsert_md(file_path)
    
    print(f"✅ Initial ingestion complete! Processed {len(markdown_files)} files.")

# === Watchdog Event Handler ===
class MarkdownEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            print(f"[Created] {event.src_path}")
            process_and_upsert_md(event.src_path)
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            print(f"[Modified] {event.src_path}")
            process_and_upsert_md(event.src_path)

if __name__ == "__main__":
    # Run initial ingestion first
    initial_ingestion()
    
    # Then start watching for changes
    event_handler = MarkdownEventHandler()
    observer = Observer()
    observer.schedule(event_handler, VAULT_PATH, recursive=True)
    observer.start()
    print(f"👀 Watching '{VAULT_PATH}' for Markdown file changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
