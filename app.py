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
# 2) Contact form (GET new + POST create)
# GET /contact/new
# POST /contact
# -------------------------------------------------------------------

@app.get("/contact/new")
def contact_new():
    return render_template_string(
        BASE,
        body = """
        <form method="post" action="/contact">
          <label>Name: <input name="name"></label><br>
          <label>Message: <textarea name="message"></textarea></label><br>
          <button type="submit">Send</button>
        </form>
        """,
        title = "Contact Us",
    )

@app.post("/contact")
def contact_create():
    name = request.form.get("name", "")
    message = request.form.get("message", "")
    body_html = render_template_string("""
        <p>Thanks, {{ name }}. We received your message:</p>
        <pre>{{ message }}</pre>
    """, name=name, message=message)
    return render_template_string(
        BASE,  # BASE must use {{ body|safe }}
        title="Contact Submitted",
        body=body_html
    )

# -------------------------------------------------------------------
# 3) Posts (index, new, create, detail, edit, update), likes, search
# RESTful-HTML conventions using only GET/POST
# -------------------------------------------------------------------

@app.get("/posts")
def posts_index():
    q = request.args.get("search")
    posts = list(POSTS.values())
    if q:
        ql = q.lower()
        posts = [p for p in posts if ql in p["title"].lower() or ql in p["body"].lower()]

    body_html = render_template_string("""
    <form method="get" action="/posts" style="margin-bottom:1rem">
        <input name="search" placeholder="search" value="{{ request.args.get('search','') }}">
        <button type="submit">Search</button>
    </form>
    <a href="/posts/new">Create Post</a>
    <ul>
    {% for p in posts %}
        <li>
        <a href="/posts/{{ p.id }}">{{ p.title }}</a>
        (likes: {{ p.likes|length }})
        </li>
    {% endfor %}
    </ul>
""", posts=posts, request=request)
    return render_template_string(BASE, title="Posts", body=body_html)


@app.get("/posts/new")
def posts_new():
    return render_template_string(
        BASE,
        title = "New Post",
        body = """
        <form method="post" action="/posts">
          <label>Title <input name="title" required></label><br>
          <label>Body <textarea name="body" required></textarea></label><br>
          <label>User ID <input type="number" name="user_id" value="1" min="1" required></label><br>
          <button type="submit">Create</button>
        </form>
        """,
    )

@app.post("/posts")
def posts_create():
    global _next_post_id
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    user_id = int(request.form.get("user_id", 1))
    pid = _next_post_id
    POSTS[pid] = {"id": pid, "user_id": user_id, "title": title, "body": body, "likes": set()}
    _next_post_id += 1
    return redirect(url_for("posts_detail", post_id=pid))

@app.get("/posts/<int:post_id>")
def posts_detail(post_id: int):
    post = POSTS.get(post_id) or abort(404)
    post_user = USERS.get(post["user_id"], {"user_name": "?"})
    post_comments = [c for c in COMMENTS.values() if c["post_id"] == post_id]

    body_html = render_template_string(
        """
        <article>
          <h2>{{ post.title }}</h2>
          <p>{{ post.body }}</p>
          <p>By user #{{ post.user_id }} ({{ post_user.username }})</p>
          <form method="post" action="/posts/{{ post.id }}/like" style="display:inline">
            <button>Like</button>
          </form>
          <form method="post" action="/posts/{{ post.id }}/like/delete" style="display:inline">
            <button>Unlike</button>
          </form>
          <p>Likes: {{ post.likes|length }}</p>
        </article>
        <p>
          <a href="/posts/{{ post.id }}/edit">Edit</a> ·
          <a href="/posts/{{ post.id }}/comments">Comments ({{ post_comments|length }})</a>
        </p>
        """,
        post = post,
        post_user = post_user,
        post_comments = post_comments,
    )
    return render_template_string(BASE, title=f"Post #{post_id}", body=body_html)

# -------------------------------------------------------------------
# Dev server entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Run: python app.py  (then open http://127.0.0.1:5000)
    app.run(debug=True)
