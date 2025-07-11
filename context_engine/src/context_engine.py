# context_engine/src/context_engine.py

import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable
from typing import List, Any, Optional, Dict

# --- Configuration ---
load_dotenv()
# Ensure Ollama is running.
# e.g., run `ollama run qwen2:1.5b` in your terminal before starting this app.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_NAME = os.environ.get("OLLAMA_MODEL_NAME", "qwen3:4b") # or "llama3", etc.

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest") # gemini-2.5-flash

# --- Data Structures (Pydantic Models) for Structured Output ---
# These models define the structure for the JSON response we expect from the LLM.
# Pydantic provides data validation and is the standard way to handle
# structured data in the Python/LangChain ecosystem.

class VocabularyItem(BaseModel):
    vocabulary: str = Field(description="A related word or phrase in the foreign language")
    translation: str = Field(description="The translation of the vocabulary in the home language")

class UsageSentence(BaseModel):
    usage: str = Field(description="A practical usage sentence in the foreign language")
    translation: str = Field(description="The translation and explanation of the usage in the home language")

class AdvancedContent(BaseModel):
    content: str = Field(description="A short conversation or multi-sentence paragraph in the foreign language")
    explanation: str = Field(description="The translation and explanation of the advanced content in the home language")

class LanguageLesson(BaseModel):
    directTranslation: str = Field(description="The direct translation of the user's word/phrase")
    relatedVocabulary: List[VocabularyItem] = Field(description="A list of related vocabulary items")
    practicalUsage: List[UsageSentence] = Field(description="A list of practical usage sentences")
    advancedContent: AdvancedContent = Field(description="Advanced content like a short conversation")

# --- Abstract Base Class for LLM Model ---
class LLMAbstractModel(ABC):
    @abstractmethod
    def invoke(self, prompt: Any, config: Optional[Dict] = None) -> Any:
        pass

# --- Specific Implementation for Ollama ---
class ChatOllama(LLMAbstractModel, Runnable):
    def __init__(self, model_name: str, base_url: str = OLLAMA_BASE_URL, format: str = "json", temperature: float = 0.7):
        from langchain_ollama.chat_models import ChatOllama as OllamaModel
        self.model = OllamaModel(base_url=base_url, model=model_name, format=format, temperature=temperature)

    def invoke(self, prompt: Any, config: Optional[Dict] = None) -> Any:
        return self.model.invoke(prompt, config=config)

# --- Specific Implementation for Google Gemini ---
class ChatGemini(LLMAbstractModel, Runnable):
    def __init__(self, api_key: str, model_name: str = GEMINI_MODEL_NAME):
        from langchain_google_genai import ChatGoogleGenerativeAI
        # FIX: Enable Gemini's native JSON mode to ensure reliable JSON output.
        # This prevents the model from returning extra fields like "thought"
        # and is more robust than relying on prompt instructions alone.
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            generation_config={"response_mime_type": "application/json"}
        )

    def invoke(self, prompt: Any, config: Optional[Dict] = None) -> Any:
        return self.model.invoke(prompt, config=config)

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- System Prompt Template ---
SYSTEM_PROMPT = """
You are an expert language tutor. Your task is to generate a comprehensive language lesson based on user input.
The user will provide a word or phrase, in their home language, and a target foreign language.
You MUST respond with a single, valid JSON object that strictly adheres to the schema provided.
Do NOT add any commentary, markdown, or any text outside of the JSON object.
"""

@app.route('/api/lesson', methods=['POST'])
def get_language_lesson():
    """
    API endpoint to generate a language lesson.
    Expects a JSON body with "word" and "foreignLanguage".
    """
    data = request.get_json()
    if not data or 'word' not in data or 'foreignLanguage' not in data:
        return jsonify({"error": "Missing 'word' or 'foreignLanguage' in request body"}), 400

    word = data['word']
    foreign_language = data['foreignLanguage']
    home_language = "English"

    try:
        if GEMINI_API_KEY:
            model = ChatGemini(api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL_NAME)
            model_name_in_use = GEMINI_MODEL_NAME
        else:
            model = ChatOllama(model_name=OLLAMA_MODEL_NAME)
            model_name_in_use = OLLAMA_MODEL_NAME

        parser = JsonOutputParser(pydantic_object=LanguageLesson)

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Generate a language lesson for the word/phrase '{word}' from {home_language} to {foreign_language}."),
            # When using native JSON mode, the format_instructions are still very helpful
            # to guide the model on the *structure* of the JSON it should create.
            ("system", "JSON Output Format:\n{format_instructions}")
        ]).partial(format_instructions=parser.get_format_instructions())

        chain = prompt | model | parser

        print(f"Generating lesson for '{word}' in {foreign_language} using model '{model_name_in_use}'...")

        lesson = chain.invoke({
            "word": word,
            "home_language": home_language,
            "foreign_language": foreign_language
        })

        return jsonify(lesson), 200

    except Exception as e:
        print(f"[ERROR] Failed to generate lesson: {e}")
        model_name_in_use = GEMINI_MODEL_NAME if GEMINI_API_KEY else OLLAMA_MODEL_NAME
        provider = "Google Gemini" if GEMINI_API_KEY else "Ollama"
        error_message = (
            f"Failed to generate lesson with {provider}. "
            f"Please ensure the service is available and the model '{model_name_in_use}' is configured correctly. Error: {e}"
        )
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    model_in_use = GEMINI_MODEL_NAME if GEMINI_API_KEY else OLLAMA_MODEL_NAME
    provider = "Google Gemini" if GEMINI_API_KEY else f"Ollama via {OLLAMA_BASE_URL}"
    print("--- Language Context Engine API ---")
    print(f"Using model: {model_in_use} from {provider}")
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found, falling back to Ollama.")
    app.run(host='0.0.0.0', port=5001, debug=True)