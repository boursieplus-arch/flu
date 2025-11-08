import gradio as gr
from openai import OpenAI
import os
import json
from datetime import datetime
import csv

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# رمز عبور ادمین (در Settings → Secrets قرار دهید)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # پیش‌فرض: admin123

# مسیر ذخیره‌سازی
STORAGE_PATH = "/data" if os.path.exists("/data") else "."
CHAT_LOG_FILE = os.path.join(STORAGE_PATH, "chat_logs.json")
CSV_LOG_FILE = os.path.join(STORAGE_PATH, "chat_logs.csv")

SYSTEM_PROMPT = """## Character Identity
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
Help teens understand they deserve freedom from addiction. Make prevention cool, real, and personal."""

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
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.8,
        max_tokens=600,
        presence_penalty=0.6,
        frequency_penalty=0.3
    )
    
    bot_response = response.choices[0].message.content
    
    # ذخیره بدون نمایش به کاربر
    session_id = datetime.now().strftime("%Y%m%d_%H%M")
    save_chat_to_json(message, bot_response, session_id)
    save_chat_to_csv(message, bot_response, session_id)
    
    return bot_response

def verify_admin(password):
    """چک کردن رمز عبور ادمین"""
    if password == ADMIN_PASSWORD:
        return True, get_admin_stats()
    else:
        return False, "❌ Wrong password!"

def get_admin_stats():
    """آمار کامل برای ادمین"""
    try:
        if os.path.exists(CHAT_LOG_FILE):
            with open(CHAT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            total = len(logs)
            sessions = len(set(log['session_id'] for log in logs))
            
            return f"""✅ **Access Granted!**

📊 **Statistics:**
- Total messages: {total}
- Unique sessions: {sessions}
- Latest: {logs[-1]['timestamp'] if logs else 'N/A'}

You can now download the logs below."""
        return "✅ Access granted! No data yet."
    except:
        return "❌ Error reading data"

def download_logs_admin(password):
    """دانلود فقط با پسورد صحیح"""
    if password == ADMIN_PASSWORD:
        if os.path.exists(CSV_LOG_FILE):
            return CSV_LOG_FILE
        return None
    return None

# CSS
mobile_css = """
.gradio-container {
    max-width: 100% !important;
    margin: 0 auto !important;
    padding: 0 !important;
}

footer {display: none !important;}

h1 {
    color: #2196F3 !important;
    text-align: center !important;
    font-size: clamp(1.5rem, 5vw, 2.5rem) !important;
    padding: 10px !important;
    margin: 10px 0 !important;
}

h3 {
    font-size: clamp(0.9rem, 3vw, 1.2rem) !important;
    text-align: center !important;
    color: #666 !important;
    padding: 5px 10px !important;
}

#chatbot {
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    min-height: 400px !important;
    max-height: 60vh !important;
}

textarea, input[type="text"], input[type="password"] {
    font-size: 16px !important;
    padding: 12px !important;
    border-radius: 12px !important;
    border: 2px solid #e0e0e0 !important;
    min-height: 50px !important;
}

button {
    min-height: 44px !important;
    font-size: clamp(0.9rem, 3vw, 1rem) !important;
    padding: 12px 20px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    margin: 5px !important;
}

.gr-row {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

@media (min-width: 768px) {
    .gradio-container {
        max-width: 900px !important;
        padding: 20px !important;
    }
}
"""

# ساخت رابط
with gr.Blocks(theme=gr.themes.Soft(), css=mobile_css, title="Dr. Alex") as demo:
    
    gr.Markdown("""
    # 🚭 Dr. Alex Harper
    ### Your friend who gets it 💙
    """)
    
    with gr.Accordion("👋 About Me", open=False):
        gr.Markdown("""
        **Hey! I'm Alex**
        
        I started vaping at 16, got addicted for 5 years, and finally broke free at 21. 
        Now I help teens like you understand what I wish someone told me back then.
        
        No lectures, no judgment - just real talk from someone who's lived it.
        """)
    
    chatbot = gr.Chatbot(
        type="messages",
        height=450,
        avatar_images=(
            "https://api.dicebear.com/7.x/avataaars/svg?seed=teen&backgroundColor=E3F2FD",
            "https://api.dicebear.com/7.x/avataaars/svg?seed=alex&backgroundColor=2196F3&clothing=hoodie"
        ),
        show_label=False,
        elem_id="chatbot"
    )
    
    msg = gr.Textbox(
        placeholder="💬 What's on your mind?",
        show_label=False,
        container=False
    )
    
    with gr.Row():
        submit = gr.Button("Send 📤", variant="primary", scale=3)
        clear = gr.Button("Clear 🗑️", scale=1)
    
    gr.Examples(
        examples=[
            "🤔 Why did you start vaping?",
            "💪 How did you quit?",
            "👥 All my friends vape...",
            "💨 What's inside a vape?",
            "❤️ What happens when I quit?",
            "💰 How much money did you save?"
        ],
        inputs=msg
    )
    
    # بخش ادمین با پسورد
    with gr.Accordion("🔐 Admin Access (Password Required)", open=False):
        gr.Markdown("**For administrators only**")
        
        admin_password = gr.Textbox(
            label="Admin Password",
            type="password",
            placeholder="Enter admin password"
        )
        
        login_btn = gr.Button("Login 🔓", variant="secondary")
        
        admin_status = gr.Markdown("🔒 Please enter password")
        
        with gr.Row(visible=True) as admin_panel:
            download_btn = gr.Button("Download CSV Logs 💾")
            download_file = gr.File(label="Download", visible=True)
    
    gr.Markdown("""
    ---
    💙 **Privacy Notice**: Your conversations are saved anonymously for research purposes to improve this chatbot.
    
    *For medical emergencies, please contact a healthcare professional immediately.*
    """)
    
    def user_submit(user_message, chat_history):
        return "", chat_history + [{"role": "user", "content": user_message}]
    
    def bot_respond(chat_history):
        history_tuples = []
        for i in range(0, len(chat_history)-1, 2):
            if i+1 < len(chat_history):
                history_tuples.append((chat_history[i]["content"], chat_history[i+1]["content"]))
        
        user_message = chat_history[-1]["content"]
        bot_message = chat_function(user_message, history_tuples)
        return chat_history + [{"role": "assistant", "content": bot_message}]
    
    # Event handlers
    msg.submit(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_respond, chatbot, chatbot
    )
    
    submit.click(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot_respond, chatbot, chatbot
    )
    
    clear.click(lambda: [], None, chatbot, queue=False)
    
    # Admin login
    login_btn.click(
        lambda pwd: verify_admin(pwd)[1],
        inputs=admin_password,
        outputs=admin_status
    )
    
    # Download logs
    download_btn.click(
        download_logs_admin,
        inputs=admin_password,
        outputs=download_file
    )

demo.launch()
