from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# Import your project files
from scrapper import run_scraper
from models import (
    init_db,
    get_all_builds,
    add_build,
    delete_build,
    add_retailer,
    delete_retailer,
    get_retailers,
    update_notification_settings,
    get_notification_settings,
)

# Create the Flask app (points static folder to React build)
app = Flask(
    __name__,
    static_folder="../frontend/build",
    static_url_path="/"
)

CORS(app)

# ==============================
#   INITIALIZE DATABASE
# ==============================
@app.before_first_request
def setup():
    init_db()


# ==============================
#   API ROUTES
# ==============================

@app.route("/api/builds", methods=["GET"])
def api_get_builds():
    return jsonify(get_all_builds())


@app.route("/api/builds", methods=["POST"])
def api_add_build():
    data = request.json
    add_build(data)
    return jsonify({"status": "success"}), 201


@app.route("/api/builds/<int:build_id>", methods=["DELETE"])
def api_delete_build(build_id):
    delete_build(build_id)
    return jsonify({"status": "deleted"})


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    result = run_scraper()
    return jsonify(result)


@app.route("/api/retailers", methods=["GET"])
def api_get_retailers():
    return jsonify(get_retailers())


@app.route("/api/retailers", methods=["POST"])
def api_add_retailer():
    data = request.json
    add_retailer(data)
    return jsonify({"status": "added"})


@app.route("/api/retailers/<int:retailer_id>", methods=["DELETE"])
def api_delete_retailer(retailer_id):
    delete_retailer(retailer_id)
    return jsonify({"status": "deleted"})


@app.route("/api/notification-settings", methods=["GET"])
def api_get_notifications():
    return jsonify(get_notification_settings())


@app.route("/api/notification-settings", methods=["POST"])
def api_update_notifications():
    data = request.json
    update_notification_settings(data)
    return jsonify({"status": "updated"})


# ==================================================
#   SERVE REACT FRONTEND (very important for Render)
# ==================================================
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    root_dir = app.static_folder

    if path != "" and os.path.exists(os.path.join(root_dir, path)):
        return send_from_directory(root_dir, path)

    # Default: always return index.html so React Router works
    return send_from_directory(root_dir, "index.html")


# ==============================
#   RUN LOCAL DEVELOPMENT
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
