/**
 * Fetch-based Anthropic Claude API Client
 */
export async function callClaude(payload: {
  systemPrompt: string;
  userMessage: string;
  history?: { role: "user" | "assistant"; content: string }[];
}) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return {
      success: false,
      content: "Error: ANTHROPIC_API_KEY is not configured.",
    };
  }

  const { systemPrompt, userMessage, history = [] } = payload;

  const messages = [
    ...history.map((h) => ({ role: h.role, content: h.content })),
    { role: "user", content: userMessage },
  ];

  try {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 1024,
        system: systemPrompt,
        messages: messages,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("Anthropic API Error response:", errText);
      return {
        success: false,
        content: `Error: Claude API responded with status ${response.status}`,
      };
    }

    const data = await response.json();
    const reply = data.content?.[0]?.text || "No response text found.";

    return {
      success: true,
      content: reply,
    };
  } catch (error) {
    console.error("Error calling Anthropic API:", error);
    return {
      success: false,
      content: "Error: Failed to connect to Claude AI services.",
    };
  }
}
