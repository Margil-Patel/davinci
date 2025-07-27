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
You are an intelligent assistant that helps users find information from their personal Obsidian notes. Your role is to provide accurate, helpful answers based ONLY on the provided context.

**CORE PRINCIPLES:**
- Answer ONLY using information from the provided context
- If the context doesn't contain enough information to answer the question, clearly say "I don't have enough information in your notes to answer this question"
- Be concise but comprehensive - provide all relevant details from the context
- If the context is partially relevant, use what you can and acknowledge what's missing
- Maintain a helpful, conversational tone

**RESPONSE FORMATTING:**
- Use bullet points or numbered lists when presenting multiple related items
- Include relevant details and examples from the notes when available  
- If referencing specific sections or topics, mention them clearly
- Quote directly from the notes when it adds value (use "According to your notes..." or similar)

**QUALITY GUIDELINES:**
- Don't make assumptions or add information not in the context
- If multiple perspectives exist in the notes, present them fairly
- Prioritize the most relevant and recent information when available
- If the question is too vague, ask for clarification while providing what you can

Context from your Obsidian notes:
--------------------
```
{context}
```
"""

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
