# Chatbot application
![Chatbot App Workflow](https://github.com/tnguyen2907/obot/tree/master/documentation/chatbot-workflow.png)

**Backend:** The app leverages **Langchain** for its RAG architecture and conversational capabilities.
- For each user query, the chatbot summarizes the entire conversation into a standalone question to enhance vector retrieval from the **Firestore**, improving the relevance of retrieved information.
- Once the relevant data is retrieved, the chatbot combines it with the user query to generate a comprehensive response, which is then displayed to the user.
- The chatbot is equipped with features to handle time-sensitive queries and includes safety checks to prevent harmful information.

**Frontend:** The app is built with **Streamlit** 

Deployment to GKE: For details, refer to the [CI/CD workflow](
