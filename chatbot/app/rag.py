import os
from langchain_google_firestore import FirestoreVectorStore
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory
from google.api_core.exceptions import ResourceExhausted
from datetime import datetime

GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
os.environ["GCLOUD_PROJECT"] = GCP_PROJECT_ID
os.environ["LANGCHAIN_PROJECT"] = "obot"
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"

start_message = "Hello! 👋  I'm Obot, your helpful guide to all things Oberlin College. How can I assist you today?"

class SafetyException(Exception):
    pass

class ConversationalRAG:
    def __init__(self):
        embedding_model = VertexAIEmbeddings(
            model_name="text-embedding-004",
            project=GCP_PROJECT_ID,
        )

        vector_store = FirestoreVectorStore(
            collection="vector_index",
            embedding_service=embedding_model,
            content_field='content',   
            embedding_field='embedding',
        )

        def add_source_url(docs):
            for doc in docs:
                doc.page_content = f"<Source> {doc.metadata['url']}\n{doc.page_content}"
            return docs

        retriever = vector_store.as_retriever(search_kwargs={"k": 10}) | add_source_url

        safety_settings = {
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH, 
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH, 
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH, 
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        instruct_llm = ChatVertexAI(
        # instruct_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            # model="gemini-1.5-flash-001",
            temperature=0.3,
            max_tokens=256,
            max_retries=6,
            # safety_settings=safety_settings
        )

        qa_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-001",
            temperature=0.7,
            max_tokens=1024,
            max_retries=6,
            safety_settings=safety_settings
        )

        def llm_output_safety_filter(ai_message):
            if ai_message.response_metadata['finish_reason'] == 'SAFETY':
                raise SafetyException("Chatbot thinks this message is unsafe\n{}".format(ai_message.response_metadata['safety_ratings']))
            return ai_message

        contextualize_question_instruction_prompt = """Given the chat history and the latest user question below, \
which might reference context in the chat history, formulate a standalone question that can be understood without \
the chat history. The standalone question will be used to retrieve relevant information.

The current date is {current_date}, and the current time is {current_time}. Use this information to provide \
time-sensitive context when relevant. If the user's question involves a time element like [when, now, next week, \
current month, next semester] or requires a time element for clarity, explicitly include the full relevant dates or \
timeframes in the standalone question.

Examples: (If current date and time is Monday, August 19, 2024, 10:00 AM)
User Question: "What is the deadline for P/NP for current semester?" Output: "What is the deadline for P/NP for for Fall 2024?"
User Question: "What events are happening next week?" Output: "What events are happening during the week of August 26, 2024?"

Do NOT answer the question nor interact with the user; just reformulate the question if needed and otherwise return it as is. \
Please keep some terms like P/NP as it is if they are better keywords for retrieval. 
"""

        self.contextualize_question_prompt = ChatPromptTemplate.from_messages(
            [   
                ("human", contextualize_question_instruction_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                
            ]
        )

        history_aware_retriever = create_history_aware_retriever(instruct_llm | llm_output_safety_filter, retriever, self.contextualize_question_prompt)

        qa_system_prompt = '''You are a helpful assistant named Obot that answers questions about Oberlin College. \
Please ensure all interactions are unabiased, polite, professional, supportive and all information is accurate. ANSWER THE QUESTION IN DETAILS.
The current date is {current_date} and the current time is {current_time}. Evaluate the user's question within this time context. \
Use this information to provide time-sensitive responses when relevant.

Please use the following data between the `context`  html blocks to answer the question. 

<context>
{context}
</context>

Note that all the data is retrieved from a knowledge bank, not part of the conversation with the user. \
It is not provided by the user, so if you need to refer to the data, say it is my retrieved data.

Focus your answers on Oberlin College. If a user asks a question that doesn't relate to Oberlin College \
and there is no relevant context, apologize and inform the user that you can only answer questions related to Oberlin College.

Note that not all the data retrieved is relevant to the question. Pay attention to the user's lastest question and only \
use the relevant data to answer the question.

Always based your answer on the retrived data. If you cannot answer a question from the retrieved data, don't make up answer. \
Apologize and, only if appropriate, suggest the user find the information on the official Oberlin College website or contact the college directly.
Don't suggest user any other sources outside of Oberlin College.

If you use any sources from the context to formulate your answer, list them at the end of your response in the following markdown format:
---
*Sources:* 
`1`: [Short description of the source](URL)
`2`: [Short description of the source](URL)
<Add more sources if needed>
'''
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ]
        )

        qa_chain = create_stuff_documents_chain(qa_llm | llm_output_safety_filter, qa_prompt, document_separator="\n=============\n\n")

        rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

        self.session_store = {}
        self.sources = []
        
        self.conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            output_messages_key="answer",
            history_messages_key="chat_history",
        )

    def get_session_history(self, session_id):
            if session_id not in self.session_store:
                self.session_store[session_id] = InMemoryChatMessageHistory(messages=[AIMessage(start_message)])
            return self.session_store[session_id]

    def get_completion(self, input, session_id="default"):
        try:
            response = self.conversational_rag_chain.invoke(    
                {
                    "input": input,
                    "current_date": datetime.now().strftime("%A, %B %d, %Y"),
                    "current_time": datetime.now().strftime("%I:%M %p"),
                },
                config={
                    "configurable": {"session_id": session_id}
                },
            )
            self.sources.append(response['context'])
        except SafetyException as e:
            response = "SAFETY_EXCEPTION"
        except ResourceExhausted as e:
            response = "RESOURCE_EXHAUSTED"
        return response
    
    def get_chat_history(self, session_id="default"):
        messages = []
        source_index = 0
        for message in self.get_session_history(session_id).messages:
            if isinstance(message, HumanMessage):
                messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                if message.content != start_message:
                    messages.append({"role": "assistant", "content": message.content, "source_index": source_index})
                    source_index += 1
                else:
                    messages.append({"role": "assistant", "content": message.content})
        return messages
    
    def clear_chat_history(self, session_id="default"):
        if session_id in self.session_store and self.session_store[session_id].messages != []:
            self.session_store[session_id] = InMemoryChatMessageHistory(messages=[AIMessage(start_message)])
            self.sources = []