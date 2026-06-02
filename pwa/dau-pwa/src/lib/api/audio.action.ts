"use server";

/**
 * Server Action to transcribe base64 audio data using Groq's Whisper API
 */
export async function transcribeAudio(payload: {
  audioBase64: string;
  filename?: string;
}) {
  const { audioBase64, filename } = payload;
  const apiKey = process.env.GROQ_API_KEY;
  
  if (!apiKey) {
    return {
      success: false,
      error: "Error: GROQ_API_KEY is not configured on the server. Please add it to your environment.",
    };
  }

  if (!audioBase64) {
    return {
      success: false,
      error: "Error: Audio data is missing.",
    };
  }

  try {
    // 1. Decode base64 to buffer
    const buffer = Buffer.from(audioBase64, "base64");

    // 2. Build FormData
    const formData = new FormData();
    const fileType = filename?.endsWith(".wav") ? "audio/wav" : "audio/webm";
    const blob = new Blob([buffer], { type: fileType });
    
    formData.append("file", blob, filename || "audio.webm");
    formData.append("model", "whisper-large-v3");

    // 3. Post to Groq Audio transcription API
    const response = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("Groq Whisper API response error:", errText);
      return {
        success: false,
        error: `Groq Whisper API returned status code ${response.status}`,
      };
    }

    const result = await response.json();
    return {
      success: true,
      text: result.text || "",
    };
  } catch (error) {
    console.error("Error calling Groq Whisper API:", error);
    const errorMessage = error instanceof Error ? error.message : "Failed to process audio transcription.";
    return {
      success: false,
      error: errorMessage,
    };
  }
}
