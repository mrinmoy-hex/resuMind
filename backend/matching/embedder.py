import streamlit as st
from sentence_transformers import SentenceTransformer

_model = None   # cached

@st.cache_resource
def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # download the model, then read from local HF cache on future runs
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str):
    # converts the text into a 384-dim vector representing its meaning
    return get_model().encode(text, convert_to_tensor=True)