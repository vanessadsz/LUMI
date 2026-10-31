import os
import streamlit as st

st.title("Gemini Model Check")

try:
    from google import genai

    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    api_key = api_key or os.environ.get("GEMINI_API_KEY")

    if not api_key:
        st.warning("Missing GEMINI_API_KEY in .streamlit/secrets.toml or environment.")
    else:
        client = genai.Client(api_key=api_key)
        models = list(client.models.list())

        for model in models:
            if "generateContent" in (
                getattr(model, "supported_actions", []) or []
            ):
                st.write(model.name)

except Exception as e:
    st.error(str(e))
