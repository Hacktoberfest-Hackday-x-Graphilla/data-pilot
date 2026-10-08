import urllib.request
import json
import os
from pathlib import Path

def test_live_discovery():
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    csv_path = Path(__file__).parent / 'sample_data.csv'
    with open(csv_path, 'rb') as f:
        csv_bytes = f.read()

    body = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="file"; filename="sample_data.csv"\r\n'
        'Content-Type: text/csv\r\n\r\n'
    ).encode('utf-8') + csv_bytes + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request(
        'http://localhost:8000/api/v1/datasets/upload',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    with urllib.request.urlopen(req) as resp:
        upload_res = json.loads(resp.read().decode('utf-8'))

    print('Upload result:', upload_res)
    dataset_id = upload_res['dataset_id']

    # 2. Call discovery endpoint
    disc_req = urllib.request.Request(
        'http://localhost:8000/api/v1/discovery',
        data=json.dumps({'dataset_id': dataset_id, 'max_findings': 5}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(disc_req) as resp:
        disc_res = json.loads(resp.read().decode('utf-8'))

    print('\n--- DISCOVERY RESPONSE ---')
    print('Dataset ID:', disc_res['dataset_id'])
    print('Summary:', json.dumps(disc_res['summary'], indent=2))
    print(f'Received {len(disc_res["findings"])} findings:')
    for i, f in enumerate(disc_res['findings'], 1):
        title = f['title'].encode('ascii', errors='replace').decode('ascii')
        expl = f['explanation'].encode('ascii', errors='replace').decode('ascii')
        print(f"\n{i}. [{f['type'].upper()}] {title}")
        print(f"   Columns: {f['columns']}")
        print(f"   Metric: {f['metric']}")
        print(f"   Explanation: {expl}")
        if f.get('caution'):
            caut = f['caution'].encode('ascii', errors='replace').decode('ascii')
            print(f"   Caution: {caut}")
        
        viz = f.get('visualization')
        if viz:
            print(f"   [VIZ] Chart Type: {viz['chart_type']}, Title: '{viz['title']}', x_key: {viz['x_key']}, y_key: {viz['y_key']}, Data Points: {len(viz['data'])}")
        else:
            print(f"   [VIZ] None (appropriate for {f['type']})")

    assert disc_res['dataset_id'] == dataset_id
    assert len(disc_res['findings']) > 0
    print('\nLive discovery verification successful!')

if __name__ == '__main__':
    test_live_discovery()
