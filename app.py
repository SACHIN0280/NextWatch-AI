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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

* { font-family: 'Outfit', sans-serif !important; }
.stApp { 
    background: #09090b !important; 
    color: #ededed !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #09090b; 
}
::-webkit-scrollbar-thumb {
    background: #3f3f46; 
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #52525b; 
}

.block-container { padding: 0 !important; max-width: 100% !important; }

/* Hero Section */
.hero {
    background: radial-gradient(circle at top, #2e0814 0%, #09090b 70%);
    padding: 6rem 2rem 4rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 50% 50%, rgba(229, 9, 20, 0.15), transparent 50%);
    z-index: 0;
    pointer-events: none;
}
.hero-title {
    position: relative;
    font-size: 5rem;
    font-weight: 800;
    background: linear-gradient(to right, #ff2e43, #e50914);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
    margin-bottom: 0.5rem;
    z-index: 1;
    animation: fadeInDown 0.8s ease-out;
}
.hero-sub {
    position: relative;
    color: #a1a1aa;
    font-size: 1.2rem;
    letter-spacing: 1px;
    font-weight: 300;
    margin-bottom: 2.5rem;
    z-index: 1;
    animation: fadeInUp 0.8s ease-out 0.2s backwards;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Selectbox */
div[data-testid="stSelectbox"] > div {
    background-color: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: white !important;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
div[data-testid="stSelectbox"] > div:hover {
    border-color: rgba(229, 9, 20, 0.5) !important;
    background-color: rgba(255, 255, 255, 0.05) !important;
}
div[data-testid="stSelectbox"] label { display: none !important; }

/* Buttons */
div[data-testid="stButton"] button {
    background: rgba(255, 255, 255, 0.05) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    height: 45px !important;
}
div[data-testid="stButton"] button:hover {
    background: #e50914 !important;
    border-color: #e50914 !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(229, 9, 20, 0.4);
}

/* Movie Card Wrappers */
.movie-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 0.8rem;
    transition: all 0.4s ease;
    height: 100%;
}
.movie-card:hover {
    transform: translateY(-8px);
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
}

/* Movie Info */
.movie-info { 
    padding: 1rem 0.5rem; 
}
.movie-title {
    color: #fff;
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 0.4rem;
    line-height: 1.3;
}
.movie-rating {
    color: #fbbf24;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 4px;
}
.movie-cast {
    color: #a1a1aa;
    font-size: 0.75rem;
    margin-bottom: 0.6rem;
    line-height: 1.4;
}
.genre-tag {
    display: inline-block;
    background: rgba(229, 9, 20, 0.1);
    border: 1px solid rgba(229, 9, 20, 0.2);
    color: #ff8a8a;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    margin: 0.15rem;
    font-weight: 500;
    transition: all 0.3s ease;
}
.genre-tag:hover {
    background: rgba(229, 9, 20, 0.2);
}
.movie-overview {
    color: #8f8f9d;
    font-size: 0.8rem;
    line-height: 1.6;
    margin-top: 0.8rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.trailer-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 1rem;
    background: linear-gradient(135deg, #e50914, #b20710);
    color: white !important;
    padding: 0.5rem 1.2rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    text-decoration: none !important;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(229, 9, 20, 0.3);
}
.trailer-btn:hover {
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(229, 9, 20, 0.5);
}

/* Headers */
.results-header {
    color: white;
    font-size: 1.8rem;
    font-weight: 800;
    padding: 2.5rem 4rem 0.3rem 4rem;
    letter-spacing: -0.5px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.results-sub {
    color: #a1a1aa;
    font-size: 0.95rem;
    padding: 0 4rem 1.5rem 4rem;
}

/* Poster Styling */
.poster-img {
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    transition: transform 0.4s ease;
    width: 100%;
}
.movie-card:hover .poster-img {
    transform: scale(1.03);
}
.no-poster {
    background: linear-gradient(135deg, #18181b, #27272a);
    height: 300px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #52525b;
    font-weight: 600;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

/* Custom st.columns padding */
div[data-testid="column"] {
    padding: 0.5rem;
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
            try:
                r = float(movie["rating"])
                rating_display = f"&#11088; {r:.1f}/10"
            except:
                rating_display = "N/A"
            
            poster_html = f'<img src="{movie["poster"]}" class="poster-img">' if movie["poster"] else "<div class='no-poster'>No Poster</div>"

            st.markdown(f"""
            <div class="movie-card">
                {poster_html}
                <div class="movie-info">
                    <div class="movie-title">{movie['title']}</div>
                    <div class="movie-rating">{rating_display}</div>
                    <div class="movie-overview">{movie['overview']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    cols2 = st.columns(5)
    for idx, col in enumerate(cols2):
        movie = trending[idx + 5]
        with col:
            try:
                r = float(movie["rating"])
                rating_display = f"&#11088; {r:.1f}/10"
            except:
                rating_display = "N/A"
            
            poster_html = f'<img src="{movie["poster"]}" class="poster-img">' if movie["poster"] else "<div class='no-poster'>No Poster</div>"

            st.markdown(f"""
            <div class="movie-card">
                {poster_html}
                <div class="movie-info">
                    <div class="movie-title">{movie['title']}</div>
                    <div class="movie-rating">{rating_display}</div>
                    <div class="movie-overview">{movie['overview']}</div>
                </div>
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
            trailer_html = f'<a class="trailer-btn" href="{trailers[idx]}" target="_blank">Watch Trailer</a>' if trailers[idx] else '<span style="color:#555; font-size:0.8rem; display:block; margin-top:1rem">No trailer available</span>'
            poster_html = f'<img src="{posters[idx]}" class="poster-img">' if posters[idx] else "<div class='no-poster'>No Poster</div>"

            st.markdown(f"""
            <div class="movie-card">
                {poster_html}
                <div class="movie-info">
                    <div class="movie-title">{names[idx]}</div>
                    <div class="movie-rating">{rating_display}</div>
                    {genre_html}
                    <div class="movie-overview">{overviews[idx]}</div>
                    {trailer_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
