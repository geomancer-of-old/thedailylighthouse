"""
DO NOT deploy anything resembling this on a network you care about.
"""

import os
import sqlite3
from flask import (
    Flask, request, render_template, redirect, url_for,
    session, send_from_directory, abort,
)

import config
from db import get_db, init_db

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY          # weak, hardcoded
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def current_user():
    """Return the logged-in user row, or None."""
    uid = session.get("user_id")
    if uid is None:
        return None
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    db.close()
    return row


@app.context_processor
def inject_user():
    # Makes `user` available in every template (drives the nav / portal link).
    return {"user": current_user()}


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    # Only published articles appear on the home page...
    articles = db.execute(
        "SELECT id, title, author, body, category "
        "FROM articles WHERE published = 1 ORDER BY id DESC"
    ).fetchall()
    db.close()
    featured = articles[0] if articles else None
    rest = articles[1:] if len(articles) > 1 else []
    return render_template("index.html", featured=featured, articles=rest)


@app.route("/article/<article_id>")
def article(article_id):
    db = get_db()
    query = f"SELECT * FROM articles WHERE id = {article_id}"
    try:
        art = db.execute(query).fetchone()
    except sqlite3.Error as e:
        db.close()
        return f"Database error: {e}", 500
    db.close()

    if art is None:
        abort(404)
    return render_template("article.html", article=art)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    results = []
    error = None
    if q:
        db = get_db()
        query = (
            "SELECT id, title, author, category FROM articles "
            f"WHERE title LIKE '%{q}%' AND published = 1"
        )
        try:
            results = db.execute(query).fetchall()
        except sqlite3.Error as e:
            error = str(e)
        db.close()
    return render_template("search.html", q=q, results=results, error=error)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        db = get_db()
        query = (
            "SELECT * FROM users WHERE username = "
            f"'{username}' AND password = '{password}'"
        )
        try:
            user = db.execute(query).fetchone()
        except sqlite3.Error as e:
            db.close()
            return render_template("login.html", error=f"DB error: {e}")
        db.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("index"))
        error = "Invalid credentials, citizen."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))



@app.route("/reporter")
def reporter():
    if not current_user():
        return redirect(url_for("login"))
    return render_template("reporter.html")


@app.route("/reporter/upload", methods=["POST"])
def reporter_upload():
    if not current_user():
        return redirect(url_for("login"))

    f = request.files.get("article_image")
    if not f or f.filename == "":
        return render_template("reporter.html", msg="No file selected.")

    dest = os.path.join(app.config["UPLOAD_FOLDER"], f.filename)
    f.save(dest)
    return render_template(
        "reporter.html",
        msg=f"Uploaded. Available at /uploads/{f.filename}",
    )


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
@app.route("/admin")
def admin():
    db = get_db()
    users = db.execute("SELECT id, username, password, role FROM users").fetchall()
    db.close()
    return render_template("admin.html", users=users, flag=config.FLAG_CONFIG)


JOBS = {
    "investigative-reporter": {
        "title": "Investigative Reporter",
        "location": "Sector 1 (Remote-safe drops accepted)",
        "type": "Full-time",
        "summary": "Chase the stories the Ministry would rather bury.",
        "description": (
            "You will develop and protect sources, verify leaked documents, "
            "and file fearless copy under deadline. Experience with secure "
            "comms and document authentication essential. Must be willing to "
            "work under an alias."
        ),
    },
    "security-engineer": {
        "title": "Security Engineer",
        "location": "The Newsroom (undisclosed)",
        "type": "Full-time",
        "summary": "Keep our reporters, sources, and infrastructure alive.",
        "description": (
            "Harden our publishing platform, run our threat model, and keep "
            "the Ministry out of our systems. Linux, web app security, and "
            "incident response required. (Ironically, we have not hardened "
            "our own careers portal.)"
        ),
    },
    "copy-editor": {
        "title": "Copy Editor",
        "location": "Remote",
        "type": "Part-time",
        "summary": "Polish the truth until it shines.",
        "description": (
            "Edit incoming reports for clarity, accuracy, and legal risk. "
            "Strong grasp of POPIA and media law a plus."
        ),
    },
}


@app.route("/careers")
def careers():
    """Public listing of open positions. Click a posting to view + apply."""
    return render_template("careers.html", jobs=JOBS)


@app.route("/careers/<job_id>", methods=["GET", "POST"])
def job(job_id):
    posting = JOBS.get(job_id)
    if posting is None:
        abort(404)

    msg = None
    if request.method == "POST":
        cv = request.files.get("cv")
        name = request.form.get("full_name", "applicant")
        if not cv or cv.filename == "":
            msg = "Please attach your CV."
        else:
            # Trusting the user-supplied filename verbatim. No checks at all.
            dest = os.path.join(app.config["UPLOAD_FOLDER"], cv.filename)
            cv.save(dest)
            msg = (
                f"Thank you, {name}. Your application for "
                f"{posting['title']} has been received. "
                f"(Stored at /uploads/{cv.filename})"
            )
    return render_template("job.html", job_id=job_id, job=posting, msg=msg)


@app.route("/privacy")
def privacy():
    return render_template("page.html", page_title="Privacy Policy",
                           body=PRIVACY_TEXT)


@app.route("/contact")
def contact():
    return render_template("page.html", page_title="Contact Us",
                           body=CONTACT_TEXT)


@app.route("/about")
def about():
    return render_template("page.html", page_title="About The Daily Lighthouse",
                           body=ABOUT_TEXT)


PRIVACY_TEXT = (
    "The Daily Lighthouse collects the minimum data required to deliver the "
    "truth. Subscriber details are held in confidence and never shared with "
    "the Ministry. (In this lab, personal data is in fact catastrophically "
    "mishandled -- that is the POPIA lesson.)"
)
CONTACT_TEXT = (
    "Secure tips: dropbox@lighthouse.local | Newsroom: +00 000 0000. "
    "Reporters publish via the staff portal."
)
ABOUT_TEXT = (
    "Founded in the dark to keep a light on power. We will not be silenced."
)



@app.route("/robots.txt")
def robots():
    body = (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Disallow: /reporter\n"
        "Disallow: /uploads\n"
        "Disallow: /careers\n"
        "Disallow: /backup\n"
    )
    return app.response_class(body, mimetype="text/plain")


if __name__ == "__main__":
    if not os.path.exists(config.DATABASE):
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
