"""The Broken Login - an intentionally vulnerable CTF challenge (SQL injection).

!! DELIBERATELY INSECURE !!  Deploy only in an isolated educational environment.
The vulnerability is limited to this app's own throwaway SQLite database, which
is opened READ-ONLY for the login query, so nothing can be modified or destroyed.
"""
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

DEFAULT_FLAG = "TECH{sqli_login_bypass}"
BASE_DIR = Path(__file__).resolve().parent


def init_db(path):
    """(Re)create the sample database. Runs on every start, so it always resets cleanly."""
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            DROP TABLE IF EXISTS users;
            CREATE TABLE users (
                id        INTEGER PRIMARY KEY,
                username  TEXT NOT NULL,
                password  TEXT NOT NULL,
                role      TEXT NOT NULL,
                full_name TEXT NOT NULL
            );
            """
        )
        conn.executemany(
            "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
            [
                # Random password: nobody is meant to guess this one. Get in another way.
                ("admin", secrets.token_urlsafe(18), "Administrator", "Portal Administrator"),
                ("intern", "welcome123", "Intern", "Ira Intern"),
                ("hr_amy", "Summer2024!", "HR Coordinator", "Amy Fernandes"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def vulnerable_login(db_path, username, password):
    """INTENTIONALLY VULNERABLE: user input is concatenated straight into the SQL string.

    The secure version uses placeholders:
        conn.execute("SELECT ... WHERE username = ? AND password = ?", (username, password))
    The connection is read-only, so only SELECTs can ever run here.
    """
    query = (
        "SELECT id, username, password, role, full_name FROM users "
        "WHERE username = '" + username + "' AND password = '" + password + "'"
    )
    conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return conn.execute(query).fetchone()
    finally:
        conn.close()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        CTF_FLAG=os.environ.get("CTF_FLAG", DEFAULT_FLAG),
        DB_PATH=os.environ.get("DB_PATH", str(BASE_DIR / "portal.db")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    init_db(app.config["DB_PATH"])

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user"):
                flash("Please sign in to view the dashboard.", "info")
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped

    @app.route("/", methods=["GET"])
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("login.html", error="Enter both a username and a password."), 400

        try:
            row = vulnerable_login(app.config["DB_PATH"], username, password)
        except (sqlite3.Error, sqlite3.Warning):
            return render_template(
                "login.html",
                error="The portal database could not process that request. Check your input and try again.",
            ), 400

        if row is None:
            return render_template("login.html", error="Invalid username or password."), 401

        # Genuine login = the typed credentials match the stored row exactly.
        # Anything else means the query was tricked into returning a row.
        genuine = row[1] == username and row[2] == password
        session.clear()
        session.update(user=row[1], role=row[3], full_name=row[4], bypassed=not genuine)
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        bypassed = bool(session.get("bypassed"))
        return render_template(
            "dashboard.html",
            full_name=session["full_name"],
            role=session["role"],
            flag=app.config["CTF_FLAG"] if bypassed else None,
        )

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    # Debug mode is deliberately OFF. Set HOST=0.0.0.0 only inside an isolated lab network.
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
