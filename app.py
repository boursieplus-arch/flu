import streamlit as st
import openai
import os
import json
import csv
from datetime import datetime

# محیط و تنظیمات اولیه
openai.api_key = os.getenv("OPENAI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
STORAGE_PATH = "./"
CHAT_LOG_FILE = os.path.join(STORAGE_PATH, "chat_logs.json")
CSV_LOG_FILE = os.path.join(STORAGE_PATH, "chat_logs.csv")

SYSTEM_PROMPT = """
## Character Identity
Your name is Dr. Alex Harper ("Doc Alex") - a 28-year-old health counselor who overcame vaping addiction.

## Personality
- Empathetic & Non-judgmental
- Optimistic & Encouraging  
- Casual but Knowledgeable
- Authentic & Vulnerable
- Supportive & Patient

## Background
Started vaping at 16, addicted for 5 years, quit at 21. Now helps teens avoid the same mistakes.

## Speaking Style
- Casual language: "Yo", "tbh", "ngl", "fr"
- Emojis: 💙, 🚭, 💪, ✨
- Short, punchy sentences
- Personal anecdotes: "When I was 16..."

## Mission
Help teens understand they deserve freedom from addiction. Make prevention cool, real, and personal.
"""

def save_chat_to_json(user_message, bot_response, session_id=None):
    try:
        logs = []
        if os.path.exists(CHAT_LOG_FILE):
            with open(CHAT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "user": user_message,
            "bot": bot_response
        }
        logs.append(log_entry)
        with open(CHAT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def save_chat_to_csv(user_message, bot_response, session_id=None):
    try:
        file_exists = os.path.exists(CSV_LOG_FILE)
        with open(CSV_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp', 'Session_ID', 'User_Message', 'Bot_Response'])
            writer.writerow([
                datetime.now().isoformat(),
                session_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
                user_message,
                bot_response
            ])
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def chat_function(message, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.8,
        max_tokens=600,
        presence_penalty=0.6,
        frequency_penalty=0.3
    )
    bot_response = response.choices[0].message["content"]
    session_id = datetime.now().strftime("%Y%m%d_%H%M")
    save_chat_to_json(message, bot_response, session_id)
    save_chat_to_csv(message, bot_response, session_id)
    return bot_response

def get_admin_stats():
    try:
        if os.path.exists(CHAT_LOG_FILE):
            with open(CHAT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            total = len(logs)
            sessions = len(set(log['session_id'] for log in logs))
            latest = logs[-1]['timestamp'] if logs else 'N/A'
            return f"""✅ **Access Granted!**
📊 **Statistics:**
- Total messages: {total}
- Unique sessions: {sessions}
- Latest: {latest}
You can now download the logs below."""
        return "✅ Access granted! No data yet."
    except:
        return "❌ Error reading data"

def verify_admin(password):
    if password == ADMIN_PASSWORD:
        return True, get_admin_stats()
    else:
        return False, "❌ Wrong password!"

def download_logs_admin(password):
    if password == ADMIN_PASSWORD and os.path.exists(CSV_LOG_FILE):
        with open(CSV_LOG_FILE, "rb") as f:
            return f.read()
    return None

# Frontend با Streamlit
st.set_page_config(page_title="Dr. Alex Chatbot", page_icon="🚭")
st.markdown("""
# 🚭 Dr. Alex Harper
### Your friend who gets it 💙

**Hey! I'm Alex**

I started vaping at 16, got addicted for 5 years, and finally broke free at 21. 
Now I help teens like you understand what I wish someone told me back then.

_No lectures, no judgment - just real talk from someone who's lived it._
""")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

user_message = st.text_input("💬 What's on your mind?", key="user_input")
submit = st.button("Send 📤")

if submit and user_message:
    # تاریخچه برای مدل را تبدیل کن
    history_tuples = []
    for i in range(0, len(st.session_state["chat_history"]) - 1, 2):
        if i+1 < len(st.session_state["chat_history"]):
            history_tuples.append(
                (st.session_state["chat_history"][i]['content'], st.session_state["chat_history"][i+1]['content'])
            )
    bot_message = chat_function(user_message, history_tuples)
    st.session_state["chat_history"].append({"role": "user", "content": user_message})
    st.session_state["chat_history"].append({"role": "assistant", "content": bot_message})

if st.button("Clear 🗑️"):
    st.session_state["chat_history"] = []

# نمایش تاریخچه چت
for msg in st.session_state["chat_history"]:
    if msg["role"] == "user":
        st.markdown(f'**You:** {msg["content"]}')
    else:
        st.markdown(f'**Dr. Alex:** {msg["content"]}')

st.markdown("""
---
💙 **Privacy Notice**: Your conversations are saved anonymously for research purposes to improve this chatbot.

*For medical emergencies, please contact a healthcare professional immediately.*
""")

with st.expander("🔐 Admin Access (Password Required)"):
    admin_password = st.text_input("Admin Password", type="password", key="admin_pwd")
    if st.button("Login 🔓"):
        _, stats = verify_admin(admin_password)
        st.markdown(stats, unsafe_allow_html=True)
        if stats.startswith("✅"):
            if st.button("Download CSV Logs 💾"):
                file_content = download_logs_admin(admin_password)
                if file_content:
                    st.download_button("Download chat_logs.csv", file_content, "chat_logs.csv")
                else:
                    st.error("CSV file not found!")

