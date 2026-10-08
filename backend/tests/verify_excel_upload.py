import urllib.request
import json
from pathlib import Path

def test_excel_and_csv_samples():
    base_dir = Path(__file__).resolve().parent.parent.parent
    sample_dir = base_dir / "sample_data"
    xlsx_path = sample_dir / "retail_sales_3500_records.xlsx"
    csv_path = sample_dir / "retail_sales_3500_records.csv"

    assert xlsx_path.exists(), f"Missing {xlsx_path}"
    assert csv_path.exists(), f"Missing {csv_path}"

    print(f"Found sample files:")
    print(f" - CSV: {csv_path} ({csv_path.stat().st_size / 1024:.1f} KB)")
    print(f" - Excel: {xlsx_path} ({xlsx_path.stat().st_size / 1024:.1f} KB)")

    # 1. Test Excel upload
    with open(xlsx_path, "rb") as f:
        excel_bytes = f.read()

    boundary = "----WebKitFormBoundaryExcelTest77"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="retail_sales_3500_records.xlsx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode("utf-8") + excel_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        "http://localhost:8000/api/v1/datasets/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as resp:
        excel_res = json.loads(resp.read().decode("utf-8"))

    print("\n[+] Excel Upload Succeeded:")
    print(f" - Dataset ID: {excel_res['dataset_id']}")
    print(f" - Filename: {excel_res['filename']}")
    print(f" - Rows: {excel_res['row_count']}")
    print(f" - Columns: {excel_res['column_count']}")
    assert excel_res["row_count"] == 3500
    assert excel_res["column_count"] == 14

    # 2. Test Discovery Engine on the 3,500-row Excel dataset
    print("\nRunning Discovery Engine on 3,500-row Excel dataset...")
    disc_req = urllib.request.Request(
        "http://localhost:8000/api/v1/discovery",
        data=json.dumps({"dataset_id": excel_res["dataset_id"], "max_findings": 5}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(disc_req) as resp:
        disc_res = json.loads(resp.read().decode("utf-8"))

    print("\n[+] Discovery Results:")
    print(f" - Candidates Examined: {disc_res['summary']['candidates_examined']}")
    print(f" - Findings Returned: {disc_res['summary']['findings_returned']}")
    print(f" - Compute Time: {disc_res['summary']['execution_time_ms']} ms")
    
    for i, f in enumerate(disc_res["findings"], 1):
        title = f['title'].encode('ascii', errors='replace').decode('ascii')
        expl = f['explanation'].encode('ascii', errors='replace').decode('ascii')
        print(f"\n{i}. [{f['type'].upper()}] {title}")
        print(f"   Columns: {f['columns']}")
        print(f"   Metric: {f['metric']}")
        print(f"   Explanation: {expl}")
        if f.get("caution"):
            caut = f['caution'].encode('ascii', errors='replace').decode('ascii')
            print(f"   Caution: {caut}")

    assert disc_res["summary"]["findings_returned"] > 0
    print("\n[SUCCESS] Excel dataset upload and Questionless Discovery fully verified!")

if __name__ == "__main__":
    test_excel_and_csv_samples()
