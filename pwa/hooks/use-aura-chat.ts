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

export interface UserSession {
  role: "student" | "parent";
  email: string;
  name: string;
  linkedStudentEmail?: string;
}

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

  const [userSession, setUserSession] = useState<UserSession | null>(null);

  const [studentProfile, setStudentProfile] = useState<StudentProfile>({
    name: "",
    branch: "B.Tech (ICT)",
    year: "3rd Year",
    semester: "Semester V",
    interests: "Artificial Intelligence, competitive coding",
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  // Always points at the latest handleSendMessage so async callbacks
  // (MediaRecorder.onstop) never act on stale messages/loading state.
  const sendMessageRef = useRef<(text: string) => Promise<void>>(
    async () => {},
  );

  const closeAudioContext = () => {
    const ctx = audioContextRef.current;
    if (ctx) {
      audioContextRef.current = null;
      if (ctx.state !== "closed") {
        ctx.close().catch(console.error);
      }
    }
  };

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

    const savedSession = localStorage.getItem("aura_session");
    if (savedSession) {
      try {
        setUserSession(JSON.parse(savedSession));
      } catch {
        console.error("Error loading user session");
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

  useEffect(() => {
    return () => {
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = null;
        recorder.stop();
      }
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      const ctx = audioContextRef.current;
      if (ctx && ctx.state !== "closed") {
        ctx.close().catch(console.error);
      }
    };
  }, []);

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
      mediaStreamRef.current = stream;
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
        closeAudioContext();

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType || "audio/webm",
        });
        stream.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;

        setIsTranscribing(true);

        try {
          const filename = mediaRecorder.mimeType?.includes("wav")
            ? "audio.wav"
            : "audio.webm";

          const result = await transcribeAudio({
            audio: audioBlob,
            filename,
          });

          if (result.success && result.text && result.text.trim()) {
            void sendMessageRef.current(result.text);
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

      // Silence (Voice Activity) Detection
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioCtxClass();
        audioContextRef.current = audioCtx;

        if (audioCtx.state === "suspended") {
          await audioCtx.resume();
        }

        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);

        const bufferLength = analyser.fftSize;
        const dataArray = new Uint8Array(bufferLength);

         
        let silenceStart = Date.now();
        const silenceThreshold = 0.01; // Slightly more sensitive volume threshold
        const silenceDurationLimit = 1500; // 1.5 seconds of silence after speaking to auto-stop
        const initialSilenceDurationLimit = 5000; // 5 seconds of initial silence before auto-stopping
        let hasSpoken = false;
        let isChecking = true;

        const checkSilence = () => {
          if (!isChecking || (mediaRecorder.state as string) === "inactive") return;

          analyser.getByteTimeDomainData(dataArray);
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            const val = (dataArray[i] - 128) / 128;
            sum += val * val;
          }
          const rms = Math.sqrt(sum / bufferLength);

          if (rms >= silenceThreshold) {
            if (!hasSpoken) {
              hasSpoken = true;
            }
            silenceStart = Date.now();
          }

          const silentTime = Date.now() - silenceStart;
          const limit = hasSpoken ? silenceDurationLimit : initialSilenceDurationLimit;

          if (silentTime > limit) {
            isChecking = false;
            if ((mediaRecorder.state as string) !== "inactive") {
              mediaRecorder.stop();
            }
            setIsRecording(false);
            closeAudioContext();
            return;
          }

          requestAnimationFrame(checkSilence);
        };

        requestAnimationFrame(checkSilence);
      } catch (audioErr) {
        console.warn("Failed to initialize silence detection audio context:", audioErr);
      }

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
    closeAudioContext();
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

    const userMsg: ChatMessage = {
      role: "user",
      content: textToSend,
      timestamp: Date.now(),
    };
    const updatedMessages = [...messages, userMsg];
    saveHistory(updatedMessages);
    setInputText("");
    setLoading(true);
    setActiveCitations([]);

    // Animate the status steps alongside the request instead of
    // delaying it — the fetch starts immediately.
    setThinkingStep("Accessing university registry database...");
    const stepTimers = [
      setTimeout(
        () =>
          setThinkingStep(
            "Scanning academics policies & student service handbooks...",
          ),
        400,
      ),
      setTimeout(
        () => setThinkingStep("Formulating RAG grounded response..."),
        850,
      ),
    ];

    try {
      const result = await askAura({
        message: textToSend,
        history: messages,
        studentProfile,
      });

      if (result.success) {
        const content = result.content?.trim()
          ? result.content
          : "I could not find that information in the available university data.";
        saveHistory([
          ...updatedMessages,
          { role: "assistant", content, timestamp: Date.now() },
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
            timestamp: Date.now(),
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
          timestamp: Date.now(),
        },
      ]);
      setErrorMessage("Network error: Could not reach registry servers.");
    } finally {
      stepTimers.forEach(clearTimeout);
      setLoading(false);
      setThinkingStep("");
    }
  };

  useEffect(() => {
    sendMessageRef.current = handleSendMessage;
  });

  const handleClearChat = () => {
    saveHistory([]);
    setActiveCitations([]);
    setErrorMessage(null);
  };

  const logout = () => {
    setUserSession(null);
    localStorage.removeItem("aura_session");
    const defaultProfile: StudentProfile = {
      name: "",
      branch: "B.Tech (ICT)",
      year: "3rd Year",
      semester: "Semester V",
      interests: "Artificial Intelligence, competitive coding",
    };
    setStudentProfile(defaultProfile);
    localStorage.setItem(profileKey, JSON.stringify(defaultProfile));
    handleClearChat();
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
    userSession,
    logout,
  };
}
