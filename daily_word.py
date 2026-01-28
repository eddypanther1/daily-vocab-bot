import smtplib
import ssl
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

FILENAME = "sat.txt"
ARCHIVE_FILE = "used_words.txt"

def load_words():
    if not os.path.exists(FILENAME): return []
    word_list = []
    with open(FILENAME, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                parts = line.split(":", 1)
                word_list.append({"word": parts[0].strip(), "definition": parts[1].strip()})
    return word_list

def save_changes(all_words, used_words):
    # 1. Identify words to keep
    used_keys = {w['word'] for w in used_words}
    remaining = [w for w in all_words if w['word'] not in used_keys]

    # 2. Rewrite sat.txt with ONLY remaining words
    with open(FILENAME, "w", encoding="utf-8") as f:
        for w in remaining:
            f.write(f"{w['word']}: {w['definition']}\n")
    
    # 3. Append used words to archive
    with open(ARCHIVE_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d')
        for w in used_words:
            f.write(f"{w['word']}: {w['definition']} [Sent {timestamp}]\n")

def send_email(words_data):
    sender_email = os.environ["GMAIL_USER"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    receiver_email = "eddypanther1@gmail.com"
    tokyo_tz = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(tokyo_tz).strftime('%Y-%m-%d %H:%M')

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🧠 Daily SAT Vocab ({current_time})"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    html_content = f"<html><body><h2>Daily Vocabulary ({current_time})</h2><hr>"
    for item in words_data:
        html_content += f"<h3>{item['word'].capitalize()}</h3><p>{item['definition']}</p><br>"
    html_content += "<hr><p>Source: sat.txt</p></body></html>"
    
    part = MIMEText(html_content, "html")
    msg.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

if __name__ == "__main__":
    all_words = load_words()
    if not all_words:
        print("No words left in sat.txt!")
        exit(0)

    count = min(3, len(all_words))
    selected_words = random.sample(all_words, count)
    
    try:
        send_email(selected_words)
        # ONLY update files if email succeeded
        save_changes(all_words, selected_words)
        print(f"Sent and archived {count} words.")
    except Exception as e:
        print(f"Failed to send email: {e}")
        exit(1)
