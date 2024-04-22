import streamlit as st

cv_contents = st.query_params.get('cv_contents', '')
if cv_contents:
    st.write(f"CV Contents: {cv_contents}")