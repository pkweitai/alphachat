import os
from langchain_community.vectorstores import Chroma  # Updated import
from google.generativeai import configure, embed_content  # Correct way to use Google AI embeddings

# Path to ChromaDB vector store
VECTORSTORE_JIRA_FILE_PATH = "vector/vector.db"

# Configure Google Generative AI
configure(api_key=os.getenv("GOOGLE_API_KEY"))  # Ensure the API key is set in environment variables



def check_chroma_db():
    """Check if ChromaDB contains stored JIRA tickets."""
    vectorstore = Chroma(persist_directory=VECTORSTORE_JIRA_FILE_PATH)

    num_docs = vectorstore._collection.count()
    print(f"📌 Total Documents in ChromaDB: {num_docs}")

    if num_docs > 0:
        stored_docs = vectorstore._collection.get(include=['documents', 'metadatas'])
        for idx, (doc, meta) in enumerate(zip(stored_docs["documents"], stored_docs["metadatas"])):
            print(f"\n--- Document {idx+1} ---")
            print(f"Content: {doc}")
            print(f"Metadata: {meta}")
    else:
        print("⚠️ No documents found in ChromaDB.")

if __name__ == "__main__":
    check_chroma_db()


def get_google_embedding(text):
    """Generate embeddings using Google Generative AI"""
    response = embed_content(model="models/embedding-001", content=text)
    return response['embedding'] if response else None

def test_vector_database():
    """Test retrieving all stored documents from ChromaDB."""
    
    # Load stored embeddings from ChromaDB
    vectorstore = Chroma(persist_directory=VECTORSTORE_JIRA_FILE_PATH, embedding_function=get_google_embedding)

    # Get number of stored documents
    num_docs = vectorstore._collection.count()
    print(f"Total documents stored in ChromaDB: {num_docs}")

    # Retrieve all stored documents
    if num_docs > 0:
        all_docs = vectorstore._collection.get(include=['documents', 'metadatas'])
        for idx, (doc, meta) in enumerate(zip(all_docs["documents"], all_docs["metadatas"])):
            print(f"\nDocument {idx+1}:")
            print(f"Content: {doc}")
            print(f"Metadata: {meta}")

        print("\n✅ Test Passed: Successfully retrieved all stored documents.")
    else:
        print("\n❌ Test Failed: No documents found in ChromaDB.")

if __name__ == "__main__":
    check_chroma_db()
