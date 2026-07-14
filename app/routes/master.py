from flask import Blueprint, jsonify

master_bp = Blueprint("master", __name__)

@master_bp.route("/api/health")
def health():
    return jsonify({"status": "ok"})
