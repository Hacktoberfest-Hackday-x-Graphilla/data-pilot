import json
import httpx

BASE_URL = "http://127.0.0.1:8000"

def verify():
    with httpx.Client(base_url=BASE_URL, timeout=45.0) as client:
        # 1. Health check
        h = client.get("/health").json()
        print("[1] Health Check:", h)
        assert h["status"] == "healthy"
        assert h["gemini_key_configured"] is True

        # 2. Upload sample_data.csv
        with open("backend/tests/sample_data.csv", "rb") as f:
            up = client.post("/api/v1/datasets/upload", files={"file": ("sample_data.csv", f, "text/csv")}).json()
        print("\n[2] Uploaded Dataset:", up["filename"], f"({up['row_count']} rows, {up['column_count']} cols)")
        ds_id = up["dataset_id"]
        assert up["row_count"] == 13
        assert "region" in up["columns"]
        assert "sales" in up["columns"]

        # 3. Profile dataset
        prof = client.post(f"/api/v1/datasets/{ds_id}/profile").json()
        print(f"[3] Dataset Profile: {len(prof['columns'])} columns detected.")
        assert "sales" in prof["numeric_columns"]
        assert "region" in prof["categorical_columns"]

        # 4. Direct Tool Execution (group_and_compare)
        comp = client.post(
            f"/api/v1/datasets/{ds_id}/tools/execute",
            json={
                "tool_name": "group_and_compare",
                "parameters": {
                    "group_by": "region",
                    "metric_columns": ["sales"],
                    "aggregations": ["mean", "count"]
                }
            }
        ).json()
        print("\n[4] Tool Execution (group_and_compare):")
        for g in comp["data"]["results"]:
            print(f"    Region: {g['group']} -> Mean Sales: ${g.get('sales_mean')}")
        assert comp["success"] is True

        # 5. Investigation Mode ("Find something interesting about this dataset.")
        print("\n[5] Testing Investigation Mode (POST /investigate)...")
        inv = client.post(f"/api/v1/datasets/{ds_id}/investigate").json()
        print("    Investigation Summary:", inv.get("summary"))
        print(f"    Findings Generated ({len(inv.get('findings', []))} findings):")
        for idx, f in enumerate(inv.get("findings", []), 1):
            print(f"      {idx}. [{f['category'].upper()}] {f['title']}: {f['description']}")
        print(f"    Investigation Tool Trace ({len(inv.get('tool_trace', []))} tools executed):")
        for t in inv.get("tool_trace", []):
            print(f"      - {t['tool_name']}: {t['summary']}")
        assert len(inv.get("findings", [])) >= 1
        assert len(inv.get("tool_trace", [])) >= 4

        # 6. Chat Endpoint: "Which region has the highest average sales?"
        print("\n[6] Testing Chat Endpoint (POST /chat)...")
        chat_q = "Which region has the highest average sales?"
        chat_res = client.post(
            f"/api/v1/datasets/{ds_id}/chat",
            json={"question": chat_q}
        ).json()
        print(f"    User Question: '{chat_q}'")
        print(f"    Model Answer:\n    {chat_res.get('answer')}")
        print(f"    Tools Executed by Agent ({len(chat_res.get('tool_trace', []))} tool calls):")
        for t in chat_res.get("tool_trace", []):
            print(f"      - {t['tool_name']} (success={t['success']}): {t['summary']}")
        
        # 7. Chat Endpoint: "Find something interesting about this dataset."
        print("\n[7] Testing Chat Endpoint with Open Investigation...")
        chat_q2 = "Find something interesting about this dataset."
        chat_res2 = client.post(
            f"/api/v1/datasets/{ds_id}/chat",
            json={"question": chat_q2}
        ).json()
        print(f"    User Question: '{chat_q2}'")
        print(f"    Model Answer:\n    {chat_res2.get('answer')}")
        print(f"    Tools Executed by Agent ({len(chat_res2.get('tool_trace', []))} tool calls):")
        for t in chat_res2.get("tool_trace", []):
            print(f"      - {t['tool_name']} (success={t['success']}): {t['summary']}")

        print("\n==========================================")
        print("ALL LIVE VERIFICATION CHECKS COMPLETED!")
        print("==========================================")

if __name__ == "__main__":
    verify()
