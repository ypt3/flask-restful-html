from flask import Flask, request, redirect, url_for, render_template_string, session, abort
# from jinja2 import DictLoader

app = Flask(__name__)

# -------------------------------------------------------------------
# Fake in-memory stores (for demo only)
# -------------------------------------------------------------------


USERS = {1: {"id": 1, "username": "alice"}, 2: {"id": 2, "username": "bob"}}
POSTS = {
    1: {"id": 1, "user_id": 1, "title": "Hello", "body": "First post", "likes": set()},
    2: {"id": 2, "user_id": 2, "title": "World", "body": "Second post", "likes": set()},
}
COMMENTS = {
    1: {"id": 1, "post_id": 1, "body": "Nice!"},
}

# Auto-increment counters
_next_user_id = 3
_next_post_id = 3
_next_comment_id = 2

# Very tiny layout
BASE = """
<!doctype html>
<title>{{ title }}</title>
<h1>{{ title }}</h1>
<nav style="margin-bottom:1rem">
  <a href="/">Home</a> ·
  <a href="/posts">Posts</a> ·
  <a href="/users/1/posts">Alice's Posts</a> ·
  <a href="/contact/new">Contact</a> ·
  <a href="/login/new">Login</a>
</nav>
<div>
  {{ body|safe }}
</div>
"""

# app.jinja_loader = DictLoader({"base.html": BASE})


@app.get("/")
def home():
    return render_template_string(
        BASE ,
        title = "Home",
        body = "<p>Welcome to the demo site.</p>",
    )

@app.get("/home")
def home_alias():
    return home()

# -------------------------------------------------------------------
# Dev server entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Run: python app.py  (then open http://127.0.0.1:5000)
    app.run(debug=True)
