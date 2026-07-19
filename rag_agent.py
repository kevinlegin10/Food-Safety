from langchain_core.tools import tool

@tool
def audit_sop_compliance(query: str) -> str:
    """
    USE THIS TOOL to check operational data against Food Safety SOPs.
    Input should be a detailed sentence describing the operational data.
    Example Input: "Batch 402 reached 152°F for 45 minutes."
    Returns: A PASS/FAIL assessment and the required corrective action.
    """
    from langchain_ollama import ChatOllama, OllamaEmbeddings
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from langchain_classic.chains import create_retrieval_chain
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate

    # 1. Load and Chunk the SOP Document
    loader = TextLoader("SOP_Cooking.txt")
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # 2. Create the Local Vector Database (Chroma)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    retriever = vectorstore.as_retriever()

    # 3. Initialize the Reasoning Model
    llm = ChatOllama(model="deepseek-r1:7b", temperature=0.0) # Temp 0.0 forces strict adherence

    # 4. Create the Strict RAG Prompt
    # This specifically commands the AI to use the retrieved context.
    system_prompt = (
        "You are a strict Food Safety QA Auditor. "
        "Use ONLY the provided context to answer the question. "
        "If the operational data violates the context rules, declare a FAIL and state the required action. "
        "Do not use outside knowledge. \n\n"
        "Context: {context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 5. Connect the Retriever, Prompt, and Model
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 6. Test the Agent
    query = "Shift Log: The cooking vat for batch #402 reached an internal temperature of 152°F for 45 minutes. What is the required action?"
    print("Searching database and thinking...")

    response = rag_chain.invoke({"input": query})

    print("\n--- Agent Response ---")
    print(response["answer"])

    return response["answer"]


if __name__ == "__main__":
    audit_sop_compliance("Shift Log: The cooking vat for batch #402 reached an internal temperature of 152°F for 45 minutes. What is the required action?")

