"""
app.py  -  The Flask website

Flask is the WAITER: it takes a request from the browser, hands it to the
Engine (the kitchen), and brings back an HTML page. It does no clever
thinking itself: every route below is "ask the Engine, then show the answer".

Run it with:   python app.py      then open   http://127.0.0.1:5000
"""

import os
import time
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, abort, jsonify)

from storage.persistent import PersistentEngine

APP_NAME = "Unipalz"
TAGLINE = "Pals are just nodes with feelings."
AVATARS = ["🦊", "🐙", "🌵", "🍙", "🐼", "🦉", "🐸", "🦄"]

app = Flask(__name__)
# the secret key signs the login cookie (use a real secret if you ever deploy)
app.secret_key = os.environ.get("UNIPALZ_SECRET", "dev-secret-change-me")

# ONE engine for the whole site: it loads the database into memory right now
engine = PersistentEngine(os.environ.get("UNIPALZ_DB", "unipalz.db"))

# templates can call get_user("ravi") to fetch a profile
app.jinja_env.globals["get_user"] = engine.get_user


# ---------- helpers ----------

def current_user():
    """The logged-in User object, or None. Being 'logged in' just means the
    session cookie holds a username."""
    username = session.get("username")
    return engine.get_user(username) if username else None


def login_required(view):
    """Put @login_required above a route to keep logged-out visitors out."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            session.clear()
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def redirect_back():
    """After a button press, go back to the page the button was on.
    (We only accept paths on our own site, so nobody can send you elsewhere.)"""
    target = request.form.get("next", "")
    if target.startswith("/") and not target.startswith("//"):
        return redirect(target)
    return redirect(url_for("home"))


def parse_year(value):
    try:
        return min(4, max(1, int(value)))
    except (TypeError, ValueError):
        return 1


def parse_skills(text):
    """'Python, UI/UX, DSA' -> ['Python', 'UI/UX', 'DSA'] (at most 8)."""
    return [s.strip() for s in text.split(",") if s.strip()][:8]


def parse_avatar(value):
    return value if value in AVATARS else AVATARS[0]


@app.context_processor
def inject_globals():
    """Variables every template can use without being passed in."""
    user = current_user()
    pending = len(engine.pending_requests(user.username)) if user else 0
    return dict(APP_NAME=APP_NAME, TAGLINE=TAGLINE, me=user, pending_count=pending)


@app.template_filter("av_class")
def av_class(username):
    """Give each user one of 5 pastel colours (always the same for the same user)."""
    return "av-%d" % (sum(ord(c) for c in username) % 5)


@app.template_filter("timeago")
def timeago(created_at):
    seconds = int(time.time() - created_at)
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return "%d min ago" % (seconds // 60)
    if seconds < 86400:
        hours = seconds // 3600
        return "%d hour%s ago" % (hours, "" if hours == 1 else "s")
    if seconds < 7 * 86400:
        days = seconds // 86400
        return "%d day%s ago" % (days, "" if days == 1 else "s")
    return time.strftime("%d %b %Y", time.localtime(created_at))


# ---------- accounts ----------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        f = request.form
        ok, msg = engine.signup(f.get("username", ""), f.get("password", ""),
                                f.get("name", ""), f.get("programme", ""),
                                parse_year(f.get("year")), f.get("bio", ""),
                                parse_skills(f.get("skills", "")),
                                parse_avatar(f.get("avatar")))
        if ok:
            session["username"] = f["username"].strip().lower()   # log them in
            flash("Welcome to " + APP_NAME + "!", "ok")
            return redirect(url_for("home"))
        flash(msg, "error")
        return render_template("signup.html", form=f, avatars=AVATARS)
    return render_template("signup.html", form={}, avatars=AVATARS)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = engine.login(request.form.get("username", ""),
                            request.form.get("password", ""))
        if user:
            session["username"] = user.username
            return redirect(url_for("home"))
        flash("Wrong username or password", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("See you soon!", "ok")
    return redirect(url_for("login"))


# ---------- the Bulletin Board (home feed) ----------

@app.route("/")
@login_required
def home():
    me = current_user()
    return render_template(
        "home.html",
        feed=engine.feed(me.username, limit=30),            # heap merge
        suggestions=engine.suggestions(me.username, 4),     # Introductions
        pal_count=len(engine.connections(me.username)),
    )


@app.route("/post", methods=["POST"])
@login_required
def create_post():
    ok, result = engine.create_post(current_user().username,
                                    request.form.get("text", ""))
    if not ok:
        flash(result, "error")          # result is the reason when it failed
    return redirect_back()


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    ok, msg = engine.delete_post(current_user().username, post_id)
    flash(msg, "ok" if ok else "error")
    return redirect_back()


# ---------- Yearbook (profiles) ----------

@app.route("/user/<username>")
@login_required
def profile(username):
    view = engine.profile_view(current_user().username, username)
    if view is None:
        abort(404)
    return render_template("profile.html", view=view)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    me = current_user()
    if request.method == "POST":
        f = request.form
        ok, msg = engine.update_profile(
            me.username, name=f.get("name", ""), programme=f.get("programme", ""),
            year=parse_year(f.get("year")), bio=f.get("bio", ""),
            skills=parse_skills(f.get("skills", "")),
            avatar=parse_avatar(f.get("avatar")))
        flash(msg, "ok" if ok else "error")
        if ok:
            return redirect(url_for("profile", username=me.username))
    return render_template("edit_profile.html", avatars=AVATARS)


# ---------- My Pals (connections) ----------

@app.route("/pals")
@login_required
def pals():
    me = current_user().username
    return render_template(
        "pals.html",
        incoming=engine.pending_requests(me),
        sent=engine.sent_requests(me),
        pals=engine.connections(me),
        suggestions=engine.suggestions(me, 6),
    )


@app.route("/request/send/<username>", methods=["POST"])
@login_required
def send_request(username):
    ok, msg = engine.send_request(current_user().username, username)
    flash(msg, "ok" if ok else "error")
    return redirect_back()


@app.route("/request/accept/<username>", methods=["POST"])
@login_required
def accept_request(username):
    ok, msg = engine.accept_request(current_user().username, username)
    flash(msg, "ok" if ok else "error")
    return redirect_back()


@app.route("/request/reject/<username>", methods=["POST"])
@login_required
def reject_request(username):
    ok, msg = engine.reject_request(current_user().username, username)
    flash(msg, "ok" if ok else "error")
    return redirect_back()


@app.route("/request/cancel/<username>", methods=["POST"])
@login_required
def cancel_request(username):
    ok, msg = engine.cancel_request(current_user().username, username)
    flash(msg, "ok" if ok else "error")
    return redirect_back()


@app.route("/remove/<username>", methods=["POST"])
@login_required
def remove_pal(username):
    ok, msg = engine.remove_connection(current_user().username, username)
    flash(msg, "ok" if ok else "error")
    return redirect_back()


# ---------- search ----------

@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    results = [engine.get_user(u) for u in engine.search(q, 20)] if q else []
    return render_template("search.html", q=q, results=results)


@app.route("/api/search")
@login_required
def api_search():
    """Used by search.js to show suggestions while you type (a trie lookup)."""
    users = [engine.get_user(u) for u in engine.search(request.args.get("q", ""), 6)]
    return jsonify([{"username": u.username, "name": u.name,
                     "avatar": u.avatar, "programme": u.programme} for u in users])

if __name__ == "__main__":
    app.run(debug=True, port=5001)
