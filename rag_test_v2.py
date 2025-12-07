import asyncio
import sys
import os

# Add server directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "synapse-server"))

from ai_service import chat_with_ai, vector_db

async def test_cot():
    print("--- Testing Chain of Thought & Citation ---")
    query = "예산 관련해서 어떤 이야기가 있었어?"
    
    # Pre-check retrieval
    print(f"Querying vector db for: {query}")
    results = vector_db.query(query, n_results=1)
    print(f"Vector DB Results: {results}")

    # Test Chat
    print("\nSending query to AI Service...")
    response = await chat_with_ai(query)
    
    print("\n--- AI Response (JSON) ---")
    print(response)
    
    if isinstance(response, dict):
        if "thought" in response and "sources" in response:
            print("\n[PASS] Response structure is correct.")
            print(f"Thinking Process: {response['thought'][:50]}...")
            print(f"Sources: {response['sources']}")
        else:
            print("\n[FAIL] Missing 'thought' or 'sources' keys.")
    else:
        print("\n[FAIL] Response is not a dict.")

if __name__ == "__main__":
    asyncio.run(test_cot())
