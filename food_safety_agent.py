from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

SystemMessage(content="""You are a strict Food Safety QA Auditor. 
1. Compare the recorded operational data exactly against the stated critical limits.
2. If ANY recorded metric falls short of the critical limit, you MUST flag a violation.
3. Do not apply external logic or assume a lower temperature is acceptable. 
State your conclusion clearly: PASS or FAIL, followed by the reason.""")

# 1. Initialize the local DeepSeek model
# Make sure the 'model' string exactly matches what you pulled (e.g., 'deepseek-r1:7b')
llm = ChatOllama(
    model="deepseek-r1:7b",
    temperature=0.2, # Low temperature for more factual, consistent answers
)

# 2. Define the agent's role and the user's query
messages = [
    SystemMessage(content="You are a strict Food Safety QA Auditor. Analyze the data provided and flag any violations of standard safety protocols."),
    HumanMessage(content="Shift Log: The cooking vat for batch #402 reached an internal temperature of 152°F for 45 minutes. The required critical limit is 165°F for 3 minutes. What is the required action?")
]

# 3. Invoke the model and print the response
print("Thinking...")
response = llm.invoke(messages)

# DeepSeek R1 models output their internal "thinking" inside  tags.
# The actual answer follows the closing tag.
print("\n--- Agent Response ---")
print(response.content)
