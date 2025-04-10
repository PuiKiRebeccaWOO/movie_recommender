import streamlit as st
import pandas as pd
import pickle
import requests
import os

# Google Drive download
FILE_ID = "1wlWqAaWzsfArkV10kBknQ4Rg8T42ZK5b"
URL = f"https://drive.google.com/uc?id={FILE_ID}"

LOCAL_PATH = "app/cosine_sim.pkl"

# Download cosine_sim.pkl if not already downloaded
if not os.path.exists(LOCAL_PATH):
    st.info("📥 Downloading similarity matrix...")
    with open(LOCAL_PATH, "wb") as f:
        response = requests.get(URL)
        f.write(response.content)

# Now load the file
with open(LOCAL_PATH, "rb") as f:
    cosine_sim = pickle.load(f)

# Load data
with open('app/new_df.pkl', 'rb') as f:
    new_df = pickle.load(f)

# Reverse index for recommendation
indices = pd.Series(new_df.index, index=new_df['title']).drop_duplicates()

# Recommender function
def recommend(title):
    if title not in new_df['title'].values:
        st.warning("Title not found.")
        return pd.DataFrame()

    idx = new_df[new_df['title'] == title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = [(i, float(score)) for i, score in sim_scores]
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
    movie_indices = [i[0] for i in sim_scores]
    return new_df.iloc[movie_indices]


# App interface
st.image("img/cinematch_banner.gif", use_column_width=True)

st.sidebar.markdown("## 🍿 **CineMatch**")
st.sidebar.markdown("_Find your next favorite movie in seconds._")
st.sidebar.markdown("## **Navigation**")
option = st.sidebar.radio("Choose a method", ["✨ Movie Matchmaker", "🎬 Pick Your Preferences"])


if option == "✨ Movie Matchmaker":
    user_input = st.text_input("🎥 Enter a movie you like — we’ll recommend similar ones!")

    matching_titles = new_df[new_df['title'].str.contains(user_input, case=False, na=False)]['title'] if user_input else pd.Series(dtype=str)

    if not matching_titles.empty:
        selected_title = st.selectbox("Select a matching title", matching_titles.sort_values())

        if st.button("Recommend"):
            selected_row = new_df[new_df['title'] == selected_title].iloc[0]
            release_year = selected_row['release_date'].year if pd.notnull(selected_row['release_date']) else "N/A"
        
            # Format rating
            rating = selected_row['vote_average']
            votes = selected_row['vote_count']
            formatted_votes = f"{int(votes):,}" if votes < 1000 else f"{int(votes // 1000)}k"
            rating_display = f"⭐ {rating:.1f} ({formatted_votes})"
        
            st.subheader("🎯 You Picked")
        
            # Layout: Poster on left, details on right
            col1, col2 = st.columns([1, 2])
        
            with col1:
                st.image(selected_row['poster_url'], width=180)
        
            with col2:
                st.markdown(f"### **{selected_row['title']}** ({release_year})")
                st.markdown(f"{rating_display}")
                st.markdown(f"🎭 **Genres**: {', '.join(selected_row['genres'])}")
                st.markdown(f"🧑‍🎤 **Cast**: {', '.join(selected_row['cast'][:3])}")
                st.markdown(f"🎬 **Director**: {selected_row['director']}")
                st.markdown("📖 **Overview**")
                st.write(selected_row['overview'])
        
            st.markdown("---")
            st.subheader("🍿 Movies You Might Like")
        
            # ✅ NOW we recommend similar movies and show them
            results = recommend(selected_title)
            for _, row in results.iterrows():
                release_year = row['release_date'].year if pd.notnull(row['release_date']) else "N/A"
                rating = row['vote_average']
                votes = row['vote_count']
                formatted_votes = f"{int(votes):,}" if votes < 1000 else f"{int(votes // 1000)}k"
                rating_display = f"⭐ {rating:.1f} ({formatted_votes})"
        
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(row['poster_url'], width=120)
        
                with col2:
                    st.markdown(f"**{row['title']}** ({release_year})")
                    st.markdown(f"{rating_display}")
                    st.markdown(f"🎭 Genres: {', '.join(row['genres'])}")
                    st.markdown(f"🧑‍🎤 Cast: {', '.join(row['cast'][:3])}")
                    st.markdown(f"🎬 Director: {row['director']}")
                    st.markdown(f"📖 {row['overview'][:1000]}")
        
                st.markdown("---")
    
    elif user_input:
        st.warning("No matching titles found. Try typing something else.")

elif option == "🎬 Pick Your Preferences":
    # Add filters
    genre = st.multiselect("Select genres", sorted({g for sublist in new_df['genres'] for g in sublist}))
    # Unique sorted options
    director_list = sorted(set(new_df['director']))
    cast_list = sorted({actor for sublist in new_df['cast'] for actor in sublist})
    # Dropdown with search
    director = st.selectbox("🎬 Select a Director", options=[""] + director_list)
    cast = st.selectbox("🧑‍🎤 Select a Cast Member", options=[""] + cast_list)
    year_range = st.slider("Release Year", 1980, 2025, (2000, 2020))
    min_runtime = st.slider("Minimum Runtime (min)", 60, 240, 90)

    # Filter logic
    filtered_df = new_df.copy()
    if genre:
        filtered_df = filtered_df[filtered_df['genres'].apply(lambda x: any(g in x for g in genre))]
    if director:
        filtered_df = filtered_df[filtered_df['director'].str.contains(director, case=False, na=False)]
    if cast:
        filtered_df = filtered_df[filtered_df['cast'].apply(lambda x: any(cast.lower() in member.lower() for member in x))]

    filtered_df = filtered_df[pd.notnull(filtered_df['release_date']) & filtered_df['release_date'].dt.year.between(*year_range)]
    filtered_df = filtered_df[filtered_df['runtime'] >= min_runtime]

    st.write(f"🎯 {len(filtered_df)} result(s) found:")
    for _, row in filtered_df.head(10).iterrows():
        release_year = row['release_date'].year if pd.notnull(row['release_date']) else "N/A"
        rating = row['vote_average']
        votes = row['vote_count']
        formatted_votes = f"{int(votes):,}" if votes < 1000 else f"{int(votes // 1000)}k"
        rating_display = f"⭐ {rating:.1f} ({formatted_votes})"

        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(row['poster_url'], width=120)

        with col2:
            st.markdown(f"**{row['title']}** ({release_year})")
            st.markdown(f"{rating_display}")
            st.markdown(f"🎭 Genres: {', '.join(row['genres'])}")
            st.markdown(f"🧑‍🎤 Cast: {', '.join(row['cast'][:3])}")
            st.markdown(f"🎬 Director: {row['director']}")
            st.markdown(f"📖 {row['overview'][:1000]}")

        st.markdown("---")

