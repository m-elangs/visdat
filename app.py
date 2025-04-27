from flask import Flask, render_template, request
import pandas as pd
import re
import random

app = Flask(__name__)

# Load data di awal
print("[INFO] Loading dataset...")
df = pd.read_csv("steam_games.csv")
df = df[["name", "popular_tags", "release_date", "all_reviews"]].dropna()
df["release_year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year

df = df.dropna(subset=["release_year", "popular_tags", "all_reviews"])
df["release_year"] = df["release_year"].astype(int)
df["genre_list"] = df["popular_tags"].str.split(",").apply(lambda x: [i.strip() for i in x])
df["rating_percent"] = df["all_reviews"].apply(lambda txt: int(re.findall(r"(\d{1,3})%", str(txt))[-1]) if re.findall(r"(\d{1,3})%", str(txt)) else None)
df = df.dropna(subset=["rating_percent"])

# Random Gaming Tips
GAMING_TIPS = [
    "💡 Remember to take breaks while gaming for better focus!",
    "🎯 Try aiming training maps to improve your accuracy.",
    "🧠 Play with friends for more fun and better strategies!",
    "🔥 Don't rage quit! Every defeat teaches something new.",
    "⚙️ Always update your drivers for best performance!",
]

# Fungsi rekomendasi game
def recommend_games(df, genre=None, year=None, min_rating=70):
    df_rec = df.copy()
    if genre:
        df_rec = df_rec[df_rec["genre_list"].apply(lambda genres: genre.lower() in [g.lower() for g in genres])]
    if year:
        df_rec = df_rec[df_rec["release_year"] == year]
    df_rec = df_rec[df_rec["rating_percent"] >= min_rating]

    recs = (
        df_rec[["name", "popular_tags", "release_year", "rating_percent"]]
        .dropna()
        .sort_values("rating_percent", ascending=False)
        .head(5)
    )
    return recs

@app.route("/")
def index():
    year = request.args.get("year", default="2018")

    # Ambil form AI rekomendasi
    genre_input = request.args.get("genre")
    rec_year_input = request.args.get("rec_year")
    min_rating_input = request.args.get("min_rating")

    ai_recommendations = None
    ai_message = None

    if genre_input and rec_year_input and min_rating_input:
        try:
            rec_year_input = int(rec_year_input)
            min_rating_input = int(min_rating_input)
        except ValueError:
            rec_year_input = 2018
            min_rating_input = 70

        recs = recommend_games(df, genre_input, rec_year_input, min_rating_input)

        if not recs.empty:
            ai_recommendations = recs.to_html(index=False, classes="table table-bordered")
            ai_message = random.choice(GAMING_TIPS)
        else:
            top_genres = df["genre_list"].explode().value_counts().head(3).index.tolist()
            suggestion = random.choice(top_genres)
            ai_message = f"😔 No game found. Maybe try '{suggestion}' genre instead?"

    try:
        with open("templates/pie_chart.html") as f:
            pie = f.read()
        with open("templates/line_chart.html") as f:
            line = f.read()
        with open("templates/scatter_chart.html") as f:
            scatter = f.read()
        with open("templates/growth_chart.html") as f:
            growth = f.read()
        with open("templates/growth_insight.txt", encoding="utf-8") as f:
            insight = f.read()
        with open(f"templates/bar_chart_{year}.html") as f:
            bar = f.read()
    except FileNotFoundError:
        bar = f"<p style='color:red'>Chart tahun {year} belum tersedia 😢</p>"

    return render_template("index_embed.html",
                           pie_chart=pie,
                           bar_chart=bar,
                           line_chart=line,
                           scatter_chart=scatter,
                           growth_chart=growth,
                           growth_insight=insight,
                           selected_year=year,
                           ai_recommendations=ai_recommendations,
                           ai_message=ai_message)

if __name__ == "__main__":
    app.run(debug=True)
