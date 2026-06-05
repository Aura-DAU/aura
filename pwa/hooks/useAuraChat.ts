import { useState, useEffect, useRef } from "react";
import {
  askAura,
  ChatMessage,
  StudentProfile,
  Citation,
} from "@/app/api/chat.service";
import { transcribeAudio } from "@/app/api/audio.service";

export interface UseAuraChatOptions {
  storageKey?: string;
  profileKey?: string;
}

const DEFAULT_THREADS = [
  "Hostel Curfew Rules",
  "Bonafide Application Guide",
  "Lost ID Replacement Steps",
  "Technical Clubs & E-Cell",
];

export function useAuraChat(options: UseAuraChatOptions = {}) {
  const {
    storageKey = "aura_chat_history",
    profileKey = "aura_student_profile",
  } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [thinkingStep, setThinkingStep] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [recentThreads, setRecentThreads] =
    useState<string[]>(DEFAULT_THREADS);

  const [studentProfile, setStudentProfile] = useState<StudentProfile>({
    name: "",
    branch: "B.Tech (ICT)",
    year: "3rd Year",
    semester: "Semester V",
    interests: "Artificial Intelligence, competitive coding",
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const savedHistory = localStorage.getItem(storageKey);
    if (savedHistory) {
      try {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setMessages(JSON.parse(savedHistory));
      } catch {
        console.error("Error loading chat history");
      }
    }

    const savedProfile = localStorage.getItem(profileKey);
    if (savedProfile) {
      try {
        setStudentProfile(JSON.parse(savedProfile));
      } catch {
        console.error("Error loading student profile");
      }
    }

    const savedThreads = localStorage.getItem("aura_recent_threads");
    if (savedThreads) {
      try {
        setRecentThreads(JSON.parse(savedThreads));
      } catch {
        setRecentThreads(DEFAULT_THREADS);
      }
    }
  }, [storageKey, profileKey]);

  const saveHistory = (newMessages: ChatMessage[]) => {
    setMessages(newMessages);
    localStorage.setItem(storageKey, JSON.stringify(newMessages));
  };

  const saveProfile = (profile: StudentProfile) => {
    setStudentProfile(profile);
    localStorage.setItem(profileKey, JSON.stringify(profile));
  };

  const startRecording = async () => {
    setErrorMessage(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setErrorMessage("Microphone access is not supported by your browser.");
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      const recorderOptions = { mimeType: "audio/webm" };
      let mediaRecorder: MediaRecorder;
      try {
        mediaRecorder = new MediaRecorder(stream, recorderOptions);
      } catch {
        mediaRecorder = new MediaRecorder(stream);
      }

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType || "audio/webm",
        });
        stream.getTracks().forEach((track) => track.stop());

        setIsTranscribing(true);

        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
          try {
            const base64data = (reader.result as string).split(",")[1];
            const filename = mediaRecorder.mimeType?.includes("wav")
              ? "audio.wav"
              : "audio.webm";

            const result = await transcribeAudio({
              audioBase64: base64data,
              filename,
            });

            if (result.success && result.text) {
              setInputText((prev) => {
                const space = prev.trim() ? " " : "";
                return prev + space + result.text;
              });
            } else if (result.error) {
              setErrorMessage(result.error);
            }
          } catch (err) {
            console.error("Transcription error:", err);
            setErrorMessage("Failed to transcribe audio.");
          } finally {
            setIsTranscribing(false);
          }
        };
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setErrorMessage("Microphone permission denied or not available.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      void startRecording();
    }
  };

  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || loading) return;

    setErrorMessage(null);

    const threadTitle =
      textToSend.length > 25 ? textToSend.substring(0, 25) + "..." : textToSend;
    if (!recentThreads.includes(threadTitle)) {
      const updatedThreads = [threadTitle, ...recentThreads.slice(0, 9)];
      setRecentThreads(updatedThreads);
      localStorage.setItem(
        "aura_recent_threads",
        JSON.stringify(updatedThreads),
      );
    }

    const userMsg: ChatMessage = { role: "user", content: textToSend };
    const updatedMessages = [...messages, userMsg];
    saveHistory(updatedMessages);
    setInputText("");
    setLoading(true);
    setActiveCitations([]);

    setThinkingStep("Accessing university registry database...");
    await new Promise((r) => setTimeout(r, 400));
    setThinkingStep("Scanning academics policies & student service handbooks...");
    await new Promise((r) => setTimeout(r, 450));
    setThinkingStep("Formulating RAG grounded response...");
    await new Promise((r) => setTimeout(r, 300));

    try {
      const result = await askAura({
        message: textToSend,
        history: messages,
        studentProfile,
      });

      if (result.success && result.content) {
        saveHistory([
          ...updatedMessages,
          { role: "assistant", content: result.content },
        ]);
        if (result.citations) {
          setActiveCitations(result.citations);
        }
      } else {
        saveHistory([
          ...updatedMessages,
          {
            role: "assistant",
            content:
              "Sorry, I had trouble processing your query. Please check your network or try again.",
          },
        ]);
        setErrorMessage(
          result.error ?? "Failed to receive response from AURA server.",
        );
      }
    } catch {
      saveHistory([
        ...updatedMessages,
        {
          role: "assistant",
          content:
            "Error: I encountered a problem communicating with the university registry servers.",
        },
      ]);
      setErrorMessage("Network error: Could not reach registry servers.");
    } finally {
      setLoading(false);
      setThinkingStep("");
    }
  };

  const handleClearChat = () => {
    saveHistory([]);
    setActiveCitations([]);
    setErrorMessage(null);
  };

  return {
    messages,
    inputText,
    setInputText,
    loading,
    thinkingStep,
    isRecording,
    isTranscribing,
    errorMessage,
    setErrorMessage,
    activeCitations,
    recentThreads,
    studentProfile,
    saveProfile,
    handleMicClick,
    handleSendMessage,
    handleClearChat,
  };
}
