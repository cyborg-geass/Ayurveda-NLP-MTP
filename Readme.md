**This is the documentation of Agentic RAG for Ayurveda Chatbot**

## Installation
1. First clone the repository by:
```bash
git clone https://github.com/cyborg-geass/Ayurveda-NLP-MTP.git
cd Ayurveda-NLP-MTP/
```
2. Use Miniconda to create a conda environment with python (3.10 or later) and after activating the environ install the libraries with pip

```bash
conda create -n "name of your project" python=3.11
conda activate "name of your project"
pip install -r requirements.txt
```

## Usage with CLI
1. Go to the multi_agent directory and create a file named '.env' in the same directory.
```bash
cd multi_agent/
```
2. In the .env file just type (don't use any spaces or ""):
```bash
GROQ_API_KEY=your_api_key
TAVILY_API_KEY=your_api_key
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=your_api_key
LANGSMITH_PROJECT="Ayurveda_companion"
```
3. Now to start the bot just type in cmd:
```bash
python chatbot.py
```
4. To exit the chatbot just type "exit" in the terminal.


## Usage (Local Deployment)
1. After activting the conda environment just go to the root directory and type in terminal:
```bash
python app.py
```
2. You will get a fastapi interface, now go to the post method and in the click 'Try it out' and then edit the question string with your query and execute the query, you will get the response.

## Docker based (Recommended)
1. Pull our docker image of "ayurveda_companion" from the docker hub.
```bash
docker pull ankit0502/ayurveda_companion
```
2. Run the container with .env file you created with your api keys in the project root.
```bash
docker run -d --env-file .env -p 8000:8000 ankit0502/ayurveda_companion
```
3. Now just go to browser and open "http://localhost:8000" or "http://127.0.0.1:8000 for welcome page and go to /docs and try out the api, test with postman as well.
4. For building it from scratch, you can clone the repo and just bulid the docker image (multi staged building) as this is better with uv package rather than pip:
```bash
docker build -t ayurveda_companion .
docker run -d --env-file .env -p 8000:8000 ankit0502/ayurveda_companion
```
5. Check your running containers:
```bash
docker ps -a
docker logs <<container_id>>
```
