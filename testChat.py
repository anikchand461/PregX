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

# ===== Step 1. Load knowledge base =====
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

knowledge_dir = "knowledge_base"
faiss_index_path = "./faiss_index"

# Build FAISS index only once
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
    "gemini-2.5-flash",
    model_provider="google_genai",
    temperature=0.8
)

chat_history = []

# ===== Step 3. Custom System Prompt =====
system_prompt = """
You are HealthMate 🩺, a caring AI assistant designed to act like an online health advisor.

### Core Purpose
- Your main goal is to provide guidance on **general health topics**: common diseases, symptoms, medicines, procedures, lifestyle, diet, and self-care.  
- Always explain in a **clear, supportive, and empathetic way** ❤️.  
- If a question is completely outside health/medical scope (like politics, coding, sports, etc.), politely say:  
  "I’m mainly here to help with health-related questions 🙂. Would you like to know about symptoms, medicines, or lifestyle advice?"

### Style
- Be warm, supportive, and empathetic 🌸.  
- If any user ask about medicine name , tell that. do not force him or her that he or she should consult a doctor.
- Keep answers short, simple, and easy to understand.  
- Use emojis where natural (🩺, 💊, 🥗, ❤️, 🌿).  
- When talking about medical issues, **always remind users to consult a qualified doctor** for personal advice.

### Context
Here’s some context from the medical knowledge base:
{context}

Question: {question}
"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=system_prompt
)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    return_source_documents=False,
    combine_docs_chain_kwargs={"prompt": prompt},
    verbose=False
)

def safe_invoke(query, history):
    result = qa_chain.invoke({"question": query, "chat_history": history})
    return result["answer"]
small_talk_responses = {
    "hi": [
        "Hey! 👋 Welcome to HealthMate.",
        "Hi there! 😊 How are you feeling today?",
        "Hello 👋 How’s your health today?"
    ],
    "hello": [
        "Hello! 🙂 Welcome to HealthMate.",
        "Hey there! 👋 How are you doing?",
        "Hi! 🌟 Here to support you with your health questions."
    ],
    "hey": [
        "Hey there! How are you feeling today? 🩺",
        "Yo! 👋 I’m here if you have any health-related questions.",
        "Heyyy 😎 Hope you’re doing well and staying healthy."
    ],
    "good morning": [
        "Good morning ☀️ Wishing you a healthy and positive day!",
        "Morning! 🌄 Don’t forget to stay hydrated 💧",
        "Rise and shine! ☀️ Take care of yourself today."
    ],
    "good afternoon": [
        "Good afternoon 🌞 Hope your day is going smoothly!",
        "Hey! 👋 How’s your afternoon going?",
        "Good afternoon! 🌻 Remember to eat something nutritious 🥗"
    ],
    "good evening": [
        "Good evening 🌙 How was your day?",
        "Evening! 🌆 Did you get some time to relax?",
        "Good evening 🌌 Take it easy and care for yourself ❤️"
    ],
    "thanks": [
        "You’re welcome! 🙌 Always here to help.",
        "No problem, happy to assist! 🙂",
        "Anytime! 🤗 Wishing you good health and happiness."
    ],
    "thank you": [
        "No problem at all, happy to help! 😊",
        "You got it! 👍 Stay safe and healthy.",
        "Always here if you need me 🙌"
    ],
    "who are you": [
        "I’m HealthMate 🤖, your friendly online health advisor built to support you with medical information 🩺",
        "I’m your digital health companion 🤖—here to guide you on general health topics.",
        "I’m HealthMate, designed to help with medicines, procedures, lifestyle, and health concerns 🚑"
    ],
    "what can you do": [
        "I can share helpful information about common diseases, medicines, symptoms, lifestyle, and health tips 🩺",
        "I can guide you with knowledge about health care and answer common medical questions 🙂",
        "I can provide insights into healthcare, self-care, and wellness 🚀"
    ]
}

def is_small_talk(query: str):
    return query.lower().strip() in small_talk_responses

def handle_small_talk(query: str) -> str:
    return random.choice(small_talk_responses[query.lower().strip()])

# ===== Step 5. Chat Loop =====
while True:
    query = input("You: ")

    if query.lower() in ["exit", "quit", "goodbye", "ok bye", "bye"]:
        print("Bot: Goodbye! 👋")
        break

    # Small talk check
    if is_small_talk(query):
        print("Bot:", handle_small_talk(query))
        continue

    # Otherwise → use RAG
    answer = safe_invoke(query, chat_history)

    # Save conversation
    chat_history.append((query, answer))

    print("Bot:", answer)