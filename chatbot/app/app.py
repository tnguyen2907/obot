import streamlit as st
from datetime import datetime, timedelta, timezone
import os
import redis

from rag import ConversationalRAG, start_message

MAX_MESSAGES_IN_ONE_CONVERSATION = 12
MAX_REQUESTS_WEEKLY = 50

if "chatbot" not in st.session_state:
    st.session_state["chatbot"] = ConversationalRAG()

# Initialize Redis client
redis_client = redis.Redis(host="redis-service-dev", port=6379, db=0, decode_responses=True)

# Read state from redis
def read_state():
    num_requests = redis_client.get("num_requests")
    next_reset_date = redis_client.get("next_reset_date")
    
    if num_requests is not None and next_reset_date is not None:
        return {
            "num_requests": int(num_requests),  # Convert num_requests back to integer
            "next_reset_date": datetime.fromisoformat(next_reset_date)  # Convert back to datetime
        }
    return None

#Write state to redis
def write_state(state):
    redis_client.set("num_requests", state["num_requests"])
    redis_client.set("next_reset_date", state["next_reset_date"].isoformat())

# Initialize or update app state from the local file
chatbot_state = read_state()
next_reset_date = datetime.now(timezone(timedelta(hours=-4))).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now(timezone(timedelta(hours=-4))).weekday()) + timedelta(days=7)
num_requests = 0

if chatbot_state is None:
    chatbot_state = {"num_requests": 0, "next_reset_date": next_reset_date.isoformat()}
    write_state(chatbot_state)
else:
    state_updated = False
    chatbot_state["next_reset_date"] = datetime.fromisoformat(chatbot_state["next_reset_date"])
    if "next_reset_date" not in chatbot_state:
        chatbot_state["next_reset_date"] = next_reset_date
        state_updated = True
    if "num_requests" in chatbot_state:
        num_requests = chatbot_state["num_requests"]  # Temporary num_requests for display
    if "num_requests" not in chatbot_state or datetime.now(timezone(timedelta(hours=-4))) > chatbot_state["next_reset_date"]:
        chatbot_state["num_requests"] = 0
        chatbot_state["next_reset_date"] = next_reset_date
        state_updated = True
    if state_updated:
        write_state(chatbot_state)

st.title("Obot: Oberlin Chatbot")

st.caption("""***Disclaimer***: This chatbot is an AI language model and may sometimes produce incorrect or misleading information. \
For the most accurate and reliable information, please refer to the sources retrieved or visit the official Oberlin College website.""")

with st.sidebar:
    st.markdown(f"### 🔄 **Weekly Requests Used: {num_requests} / {MAX_REQUESTS_WEEKLY}**")
    st.markdown("*Note: This number may have increased due to other users' usage*")
    st.markdown("---")
    st.markdown("### **About**")
    st.markdown("This chatbot uses data from Oberlin College's website and catalog to answer questions.")
    st.markdown("---")
    st.markdown("### 💡 **Tips**")
    st.markdown("- **Be specific** in your questions *(especially if they are time-sensitive.)*")
    st.markdown("- **Start a new conversation** if the chatbot repeatedly fails to answer your questions.")
    st.markdown("- **Rephrasing questions** may help the chatbot retrieve better results *(e.g. P/NP may work better than Pass/No Pass.)*")

def fix_markdown(text):
    return text.replace("$", "\$")

# Display chat history
for message in st.session_state["chatbot"].get_chat_history():
    with st.chat_message(message["role"]):
        st.markdown(fix_markdown(message["content"]))

# Main chatbot logic
if len(st.session_state["chatbot"].get_chat_history()) < MAX_MESSAGES_IN_ONE_CONVERSATION:
    if input := st.chat_input("Ask a question about Oberlin College"):
        chatbot_state = read_state()
        if chatbot_state["num_requests"] < MAX_REQUESTS_WEEKLY:
            st.chat_message("user").markdown(input)
            with st.empty():
                st.chat_message("assistant").markdown("*Hmmmm...*")
                response = st.session_state["chatbot"].get_completion(input)
                chatbot_state["num_requests"] += 1
                write_state(chatbot_state)
                st.empty()

            if response == "SAFETY_EXCEPTION":
                st.markdown("*Sorry, Obot has detected that this message could generate harmful content.* 🤐 *Please rephrase your question or try asking something different.*")
            elif response == "RESOURCE_EXHAUSTED":
                st.markdown("*Sorry, Obot is currently overloaded and cannot answer your question. Please wait one minute.* 😢  \n*If the problem persists, the daily limit of number of questions may have been reached.* 😭")          
            else:
                st.chat_message("assistant").markdown(fix_markdown(response['answer']))
                st.rerun()
        else:
            st.markdown("*Sorry, the weekly request limit has been reached.* 😭 Please try again next week")
else:
    st.markdown("*Sorry, this conversation has reached the maximum number of messages.*  😪 *Please start a new conversation.*")

# Clear chat history button
if len(st.session_state["chatbot"].get_chat_history()) > 1:
    clear_history = st.button("Clear chat history")
    if clear_history:
        st.session_state["chatbot"].clear_chat_history()
        st.rerun()
