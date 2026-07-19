from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# 1. Load all text and PDF files from the 'SOP's' folder
txt_loader = DirectoryLoader("./SOP's", glob="*.txt", loader_cls=TextLoader)
txt_docs = txt_loader.load()

pdf_loader = DirectoryLoader("./SOP's", glob="*.pdf", loader_cls=PyPDFLoader)
pdf_docs = pdf_loader.load()

docs = txt_docs + pdf_docs

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = text_splitter.split_documents(docs)

# 2. Build/Overwrite the database with all documents
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(
    documents=splits, 
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print(f"Database successfully built with {len(docs)} SOP documents!")
