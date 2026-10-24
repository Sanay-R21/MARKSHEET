"""Flask web app for Student Marksheet Automation (uses marksheet.py)."""

import io
import os
import tempfile
import zipfile

from flask import Flask, request, send_file, render_template_string

import marksheet as ms

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Student Marksheet Automation</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1rem; }
    button { padding: .5rem 1rem; margin-right: .5rem; cursor: pointer; }
    table { border-collapse: collapse; width: 100%; font-size: .9rem; }
    th, td { border: 1px solid #ddd; padding: .35rem .5rem; text-align: left; }
    th { background: #f4f4f4; }
    .err { color: #b00020; }
    .wrap { overflow-x: auto; }
  </style>
</head>
<body>
  <h1>Student Marksheet Automation</h1>

  <div class="card">
    <p>CSV format: <code>roll,name,Maths,Physics,Chemistry,English,Computer</code></p>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".csv" required>
      <p>
        <button type="submit" formaction="/preview">Preview results</button>
        <button type="submit" formaction="/download">Download marksheets (ZIP)</button>
      </p>
    </form>
    <p><a href="/sample">Download sample CSV</a></p>
  </div>

  {% if error %}<p class="err">{{ error }}</p>{% endif %}

  {% if summary %}
  <div class="card">
    <h2>Class summary</h2>
    <p>Students: {{ summary.count }} | Pass: {{ summary.passed }} | Fail: {{ summary.failed }}
       | Average: {{ summary.average }}%</p>
    {% if bad %}
      <p class="err">Invalid rows skipped: {{ bad|length }}</p>
      <ul>{% for n, why in bad[:10] %}<li>Row {{ n }}: {{ why }}</li>{% endfor %}</ul>
    {% endif %}
  </div>
  <div class="card wrap">
    <table>
      <tr><th>Rank</th><th>Roll</th><th>Name</th><th>Total</th><th>%</th><th>Grade</th><th>Result</th></tr>
      {% for s in students %}
      <tr><td>{{ s.rank }}</td><td>{{ s.roll }}</td><td>{{ s.name }}</td>
          <td>{{ "%g"|format(s.total) }}</td><td>{{ s.pct }}</td><td>{{ s.grade }}</td><td>{{ s.result }}</td></tr>
      {% endfor %}
    </table>
  </div>
  {% endif %}
</body>
</html>
"""


def process_upload():
    """Read the uploaded CSV and return (students, bad_rows, error)."""
    uploaded = request.files.get("file")

    if not uploaded or not uploaded.filename:
        return None, None, "Please choose a CSV file."

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "students.csv")
        uploaded.save(path)

        try:
            students, bad = ms.load_csv(path)
        except (OSError, UnicodeDecodeError) as exc:
            return None, None, f"Could not read file: {exc}"

    if not students:
        reasons = "; ".join(f"Row {n}: {r}" for n, r in bad[:5])
        return None, None, f"No valid student rows found. {reasons}"

    return ms.assign_ranks(students), bad, None


@app.route("/", methods=["GET"])
def home():
    return render_template_string(PAGE)


@app.route("/healthz")
def health():
    return "ok"


@app.route("/preview", methods=["POST"])
def preview():
    students, bad, error = process_upload()

    if error:
        return render_template_string(PAGE, error=error), 400

    count = len(students)
    passed = sum(s["result"] == "PASS" for s in students)
    summary = {
        "count": count,
        "passed": passed,
        "failed": count - passed,
        "average": round(sum(s["pct"] for s in students) / count, 2),
    }

    return render_template_string(PAGE, students=students, bad=bad, summary=summary)


@app.route("/download", methods=["POST"])
def download():
    students, bad, error = process_upload()

    if error:
        return render_template_string(PAGE, error=error), 400

    buffer = io.BytesIO()

    with tempfile.TemporaryDirectory() as tmp:
        folder = os.path.join(tmp, "marksheets")
        ms.save_all(students, folder)

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for name in sorted(os.listdir(folder)):
                zf.write(os.path.join(folder, name), arcname=name)

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="marksheets.zip",
    )


@app.route("/sample")
def sample():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.csv")
        ms.make_demo_csv(path, 10)
        with open(path, "rb") as f:
            data = io.BytesIO(f.read())

    return send_file(
        data, mimetype="text/csv", as_attachment=True, download_name="sample_students.csv"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
