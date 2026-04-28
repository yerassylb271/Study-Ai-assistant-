import json
import sqlite3
from flask import Flask, render_template, request, redirect, session, jsonify
from groq import Groq

app = Flask(__name__)
app.secret_key = "free_ai_project_key"

# 🤖 GROQ SETUP
client = Groq(api_key="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")


def ask_ai(prompt, is_quiz=False):
    try:
        system_msg = "You are a helpful study assistant."
        if is_quiz:
            system_msg = (
                "You must respond ONLY with a JSON object. "
                "Format: {'questions': [{'question': '...', 'options': ['a', 'b', 'c', 'd'], 'correct_idx': 0}]}. "
                "Create 3-5 questions."
            )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"} if is_quiz else None
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


# 📦 DATABASE INIT
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, topic TEXT, mode TEXT, response TEXT)")
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    if "user_id" not in session: return redirect("/login")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        conn.close()
        if user:
            session["user_id"] = user[0]
            return redirect("/")
    return render_template("login.html")
    
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

@app.route("/generate", methods=["POST"])
def generate():
    if "user_id" not in session: return jsonify({"response": "Not logged in"})

    data = request.json
    topic, mode = data.get("topic"), data.get("mode")

    is_quiz = (mode == "quiz")
    prompts = {
        "explain": f"Explain {topic} simply with examples.",
        "quiz": f"Create a quiz about {topic}.",
        "summary": f"Summarize {topic} in bullet points.",
        "plan": f"7-day study plan for {topic}."
    }

    answer = ask_ai(prompts.get(mode, topic), is_quiz=is_quiz)

    # Сохраняем в БД
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, topic, mode, response) VALUES (?, ?, ?, ?)",
              (session["user_id"], topic, mode, answer))
    conn.commit()
    conn.close()

    if is_quiz:
        try:
            return jsonify({"quiz_data": json.loads(answer)})
        except:
            return jsonify({"response": "AI failed to format quiz. Try again."})

    return jsonify({"response": answer})
    
@app.route("/logout")
def logout():
    session.clear()  # Полностью очищаем сессию пользователя
    return redirect("/login") # Перенаправляем на страницу входа


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
