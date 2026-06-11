import streamlit as st
import pickle
import pandas as pd
import requests
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# -------------------- CONFIG --------------------
API_KEY = "21dc30dc0e6b7c30e8abc1fd5aaca6e8"

MOVIES_URL = "https://www.dropbox.com/scl/fi/voxy7ruwtunr02k9xs4rx/movies.pkl?rlkey=oa6ckbwieqt4k6ksv8hz00720&st=qcu9h1a5&dl=1"
SIMILARITY_URL = "https://www.dropbox.com/scl/fi/f08d8z5onggk2rgnty2oj/similarity_compressed.pkl?rlkey=hh413cudopudfgtgf746waxzr&st=4fpqaw9j&dl=1"

# -------------------- LOAD FILES --------------------
@st.cache_resource
def load_data():
    if not os.path.exists('movies_dict_dl.pkl'):
        urllib.request.urlretrieve(MOVIES_URL, 'movies_dict_dl.pkl')
    if not os.path.exists('similarity_compressed_dl.pkl'):
        urllib.request.urlretrieve(SIMILARITY_URL, 'similarity_compressed_dl.pkl')
    m_dict = pickle.load(open('movies_dict_dl.pkl', 'rb'))
    sim = pickle.load(open('similarity_compressed_dl.pkl', 'rb'))
    return m_dict, sim

movies_dict, similarity = load_data()
movies = pd.DataFrame(movies_dict)

# -------------------- FETCH FUNCTIONS --------------------
def fetch_movie_details(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        data = requests.get(url, timeout=10).json()
        poster_path = data.get('poster_path', '')
        poster = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        rating = data.get('vote_average', 'N/A')
        overview = data.get('overview', 'No description available.')
        genres = [g['name'] for g in data.get('genres', [])][:3]
        return poster, rating, overview, genres
    except Exception:
        return None, 'N/A', 'No description available.', []

def fetch_trailer(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}&language=en-US"
        data = requests.get(url, timeout=10).json()
        results = data.get('results') or []
        for video in results:
            if video['type'] == 'Trailer':
                return f"https://www.youtube.com/watch?v={video['key']}"
        return None
    except Exception:
        return None

def fetch_all(movie_id):
    poster, rating, overview, genres = fetch_movie_details(movie_id)
    trailer = fetch_trailer(movie_id)
    return poster, rating, overview, genres, trailer

def fetch_trending():
    try:
        url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={API_KEY}"
        data = requests.get(url, timeout=10).json()
        results = data.get('results', [])[:10]
        movies_list = []
        for movie in results:
            poster_path = movie.get('poster_path', '')
            movies_list.append({
                "title": movie.get('title', 'Unknown'),
                "poster": f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None,
                "rating": movie.get('vote_average', 'N/A'),
                "overview": movie.get('overview', 'No description available.'),
                "id": movie.get('id')
            })
        return movies_list
    except Exception:
        return []

# -------------------- RECOMMEND --------------------
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    movie_ids = [movies.iloc[i[0]].movie_id for i in movie_list]
    movie_names = [movies.iloc[i[0]].title for i in movie_list]

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_all, movie_ids))

    posters   = [r[0] for r in results]
    ratings   = [r[1] for r in results]
    overviews = [r[2] for r in results]
    genres    = [r[3] for r in results]
    trailers  = [r[4] for r in results]

    return movie_names, posters, ratings, overviews, genres, trailers

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="NextWatch.AI", page_icon="🎬", layout="wide")

# -------------------- CSS --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
* { font-family: 'Inter', sans-serif !important; }
.stApp { background: #0f0f0f !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.hero {
    background: linear-gradient(180deg, #1a0000 0%, #0f0f0f 100%);
    padding: 5rem 4rem 3rem 4rem;
    text-align: center;
    border-bottom: 1px solid #1a1a1a;
}
.hero-title {
    font-size: 4rem;
    font-weight: 900;
    color: #E50914;
    letter-spacing: 3px;
    text-shadow: 0 0 40px rgba(229,9,20,0.4);
    margin-bottom: 0.5rem;
}
.hero-sub {
    color: #888;
    font-size: 1rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 2.5rem;
}
div[data-testid="stSelectbox"] > div {
    background-color: #1a1a1a !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: white !important;
}
div[data-testid="stSelectbox"] label { display: none !important; }
div[data-testid="stButton"] button {
    background: #E50914 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    height: 45px !important;
    white-space: nowrap !important;
    width: 100% !important;
}
div[data-testid="stButton"] button:hover { background: #ff1a27 !important; }
.movie-info { padding: 1rem; }
.movie-title {
    color: white;
    font-weight: 700;
    font-size: 0.95rem;
    margin-bottom: 0.4rem;
    line-height: 1.3;
}
.movie-rating {
    color: #f5c518;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.genre-tag {
    display: inline-block;
    background: #2a2a2a;
    color: #aaa;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    margin: 0.1rem;
}
.movie-overview {
    color: #888;
    font-size: 0.78rem;
    line-height: 1.5;
    margin-top: 0.6rem;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.trailer-btn {
    display: inline-block;
    margin-top: 0.8rem;
    background: #E50914;
    color: white !important;
    padding: 0.4rem 1rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    text-decoration: none !important;
}
.results-header {
    color: white;
    font-size: 1.3rem;
    font-weight: 700;
    padding: 2rem 4rem 1rem 4rem;
    border-top: 1px solid #1a1a1a;
}
.results-sub {
    color: #666;
    font-size: 0.85rem;
    padding: 0 4rem 1.5rem 4rem;
}
div[data-testid="stSpinner"] { color: white !important; }
div, span, p, label { color: inherit; }
</style>
""", unsafe_allow_html=True)

# -------------------- HERO --------------------
st.markdown("""
<div class="hero">
    <div class="hero-title">NEXTWATCH.AI</div>
    <div class="hero-sub">Discover your next favorite movie</div>
</div>
""", unsafe_allow_html=True)

# -------------------- SEARCH --------------------
st.markdown('<div style="padding: 2rem 4rem;">', unsafe_allow_html=True)
col_left, col_center, col_right = st.columns([1, 3, 1])
with col_center:
    search_col, btn_col = st.columns([5, 1])
    with search_col:
        selected_movie = st.selectbox("", movies['title'].values)
    with btn_col:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        search_clicked = st.button("Search")
st.markdown('</div>', unsafe_allow_html=True)

# -------------------- TRENDING --------------------
trending = fetch_trending()
if trending:
    st.markdown("""
    <div style='padding: 2rem 4rem 1rem 4rem; border-top: 1px solid #1a1a1a;'>
        <div style='color:white; font-size:1.3rem; font-weight:700; margin-bottom:0.3rem'>Trending This Week</div>
        <div style='color:#666; font-size:0.85rem; margin-bottom:1.5rem'>Most popular movies right now</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding: 0 4rem;">', unsafe_allow_html=True)
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        movie = trending[idx]
        with col:
            if movie["poster"]:
                st.image(movie["poster"], use_container_width=True)
            else:
                st.markdown("<div style='background:#2a2a2a; height:300px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#555'>No Poster</div>", unsafe_allow_html=True)
            try:
                r = float(movie["rating"])
                rating_display = f"&#11088; {r:.1f}/10"
            except:
                rating_display = "N/A"
            st.markdown(f"""
            <div class="movie-info">
                <div class="movie-title">{movie['title']}</div>
                <div class="movie-rating">{rating_display}</div>
                <div class="movie-overview">{movie['overview']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    cols2 = st.columns(5)
    for idx, col in enumerate(cols2):
        movie = trending[idx + 5]
        with col:
            if movie["poster"]:
                st.image(movie["poster"], use_container_width=True)
            else:
                st.markdown("<div style='background:#2a2a2a; height:300px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#555'>No Poster</div>", unsafe_allow_html=True)
            try:
                r = float(movie["rating"])
                rating_display = f"&#11088; {r:.1f}/10"
            except:
                rating_display = "N/A"
            st.markdown(f"""
            <div class="movie-info">
                <div class="movie-title">{movie['title']}</div>
                <div class="movie-rating">{rating_display}</div>
                <div class="movie-overview">{movie['overview']}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- RESULTS --------------------
if search_clicked:
    with st.spinner('Finding recommendations...'):
        names, posters, ratings, overviews, genres, trailers = recommend(selected_movie)

    st.markdown(f"""
    <div class="results-header">Recommended for you</div>
    <div class="results-sub">Because you liked <strong style="color:white">{selected_movie}</strong></div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding: 0 4rem 4rem 4rem;">', unsafe_allow_html=True)
    cols = st.columns(5)

    for idx, col in enumerate(cols):
        with col:
            try:
                r = float(ratings[idx])
                stars = "&#11088;" * round(r / 2)
                rating_display = f"{r:.1f}/10 {stars}"
            except:
                rating_display = "N/A"

            genre_html = "".join([f'<span class="genre-tag">{g}</span>' for g in genres[idx]])
            trailer_html = f'<a class="trailer-btn" href="{trailers[idx]}" target="_blank">Watch Trailer</a>' if trailers[idx] else '<span style="color:#555; font-size:0.8rem">No trailer available</span>'

            if posters[idx]:
                st.image(posters[idx], use_container_width=True)
            else:
                st.markdown("<div style='background:#2a2a2a; height:300px; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#555'>No Poster</div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="movie-info">
                <div class="movie-title">{names[idx]}</div>
                <div class="movie-rating">{rating_display}</div>
                {genre_html}
                <div class="movie-overview">{overviews[idx]}</div>
                {trailer_html}
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
