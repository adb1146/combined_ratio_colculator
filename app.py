import streamlit as st
from streamlit_chat import message

# Set up the Streamlit app
st.title("Chat Application")

# Example usage of the `message` function from `streamlit_chat`
message("Hello, this is a test message!", is_user=True)