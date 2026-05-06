// Default LLM client for AeroQ (Google AI / Gemini).
// Set env var GOOGLE_API_KEY to enable.

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

