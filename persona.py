import praw
import openai
import argparse
from dotenv import load_dotenv
import os
import re


load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Reddit client 
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent="PersonaScript/1.0"
)

def extract_username(profile_url):
    return profile_url.rstrip('/').split('/')[-1]

def fetch_user_data(username, limit=50):
    user = reddit.redditor(username)
    posts, comments = [], []
    for submission in user.submissions.new(limit=limit):
        posts.append({
            "title": submission.title,
            "body": submission.selftext,
            "url": submission.url
        })
    for comment in user.comments.new(limit=limit):
        comments.append({
            "body": comment.body,
            "permalink": f"https://www.reddit.com{comment.permalink}"
        })
    return posts, comments

def clean(text):
    return re.sub(r'\s+', ' ', text.strip())

def build_prompt(posts, comments):
    content = []
    for p in posts[:10]:
        content.append(f"[POST] Title: {p['title']} | Body: {clean(p['body'])}")
    for c in comments[:10]:
        content.append(f"[COMMENT] {clean(c['body'])}")
    joined = "\n".join(content)
    return f"""
You are an AI trained to analyze Reddit content and infer a user persona.

From the posts and comments below, generate a user profile including:
- Personality Traits
- Interests and Hobbies
- Writing Style
- Age Group/Demographic (if guessable)
- Common Topics
- Language/Slang

Cite the relevant content for each point.

Reddit Data:
{joined}
"""

def generate_persona(posts, comments):
    prompt = build_prompt(posts, comments)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

def save_persona(username, content):
    filename = f"{username}_persona.txt"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(content)
    print(f"[✔] Saved: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Reddit User Persona Generator")
    parser.add_argument("profile_url", type=str, help="Reddit profile URL")
    args = parser.parse_args()

    username = extract_username(args.profile_url)
    print(f"[INFO] Username: {username}")

    posts, comments = fetch_user_data(username)
    print(f"[INFO] Retrieved {len(posts)} posts, {len(comments)} comments")

    persona = generate_persona(posts, comments)
    save_persona(username, persona)

if __name__ == "__main__":
    main()

