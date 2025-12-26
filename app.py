from flask import Flask, request, redirect, url_for, render_template_string, session, abort
# from jinja2 import DictLoader

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # Required for sessions

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
  {% if session.get('user_id') %}
    <span>Logged in as User #{{ session['user_id'] }}</span> ·
    <form method="post" action="/logout" style="display:inline">
      <button type="submit" style="background:none;border:none;color:blue;text-decoration:underline;cursor:pointer">Logout</button>
    </form>
  {% else %}
    <a href="/login/new">Login</a>
  {% endif %}
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
        session = session,
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
          <a href="/posts/{{ post.id }}/comments">Comments ({{ post_comments|length }})</a> ·
          <form method="post" action="/posts/{{ post.id }}/delete" style="display:inline" onsubmit="return confirm('Are you sure you want to delete this post?')">
            <button type="submit" style="color:red">Delete</button>
          </form>
        </p>
        """,
        post = post,
        post_user = post_user,
        post_comments = post_comments,
    )
    return render_template_string(BASE, title=f"Post #{post_id}", body=body_html, session=session)

@app.get("/posts/<int:post_id>/edit")
def posts_edit(post_id: int):
    post = POSTS.get(post_id) or abort(404)
    body_html = render_template_string(
        """
        <form method="post" action="/posts/{{ post.id }}">
          <label>Title <input name="title" value="{{ post.title }}"></label><br>
          <label>Body <textarea name="body">{{ post.body }}</textarea></label><br>
          <button type="submit">Save</button>
        </form>
        """,
        post=post,
    )
    return render_template_string(BASE, title=f"Edit Post #{post_id}", body=body_html)

@app.post("/posts/<int:post_id>")
def posts_update(post_id: int):
    post = POSTS.get(post_id) or abort(404)
    post["title"] = request.form.get("title", post["title"]).strip()
    post["body"] = request.form.get("body", post["body"]).strip()
    return redirect(url_for("posts_detail", post_id=post_id))

@app.post("/posts/<int:post_id>/like")
def posts_like(post_id: int):
    post = POSTS.get(post_id) or abort(404)
    user_id = session.get("user_id", 1)
    post["likes"].add(user_id)
    return redirect(url_for("posts_detail", post_id=post_id))

@app.post("/posts/<int:post_id>/like/delete")
def posts_unlike(post_id: int):
    post = POSTS.get(post_id) or abort(404)
    user_id = session.get("user_id", 1)
    post["likes"].discard(user_id)
    return redirect(url_for("posts_detail", post_id=post_id))

@app.post("/posts/<int:post_id>/delete")
def posts_delete(post_id: int):
    post = POSTS.pop(post_id, None) or abort(404)

    # Delete all comments associated with this post
    comments_to_delete = [c_id for c_id, c in COMMENTS.items() if c["post_id"] == post_id]
    for c_id in comments_to_delete:
        COMMENTS.pop(c_id, None)

    return redirect(url_for("posts_index"))

@app.post("/posts/search")
def posts_search_submit():
    term = request.form.get("q", "")
    return redirect(url_for("posts_index", search=term))

# -------------------------------------------------------------------
# Users + “user’s posts”
# -------------------------------------------------------------------
@app.get("/users/new")
def users_new():
        body_html = render_template_string(
            """
           <form method="post" action="/users">
                <label>Username <input name="username" required></label>
                <button type="submit">Create User</button>
            </form>
            """,
        )
        return render_template_string(BASE, title="New User", body=body_html)
@app.post("/users")
def users_create():
    global _next_user_id
    username = request.form.get("username", "").strip()
    if not username:
        abort(400)
    uid = _next_user_id
    USERS[uid] = {"id": uid, "username": username}
    _next_user_id += 1
    return redirect(url_for("user_posts", user_id=uid))

@app.get("/users/<int:user_id>/posts")
def user_posts(user_id: int):
    user = USERS.get(user_id) or abort(404)
    posts = [p for p in POSTS.values() if p["user_id"] == user_id]
    body_html = render_template_string(
        """
        <p>Posts by {{ user.username }}:</p>
            <ul>
            {% for p in posts %}
            <li><a href="/posts/{{ p.id }}">{{ p.title }}</a></li>
            {% endfor %}
        </ul>
        """,
        user=user,
        posts=posts,
    )
    return render_template_string(BASE, title=f"{user['username']}'s Posts", body=body_html)

# -------------------------------------------------------------------
# 5) Auth (login form + submit, logout submit)
# GET /login/new
# POST /login
# POST /logout
# -------------------------------------------------------------------
@app.get("/login/new")
def login_new():
    body_html = render_template_string(
        """
        <form method="post" action="/login">
            <label>User ID <input type="number" min="1" name="user_id" value="1"></label>
            <button type="submit">Log In</button>
        </form>
        """
    )
    return render_template_string(BASE, title="Log in", body=body_html)

@app.post("/login")
def login_create():
    uid = int(request.form.get("user_id", 1))
    if uid not in USERS:
        # Better error handling with user feedback
        body_html = render_template_string(
            """
            <p style="color:red">Invalid user ID. Please try again.</p>
            <form method="post" action="/login">
                <label>User ID <input type="number" min="1" name="user_id" value="{{ uid }}"></label>
                <button type="submit">Log In</button>
            </form>
            <p><a href="/users/new">Create a new user</a></p>
            """,
            uid=uid
        )
        return render_template_string(BASE, title="Login Error", body=body_html)

    session["user_id"] = uid
    return redirect("/")

@app.post("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

# -------------------------------------------------------------------
# 6) Comments (nested under posts) + edit/update/delete
# GET /posts/:post_id/comments
# GET /posts/:post_id/comments/new
# POST /posts/:post_id/comments
# GET /comments/:comment_id/edit
# POST /comments/:comment_id
# POST /comments/:comment_id/delete
# -------------------------------------------------------------------

@app.get("/posts/<int:post_id>/comments")
def comments_index(post_id: int):
    post = POSTS.get(post_id) or abort(404)
    post_comments = [c for c in COMMENTS.values() if c["post_id"] == post_id]
    body_html = render_template_string(
        """
        <p>Comments for <strong>{{ post.title }}</strong></p>
        <p><a href="/posts/{{ post.id }}">← Back to Post</a></p>
        <a href="/posts/{{ post.id }}/comments/new">Add Comment</a>
        <ul>
            {% for c in comments %}
                <li>
                {{ c.body }}
                [<a href="/comments/{{ c.id }}/edit">edit</a>]
                </li>
            {% endfor %}
        </ul>
        """,
        post=post,
        comments=post_comments
    )
    return render_template_string(BASE, title=f"Comments for Post #{post_id}", body=body_html, session=session)

@app.get("/posts/<int:post_id>/comments/new")
def comments_new(post_id: int):
    post = POSTS.get(post_id) or abort(404)
    body_html = render_template_string(
        """
        <p><a href="/posts/{{ post.id }}/comments">← Back to Comments</a></p>
        <form method="post" action="/posts/{{ post.id }}/comments">
            <label>Comment <textarea name="body" required></textarea></label>
            <button type="submit">Add</button>
        </form>
        """,
        post=post
    )
    return render_template_string(BASE, title=f"New Comment for Post #{post_id}", body=body_html, session=session)

@app.post("/posts/<int:post_id>/comments")
def comments_create(post_id: int):
    global _next_comment_id
    post = POSTS.get(post_id) or abort(404)
    body = request.form.get("body", "").strip()
    if not body:
        abort(400)

    comment_id = _next_comment_id
    COMMENTS[comment_id] = {"id": comment_id, "post_id": post_id, "body": body}
    _next_comment_id += 1
    return redirect(url_for("comments_index", post_id=post_id))

@app.get("/comments/<int:comment_id>/edit")
def comments_edit(comment_id: int):
    c = COMMENTS.get(comment_id) or abort(404)
    body_html = render_template_string(
        """
        <p><a href="/posts/{{ c.post_id }}/comments">← Back to Comments</a></p>
        <form method="post" action="/comments/{{ c.id }}">
            <label>Edit <textarea name="body">{{ c.body }}</textarea></label>
            <button type="submit">Save</button>
        </form>
        <form method="post" action="/comments/{{ c.id }}/delete" style="margin-top:0.5rem">
            <button type="submit">Delete</button>
        </form>
        """,
        c=c
    )
    return render_template_string(BASE, title=f"Edit Comment #{comment_id}", body=body_html, session=session)

@app.post("/comments/<int:comment_id>")
def comments_update(comment_id: int):
    c = COMMENTS.get(comment_id) or abort(404)
    c["body"] = request.form.get("body", c["body"]).strip()
    return redirect(url_for("comments_index", post_id=c["post_id"]))

@app.post("/comments/<int:comment_id>/delete")
def comments_delete(comment_id: int):
    c = COMMENTS.pop(comment_id, None) or abort(404)
    return redirect(url_for("comments_index", post_id=c["post_id"]))


# -------------------------------------------------------------------
# Dev server entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Run: python app.py  (then open http://127.0.0.1:5000)
    app.run(debug=True)
