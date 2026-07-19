# Food Safety QA Auditor

This repository contains an intelligent Food Safety Quality Assurance agent built with LangChain, Flask, and local LLMs via Ollama. It extracts operational shift log data (e.g., temperatures, microbial swab results, allergen storage statuses) and automatically audits it against Standard Operating Procedures (SOPs) stored in a Chroma vector database.

## Features

- **Automated Compliance Checks**: Analyzes operational data against standard protocols.
- **RAG Architecture**: Uses Chroma vector store to embed and retrieve PDF and TXT SOP guidelines dynamically.
- **Local Reasoning Engine**: Integrates with [Ollama](https://ollama.ai/) to run `deepseek-r1:7b` locally for private and robust reasoning.
- **Web Dashboard**: An interactive, premium glassmorphism-styled Flask UI for visualizing master QA logs and pending audits.

## Prerequisites

1. **Python 3.8+**
2. **Ollama**: You must have [Ollama installed](https://ollama.ai/) and the DeepSeek model downloaded:
   ```bash
   ollama run deepseek-r1:7b
   ```
   You also need the nomic embedder:
   ```bash
   ollama pull nomic-embed-text
   ```

## Setup & Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd Food-Safety-QA-Agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Build the Vector Database:
   Before running the app, you need to ingest the SOP documents into Chroma:
   ```bash
   python build_db.py
   ```
   *This creates a local `chroma_db` folder containing embeddings for all guidelines in the `SOP's` folder.*

## Running the Application

Start the Flask web server:
```bash
python web_db.py
```

- Navigate to `http://127.0.0.1:5000` in your web browser.
- The web app will automatically initialize a local SQLite database (`food_safety_test.db`) and ingest sample records from `master_qa_log.csv`.
- From the dashboard, you can click **Run Audit** on any pending batch to trigger the agent.

## Repository Structure

- `web_db.py`: The Flask web server and primary database controller.
- `agent.py`: The LangChain tool defining the RAG-based AI compliance agent.
- `build_db.py`: Script to parse documents from the `SOP's/` folder and build the Chroma database.
- `rag_agent.py` & `food_safety_agent.py`: Standalone CLI testing scripts for the agent logic.
- `master_qa_log.csv`: Sample batch history data.
- `SOP's/`: Directory containing all the standard operating procedure documents (PDFs/TXT).
