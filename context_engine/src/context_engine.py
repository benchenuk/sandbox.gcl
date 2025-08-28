# context_engine/src/context_engine.py

import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field
from typing import List, Any, Optional, Dict, Union

# --- Configuration ---
load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL_NAME = os.environ.get("OPENROUTER_MODEL_NAME", "google/gemini-flash-1.5")
# Optional headers for OpenRouter analytics
# OPENROUTER_REFERRER = os.environ.get("YOUR_SITE_URL")
# OPENROUTER_APP_NAME = os.environ.get("YOUR_APP_NAME")

# Priority 2: Google Gemini (direct)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest")

# Priority 3: Ollama (Local Fallback)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_NAME = os.environ.get("OLLAMA_MODEL_NAME", "gemma3:4b-it-qat")

# --- Data Structures (Pydantic Models) ---
class JapaneseTextBlock(BaseModel):
    lm: str = Field(description="The main Japanese line, with Furigana in parentheses after the Kanji, e.g., '日本語(にほんご)を勉強(べんきょう)しています'.")
    lrm: str = Field(description="Romaji pronunciation below the main line, e.g., 'nyuuryoku shite kudasai'.")
    lt: str = Field(description="Line-by-line translation in the home language, e.g., 'Please enter'.")

class VocabularyItem(BaseModel):
    vocabulary: Union[str, JapaneseTextBlock] = Field(description="A related word or phrase. For Japanese, this will be a detailed block.")
    translation: str = Field(description="The translation or explanation of the vocabulary in the home language.")

class UsageSentence(BaseModel):
    usage: Union[str, JapaneseTextBlock] = Field(description="A practical usage sentence. For Japanese, this will be a detailed block.")
    translation: str = Field(description="The translation and explanation of the usage in the home language")

class AdvancedContent(BaseModel):
    content: Union[str, JapaneseTextBlock] = Field(description="A short conversation or multi-sentence paragraph. For Japanese, this will be a detailed block.")
    explanation: str = Field(description="The translation and explanation of the advanced content in the home language")

class LanguageLesson(BaseModel):
    directTranslation: Union[str, JapaneseTextBlock] = Field(description="The direct translation of the user's word/phrase. For Japanese, this will be a detailed block.")
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
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
        )

    def invoke(self, prompt: Any, config: Optional[Dict] = None) -> Any:
        return self.model.invoke(prompt, config=config)

# --- Implementation for OpenRouter using the OpenAI class ---
class ChatOpenRouter(LLMAbstractModel, Runnable):
    def __init__(self, api_key: str, model_name: str = OPENROUTER_MODEL_NAME):
        # This is the robust, recommended way to use OpenRouter with LangChain
        from langchain_openai import ChatOpenAI

        self.model = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            # Optional, but recommended for analytics and logging on OpenRouter's end
            # default_headers={
            #     "HTTP-Referer": OPENROUTER_REFERRER,
            #     "X-Title": OPENROUTER_APP_NAME,
            # }
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

--- Special Instructions for Japanese ---
When the target language is Japanese, you MUST provide detailed phonetic and translation information for any field that contains Japanese sentences or complex phrases.
Specifically, for the `directTranslation`, `relatedVocabulary.vocabulary`, `practicalUsage.usage`, and `advancedContent.content` fields, you MUST use the following JSON object structure instead of a simple string:
{{
  "lm": "The main Japanese line, with Furigana in parentheses right after the corresponding Kanji. Example: '日本語(にほんご)を勉強(べんきょう)しています'.",
  "lrm": "The Romaji pronunciation of the entire line, e.g., 'Nihongo o benkyō shite imasu'.",
  "lt": "The direct English translation of the line, e.g., 'I am studying Japanese.'."
}}
For simpler, single-word vocabulary items without complex Kanji, you may use a simple string.
The separate `translation` or `explanation` fields should still be used for broader context, grammar points, or cultural nuances, not for the direct line-by-line translation which belongs in the `lt` field.
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
        # --- Model and Chain Initialization (with provider priority) ---
        chain = None
        provider = "N/A"
        model_name_in_use = "N/A"

        # Priority 1: OpenRouter
        if OPENROUTER_API_KEY:
            provider = "OpenRouter"
            model_name_in_use = OPENROUTER_MODEL_NAME
            # For OpenAI-compatible endpoints, we use the reliable JsonOutputParser
            model = ChatOpenRouter(api_key=OPENROUTER_API_KEY, model_name=model_name_in_use).model
            parser = JsonOutputParser(pydantic_object=LanguageLesson)
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "Generate a language lesson for the word/phrase '{word}' from {home_language} to {foreign_language}."),
                ("system", "JSON Output Format:\n{format_instructions}")
            ]).partial(format_instructions=parser.get_format_instructions())
            chain = prompt | model | parser

        # Priority 2: Google Gemini (direct)
        elif GEMINI_API_KEY:
            provider = "Google Gemini"
            model_name_in_use = GEMINI_MODEL_NAME
            model = ChatGemini(api_key=GEMINI_API_KEY, model_name=model_name_in_use).model
            # Use the modern .with_structured_output for direct Gemini calls
            structured_llm = model.with_structured_output(LanguageLesson)
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "Generate a language lesson for the word/phrase '{word}' from {home_language} to {foreign_language}.")
            ])
            chain = prompt | structured_llm

        # Priority 3: Ollama (local fallback)
        else:
            provider = "Ollama"
            model_name_in_use = OLLAMA_MODEL_NAME
            model = ChatOllama(model_name=model_name_in_use).model
            parser = JsonOutputParser(pydantic_object=LanguageLesson)
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "Generate a language lesson for the word/phrase '{word}' from {home_language} to {foreign_language}."),
                ("system", "JSON Output Format:\n{format_instructions}")
            ]).partial(format_instructions=parser.get_format_instructions())
            chain = prompt | model | parser

        if not chain:
            return jsonify({"error": "No LLM provider is configured. Please set an API key or ensure Ollama is running."}), 500

        print(f"Generating lesson for '{word}' in {foreign_language} using '{model_name_in_use}' via {provider}...")

        # --- Invoke Chain and Process Result ---
        lesson_result = chain.invoke({
            "word": word,
            "home_language": home_language,
            "foreign_language": foreign_language
        })

        # The result might be a Pydantic model (from Gemini) or a dict (from parsers)
        if isinstance(lesson_result, BaseModel):
            lesson = lesson_result.model_dump()
        else:
            lesson = lesson_result

        return jsonify(lesson), 200

    except Exception as e:
        print(f"[ERROR] Failed to generate lesson: {e}")
        error_message = (
            f"Failed to generate lesson with {provider} "
            f"using model '{model_name_in_use}'. Please check your API keys and model configuration. Error: {e}"
        )
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    # Determine which provider will be used on startup for clear logging
    provider_in_use = "Ollama"
    model_in_use = OLLAMA_MODEL_NAME
    if OPENROUTER_API_KEY:
        provider_in_use = f"OpenRouter (via OpenAI SDK)"
        model_in_use = OPENROUTER_MODEL_NAME
    elif GEMINI_API_KEY:
        provider_in_use = "Google Gemini"
        model_in_use = GEMINI_MODEL_NAME

    print("--- Language Context Engine API ---")
    print(f"Using model: {model_in_use} from {provider_in_use}")
    if provider_in_use == "Ollama":
        print("No cloud provider API key found. Falling back to local Ollama.")

    app.run(host='0.0.0.0', port=5001, debug=True)