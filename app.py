from flask import Flask, request, jsonify, render_template
import pandas as pd
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_json():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    with open(filepath, 'r') as f:
        data = json.load(f)

    label_map = {i: label['name'] for i, label in enumerate(data['categories']['label']['labels'])}

    used_labels = set()
    for item in data['items']:
        for ann in item.get('annotations', []):
            if 'label_id' in ann:
                used_labels.add(ann['label_id'])
    used_labels = sorted(list(used_labels))
    label_names = [label_map[i] for i in used_labels]

    rows = []
    for item in data['items']:
        name = item['id']
        frame = item.get('attr', {}).get('frame', '')
        annotations = item.get('annotations', [])

        counts = {label_map[i]: 0 for i in used_labels}
        for ann in annotations:
            lid = ann.get('label_id')
            if lid in counts:
                counts[label_map[lid]] += 1

        row = {
            "Image Name": name,
            "Frame Number": frame,
            "Total Annotations": len(annotations),
            **counts
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Basic stats per label
    stats = {}
    for label in label_names:
        values = df[label]
        stats[label] = {
            "mean": values.mean(),
            "max": values.max(),
            "min": values.min(),
            "std": values.std(),
            "sum": values.sum()
        }

    response = {
        "columns": df.columns.tolist(),
        "data": df.to_dict(orient='records'),
        "stats": stats
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
