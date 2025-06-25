from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
import random

# Load and split a PDF into text chunks
def load_chunks(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    for i, p in enumerate(pages):
        p.metadata["page_number"] = i + 1
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(pages)

# Create a QA chain using Ollama + FAISS
def create_qa_chain(docs):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.from_documents(docs, embedding=embeddings)
    retriever = db.as_retriever()
    llm = ChatOllama(model="llama3.1:latest", temperature=0)
    return RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff")

# Ask a question with a request for justification in the output
def ask_question_with_justification(user_question, chain):
    system_instruction = (
        "Answer the following question using only the provided document content. "
        "Include a brief justification at the end like 'This is supported by paragraph 2 on page X.'"
    )
    full_prompt = f"{system_instruction}\n\nQuestion: {user_question}"
    response = chain.invoke(full_prompt)
    if isinstance(response, dict):
        response["query"] = user_question
    return response

# Generate 3 logic-based comprehension questions from the document
def generate_questions(doc_text, chain):
    safe_text = doc_text[:3000] if doc_text else "The document could not be parsed."
    gen_prompt = (
        "Based on the following document, generate three logic-based or comprehension questions. "
        "Each must test reader understanding and be answerable only using the document.\n\n"
        f"Document:\n{safe_text}"
    )
    raw = chain.invoke(gen_prompt)
    if isinstance(raw, dict):
        raw = raw.get("result") or next(iter(raw.values()), "")
    questions = [q.strip("-•1234567890. ") for q in raw.split("\n") if "?" in q]
    return questions[:3]

# Evaluate a user's answer and cite document-based feedback
def evaluate_user_answer(question, answer, chain):
    eval_prompt = (
        "Evaluate the user's answer only using the uploaded document content. "
        "Provide specific feedback and cite paragraph or page if possible.\n\n"
        f"Question: {question}\n"
        f"User's Answer: {answer}"
    )
    return chain.invoke(eval_prompt)

# Evaluate answer and store it for session tracking
def evaluate_and_store_response(question, user_answer, qa_chain, responses_list):
    if not user_answer.strip():
        return "No answer provided."
    feedback = evaluate_user_answer(question, user_answer, qa_chain)
    responses_list.append((question, user_answer))
    return feedback