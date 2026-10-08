import httpx

BASE_URL = "http://127.0.0.1:8000"

def verify():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health
        h = client.get("/health").json()
        print("[1] Health Check:", h)
        assert h["status"] == "healthy"
        assert h["gemini_model"] == "gemini-2.5-pro"
        assert h["gemini_key_configured"] is True

        # 2. Upload CSV
        with open("backend/tests/sample_data.csv", "rb") as f:
            up = client.post("/api/v1/datasets/upload", files={"file": ("sample_data.csv", f, "text/csv")}).json()
        print("[2] Upload Response:", up)
        ds_id = up["dataset_id"]
        assert up["row_count"] == 8
        assert up["column_count"] == 5

        # 3. Profile Dataset
        prof = client.post(f"/api/v1/datasets/{ds_id}/profile").json()
        print("[3] Profile Summary: rows=", prof["row_count"], "cols=", prof["column_count"])
        assert len(prof["columns"]) == 5
        assert "temperature" in prof["numeric_columns"]

        # 4. Execute calculate_statistics
        stat = client.post(
            f"/api/v1/datasets/{ds_id}/tools/execute",
            json={"tool_name": "calculate_statistics", "parameters": {"columns": ["temperature", "humidity"]}}
        ).json()
        print("[4] calculate_statistics:", stat["success"], "mean temp =", stat["data"]["numeric_stats"]["temperature"]["mean"])
        assert stat["success"] is True

        # 5. Execute group_and_compare
        comp = client.post(
            f"/api/v1/datasets/{ds_id}/tools/execute",
            json={
                "tool_name": "group_and_compare",
                "parameters": {"group_by": "city", "metric_columns": ["temperature"], "aggregations": ["mean"]}
            }
        ).json()
        print("[5] group_and_compare:", comp["success"], "groups =", comp["data"]["total_groups"])
        assert comp["success"] is True

        # 6. Execute detect_anomalies
        anom = client.post(
            f"/api/v1/datasets/{ds_id}/tools/execute",
            json={"tool_name": "detect_anomalies", "parameters": {"columns": ["rainfall"], "method": "iqr"}}
        ).json()
        print("[6] detect_anomalies:", anom["success"], "rainfall outliers =", anom["data"]["anomalies"]["rainfall"]["outlier_count"])
        assert anom["success"] is True

        # 7. Execute create_chart
        chart = client.post(
            f"/api/v1/datasets/{ds_id}/tools/execute",
            json={"tool_name": "create_chart", "parameters": {"chart_type": "bar", "x": "city", "y": "temperature"}}
        ).json()
        print("[7] create_chart:", chart["success"], "points =", len(chart["data"]["data"]))
        assert chart["success"] is True

        # 8. Execute find_correlations
        corr = client.post(
            f"/api/v1/datasets/{ds_id}/tools/execute",
            json={"tool_name": "find_correlations", "parameters": {"columns": ["temperature", "humidity", "rainfall"]}}
        ).json()
        print("[8] find_correlations:", corr["success"], "top pairs =", len(corr["data"]["top_correlated_pairs"]))
        assert corr["success"] is True

        # 9. Get tools schema
        tools = client.get("/api/v1/tools").json()
        print("[9] Available tools:", len(tools["tools"]), "Gemini declarations:", len(tools["gemini_function_declarations"]))
        assert len(tools["tools"]) == 6

        print("\nALL 9 LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    verify()
