import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

DEFAULT_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "data.json"
)


def load_data(data_file):
    """Read the JSON data file. Returns a fresh structure if it doesn't exist yet."""
    if not os.path.exists(data_file):
        return {"vehicles": [], "next_vehicle_id": 1, "next_service_id": 1}
    with open(data_file, "r") as f:
        return json.load(f)


def save_data(data_file, data):
    """Write the data structure back to the JSON file."""
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2)


def get_git_commit():
    """
    Figure out the current git commit to show in the footer.
    Order of preference:
      1. GIT_COMMIT env var (set manually, or by CI/Docker build)
      2. RENDER_GIT_COMMIT env var (Render sets this automatically for many deploys)
      3. commit_sha.txt file (written during `docker build`)
      4. "dev" fallback for local runs
    """
    commit = os.environ.get("GIT_COMMIT") or os.environ.get("RENDER_GIT_COMMIT")
    if commit:
        return commit[:7]
    commit_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit_sha.txt")
    if os.path.exists(commit_file):
        with open(commit_file) as f:
            sha = f.read().strip()
            if sha:
                return sha[:7]
    return "dev"


def create_app(data_file=None):
    """Application factory. Passing data_file lets tests use an isolated file."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["DATA_FILE"] = data_file or DEFAULT_DATA_FILE

    @app.context_processor
    def inject_globals():
        return {"git_commit": get_git_commit()}

    def _data():
        return load_data(app.config["DATA_FILE"])

    def _save(data):
        save_data(app.config["DATA_FILE"], data)

    def find_vehicle(data, vehicle_id):
        return next((v for v in data["vehicles"] if v["id"] == vehicle_id), None)

    def upcoming_services(data, days=30):
        """Services due within `days`, including overdue ones (negative days_remaining)."""
        upcoming = []
        today = datetime.today().date()
        for v in data["vehicles"]:
            for s in v.get("services", []):
                due = s.get("next_due_date")
                if not due:
                    continue
                try:
                    due_date = datetime.strptime(due, "%Y-%m-%d").date()
                except ValueError:
                    continue
                delta = (due_date - today).days
                if delta <= days:
                    upcoming.append({"vehicle": v, "service": s, "days_remaining": delta})
        upcoming.sort(key=lambda x: x["days_remaining"])
        return upcoming

    # ---------- Pages ----------

    @app.route("/")
    def dashboard():
        data = _data()
        return render_template(
            "index.html",
            vehicle_count=len(data["vehicles"]),
            upcoming=upcoming_services(data),
        )

    @app.route("/vehicles")
    def list_vehicles():
        data = _data()
        return render_template("vehicles.html", vehicles=data["vehicles"])

    @app.route("/vehicles/add", methods=["GET", "POST"])
    def add_vehicle():
        if request.method == "POST":
            data = _data()
            vehicle = {
                "id": data["next_vehicle_id"],
                "make": request.form["make"].strip(),
                "model": request.form["model"].strip(),
                "year": request.form.get("year", "").strip(),
                "license_plate": request.form.get("license_plate", "").strip(),
                "owner_name": request.form.get("owner_name", "").strip(),
                "services": [],
            }
            data["vehicles"].append(vehicle)
            data["next_vehicle_id"] += 1
            _save(data)
            flash("Vehicle added successfully.", "success")
            return redirect(url_for("vehicle_detail", vehicle_id=vehicle["id"]))
        return render_template("add_vehicle.html")

    @app.route("/vehicles/<int:vehicle_id>")
    def vehicle_detail(vehicle_id):
        data = _data()
        vehicle = find_vehicle(data, vehicle_id)
        if not vehicle:
            return render_template("404.html"), 404
        services = sorted(vehicle.get("services", []), key=lambda s: s["date"], reverse=True)
        return render_template("vehicle_detail.html", vehicle=vehicle, services=services)

    @app.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
    def edit_vehicle(vehicle_id):
        data = _data()
        vehicle = find_vehicle(data, vehicle_id)
        if not vehicle:
            return render_template("404.html"), 404
        if request.method == "POST":
            vehicle["make"] = request.form["make"].strip()
            vehicle["model"] = request.form["model"].strip()
            vehicle["year"] = request.form.get("year", "").strip()
            vehicle["license_plate"] = request.form.get("license_plate", "").strip()
            vehicle["owner_name"] = request.form.get("owner_name", "").strip()
            _save(data)
            flash("Vehicle updated.", "success")
            return redirect(url_for("vehicle_detail", vehicle_id=vehicle_id))
        return render_template("edit_vehicle.html", vehicle=vehicle)

    @app.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
    def delete_vehicle(vehicle_id):
        data = _data()
        data["vehicles"] = [v for v in data["vehicles"] if v["id"] != vehicle_id]
        _save(data)
        flash("Vehicle deleted.", "info")
        return redirect(url_for("list_vehicles"))

    @app.route("/vehicles/<int:vehicle_id>/services/add", methods=["GET", "POST"])
    def add_service(vehicle_id):
        data = _data()
        vehicle = find_vehicle(data, vehicle_id)
        if not vehicle:
            return render_template("404.html"), 404
        if request.method == "POST":
            service = {
                "id": data["next_service_id"],
                "service_type": request.form["service_type"].strip(),
                "date": request.form["date"].strip(),
                "cost": request.form.get("cost", "").strip(),
                "notes": request.form.get("notes", "").strip(),
                "next_due_date": request.form.get("next_due_date", "").strip(),
            }
            vehicle.setdefault("services", []).append(service)
            data["next_service_id"] += 1
            _save(data)
            flash("Service record added.", "success")
            return redirect(url_for("vehicle_detail", vehicle_id=vehicle_id))
        return render_template("add_service.html", vehicle=vehicle)

    @app.route("/vehicles/<int:vehicle_id>/services/<int:service_id>/edit", methods=["GET", "POST"])
    def edit_service(vehicle_id, service_id):
        data = _data()
        vehicle = find_vehicle(data, vehicle_id)
        if not vehicle:
            return render_template("404.html"), 404
        service = next((s for s in vehicle.get("services", []) if s["id"] == service_id), None)
        if not service:
            return render_template("404.html"), 404
        if request.method == "POST":
            service["service_type"] = request.form["service_type"].strip()
            service["date"] = request.form["date"].strip()
            service["cost"] = request.form.get("cost", "").strip()
            service["notes"] = request.form.get("notes", "").strip()
            service["next_due_date"] = request.form.get("next_due_date", "").strip()
            _save(data)
            flash("Service record updated.", "success")
            return redirect(url_for("vehicle_detail", vehicle_id=vehicle_id))
        return render_template("edit_service.html", vehicle=vehicle, service=service)

    @app.route("/vehicles/<int:vehicle_id>/services/<int:service_id>/delete", methods=["POST"])
    def delete_service(vehicle_id, service_id):
        data = _data()
        vehicle = find_vehicle(data, vehicle_id)
        if vehicle:
            vehicle["services"] = [s for s in vehicle.get("services", []) if s["id"] != service_id]
            _save(data)
        flash("Service record deleted.", "info")
        return redirect(url_for("vehicle_detail", vehicle_id=vehicle_id))

    # ---------- APIs ----------

    @app.route("/api/vehicles")
    def api_vehicles():
        data = _data()
        return jsonify(data["vehicles"])

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
