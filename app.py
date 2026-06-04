import streamlit as st
import pickle
import pandas as pd
import requests
import base64
from concurrent.futures import ThreadPoolExecutor

# -------------------- CONFIG --------------------
API_KEY = "21dc30dc0e6b7c30e8abc1fd5aaca6e8"

# -------------------- LOAD FILES --------------------
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity_compressed.pkl', 'rb'))

# -------------------- BACKGROUND --------------------
def set_background(image_file):
    with open(image_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{data}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .block-container {{
        background-color: transparent !important;
        padding-top: 8rem !important;
    }}
    /* Netflix-style title */
    h1 {{
        color: #E50914 !important;
        text-align: center !important;
        font-size: 4rem !important;
        font-weight: 900 !important;
        font-family: 'Arial Black', sans-serif !important;
        text-shadow: 2px 2px 0px #000, 4px 4px 0px rgba(0,0,0,0.3) !important;
        letter-spacing: 2px !important;
        margin-bottom: 0.5rem !important;
    }}
    /* Subtitle */
    p {{
        text-align: center !important;
        color: white !important;
        text-shadow: 1px 1px 3px black !important;
    }}
    /* Center and style selectbox */
    div[data-testid="stSelectbox"] {{
        width: 100% !important;
        margin: 0 auto !important;
    }}
    div[data-testid="stSelectbox"] label {{
        display: none !important;
    }}
    div[data-testid="stSelectbox"] > div {{
        background-color: rgba(0,0,0,0.7) !important;
        border: 1px solid #E50914 !important;
        border-radius: 5px !important;
        color: white !important;
    }}
    /* Center search button */
    div[data-testid="stButton"] {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }}
    div[data-testid="stButton"] button {{
        background-color: #E50914 !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 0.6rem 4rem !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        width: 100% !important;
    }}
    div[data-testid="stButton"] button:hover {{
        background-color: #b20710 !important;
    }}
    /* White text everywhere */
    div, span, label {{
        color: white !important;
    }}
    /* Results dark background */
    div[data-testid="stColumns"] {{
        background-color: rgba(0, 0, 0, 0.75);
        border-radius: 10px;
        padding: 1rem;
        margin-top: 2rem;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# -------------------- FETCH MOVIE DETAILS --------------------
def fetch_movie_details(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        data = requests.get(url, timeout=10).json()
        poster_path = data.get('poster_path', '')
        poster = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        rating = data.get('vote_average', 'N/A')
        return poster, rating
    except Exception:
        return None, 'N/A'

# -------------------- FETCH TRAILER --------------------
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

# -------------------- FETCH ALL --------------------
def fetch_all(movie_id):
    poster, rating = fetch_movie_details(movie_id)
    trailer = fetch_trailer(movie_id)
    return poster, rating, trailer

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

    posters = [r[0] for r in results]
    ratings = [r[1] for r in results]
    trailers = [r[2] for r in results]

    return movie_names, posters, ratings, trailers

# -------------------- UI --------------------
# -------------------- UI --------------------
set_background("Image.jpg")

st.markdown("<h1>NEXTWATCH.AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:1.1rem; color:#cccccc; text-shadow: 1px 1px 3px black;'>Find movies you'll love</p>", unsafe_allow_html=True)

# Force button to align with selectbox using custom HTML layout
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    st.markdown("""
    <style>
    /* Make selectbox and button sit on same row */
    [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 8px !important;
    }
    /* Fix button height and prevent text wrap */
    [data-testid="stButton"] button {
        height: 45px !important;
        white-space: nowrap !important;
        padding: 0 20px !important;
        margin-top: 4px !important;
        background-color: #E50914 !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        font-size: 1rem !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

    search_col, btn_col = st.columns([4, 1])
    with search_col:
        selected_movie = st.selectbox("", movies['title'].values)
    with btn_col:
        search_clicked = st.button("🔍")

# -------------------- RESULTS --------------------
if search_clicked:
    with st.spinner('Finding recommendations...'):
        names, posters, ratings, trailers = recommend(selected_movie)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]

    for idx, col in enumerate(cols):
        with col:
            st.text(names[idx])
            if posters[idx]:
                st.image(posters[idx])
            else:
                st.write("No poster available")
            st.write(f"⭐ {ratings[idx]}")
            if trailers[idx]:
                st.markdown(f"[▶ Trailer]({trailers[idx]})")
            else:
                st.write("No trailer")