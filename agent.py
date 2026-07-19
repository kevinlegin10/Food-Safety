from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

@tool
def audit_sop_compliance(query: str) -> str:
    """
    USE THIS TOOL to check operational data against Food Safety SOPs.
    Input should be a detailed sentence describing the operational data.
    Example Input: "Batch 402 reached 152°F for 45 minutes."
    Returns: A PASS/FAIL assessment and the required corrective action.
    """
    # 1. Connect to the ALREADY SAVED Local Vector Database
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma(
        persist_directory="./chroma_db", 
        embedding_function=embeddings
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 12})

    # 2. Initialize the Reasoning Model (using your DeepSeek model)[cite: 4]
    llm = ChatOllama(model="deepseek-r1:7b", temperature=0.0) 

    # 3. Create the Strict RAG Prompt[cite: 4]
    system_prompt = (
        "You are a strict Food Safety QA Auditor. "
        "Use ONLY the provided context to answer the question. "
        "Carefully check every parameter in the operational data (pathogen swab test results, freezer/fridge temperatures, vendor certification, material storage status, allergen compliance, and CIP cleaning steps/temperatures) against the standard operating procedures in the context. "
        "If ANY operational parameter or swab result violates the safety rules, you MUST declare a FAIL, list the violations, and state the required corrective action. "
        "Do not use outside knowledge. \n\n"
        "Context: {context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 4. Connect the Retriever, Prompt, and Model[cite: 4]
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 5. Execute the query
    # Notice we pass the 'query' variable dynamically instead of a hardcoded string[cite: 4]
    response = rag_chain.invoke({"input": query}) 

    return response["answer"]


if __name__ == "__main__":
    test_query = "Shift Log: The cooking vat for batch #402 reached an internal temperature of 152°F for 45 minutes. What is the required action?"
    print(f"Running agent with query: '{test_query}'")
    result = audit_sop_compliance.invoke(test_query)
    print("\n--- Agent Audit Result ---")
    print(result)
