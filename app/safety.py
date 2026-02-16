import random
import time

recent_posts = []

def human_delay():
    time.sleep(random.randint(5, 20))

def is_duplicate(text):
    return any(text[:50] in p for p in recent_posts)

def remember_post(text):
    recent_posts.append(text)
    if len(recent_posts) > 100:
        recent_posts.pop(0)
