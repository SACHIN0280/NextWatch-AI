import streamlit as st
import pickle
import pandas as pd
import requests
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import streamlit.components.v1 as components

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

def fetch_full_movie_details(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{{movie_id}}?api_key={{API_KEY}}&language=en-US"
        data = requests.get(url, timeout=10).json()
        poster_path = data.get('poster_path', '')
        backdrop_path = data.get('backdrop_path', '')
        poster = f"https://image.tmdb.org/t/p/w500/{{poster_path}}" if poster_path else None
        backdrop = f"https://image.tmdb.org/t/p/original/{{backdrop_path}}" if backdrop_path else None
        
        r = data.get('vote_average', 0)
        rating = f"{{int(float(r) * 10)}}%" if r else "N/A"
        
        overview = data.get('overview', 'No description available.')
        genres = [g['name'] for g in data.get('genres', [])]
        title = data.get('title', 'Unknown')
        
        trailer_url = f"https://api.themoviedb.org/3/movie/{{movie_id}}/videos?api_key={{API_KEY}}&language=en-US"
        trailer_data = requests.get(trailer_url, timeout=10).json()
        trailer = None
        for video in trailer_data.get('results', []):
            if video['type'] == 'Trailer':
                trailer = f"https://www.youtube.com/watch?v={{video['key']}}"
                break
                
        return title, poster, backdrop, rating, overview, genres, trailer
    except Exception:
        return 'Unknown', None, None, 'N/A', 'No description available.', [], None

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

    return movie_names, posters, ratings, overviews, genres, trailers, movie_ids

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="NextWatch.AI", page_icon="🎬", layout="wide")

# -------------------- CSS --------------------
custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap');

* {{ font-family: 'Inter', sans-serif !important; }}
.stApp {{ 
    background: #05070D !important; 
    color: #FFFFFF !important;
    z-index: 0;
}}
.stApp::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100vh;
    background: linear-gradient(to top, #05070D 0%, rgba(5,7,13,0.4) 50%, #05070D 100%), 
                linear-gradient(to right, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 100%), 
                url("https://raw.githubusercontent.com/SACHIN0280/NextWatch-AI/main/bg_collage.png") no-repeat center center / cover;
    z-index: -1;
    filter: blur(3px);
    transform: scale(1.02); /* prevent blur edges */
}}

/* Custom Scrollbar */
::-webkit-scrollbar {{
    width: 10px;
}}
::-webkit-scrollbar-track {{
    background: #05070D; 
}}
::-webkit-scrollbar-thumb {{
    background: #1E293B; 
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: #CBD5E1; 
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
    color: #FF1E1E;
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -1px;
    text-shadow: 0 0 20px rgba(255, 30, 30, 0.4);
}}
.nav-icons {{
    display: flex;
    gap: 1.5rem;
    align-items: center;
}}
.nav-icons svg {{
    width: 24px;
    height: 24px;
    stroke: #FFFFFF;
    fill: none;
    cursor: pointer;
    transition: stroke 0.2s, transform 0.2s;
}}
.nav-icons svg:hover {{
    stroke: #FF1E1E;
    transform: scale(1.1);
}}

/* Search Area Glassmorphism */
div[data-testid="stHorizontalBlock"] {{
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 0.5rem 1rem;
    max-width: 800px;
    margin: 0 auto;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    align-items: center;
}}

/* Selectbox */
div[data-testid="stSelectbox"] > div {{
    background-color: #0F172A !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    min-height: 48px !important;
    display: flex;
    align-items: center;
}}
div[data-testid="stSelectbox"] label {{ display: none !important; }}

/* Buttons */
div[data-testid="stButton"] button {{
    background: #FF1E1E !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    font-size: 1.1rem !important;
    height: 48px !important;
    box-shadow: 0 0 15px rgba(255, 30, 30, 0.4) !important;
    transition: all 0.3s ease !important;
}}
div[data-testid="stButton"] button:hover {{
    background: #ff3333 !important;
    box-shadow: 0 0 25px rgba(255, 30, 30, 0.6) !important;
    transform: translateY(-2px) !important;
}}

/* Slider Wrapper */
.slider-wrapper {{
    position: relative;
    padding: 0 1rem;
    margin-bottom: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}}
.slider-row {{
    display: flex;
    gap: 15px;
    overflow-x: auto;
    padding-bottom: 2rem;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    -ms-overflow-style: none;
    scrollbar-width: none;
}}
.center-row {{
    justify-content: center;
}}
.slider-row::-webkit-scrollbar {{
    display: none;
}}
.slider-item {{
    flex: 0 0 180px; 
    scroll-snap-align: start;
}}
.slider-btn {{
    position: absolute;
    top: 45%;
    transform: translateY(-50%);
    z-index: 10;
    background: rgba(15, 23, 42, 0.8);
    color: #FFFFFF;
    border: 1px solid rgba(255,255,255,0.08);
    font-size: 2.5rem;
    padding: 1rem 0.5rem;
    cursor: pointer;
    opacity: 0;
    transition: all 0.3s ease;
    height: 90%;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
    border-radius: 8px;
}}
.slider-wrapper:hover .slider-btn {{
    opacity: 1;
}}
.slider-btn:hover {{
    background: #1E293B;
    color: #FF1E1E;
}}
.left-btn {{
    left: 0;
    border-radius: 0 8px 8px 0;
}}
.right-btn {{
    right: 0;
    border-radius: 8px 0 0 8px;
}}

/* Movie Card Wrappers */
.movie-card {{
    position: relative;
    background: #0F172A;
    aspect-ratio: 2 / 3;
    border-radius: 12px;
    transition: transform 0.3s ease, z-index 0.3s ease, box-shadow 0.3s ease;
    cursor: pointer;
    z-index: 1;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
}}
.movie-card:hover {{
    transform: scale(1.05) translateY(-8px);
    z-index: 100;
    box-shadow: 0 20px 40px rgba(0,0,0,0.8), 0 0 20px rgba(255, 30, 30, 0.2);
}}

/* Movie Info */
.movie-info {{ 
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 100%;
    padding: 2rem 1rem 1rem 1rem;
    background: linear-gradient(to top, rgba(5,7,13,1) 0%, rgba(5,7,13,0.9) 60%, transparent 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
}}
.movie-card:hover .movie-info {{
    opacity: 1;
}}

.movie-title {{
    color: #FFFFFF;
    font-weight: 800;
    font-size: 1.1rem;
    margin-bottom: 0.3rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.movie-rating {{
    color: #46d369; 
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 0.4rem;
}}
.movie-cast {{
    display: none;
}}
.movie-overview {{
    color: #CBD5E1;
    font-size: 0.75rem;
    margin-bottom: 0.5rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
.genre-tag {{
    color: #CBD5E1;
    font-size: 0.75rem;
    margin-right: 0.3rem;
}}
.genre-tag::after {{
    content: ' •';
    color: rgba(255,255,255,0.2);
    margin-left: 0.3rem;
}}
.genre-tag:last-child::after {{
    content: '';
}}
.trailer-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 0.5rem;
    background: rgba(255,255,255,0.1);
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.2);
    padding: 0.4rem 1rem;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    text-decoration: none !important;
    width: 100%;
    transition: all 0.2s ease;
    backdrop-filter: blur(4px);
}}
.trailer-btn:hover {{
    background: #FF1E1E;
    border-color: #FF1E1E;
}}

/* Headers */
.results-header {{
    color: #FFFFFF;
    font-size: 2rem;
    font-weight: 800;
    padding: 2rem 1rem 0.5rem 1rem;
    max-width: 1200px;
    margin: 0 auto;
    text-align: center;
}}
.results-sub {{
    color: #CBD5E1;
    font-size: 1.1rem;
    padding: 0 1rem 2rem 1rem;
    max-width: 1200px;
    margin: 0 auto;
    text-align: center;
}}

/* Poster Styling */
.poster-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}}
.no-poster {{
    background: #0F172A;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #CBD5E1;
    font-weight: 500;
}}

/* Custom st.columns padding */
div[data-testid="column"] {{
    padding: 0.25rem;
}}
div[data-testid="stSpinner"] {{ color: #FF1E1E !important; }}
div, span, p, label {{ color: inherit; }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------- ROUTING --------------------
query_params = st.query_params
if "movie_id" in query_params:
    movie_id = query_params["movie_id"]
    title, poster, backdrop, rating, overview, genres, trailer = fetch_full_movie_details(movie_id)
    
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
    if st.button("❮ Back to Home", key="back_btn"):
        del st.query_params["movie_id"]
        st.rerun()
        
    bg_img = backdrop if backdrop else (poster if poster else "")
    st.markdown(f"""
    <div style="position: absolute; top:0; left:0; width:100%; height:70vh; background: url('{bg_img}') center/cover; opacity:0.15; z-index:-1; filter:blur(8px); mask-image: linear-gradient(to bottom, black 40%, transparent 100%); -webkit-mask-image: linear-gradient(to bottom, black 40%, transparent 100%);"></div>
    <div style="max-width: 1200px; margin: 0 auto; display: flex; gap: 4rem; padding: 2rem 1rem 4rem 1rem; align-items: flex-start; flex-wrap: wrap;">
        <img src="{poster}" style="border-radius: 16px; width: 350px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.1);">
        <div style="flex: 1; min-width: 300px; padding-top: 1rem;">
            <h1 style="font-size: 4rem; font-weight:800; margin-bottom: 0.5rem; line-height: 1.1; color: #FFFFFF; text-shadow: 0 4px 20px rgba(0,0,0,0.5);">{title}</h1>
            <div style="color: #46d369; font-size: 1.2rem; font-weight:700; margin-bottom: 1rem;">{rating} Match</div>
            <div style="margin-bottom: 1.5rem;">{" ".join([f'<span class="genre-tag" style="font-size:1rem;">{g}</span>' for g in genres])}</div>
            <p style="font-size: 1.2rem; line-height: 1.6; color: #CBD5E1; margin-bottom: 2rem; max-width: 800px;">{overview}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if trailer:
        st.markdown("<h2 style='max-width: 1200px; margin: 0 auto; padding: 0 1rem; margin-bottom: 1rem; font-weight: 800;'>Official Trailer</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 10, 1])
        with col2:
            st.video(trailer)
            
    st.stop() # Halt execution so the home page does not render

# -------------------- HERO & SEARCH --------------------
st.markdown("""
<div class="nav-header">
    <div class="nav-logo">NEXTWATCH.AI</div>
    <div class="nav-icons">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
    </div>
</div>
<div style="height: 15vh;"></div>
<div style="text-align: center; max-width: 900px; margin: 0 auto; padding: 2rem; position: relative; z-index: 2;">
    <h1 style="font-size: 4.5rem; font-weight: 800; color: #FFFFFF; margin-bottom: 1rem; line-height: 1.1; text-shadow: 0 4px 20px rgba(0,0,0,0.5);">Discover your next cinematic obsession.</h1>
    <p style="font-size: 1.5rem; color: #CBD5E1; margin-bottom: 2rem; font-weight: 500;">Powered by AI. Discover hidden gems instantly.</p>
    <p style="font-size: 1.2rem; color: #CBD5E1; margin-bottom: 1.5rem;">Ready to watch? Search for a movie to get recommendations.</p>
</div>
""", unsafe_allow_html=True)

search_col, btn_col = st.columns([7, 3])
with search_col:
    selected_movie = st.selectbox("Email address", movies['title'].values, label_visibility="collapsed")
with btn_col:
    search_clicked = st.button("Get Started >")
st.markdown('<div style="height: 15vh;"></div>', unsafe_allow_html=True)

MovieSlider = components.declare_component("movie_slider", path="movie_slider")

# -------------------- TRENDING --------------------
trending = fetch_trending()
if trending:
    st.markdown("""
    <div style='max-width: 1200px; margin: 0 auto; padding: 2rem 1rem 1rem 1rem;'>
        <div style='color:#FFFFFF; font-size:2rem; font-weight:800; margin-bottom:0.3rem'>Trending This Week</div>
        <div style='color:#CBD5E1; font-size:1.1rem; margin-bottom:1.5rem; font-weight:500;'>Most popular movies right now</div>
    </div>
    """, unsafe_allow_html=True)

    for m in trending:
        try:
            r = float(m["rating"])
            m["rating"] = f"{int(r * 10)}% Match"
        except:
            m["rating"] = "N/A"
            
    clicked_trend = MovieSlider(movies=trending, mode="slider", key="trending_slider")
    if clicked_trend:
        st.query_params["movie_id"] = clicked_trend
        st.rerun()

# -------------------- RESULTS --------------------
if search_clicked:
    with st.spinner('Finding recommendations...'):
        names, posters, ratings, overviews, genres, trailers, movie_ids = recommend(selected_movie)

    st.markdown(f"""
    <div class="results-header">Recommended for you</div>
    <div class="results-sub">Because you liked <strong style="color:#FFFFFF">{selected_movie}</strong></div>
    """, unsafe_allow_html=True)

    results_data = []
    for idx in range(len(names)):
        try:
            r = float(ratings[idx])
            rating_display = f"{int(r * 10)}% Match"
        except:
            rating_display = "N/A"

        results_data.append({
            "id": str(movie_ids[idx]),
            "title": names[idx],
            "poster": posters[idx],
            "rating": rating_display,
            "overview": overviews[idx],
            "genres": genres[idx]
        })

    clicked_res = MovieSlider(movies=results_data, mode="grid", key="results_slider")
    if clicked_res:
        st.query_params["movie_id"] = clicked_res
        st.rerun()
