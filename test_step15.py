"""
test_step15.py - checks likes, comments, replies and photo upload on the website.
"""

import base64
import io
import os
os.environ["UNIPALZ_DB"] = "test_web15.db"
if os.path.exists("test_web15.db"):
    os.remove("test_web15.db")

from app import app, UPLOAD_DIR

def text(r):
    return r.get_data(as_text=True)

def join(username, name):
    c = app.test_client()
    c.post("/signup", data={"username": username, "password": "secret123", "name": name})
    return c

# a real 1x1 PNG picture
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
before = set(os.listdir(UPLOAD_DIR))

asha = join("asha", "Asha Rao")
ravi = join("ravi", "Ravi Kumar")
ravi.post("/request/send/asha"); asha.post("/request/accept/ravi")

# 1. photo post: the file is saved and the picture shows on the page
r = ravi.post("/post", data={"text": "My first photo", "image": (io.BytesIO(PNG), "pic.png")},
              content_type="multipart/form-data", follow_redirects=True)
new_files = set(os.listdir(UPLOAD_DIR)) - before
assert len(new_files) == 1
photo = new_files.pop()
page = text(asha.get("/"))
assert 'class="post-img"' in page and photo in page and "My first photo" in page
print("1. photo post OK")

# 2. a photo alone (no text) is allowed
ravi.post("/post", data={"text": "", "image": (io.BytesIO(PNG), "second.png")},
          content_type="multipart/form-data")
assert page.count("post-img") < text(asha.get("/")).count("post-img")
print("2. photo-only post OK")

# 3. fake images and wrong file types are refused
r = ravi.post("/post", data={"text": "x", "image": (io.BytesIO(b"just text"), "fake.png")},
              content_type="multipart/form-data", follow_redirects=True)
assert "not a real image" in text(r)
r = ravi.post("/post", data={"text": "x", "image": (io.BytesIO(PNG), "virus.exe")},
              content_type="multipart/form-data", follow_redirects=True)
assert "PNG, JPG, GIF or WEBP" in text(r)
assert len(set(os.listdir(UPLOAD_DIR)) - before) == 2      # nothing extra was saved
print("3. bad uploads refused")

# 4. like and unlike
page = text(asha.get("/"))
assert "Like · 0" in page
asha.post("/post/1/like", data={"next": "/"})
assert "Liked · 1" in text(asha.get("/"))
asha.post("/post/1/like", data={"next": "/"})              # press again = unlike
page = text(asha.get("/"))
assert "Like · 0" in page and "Liked · " not in page
print("4. like / unlike OK")

# 5. comment and reply on the post page
asha.post("/post/1/comment", data={"text": "Love it!"})
ok_page = text(asha.get("/post/1"))
assert "Love it!" in ok_page and "Comments (1)" in ok_page
ravi.post("/post/1/comment", data={"text": "Thanks Asha", "parent_id": "1"})
page = text(asha.get("/post/1"))
assert "Thanks Asha" in page and "Comments (2)" in page and 'class="indent"' in page
assert "Comments · 2" in text(asha.get("/"))               # the count shows on the board
print("5. comment + reply OK")

# 6. empty comments refused, unknown post is a 404
r = asha.post("/post/1/comment", data={"text": "  "}, follow_redirects=True)
assert "empty" in text(r)
assert asha.get("/post/999").status_code == 404
print("6. comment rules OK")

# 7. you can only delete your own comment (the branch goes with it)
asha.post("/comment/2/delete")                             # comment 2 is ravi's reply
assert "Thanks Asha" in text(asha.get("/post/1"))
asha.post("/comment/1/delete", data={"next": "/post/1"})   # asha's root comment
page = text(asha.get("/post/1"))
assert "Love it!" not in page and "Thanks Asha" not in page and "No comments yet" in page
print("7. delete comment OK")

# 8. deleting the post also deletes the photo file and its comments
asha.post("/post/1/comment", data={"text": "again"})
ravi.post("/post/1/delete", data={"next": "/"})
assert photo not in os.listdir(UPLOAD_DIR)
assert asha.get("/post/1").status_code == 404
print("8. post + photo deleted OK")

# 9. login needed
r = app.test_client().post("/post/2/like")
assert r.status_code == 302 and "/login" in r.headers["Location"]
print("9. login required")

# tidy up: remove the second test photo too
for f in set(os.listdir(UPLOAD_DIR)) - before:
    os.remove(os.path.join(UPLOAD_DIR, f))
os.remove("test_web15.db")
print("\nAll Step 15 tests passed!")