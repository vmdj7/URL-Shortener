from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import random
import string
import os

# Initialize Flask app
app = Flask(__name__)

# Configure PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", 
            "postgresql://vic:vmdj2000@localhost/vlink_db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database model for URL mapping
class URLMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    long_url = db.Column(db.String(2048), nullable=False)

# Function to generate a short URL or use a custom name if provided
def generate_short_url(custom_name=None):
    if custom_name:
        if not URLMapping.query.filter_by(short_url=custom_name).first():
            return custom_name  # Return custom name if unique
        else:
            return None  # Custom name already exists
    while True:
        short_url = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        if not URLMapping.query.filter_by(short_url=short_url).first():
            return short_url

# Route to render the main HTML page
@app.route("/")
def index():
    return render_template("index.html")  # Serve the HTML file as the web interface

# API route to shorten a long URL
@app.route("/shorten", methods=["POST"])
def shorten():
    BASE_URL = request.host_url
    data = request.get_json()
    long_url = data.get("long_url", "").strip()
    custom_name = data.get("custom_name", "").strip()

    if not long_url:
        return jsonify({"error": "Please enter a valid URL"}), 400

    # Generate short URL
    short_url = generate_short_url(custom_name)
    if not short_url:
        return jsonify({"error": "Custom name already exists"}), 400

    # Save to database
    new_mapping = URLMapping(short_url=short_url, long_url=long_url)
    db.session.add(new_mapping)
    db.session.commit()

    # Return the shortened URL
    return jsonify({"short_url": BASE_URL + short_url})

# Route to redirect short URL to the corresponding long URL
@app.route("/<short_url>")
def redirect_url(short_url):
    mapping = URLMapping.query.filter_by(short_url=short_url).first()
    if mapping:
        return f"<script>window.location.href='{mapping.long_url}';</script>"
    return "<h1>URL not found</h1>", 404

# Run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True, host="0.0.0.0", port=5000)
