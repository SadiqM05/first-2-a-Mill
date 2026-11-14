import streamlit as st

st.set_page_config(
    page_title="ResLink AI",
    page_icon="📚",
    layout="wide"
)

st.title("ResLink AI")
st.subheader("Your Intelligent RA Resource Navigator")

st.write("Find resources, understand procedures, and get answers.")

question = st.chat_input("What do you need help with?")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        st.info("AI integration coming soon!")