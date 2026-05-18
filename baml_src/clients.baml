// Default client (local first): Ollama on macOS.
//
// Start Ollama:
//   ollama serve
// Pull a model:
//   ollama pull llama3.1:8b
//
// Environment:
// - OLLAMA_BASE_URL (default: http://localhost:11434/v1)
// - OLLAMA_MODEL (default: llama3.1:8b)
// - OLLAMA_API_KEY (optional; Ollama typically ignores it but OpenAI-compatible clients expect one)
//
// Note: Uses OpenAI-compatible API. If you prefer cloud LLMs, keep Gemini configured below.

client<llm> DefaultLLM {
  provider openai-generic
  options {
    base_url env.OLLAMA_BASE_URL
    api_key env.OLLAMA_API_KEY
    model env.OLLAMA_MODEL
    temperature 0.2
  }
}

// Optional cloud fallback: Gemini 1.5 Pro (Google AI).
// For Vertex AI on GCP, set base_url / auth per BoundaryML Vertex docs.

client<llm> Gemini15Pro {
  provider google-ai
  options {
    model "gemini-1.5-pro"
    api_key env.GOOGLE_API_KEY
    generationConfig {
      temperature 0.2
    }
  }
}
