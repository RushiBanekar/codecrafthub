import json
import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = "courses.json"
VALID_STATUS = ["Not Started", "In Progress", "Completed"]


def load():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save(courses):
    with open(DATA_FILE, "w") as f:
        json.dump(courses, f, indent=2)


def find(courses, cid):
    return next((c for c in courses if c["id"] == cid), None)


def validate(data, partial=False):
    if not data:
        return "Request body must be JSON"
    if not partial:
        for field in ("name", "target_date", "status"):
            if not data.get(field):
                return f"'{field}' is required"
    if "status" in data and data["status"] not in VALID_STATUS:
        return f"'status' must be one of {VALID_STATUS}"
    if "target_date" in data:
        try:
            datetime.strptime(data["target_date"], "%Y-%m-%d")
        except ValueError:
            return "'target_date' must be YYYY-MM-DD"
    return None


@app.route("/api/courses", methods=["GET"])
def get_courses():
    return jsonify(load()), 200


@app.route("/api/courses/<int:cid>", methods=["GET"])
def get_course(cid):
    course = find(load(), cid)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(course), 200


@app.route("/api/courses", methods=["POST"])
def add_course():
    data = request.get_json(silent=True)
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400
    courses = load()
    new_id = max((c["id"] for c in courses), default=0) + 1
    course = {
        "id": new_id,
        "name": data["name"],
        "description": data.get("description", ""),
        "target_date": data["target_date"],
        "status": data["status"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    courses.append(course)
    save(courses)
    return jsonify(course), 201


@app.route("/api/courses/<int:cid>", methods=["PUT"])
def update_course(cid):
    data = request.get_json(silent=True)
    error = validate(data, partial=True)
    if error:
        return jsonify({"error": error}), 400
    courses = load()
    course = find(courses, cid)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    for field in ("name", "description", "target_date", "status"):
        if field in data:
            course[field] = data[field]
    save(courses)
    return jsonify(course), 200


@app.route("/api/courses/<int:cid>", methods=["DELETE"])
def delete_course(cid):
    courses = load()
    course = find(courses, cid)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    courses.remove(course)
    save(courses)
    return jsonify({"message": "Course deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
