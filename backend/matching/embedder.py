import streamlit as st

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


@st.cache_resource(show_spinner=False)
def get_model() -> SentenceTransformer:
    """
    Load and cache the Sentence Transformer model.

    Streamlit keeps this model in memory between reruns so we don't
    repeatedly load the model every time the UI changes.
    """
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str):
    """
    Convert one piece of text into a normalized embedding.
    """
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")

    return get_model().encode(
        text,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )


def embed_texts(texts: list[str]):
    """
    Convert multiple texts into embeddings in one batch.
    """
    cleaned = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not cleaned:
        return None

    return get_model().encode(
        cleaned,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )