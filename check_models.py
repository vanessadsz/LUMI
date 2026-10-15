
import streamlit as st
from google import genai

st.title("Gemini Model Check")

try:
    client = genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )

    models = list(client.models.list())

    for model in models:
        if "generateContent" in (
            getattr(model, "supported_actions", []) or []
        ):
            st.write(model.name)

except Exception as e:
    st.error(str(e))
