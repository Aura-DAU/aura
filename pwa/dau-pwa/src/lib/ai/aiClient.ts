import Anthropic from "@anthropic-ai/sdk";

// Initialize Anthropic client
const apiKey = process.env.ANTHROPIC_API_KEY;
const anthropic = new Anthropic({
  apiKey: apiKey || "",
});

/**
 * Anthropic Claude API Client using SDK with Prompt Caching
 */
export async function callClaude(payload: {
  systemPrompt: string;
  userMessage: string;
  history?: { role: "user" | "assistant"; content: string }[];
}) {
  if (!apiKey) {
    return {
      success: false,
      content: "Error: ANTHROPIC_API_KEY is not configured.",
    };
  }

  const { systemPrompt, userMessage, history = [] } = payload;

  try {
    const messages = [
      ...history.map((h) => ({ role: h.role as "user" | "assistant", content: h.content })),
      { role: "user" as const, content: userMessage },
    ];

    // Call Anthropic API with prompt caching
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 1024,
      system: [
        {
          type: "text",
          text: systemPrompt,
          cache_control: { type: "ephemeral" },
        },
      ],
      messages: messages,
    }, {
      headers: {
        "anthropic-beta": "prompt-caching-2024-07-31"
      }
    });

    const reply = response.content[0].type === "text" ? response.content[0].text : "No response text found.";

    return {
      success: true,
      content: reply,
    };
  } catch (error) {
    console.error("Error calling Anthropic API via SDK:", error);
    return {
      success: false,
      content: "Error: Failed to connect to Claude AI services.",
    };
  }
}
