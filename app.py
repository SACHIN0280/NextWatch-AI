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
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@300;400;500;700&display=swap');

* {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }}
.stApp {{ 
    background: #141414 !important; 
    color: #e5e5e5 !important;
    z-index: 0;
}}
.stApp::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 75vh;
    background: linear-gradient(to top, #141414 0%, rgba(20,20,20,0.2) 50%, rgba(20,20,20,0.8) 100%), 
                linear-gradient(to right, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 100%), 
                url("https://raw.githubusercontent.com/SACHIN0280/NextWatch-AI/main/bg_collage.png") no-repeat center center / cover;
    z-index: -1;
    border-bottom: 8px solid #222;
}}

/* Custom Scrollbar */
::-webkit-scrollbar {{
    width: 10px;
}}
::-webkit-scrollbar-track {{
    background: #141414; 
}}
::-webkit-scrollbar-thumb {{
    background: #333; 
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: #52525b; 
}}

.block-container {{ padding: 0 !important; max-width: 100% !important; margin-top: -6rem; }}

/* Nav Header */
.nav-header {{
    position: relative;
    width: 100%;
    padding: 2rem 4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 10;
}}
.nav-logo {{
    color: #E50914;
    font-size: 2.5rem;
    font-weight: 900;
    letter-spacing: -1px;
}}
.nav-signin {{
    background: #E50914;
    color: white;
    padding: 0.4rem 1rem;
    border-radius: 4px;
    font-weight: bold;
    text-decoration: none;
    font-size: 0.9rem;
}}

/* Selectbox */
div[data-testid="stSelectbox"] > div {{
    background-color: rgba(0, 0, 0, 0.7) !important;
    border: 1px solid #333 !important;
    border-radius: 4px !important;
    color: white !important;
}}
div[data-testid="stSelectbox"] label {{ display: none !important; }}

/* Buttons */
div[data-testid="stButton"] button {{
    background: #e50914 !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: bold !important;
    font-size: 1.1rem !important;
    height: 48px !important;
    transition: background 0.2s ease !important;
}}
div[data-testid="stButton"] button:hover {{
    background: #f40612 !important;
}}

/* Slider Row */
.slider-wrapper {{
    position: relative;
    padding: 0 4rem;
    margin-bottom: 2rem;
}}
.slider-row {{
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 1.5rem;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    -ms-overflow-style: none;
    scrollbar-width: none;
}}
.slider-row::-webkit-scrollbar {{
    display: none;
}}
.slider-item {{
    flex: 0 0 160px;
    scroll-snap-align: start;
}}
.slider-btn {{
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
    background: rgba(0,0,0,0.5);
    color: white;
    border: none;
    font-size: 2.5rem;
    padding: 1rem 0.5rem;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.3s, background 0.3s;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.slider-wrapper:hover .slider-btn {{
    opacity: 1;
}}
.slider-btn:hover {{
    background: rgba(0,0,0,0.8);
}}
.left-btn {{
    left: 0;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}}
.right-btn {{
    right: 0;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}}

/* Movie Card Wrappers */
.movie-card {{
    position: relative;
    background: #141414;
    height: 100%;
    border-radius: 4px;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), z-index 0.3s, box-shadow 0.3s;
    cursor: pointer;
    z-index: 1;
}}
.movie-card:hover {{
    transform: scale(1.15) translateY(-10px);
    z-index: 100;
    box-shadow: 0 10px 20px rgba(0,0,0,0.8);
    border-radius: 4px;
}}

/* Movie Info */
.movie-info {{ 
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 1.5rem 1rem 1rem 1rem;
    background: linear-gradient(to top, rgba(20,20,20,1) 0%, rgba(20,20,20,0.8) 60%, transparent 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
}}
.movie-card:hover .movie-info {{
    opacity: 1;
}}

.movie-title {{
    color: #fff;
    font-weight: bold;
    font-size: 1rem;
    margin-bottom: 0.2rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.movie-rating {{
    color: #46d369; /* Netflix Match Green */
    font-size: 0.85rem;
    font-weight: bold;
    margin-bottom: 0.4rem;
}}
.movie-cast {{
    display: none;
}}
.genre-tag {{
    color: #fff;
    font-size: 0.75rem;
    margin-right: 0.3rem;
}}
.genre-tag::after {{
    content: ' •';
    color: #646464;
    margin-left: 0.3rem;
}}
.genre-tag:last-child::after {{
    content: '';
}}
.movie-overview {{
    display: none;
}}
.trailer-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 0.5rem;
    background: white;
    color: black !important;
    padding: 0.4rem 1rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: bold;
    text-decoration: none !important;
    width: 100%;
    transition: background 0.2s;
}}
.trailer-btn:hover {{
    background: #e6e6e6;
}}

/* Headers */
.results-header {{
    color: #e5e5e5;
    font-size: 1.6rem;
    font-weight: bold;
    padding: 2rem 4rem 0.5rem 4rem;
}}
.results-sub {{
    display: none;
}}

/* Poster Styling */
.poster-img {{
    width: 100%;
    border-radius: 4px;
    display: block;
}}
.no-poster {{
    background: #222;
    height: 300px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    font-weight: bold;
}}

/* Custom st.columns padding */
div[data-testid="column"] {{
    padding: 0.25rem;
}}
div[data-testid="stSpinner"] {{ color: white !important; }}
div, span, p, label {{ color: inherit; }}
</style>
""", unsafe_allow_html=True)

# -------------------- HERO & SEARCH --------------------
st.markdown("""
<div class="nav-header">
    <div class="nav-logo">NEXTWATCH.AI</div>
</div>
<div style="height: 10vh;"></div>
<div style="text-align: center; max-width: 800px; margin: 0 auto; padding: 2rem;">
    <h1 style="font-size: 3.5rem; font-weight: 900; color: white; margin-bottom: 1rem; line-height: 1.2;">Discover your next cinematic obsession.</h1>
    <p style="font-size: 1.5rem; color: white; margin-bottom: 2rem; font-weight: 500;">Powered by AI. Discover hidden gems instantly.</p>
    <p style="font-size: 1.2rem; color: white; margin-bottom: 1.5rem;">Ready to watch? Search for a movie to get recommendations.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="max-width: 800px; margin: 0 auto;">', unsafe_allow_html=True)
search_col, btn_col = st.columns([7, 3])
with search_col:
    selected_movie = st.selectbox("Email address", movies['title'].values, label_visibility="collapsed")
with btn_col:
    search_clicked = st.button("Get Started >")
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div style="height: 12vh;"></div>', unsafe_allow_html=True)

# -------------------- TRENDING --------------------
trending = fetch_trending()
if trending:
    st.markdown("""
    <div style='padding: 2rem 4rem 1rem 4rem; border-top: 1px solid #1a1a1a;'>
        <div style='color:white; font-size:1.3rem; font-weight:700; margin-bottom:0.3rem'>Trending This Week</div>
        <div style='color:#666; font-size:0.85rem; margin-bottom:1.5rem'>Most popular movies right now</div>
    </div>
    """, unsafe_allow_html=True)

    slider_html = '''<div class="slider-wrapper">
        <button class="slider-btn left-btn" onclick="this.nextElementSibling.scrollBy({left: -600, behavior: 'smooth'})">&#10094;</button>
        <div class="slider-row">'''
    for movie in trending:
        try:
            r = float(movie["rating"])
            rating_display = f"{int(r * 10)}% Match"
        except:
            rating_display = "N/A"
        
        poster_html = f'<img src="{movie["poster"]}" class="poster-img">' if movie["poster"] else "<div class='no-poster'>No Poster</div>"

        slider_html += f"""
        <div class="slider-item">
            <div class="movie-card">
                {poster_html}
                <div class="movie-info">
                    <div class="movie-title">{movie['title']}</div>
                    <div class="movie-rating">{rating_display}</div>
                    <div class="movie-overview">{movie['overview']}</div>
                </div>
            </div>
        </div>
        """
    slider_html += '''</div>
        <button class="slider-btn right-btn" onclick="this.previousElementSibling.scrollBy({left: 600, behavior: 'smooth'})">&#10095;</button>
    </div>'''
    st.markdown(slider_html, unsafe_allow_html=True)

# -------------------- RESULTS --------------------
if search_clicked:
    with st.spinner('Finding recommendations...'):
        names, posters, ratings, overviews, genres, trailers = recommend(selected_movie)

    st.markdown(f"""
    <div class="results-header">Recommended for you</div>
    <div class="results-sub">Because you liked <strong style="color:white">{selected_movie}</strong></div>
    """, unsafe_allow_html=True)

    slider_html = '''<div class="slider-wrapper">
        <button class="slider-btn left-btn" onclick="this.nextElementSibling.scrollBy({left: -600, behavior: 'smooth'})">&#10094;</button>
        <div class="slider-row">'''
    for idx in range(len(names)):
        try:
            r = float(ratings[idx])
            rating_display = f"{int(r * 10)}% Match"
        except:
            rating_display = "N/A"

        genre_html = "".join([f'<span class="genre-tag">{g}</span>' for g in genres[idx]])
        trailer_html = f'<a class="trailer-btn" href="{trailers[idx]}" target="_blank">Watch Trailer</a>' if trailers[idx] else '<span style="color:#555; font-size:0.8rem; display:block; margin-top:1rem">No trailer available</span>'
        poster_html = f'<img src="{posters[idx]}" class="poster-img">' if posters[idx] else "<div class='no-poster'>No Poster</div>"

        slider_html += f"""
        <div class="slider-item">
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
        </div>
        """
    slider_html += '''</div>
        <button class="slider-btn right-btn" onclick="this.previousElementSibling.scrollBy({left: 600, behavior: 'smooth'})">&#10095;</button>
    </div>'''
    st.markdown(slider_html, unsafe_allow_html=True)
