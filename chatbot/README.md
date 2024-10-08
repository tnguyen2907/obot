# Chatbot application
![Chatbot App Workflow](../assets/chatbot-workflow.png)

**Backend:** The app leverages **Langchain** for its RAG architecture and conversational capabilities.
- For each user query, the chatbot summarizes the entire conversation into a standalone question to enhance vector retrieval from the **Firestore**, improving the relevance of retrieved information.
- Once the relevant data is retrieved, the chatbot combines it with the user query to generate a comprehensive response, which is then displayed to the user.
- The chatbot is equipped with features to handle time-sensitive queries and includes safety checks to prevent harmful information.

**Frontend:** The app is built with **Streamlit** 

**Database:** The chatbot uses **Redis** for state management

**Deployment:** The chatbot is deployed on **Google Kubernetes Engine (GKE)** via a **Helm** chart. For more details, see the [CI/CD pipeline README](../.github/workflows/README.md).
