# chat.py
import os
import random
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chat_models import init_chat_model
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

class HealthMateChatbot:
    def __init__(self):
        # ===== Step 1. Load knowledge base =====
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        knowledge_dir = "knowledge_base"
        faiss_index_path = "./faiss_index"

        if not os.path.exists(faiss_index_path):
            documents = []
            for file in os.listdir(knowledge_dir):
                if file.endswith(".txt"):
                    loader = TextLoader(os.path.join(knowledge_dir, file), encoding="utf-8")
                    documents.extend(loader.load())

            db = FAISS.from_documents(documents, embeddings)
            db.save_local(faiss_index_path)
        else:
            db = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)

        retriever = db.as_retriever()

        # ===== Step 2. Gemini Flash model =====
        llm = init_chat_model(
            "gemini-1.5-flash",
            model_provider="google_genai",
            temperature=0.8
        )

        # ===== Step 3. Custom System Prompt =====
        system_prompt = """
        You are HealthMate 🩺, a caring AI assistant designed to act like an online health advisor.

        ### Core Purpose
        - Provide guidance on **general health topics**: diseases, symptoms, medicines, lifestyle, diet, self-care.
        - Always explain in a **clear, supportive, and empathetic way** ❤️.
        - If user asks outside scope → say: "I’m mainly here to help with health-related questions 🙂."

        ### Style
        - Warm, supportive, and empathetic 🌸.
        - Use emojis 🩺💊🥗❤️🌿.
        - Keep answers short & simple.
        - Always remind users to consult a doctor for personal advice.

        ### Context
        {context}

        Question: {question}
        """

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=system_prompt
        )

        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            return_source_documents=False,
            combine_docs_chain_kwargs={"prompt": prompt},
            verbose=False
        )

        self.chat_history = []

        # Small talk dictionary
        self.small_talk_responses = {
            "hi": ["Hey! 👋 Welcome to HealthMate.", "Hi there! 😊 How are you feeling today?"],
            "hello": ["Hello! 🙂 Welcome to HealthMate.", "Hey there! 👋 How are you doing?"],
            "thanks": ["You’re welcome! 🙌 Always here to help.", "No problem, happy to assist! 🙂"],
            "who are you": ["I’m HealthMate 🤖, your friendly online health advisor 🩺"],
            "what can you do": ["I can share info about diseases, medicines, lifestyle & health tips 🩺"]
        }

    def is_small_talk(self, query: str):
        return query.lower().strip() in self.small_talk_responses

    def handle_small_talk(self, query: str) -> str:
        return random.choice(self.small_talk_responses[query.lower().strip()])

    def get_response(self, query: str) -> str:
        # Small talk check
        if self.is_small_talk(query):
            return self.handle_small_talk(query)

        # Otherwise → use RAG
        result = self.qa_chain.invoke({"question": query, "chat_history": self.chat_history})
        answer = result["answer"]

        # Save history
        self.chat_history.append((query, answer))

        return answer