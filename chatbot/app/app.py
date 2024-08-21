import streamlit as st

from rag import ConversationalRAG

if "chatbot" not in st.session_state:
    st.session_state["chatbot"] = ConversationalRAG()

# Streamlit app
st.title("Obot: Oberlin Chatbot")

st.caption("""***Disclaimer***: This chatbot is an AI language model and may sometimes produce incorrect or misleading information. \
For the most accurate and reliable information, please refer to the sources retrieved or visit the official Oberlin College website.""")


def print_sources(docs):
    sources = [doc.metadata['url'] for doc in docs]
    st.markdown("*Sources:*  \n" + "  \n".join(["{}".format(source) for source in sources]))

def fix_markdown(text):
    return text.replace("$", "\$")

for message in st.session_state["chatbot"].get_chat_history():
    # print(message)
    with st.chat_message(message["role"]):
        st.markdown(fix_markdown(message["content"]))
    if message["role"] == "assistant":
        print_sources(st.session_state["chatbot"].sources[message["source_index"]])

if input := st.chat_input("Ask a question about Oberlin College"):
    st.chat_message("user").markdown(input)
    # with st.spinner("Hmmmm..."):
    with st.empty():
        st.chat_message("assistant").markdown("*Hmmmm...*")
        response = st.session_state["chatbot"].get_completion(input)
        st.empty()
    if response != "SAFETY_EXCEPTION":
        st.chat_message("assistant").markdown(fix_markdown(response['answer']))
        print_sources(response['context'])    
    else:
        st.markdown("*Sorry, Obot has detected that this message could generate harmful content. Please rephrase your question or try asking something different.*")

if st.session_state["chatbot"].get_chat_history() != []:
    clear_history = st.button("Clear chat history")
    if clear_history:
        st.session_state["chatbot"].clear_chat_history()
        st.rerun() 