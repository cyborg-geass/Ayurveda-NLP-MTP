import os
from langchain_core.callbacks.manager import CallbackManager
from langchain_core.tracers.langchain import LangChainTracer

os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_TRACING_PROJECT_NAME'] = "Ayurveda_Companion"

tracer = LangChainTracer()
callback_manager = CallbackManager([tracer])
