// Gemini 1.5 Pro (Google AI). For Vertex AI on GCP, set base_url / auth per BoundaryML Vertex docs.

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
