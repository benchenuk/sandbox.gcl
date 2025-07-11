# app.py

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

# --- Configuration ---
# Ensure Ollama is running.
# e.g., run `ollama run qwen2:1.5b` in your terminal before starting this app.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_NAME = os.environ.get("OLLAMA_MODEL_NAME", "qwen3:4b") # or "llama3", etc.

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


# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- System Prompt Template ---
# This is the equivalent of the @SystemMessage in the Java code.
# It instructs the LLM on its role and the exact JSON format required.
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
    # 1. Get and validate request data
    data = request.get_json()
    if not data or 'word' not in data or 'foreignLanguage' not in data:
        return jsonify({"error": "Missing 'word' or 'foreignLanguage' in request body"}), 400

    word = data['word']
    foreign_language = data['foreignLanguage']
    # Per requirements, the home language is English by default.
    home_language = "English"

    try:
        # 2. Initialize the LLM
        # We specify format="json" to instruct Ollama to output a valid JSON object.
        # This is crucial for reliable parsing.
        model = ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL_NAME,
            format="json",
            temperature=0.7
        )

        # 3. Set up the parser and the prompt template
        # The parser will automatically validate the LLM's output against our Pydantic model.
        parser = JsonOutputParser(pydantic_object=LanguageLesson)

        # The user message template, equivalent to @UserMessage in Java.
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Generate a language lesson for the word/phrase '{word}' from {home_language} to {foreign_language}."),
            ("system", "JSON Output Format:\n{format_instructions}")
        ]).partial(format_instructions=parser.get_format_instructions())


        # 4. Create and invoke the LangChain chain
        # The chain combines the prompt, model, and parser into a single runnable component.
        chain = prompt | model | parser

        print(f"Generating lesson for '{word}' in {foreign_language} using model '{OLLAMA_MODEL_NAME}'...")

        lesson = chain.invoke({
            "word": word,
            "home_language": home_language,
            "foreign_language": foreign_language
        })

        # 5. Return the successful response
        # The 'lesson' variable is now a dictionary-like object.
        return jsonify(lesson), 200

    except Exception as e:
        print(f"[ERROR] Failed to generate lesson: {e}")
        error_message = (
            f"Failed to generate lesson. Please ensure Ollama is running, "
            f"and the model '{OLLAMA_MODEL_NAME}' is available. Error: {e}"
        )
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    print("--- Language Context Engine API ---")
    print(f"Using model: {OLLAMA_MODEL_NAME} via {OLLAMA_BASE_URL}")
    app.run(host='0.0.0.0', port=5001, debug=True)