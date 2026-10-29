import requests
import time
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SAMPLE_PDF = Path("../samples/sample_text_contract.pdf")

def run_test():
    print(f"=== 1. Uploading {SAMPLE_PDF.name} ===")
    with open(SAMPLE_PDF, "rb") as f:
        files = {"file": (SAMPLE_PDF.name, f, "application/pdf")}
        res = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    
    print("Upload status code:", res.status_code)
    if res.status_code != 200:
        print("Upload failed:", res.text)
        return
    
    status_data = res.json()
    doc_id = status_data["document_id"]
    print("Document ID:", doc_id)
    print("Initial status:", status_data["status"], f"({status_data['progress_percentage']}%)")

    print("\n=== 2. Polling Processing Status ===")
    for _ in range(60):
        time.sleep(2)
        poll_res = requests.get(f"{BASE_URL}/api/documents/{doc_id}/status")
        poll_data = poll_res.json()
        print(f"[{poll_data['status'].upper()}] {poll_data['progress_percentage']}% - {poll_data['current_step_message']}")
        if poll_data["status"] == "ready":
            break
        elif poll_data["status"] == "failed":
            print("Processing failed:", poll_data.get("error"))
            return

    print("\n=== 3. Fetching Stage 1 Analysis Card ===")
    analysis_res = requests.get(f"{BASE_URL}/api/documents/{doc_id}/analysis")
    print("Analysis status code:", analysis_res.status_code)
    analysis = analysis_res.json()
    print("Document Title:", analysis["metadata"].get("document_title"))
    print("Document Type:", analysis["metadata"].get("document_type"))
    print("Executive Summary:\n ", analysis.get("executive_summary"))
    print("Key Points count:", len(analysis.get("key_points", [])))
    for kp in analysis.get("key_points", [])[:3]:
        print(f" - [{kp.get('category')}]: {kp.get('point')}")
    print("Outline count:", len(analysis.get("outline", [])))
    print("Entities count:", len(analysis.get("entities", [])))

    print("\n=== 4. Testing Stage 2 Chat (SSE Stream) ===")
    chat_payload = {
        "document_id": doc_id,
        "question": "What is the governing law and what are the confidentiality obligations?",
        "conversation_history": []
    }
    with requests.post(f"{BASE_URL}/api/chat", json=chat_payload, stream=True) as chat_res:
        print("Chat status code:", chat_res.status_code)
        tokens = []
        sources = []
        follow_ups = []
        for line in chat_res.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                print(f"RAW: {line_str}")

        print("\n\nTokens count:", len(tokens))
        print("Sources count:", len(sources))
        print("Suggested Follow-ups:", follow_ups)

    print("\n=== E2E Backend Verification Complete! ===")

if __name__ == "__main__":
    run_test()
