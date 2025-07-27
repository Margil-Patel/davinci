from flask import Flask, request, jsonify
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from flask_cors import CORS
import os
import uuid

# === ChromaDB Setup ===
VAULT_PATH = "C:/Users/Margil/Documents/MyNotes/drone"  # Your Obsidian folder
CHROMA_PATH = os.path.join("chroma_db", uuid.uuid5(uuid.NAMESPACE_DNS, VAULT_PATH).hex)
COLLECTION_NAME = "obsidian_notes"
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

app = Flask(__name__)
CORS(app, origins=["*"])

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    results = collection.query(
        query_texts=[query],
        n_results=2,
        include=["documents", "distances", "metadatas"]
    )

    print(results)

    documents = results["documents"][0]

    if not documents or all(doc.strip() == "" for doc in documents):
        return jsonify({'answer': "❌ No matching content found in your Obsidian notes."})

    # === Prepare Prompt for GPT ===
    context = "\n---\n".join(documents)

    system_prompt = f"""
You are an assistant that answers questions using only the provided notes context.

Rules:
- Only use information from the context below
- If the context doesn't have enough information, say "I don't have enough information in your notes to answer this"
- Be helpful and conversational

Context from your notes:
{context}
"""
    print(system_prompt)

    client = OpenAI(
        base_url = 'http://localhost:11434/v1',
        api_key='ollama', # required, but unused
    )
    response = client.chat.completions.create(
        model="llama3.2:1b",  # or gpt-3.5-turbo
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )

    answer = response.choices[0].message.content
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
