from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "free_ai_project_key"

# =======================
from groq import Groq  # Add this import at the very top of the file

# =======================
# 🤖 GROQ AI SETUP (Instead of Gemini)
# =======================
# Your gsk_... key works here
client = Groq(api_key="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")

def ask_ai(prompt):
    try:
        # Use the Llama 3 model, it is free and very fast in Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"AI error: {str(e)}"

# 📦 DATABASE
# =======================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        topic TEXT,
        mode TEXT,
        response TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# =======================
# 🔐 AUTH
# =======================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =======================
# 🏠 HOME
# =======================
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")


# =======================
# 🧠 AI GENERATE
# =======================
@app.route("/generate", methods=["POST"])
def generate():
    if "user_id" not in session:
        return jsonify({"response": "Not logged in"})

    data = request.json
    topic = data.get("topic")
    mode = data.get("mode")

    prompts = {
        "explain": f"Explain {topic} in a simple way with examples.",
        "quiz": f"Create 5 quiz questions with answers about {topic}.",
        "summary": f"Summarize {topic} in simple bullet points.",
        "plan": f"Create a 7-day study plan for {topic}.",
    }

    prompt = prompts.get(mode, topic)

    answer = ask_ai(prompt)

    # save history
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO history (user_id, topic, mode, response) VALUES (?, ?, ?, ?)",
        (session["user_id"], topic, mode, answer)
    )
    conn.commit()
    conn.close()

    return jsonify({"response": answer})


# =======================
# 📜 HISTORY
# =======================
@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT topic, mode, response 
        FROM history 
        WHERE user_id=?
        ORDER BY id DESC
    """, (session["user_id"],))

    data = c.fetchall()
    conn.close()

    return render_template("history.html", data=data)


# =======================
# 🚀 RUN APP
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
