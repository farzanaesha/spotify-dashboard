"""
🎵 Spotify EDA Dashboard
Deploy: Render.com
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# 1. DATASET — tries real CSV, falls back to mock
# ─────────────────────────────────────────────
def load_data():
    urls = [
        "https://raw.githubusercontent.com/amankharwal/Website-data/master/spotify.csv",
        "https://raw.githubusercontent.com/amankharwal/Website-data/master/spotify_dataset.csv",
    ]
    for url in urls:
        try:
            d = pd.read_csv(url)
            if len(d) > 100:
                print(f"Loaded real data: {len(d):,} rows")
                return d, True
        except Exception as e:
            print(f"URL failed: {e}")
    print("Using mock data")
    return None, False

raw, is_real = load_data()

if is_real:
    df = raw.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    col_map = {}
    for c in df.columns:
        if "track" in c and "name" in c: col_map[c] = "track_name"
        if c == "artists":               col_map[c] = "artist"
        if c == "track_genre":           col_map[c] = "genre"
    df.rename(columns=col_map, inplace=True)
    for col in ["track_name", "artist", "genre"]:
        if col not in df.columns:
            df[col] = col.capitalize()
    df.drop_duplicates(subset=["track_name", "artist"], inplace=True)
    df.dropna(subset=["popularity", "danceability", "energy"], inplace=True)
    if "duration_ms" in df.columns:
        df["duration_min"] = (df["duration_ms"] / 60000).round(2)
    if "release_date" in df.columns:
        df["year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year.fillna(2020).astype(int)
    elif "year" not in df.columns:
        df["year"] = 2020
    df = df[df["year"].between(2000, 2024)]
    df["year"] = df["year"].astype(int)
else:
    np.random.seed(42)
    n = 1000
    genres = ["Pop","Hip-Hop","Rock","Electronic","R&B","Latin","Jazz","Classical","Metal","Indie"]
    df = pd.DataFrame({
        "track_name":       [f"Track {i}"      for i in range(n)],
        "artist":           [f"Artist_{i%50}"  for i in range(n)],
        "genre":            np.random.choice(genres, n, p=[.18,.16,.12,.10,.10,.09,.07,.06,.06,.06]),
        "year":             np.random.randint(2015, 2024, n),
        "popularity":       np.random.randint(0, 101, n),
        "danceability":     np.round(np.random.beta(5, 3, n), 3),
        "energy":           np.round(np.random.beta(4, 3, n), 3),
        "valence":          np.round(np.random.beta(3, 3, n), 3),
        "tempo":            np.round(np.random.normal(120, 25, n).clip(60, 200), 1),
        "loudness":         np.round(np.random.normal(-8, 4, n).clip(-30, 0), 2),
        "speechiness":      np.round(np.random.beta(2, 8, n), 3),
        "acousticness":     np.round(np.random.beta(2, 5, n), 3),
        "instrumentalness": np.round(np.random.beta(1, 10, n), 3),
        "duration_ms":      np.random.randint(120000, 360000, n),
    })
    df["duration_min"] = (df["duration_ms"] / 60000).round(2)
    df["year"] = df["year"].astype(int)

print(f"Ready: {len(df):,} tracks | {df['genre'].nunique()} genres")

# ─────────────────────────────────────────────
# 2. THEME
# ─────────────────────────────────────────────
BG        = "#0D0D0D"
CARD      = "#161616"
BORDER    = "#282828"
GREEN     = "#1DB954"
GREEN2    = "#1ED760"
TEXT      = "#FFFFFF"
SUBTEXT   = "#B3B3B3"
PLOTBG    = "#111111"
GRIDCOLOR = "#1F1F1F"
COLORS    = px.colors.qualitative.Vivid

def hex_to_rgba(hex_color, alpha=0.15):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def apply_theme(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT, size=14, family="Courier New"), x=0.01),
        paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
        font=dict(color=SUBTEXT, family="Courier New"),
        margin=dict(l=40, r=20, t=45, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=SUBTEXT)),
        xaxis=dict(gridcolor=GRIDCOLOR, zerolinecolor=GRIDCOLOR),
        yaxis=dict(gridcolor=GRIDCOLOR, zerolinecolor=GRIDCOLOR),
    )
    return fig

def kpi_card(label, value):
    return html.Div([
        html.P(label, style={"color": SUBTEXT, "fontSize": "11px", "margin": "0 0 6px 0",
                              "textTransform": "uppercase", "letterSpacing": "1.5px"}),
        html.H2(str(value), style={"color": GREEN, "margin": "0", "fontSize": "28px",
                                    "fontWeight": "700", "fontFamily": "monospace"}),
    ], style={"backgroundColor": CARD, "border": f"1px solid {BORDER}",
               "borderRadius": "12px", "padding": "18px 22px", "flex": "1", "minWidth": "140px"})

def card(children, extra=None):
    base = {"backgroundColor": CARD, "border": f"1px solid {BORDER}",
            "borderRadius": "12px", "padding": "20px", "marginBottom": "20px"}
    if extra:
        base.update(extra)
    return html.Div(children, style=base)

# ─────────────────────────────────────────────
# 3. APP LAYOUT
# ─────────────────────────────────────────────
app = dash.Dash(__name__, title="Spotify EDA")
server = app.server  # required for Render

GENRES = sorted(df["genre"].unique())
MIN_YR = int(df["year"].min())
MAX_YR = int(df["year"].max())

app.layout = html.Div(
    style={"backgroundColor": BG, "minHeight": "100vh",
           "fontFamily": "'Courier New', monospace", "color": TEXT},
    children=[

    # Header
    html.Div([
        html.Span("🎵", style={"fontSize": "32px"}),
        html.Div([
            html.H1("Spotify EDA Dashboard",
                    style={"margin": "0", "fontSize": "24px", "fontWeight": "700", "color": GREEN}),
            html.P(f"{'Real' if is_real else 'Demo'} Data · {len(df):,} Tracks · {df['genre'].nunique()} Genres",
                   style={"margin": "0", "color": SUBTEXT, "fontSize": "12px"}),
        ])
    ], style={"display": "flex", "alignItems": "center", "gap": "14px",
               "padding": "24px 36px 18px", "borderBottom": f"1px solid {BORDER}"}),

    # Filters
    html.Div([
        html.Div([
            html.Label("GENRE", style={"color": SUBTEXT, "fontSize": "10px", "letterSpacing": "1.5px"}),
            dcc.Dropdown(
                id="genre-filter",
                options=[{"label": "All Genres", "value": "All"}] +
                        [{"label": g, "value": g} for g in GENRES],
                value="All", clearable=False,
                style={"backgroundColor": CARD, "color": "#000", "borderRadius": "8px",
                        "border": f"1px solid {BORDER}", "minWidth": "200px"},
            ),
        ]),
        html.Div([
            html.Label("YEAR RANGE", style={"color": SUBTEXT, "fontSize": "10px", "letterSpacing": "1.5px"}),
            dcc.RangeSlider(
                id="year-slider", min=MIN_YR, max=MAX_YR,
                value=[MIN_YR, MAX_YR], step=1,
                marks={y: {"label": str(y), "style": {"color": SUBTEXT, "fontSize": "10px"}}
                       for y in range(MIN_YR, MAX_YR+1, 2)},
            ),
        ], style={"flex": "1", "minWidth": "280px"}),
        html.Div([
            html.Label("MIN POPULARITY", style={"color": SUBTEXT, "fontSize": "10px", "letterSpacing": "1.5px"}),
            dcc.Slider(id="pop-slider", min=0, max=100, step=5, value=0,
                        marks={0: {"label": "0", "style": {"color": SUBTEXT}},
                               50: {"label": "50", "style": {"color": SUBTEXT}},
                               100: {"label": "100", "style": {"color": SUBTEXT}}},
                        tooltip={"placement": "bottom"}),
        ], style={"minWidth": "200px"}),
    ], style={"display": "flex", "flexWrap": "wrap", "gap": "28px", "alignItems": "flex-end",
               "padding": "18px 36px", "backgroundColor": CARD,
               "borderBottom": f"1px solid {BORDER}"}),

    # Body
    html.Div(style={"padding": "24px 36px"}, children=[

        html.Div(id="kpi-row",
                 style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginBottom": "22px"}),

        html.Div([
            card([dcc.Graph(id="genre-bar", style={"height": "300px"})],
                  {"flex": "1", "minWidth": "300px", "marginBottom": "0"}),
            card([dcc.Graph(id="year-line", style={"height": "300px"})],
                  {"flex": "1", "minWidth": "300px", "marginBottom": "0"}),
        ], style={"display": "flex", "gap": "18px", "marginBottom": "18px"}),

        html.Div([
            card([dcc.Graph(id="radar-chart",  style={"height": "340px"})],
                  {"flex": "1", "minWidth": "300px", "marginBottom": "0"}),
            card([dcc.Graph(id="scatter-plot", style={"height": "340px"})],
                  {"flex": "1.4", "minWidth": "340px", "marginBottom": "0"}),
        ], style={"display": "flex", "gap": "18px", "marginBottom": "18px"}),

        html.Div([
            card([dcc.Graph(id="corr-heatmap", style={"height": "340px"})],
                  {"flex": "1.2", "minWidth": "320px", "marginBottom": "0"}),
            card([dcc.Graph(id="box-plot",     style={"height": "340px"})],
                  {"flex": "1", "minWidth": "300px", "marginBottom": "0"}),
        ], style={"display": "flex", "gap": "18px", "marginBottom": "18px"}),

        card([
            html.H3("🏆 Top 10 Artists by Avg Popularity",
                    style={"color": GREEN, "margin": "0 0 14px 0",
                           "fontSize": "13px", "letterSpacing": "1px"}),
            html.Div(id="artists-table"),
        ]),
    ]),
])

# ─────────────────────────────────────────────
# 4. CALLBACKS
# ─────────────────────────────────────────────
@app.callback(
    Output("kpi-row",       "children"),
    Output("genre-bar",     "figure"),
    Output("year-line",     "figure"),
    Output("radar-chart",   "figure"),
    Output("scatter-plot",  "figure"),
    Output("corr-heatmap",  "figure"),
    Output("box-plot",      "figure"),
    Output("artists-table", "children"),
    Input("genre-filter",   "value"),
    Input("year-slider",    "value"),
    Input("pop-slider",     "value"),
)
def update(genre, year_range, min_pop):
    fdf = df.copy()
    if genre != "All":
        fdf = fdf[fdf["genre"] == genre]
    fdf = fdf[(fdf["year"] >= year_range[0]) & (fdf["year"] <= year_range[1])]
    fdf = fdf[fdf["popularity"] >= min_pop]

    if fdf.empty:
        empty = apply_theme(go.Figure(), "No data for selected filters")
        return [], empty, empty, empty, empty, empty, empty, \
               html.P("No data.", style={"color": SUBTEXT})

    # KPIs
    kpis = [
        kpi_card("Tracks",           f"{len(fdf):,}"),
        kpi_card("Avg Popularity",   f"{fdf['popularity'].mean():.1f}"),
        kpi_card("Avg Energy",       f"{fdf['energy'].mean():.2f}"),
        kpi_card("Avg Danceability", f"{fdf['danceability'].mean():.2f}"),
        kpi_card("Avg Tempo",        f"{fdf['tempo'].mean():.0f} BPM"),
        kpi_card("Artists",          f"{fdf['artist'].nunique():,}"),
    ]

    # Genre Bar
    gc = fdf["genre"].value_counts().head(12).reset_index()
    gc.columns = ["genre", "count"]
    fig1 = px.bar(gc, x="genre", y="count", color="genre",
                   color_discrete_sequence=COLORS, text="count")
    fig1.update_traces(textposition="outside", marker_line_width=0)
    apply_theme(fig1, "TRACKS BY GENRE")
    fig1.update_layout(showlegend=False,
                        xaxis=dict(tickangle=-30, gridcolor=GRIDCOLOR), height=300)

    # Year Line
    yr = fdf.groupby("year")["popularity"].mean().reset_index()
    fig2 = px.line(yr, x="year", y="popularity", markers=True,
                    color_discrete_sequence=[GREEN])
    fig2.update_traces(line_width=2.5, marker_size=7, marker_color=GREEN2)
    fig2.add_hline(y=yr["popularity"].mean(), line_dash="dot",
                    line_color="rgba(29,185,84,0.35)",
                    annotation_text=f"avg {yr['popularity'].mean():.1f}",
                    annotation_font_color=GREEN)
    apply_theme(fig2, "AVG POPULARITY BY YEAR")
    fig2.update_layout(height=300)

    # Radar
    rf = [f for f in ["danceability","energy","valence","acousticness","speechiness"]
          if f in fdf.columns]
    radar_colors = ["#1DB954","#FF6B6B","#4ECDC4","#FFE66D","#A29BFE"]
    genres_radar = fdf["genre"].value_counts().head(5).index if genre == "All" else [genre]
    fig3 = go.Figure()
    for i, g in enumerate(genres_radar):
        vals = fdf[fdf["genre"] == g][rf].mean().tolist()
        vals += [vals[0]]
        c = radar_colors[i % len(radar_colors)]
        fig3.add_trace(go.Scatterpolar(
            r=vals, theta=rf+[rf[0]], fill="toself", name=g,
            line_color=c, fillcolor=hex_to_rgba(c, 0.15), opacity=0.85,
        ))
    fig3.update_layout(
        polar=dict(bgcolor=PLOTBG,
                   radialaxis=dict(visible=True, range=[0,1], color=SUBTEXT,
                                   gridcolor=GRIDCOLOR, tickfont=dict(size=8)),
                   angularaxis=dict(color=SUBTEXT, gridcolor=GRIDCOLOR)),
        paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
        font=dict(color=SUBTEXT, family="Courier New"),
        title=dict(text="AUDIO FEATURES RADAR", font=dict(color=TEXT, size=14), x=0.01),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=SUBTEXT)),
        margin=dict(l=60, r=40, t=50, b=40), height=340,
    )

    # Scatter
    sample = fdf.sample(min(1200, len(fdf)), random_state=42)
    fig4 = px.scatter(sample, x="energy", y="popularity", color="genre",
                       size="danceability", opacity=0.72,
                       hover_data=["track_name","artist","tempo"],
                       color_discrete_sequence=COLORS)
    fig4.update_traces(marker_line_width=0)
    apply_theme(fig4, "ENERGY vs POPULARITY  (size = danceability)")
    fig4.update_layout(height=340)

    # Heatmap
    num_cols = [c for c in ["popularity","danceability","energy","valence",
                             "tempo","loudness","speechiness","acousticness"]
                if c in fdf.columns]
    corr = fdf[num_cols].corr().round(2)
    fig5 = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale=[[0,"#0D3B2A"],[0.5,PLOTBG],[1,GREEN]],
        text=corr.values, texttemplate="%{text}",
        textfont={"size": 9}, zmin=-1, zmax=1,
        colorbar=dict(tickfont=dict(color=SUBTEXT)),
    ))
    apply_theme(fig5, "FEATURE CORRELATION MATRIX")
    fig5.update_layout(margin=dict(l=100, r=20, t=45, b=100), height=340)

    # Box Plot
    top8g = fdf["genre"].value_counts().head(8).index
    fig6 = px.box(fdf[fdf["genre"].isin(top8g)], x="genre", y="danceability",
                   color="genre", color_discrete_sequence=COLORS, points="outliers")
    apply_theme(fig6, "DANCEABILITY BY GENRE")
    fig6.update_layout(showlegend=False,
                        xaxis=dict(tickangle=-30, gridcolor=GRIDCOLOR), height=340)

    # Top Artists
    top = (fdf.groupby("artist")
              .agg(tracks=("track_name","count"),
                   avg_pop=("popularity","mean"),
                   avg_energy=("energy","mean"),
                   avg_dance=("danceability","mean"))
              .query("tracks >= 2")
              .sort_values("avg_pop", ascending=False)
              .head(10).reset_index())
    top["avg_pop"]    = top["avg_pop"].round(1)
    top["avg_energy"] = top["avg_energy"].round(2)
    top["avg_dance"]  = top["avg_dance"].round(2)
    top.columns = ["Artist","Tracks","Avg Popularity","Avg Energy","Avg Danceability"]

    table = dash_table.DataTable(
        data=top.to_dict("records"),
        columns=[{"name": c, "id": c} for c in top.columns],
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": BORDER, "color": GREEN, "fontWeight": "700",
                       "fontSize": "11px", "textTransform": "uppercase",
                       "letterSpacing": "1px", "border": f"1px solid {BORDER}"},
        style_cell={"backgroundColor": CARD, "color": TEXT, "fontSize": "13px",
                     "fontFamily": "Courier New", "border": f"1px solid {BORDER}",
                     "padding": "10px 14px", "textAlign": "left"},
        style_data_conditional=[
            {"if": {"row_index": 0},
             "backgroundColor": "rgba(29,185,84,0.08)", "color": GREEN2},
            {"if": {"row_index": "odd"}, "backgroundColor": "#131313"},
        ],
    )

    return kpis, fig1, fig2, fig3, fig4, fig5, fig6, table


# ─────────────────────────────────────────────
# 5. RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
