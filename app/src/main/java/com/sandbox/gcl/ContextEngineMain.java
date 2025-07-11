package com.sandbox.gcl;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.ollama.OllamaChatModel;
import dev.langchain4j.service.AiServices;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;

import java.time.Duration;
import java.util.List;
import java.util.Scanner;

/**
 * A command-line application for language learning that uses a local LLM via Ollama
 * to generate rich, contextual information for a given word or phrase.
 *
 * This implementation is based on the LangChain4j framework, which simplifies
 * interaction with the language model.
 */
public class ContextEngineMain {

    // --- Configuration ---
    // Ensure Ollama is running and the model is downloaded.
    // e.g., run `ollama run llama3` in your terminal before starting this app.
    private static final String OLLAMA_BASE_URL = "http://localhost:11434";
    private static final String OLLAMA_MODEL_NAME = "qwen3:4b"; // or "gemma3:1b", etc.

    // --- Data Structures (POJOs) for Structured Output ---

    /**
     * Defines the structure for the JSON response we expect from the LLM.
     * Using POJOs (Plain Old Java Objects) with a library like Gson makes
     * handling structured data much cleaner and safer than manual JSON parsing.
     */
    static class LanguageLesson {
        private String directTranslation;
        private List<VocabularyItem> relatedVocabulary;
        private List<UsageSentence> practicalUsage;
        private AdvancedContent advancedContent;

        /**
         * Overrides toString() to provide a clean, pretty-printed JSON output.
         * @return A formatted JSON string representing the lesson.
         */
        @Override
        public String toString() {
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            return gson.toJson(this);
        }
    }

    static class VocabularyItem {
        private String vocabulary;
        private String translation;
    }

    static class UsageSentence {
        private String usage;
        private String translation;
    }

    static class AdvancedContent {
        private String content;
        private String explanation;
    }

    /**
     * This is the LangChain4j AiService interface.
     * This powerful feature allows us to define the interaction with the LLM
     * as a simple Java interface. LangChain4j handles the heavy lifting of
     * creating prompts, calling the model, and parsing the response into our POJOs.
     */
    interface LanguageTutor {

        @SystemMessage("""
            You are an expert language tutor. Your task is to generate a comprehensive language lesson based on user input.
            The user will provide a word or phrase, in the home language, and a foreign language.
            You MUST respond with a single, valid JSON object that strictly adheres to the following structure.
            Do NOT add any commentary, markdown, or any text outside of the JSON object.

            {
              "directTranslation": "string",
              "relatedVocabulary": [
                {
                  "vocabulary": "string (in the foreign language)",
                  "translation": "string (in the home language)"
                }
              ],
              "practicalUsage": [
                {
                  "usage": "string (in the foreign language)",
                  "translation": "string (explanation in the home language)"
                }
              ],
              "advancedContent": {
                "content": "string (a short conversation or multi-sentence paragraph, in the foreign language)",
                "explanation": "string (translation and explanation in the home language)"
              }
            }
            """)
        @UserMessage("Generate a language lesson for the word/phrase '{{word}}' from {{homeLanguage}} to {{foreignLanguage}}.")
        LanguageLesson generateLesson(
                @V("word") String word,
                @V("homeLanguage") String homeLanguage,
                @V("foreignLanguage") String foreignLanguage);
    }

    public static void main(String[] args) {
        // 1. Build the ChatLanguageModel using the Ollama integration.
        // We specify a generous timeout and, crucially, set the format to "json"
        // to instruct the model to output a valid JSON object.
        ChatLanguageModel model = OllamaChatModel.builder()
                .baseUrl(OLLAMA_BASE_URL)
                .modelName(OLLAMA_MODEL_NAME)
                .timeout(Duration.ofSeconds(120))
                .format("json")
                .build();

        // 2. Create the AiService, which dynamically implements the LanguageTutor interface.
        LanguageTutor tutor = AiServices.create(LanguageTutor.class, model);

        // 3. Start the interactive command-line loop.
        try (Scanner scanner = new Scanner(System.in)) {
            System.out.println("--- Language Context Engine ---");
            System.out.println("Using model: " + OLLAMA_MODEL_NAME);
            System.out.println("Enter a word or phrase to learn. Type 'exit' to quit.");

            while (true) {
                System.out.print("\nEnter word/phrase (e.g., 'good morning'): ");
                String word = scanner.nextLine();
                if (word == null || "exit".equalsIgnoreCase(word.trim())) {
                    break;
                }

                System.out.print("Enter foreign language (e.g., 'Japanese'): ");
                String foreignLanguage = scanner.nextLine();
                if (foreignLanguage == null || foreignLanguage.trim().isEmpty()) {
                    System.out.println("Foreign language cannot be empty. Please try again.");
                    continue;
                }

                // Per requirements, the home language is English by default.
                String homeLanguage = "English";

                System.out.println("\nGenerating lesson for '" + word + "' in " + foreignLanguage + "...");

                try {
                    // 4. Call the AiService. LangChain4j handles prompt creation,
                    // API call, and parsing the JSON response into our LanguageLesson object.
                    LanguageLesson lesson = tutor.generateLesson(word, homeLanguage, foreignLanguage);

                    // 5. Print the pretty-printed JSON output from the lesson object.
                    System.out.println(lesson);

                } catch (Exception e) {
                    System.err.println("\n[ERROR] Failed to generate lesson: " + e.getMessage());
                    System.err.println("Please ensure Ollama is running and the model '" + OLLAMA_MODEL_NAME + "' is downloaded and available.");
                }
            }
        }
        System.out.println("Goodbye!");
    }
}