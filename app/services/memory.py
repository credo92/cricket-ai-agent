import json
import os

def load_style_examples(limit=20):
    path = "data/posts_history.json"
    if not os.path.isfile(path):
        return "Short. Punchy. Emotional."
    with open(path, "r") as f:
        posts = json.load(f)
    if not posts:
        return "Short. Punchy. Emotional."
    return "\n".join(posts[:limit])
