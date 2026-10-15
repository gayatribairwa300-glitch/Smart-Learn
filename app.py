
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.request import urlopen
import sqlite3, json, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-before-deployment")
DB = os.path.join(app.root_path, "learning.db")


def query(sql, values=()):
    with sqlite3.connect(DB) as db:
        return db.execute(sql, values)


with sqlite3.connect(DB) as db:
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)""")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or len(name) > 80 or len(email) > 254 or "@" not in email or not 8 <= len(password) <= 128:
            flash("Enter valid details and an 8–128 character password.")
        else:
            try:
                query("INSERT INTO users(name,email,password) VALUES(?,?,?)",
                      (name, email, generate_password_hash(password)))
                flash("Account created! Please log in.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Email already registered.")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query("SELECT id,name,password FROM users WHERE email=?",
                     (email,)).fetchone()

        if user and check_password_hash(user[2], password):
            session.clear()
            session["user_id"], session["name"] = user[0], user[1]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    try:
        url = "https://openlibrary.org/search.json?q=python&limit=6"
        with urlopen(url, timeout=5) as r:
            books = json.loads(r.read().decode()).get("docs", [])
        error = None
    except Exception:
        books, error = [], "Books temporarily unavailable."

    return render_template("dashboard.html", name=session["name"],
                           books=books, error=error)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
