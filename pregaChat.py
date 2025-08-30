import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chat_models import init_chat_model
from langchain.chains import RetrievalQA

load_dotenv()

# 1. Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# 2. Load all text files from knowledge_base/
knowledge_dir = "knowledge_base"
documents = []

for file in os.listdir(knowledge_dir):
    if file.endswith(".txt"):
        loader = TextLoader(os.path.join(knowledge_dir, file), encoding="utf-8")
        documents.extend(loader.load())

# 3. Build FAISS index (combine all docs)
faiss_index_path = "./faiss_index"

if not os.path.exists(faiss_index_path):
    db = FAISS.from_documents(documents, embeddings)
    db.save_local(faiss_index_path)
else:
    db = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)

# 4. Retriever
retriever = db.as_retriever()

# 5. Gemini Flash model
llm = init_chat_model("gemini-1.5-flash", model_provider="google_genai")

# 6. Retrieval-Augmented QA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# 7. Query Example
query = "What should I do and what shouldn't I do while pregnancy?"
result = qa_chain({"query": query})

print("Answer:", result["result"])
