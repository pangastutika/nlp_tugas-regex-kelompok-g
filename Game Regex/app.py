from flask import Flask, render_template, request, redirect, url_for, session
import random, re, os, string

app = Flask(__name__)
app.secret_key = "rahasia_banget"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITIES_FILE = os.path.join(BASE_DIR, "cities.txt")

def load_cities_from_txt(path):
    cities = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                parts = [p.strip() for p in ln.split("|")]
                if len(parts) != 4:
                    continue
                name, province, fact, image = parts
                cities.append({
                    "name": name,
                    "province": province,
                    "fact": fact,
                    "image": image,  
                })
    except FileNotFoundError:
        raise RuntimeError(f"File tidak ditemukan: {path}")
    if not cities:
        raise RuntimeError("cities.txt kosong / format salah. Format: Nama|Provinsi|Fact|path_gambar")
    print(f"[INIT] Loaded {len(cities)} cities from {path}")
    return cities

CITIES = load_cities_from_txt(CITIES_FILE)

def _rand_like(ch: str) -> str:
    pool = string.ascii_uppercase if ch.isupper() else string.ascii_lowercase
    pool = pool.replace(ch, "")             
    return random.choice(pool)

def generate_hint_from_name(name: str) -> str:
    hint = "^"
    for ch in name:
        if ch.isalpha():
            choice = random.choice([0, 1, 2])  
            if choice == 0:
                hint += re.escape(ch)
            elif choice == 1:
                hint += "."
            else:
                hint += f"[{re.escape(ch)}{_rand_like(ch)}]"
        elif ch in (" ", "-"):
            hint += r"(?:\s|-)?"
        else:
            hint += re.escape(ch)
    hint += "$"
    return hint

def create_quiz(num_questions=10):
    n = min(num_questions, len(CITIES))
    indices = random.sample(range(len(CITIES)), n)
    questions = [{"idx": i, "hint": generate_hint_from_name(CITIES[i]["name"])} for i in indices]
    return questions

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/start")
def start():
    session["score"] = 0
    session["round"] = 0
    session["questions"] = create_quiz(10)
    return redirect(url_for("game"))

@app.route("/game", methods=["GET", "POST"])
def game():
    round_num = session.get("round", 0)
    score = session.get("score", 0)
    questions = session.get("questions", [])

    if round_num >= 10:
        return redirect(url_for("result"))

    q = questions[round_num]
    city = CITIES[q["idx"]]   
    hint = q["hint"]

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        if answer.lower() == city["name"].lower():
            session["score"] = score + 1
            result = f"✅ Benar! Kota itu adalah {city['name']}."
        else:
            result = f"❌ Salah. Jawaban yang benar adalah {city['name']}."
        session["round"] = round_num + 1
        return render_template("feedback.html", result=result, city=city)

    return render_template("game.html", round=round_num+1, city=city, hint=hint, score=score)


@app.route("/result")
def result():
    score = session.get("score", 0)
    if score <= 3:
        badge = "🔰 Regex Newbie"
    elif score <= 7:
        badge = "🕵️ Regex Explorer"
    else:
        badge = "👑 Regex Master"
    return render_template("result.html", score=score, badge=badge)

if __name__ == "__main__":
    app.run(debug=True)
