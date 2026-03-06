# 🎵 Spotify EDA Dashboard

An interactive Exploratory Data Analysis dashboard built with **Dash** and **Plotly**, deployed on Render.

## 📊 Features
- Genre distribution bar chart
- Popularity trend over years
- Energy vs Popularity scatter plot
- Audio features radar chart
- Feature correlation heatmap
- Danceability box plot by genre
- Top 10 artists table
- Live filters: Genre, Year Range, Min Popularity

## 🚀 Run Locally

```bash
pip install -r requirements.txt
python app.py
```
Open → http://127.0.0.1:8050

## 🌐 Deploy on Render
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect this repo
4. Set start command: `gunicorn app:server`
5. Done ✅

## 📦 Data
Dataset loaded directly from URL — no download needed.
Source: [Spotify Tracks Dataset](https://github.com/amankharwal/Website-data)
