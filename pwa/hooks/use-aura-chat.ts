/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect, useRef } from "react";
import {
  askAura,
  ChatMessage,
  StudentProfile,
  Citation,
} from "@/app/api/chat.service";
import { transcribeAudio } from "@/app/api/audio.service";
import {
  getSession,
  logout as logoutServerAction,
  updateProfile as updateProfileServerAction,
} from "@/lib/api/auth.action";

export interface UseAuraChatOptions {
  storageKey?: string;
  profileKey?: string;
}

export interface ChatThread {
  id: string;
  title: string;
  messages: ChatMessage[];
  timestamp: number;
}



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

  const [threads, setThreads] = useState<ChatThread[]>([]);
  const getThreadsKey = (session: UserSession | null) =>
    session ? `aura_chat_threads_${session.email.toLowerCase()}` : "aura_chat_threads_guest";
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

  // Derived messages for the active thread
  const activeThread = threads.find((t) => t.id === activeThreadId);
  const messages = activeThread ? activeThread.messages : [];

  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [thinkingStep, setThinkingStep] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);

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

    const savedProfile = localStorage.getItem(profileKey);
    if (savedProfile) {
      try {
        setStudentProfile(JSON.parse(savedProfile));
      } catch {
        console.error("Error loading student profile");
      }
    }

    const initSession = async () => {
      try {
        const session = await getSession();
        if (session) {
          setUserSession(session);
        } else {
          setUserSession(null);
        }
      } catch (err) {
        console.error("Error fetching user session from server:", err);
      }
    };
    void initSession();
  }, [profileKey]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const emailKey = getThreadsKey(userSession);
    let initialThreads: ChatThread[] = [];
    const savedThreads = localStorage.getItem(emailKey);

    if (savedThreads) {
      try {
        initialThreads = JSON.parse(savedThreads);
      } catch {
        console.error("Error loading chat threads");
      }
    } else {
      // Migrate legacy chat history if present
      const legacyHistory = localStorage.getItem(storageKey);
      if (legacyHistory) {
        try {
          const parsedHistory = JSON.parse(legacyHistory) as ChatMessage[];
          if (parsedHistory.length > 0) {
            const firstUserMsg = parsedHistory.find((m) => m.role === "user");
            const title = firstUserMsg
              ? firstUserMsg.content.length > 25
                ? firstUserMsg.content.substring(0, 25) + "..."
                : firstUserMsg.content
              : "Migrated Conversation";

            const legacyThread: ChatThread = {
              id: "thread_legacy",
              title,
              messages: parsedHistory,
              timestamp: Date.now(),
            };
            initialThreads = [legacyThread];
            localStorage.setItem(emailKey, JSON.stringify(initialThreads));
            localStorage.removeItem(storageKey);
          }
        } catch {
          console.error("Error migrating legacy history");
        }
      }
    }

    // Limit to 10 threads
    if (initialThreads.length > 10) {
      initialThreads = initialThreads.slice(0, 10);
      localStorage.setItem(emailKey, JSON.stringify(initialThreads));
    }

    setThreads(initialThreads);
    if (initialThreads.length > 0) {
      setActiveThreadId(initialThreads[0].id);
    } else {
      setActiveThreadId(null);
    }
  }, [userSession, storageKey]);

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



  const saveProfile = async (profile: StudentProfile) => {
    setStudentProfile(profile);
    localStorage.setItem(profileKey, JSON.stringify(profile));
    if (userSession) {
      try {
        await updateProfileServerAction(userSession.email, userSession.role, {
          name: profile.name,
          branch: profile.branch,
          semester: profile.semester,
          interests: profile.interests,
        });
      } catch (err) {
        console.error("Failed to sync profile changes to server:", err);
      }
    }
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

    const userMsg: ChatMessage = {
      role: "user",
      content: textToSend,
      timestamp: Date.now(),
    };

    let currentThreadId = activeThreadId;
    const currentMessages = [...messages, userMsg];

    if (!currentThreadId) {
      currentThreadId = `thread_${Date.now()}`;
      const title =
        textToSend.length > 25 ? textToSend.substring(0, 25) + "..." : textToSend;
      const newThread: ChatThread = {
        id: currentThreadId,
        title,
        messages: [userMsg],
        timestamp: Date.now(),
      };

      const updatedThreads = [newThread, ...threads];
      const limitedThreads = updatedThreads.slice(0, 10);
      setThreads(limitedThreads);
      setActiveThreadId(currentThreadId);
      localStorage.setItem(getThreadsKey(userSession), JSON.stringify(limitedThreads));
    } else {
      const updatedThreads = threads.map((t) => {
        if (t.id === currentThreadId) {
          return {
            ...t,
            messages: currentMessages,
            timestamp: Date.now(),
          };
        }
        return t;
      });
      updatedThreads.sort((a, b) => b.timestamp - a.timestamp);
      const limitedThreads = updatedThreads.slice(0, 10);
      setThreads(limitedThreads);
      localStorage.setItem(getThreadsKey(userSession), JSON.stringify(limitedThreads));
    }

    setInputText("");
    setLoading(true);
    setActiveCitations([]);

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

      let assistantContent = "";
      if (result.success) {
        assistantContent = result.content?.trim()
          ? result.content
          : "I could not find that information in the available university data.";
        if (result.citations) {
          setActiveCitations(result.citations);
        }
      } else {
        assistantContent =
          "Sorry, I had trouble processing your query. Please check your network or try again.";
        setErrorMessage(
          result.error ?? "Failed to receive response from AURA server.",
        );
      }

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: assistantContent,
        timestamp: Date.now(),
      };

      const finalMessages = [...currentMessages, assistantMsg];
      
      setThreads((prevThreads) => {
        const updated = prevThreads.map((t) => {
          if (t.id === currentThreadId) {
            return {
              ...t,
              messages: finalMessages,
              timestamp: Date.now(),
            };
          }
          return t;
        });
        updated.sort((a, b) => b.timestamp - a.timestamp);
        const limitedThreads = updated.slice(0, 10);
        localStorage.setItem(getThreadsKey(userSession), JSON.stringify(limitedThreads));
        return limitedThreads;
      });
    } catch {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content:
          "Error: I encountered a problem communicating with the university registry servers.",
        timestamp: Date.now(),
      };
      const finalMessages = [...currentMessages, errorMsg];
      setThreads((prevThreads) => {
        const updated = prevThreads.map((t) => {
          if (t.id === currentThreadId) {
            return {
              ...t,
              messages: finalMessages,
              timestamp: Date.now(),
            };
          }
          return t;
        });
        updated.sort((a, b) => b.timestamp - a.timestamp);
        const limitedThreads = updated.slice(0, 10);
        localStorage.setItem(getThreadsKey(userSession), JSON.stringify(limitedThreads));
        return limitedThreads;
      });
      setErrorMessage("Network error: Could not reach registry servers.");
    } finally {
      stepTimers.forEach(clearTimeout);
      setLoading(false);
      setThinkingStep("");
    }
  };

  const startNewChat = () => {
    setActiveThreadId(null);
    setActiveCitations([]);
    setErrorMessage(null);
  };

  const deleteThread = (id: string) => {
    const updatedThreads = threads.filter((t) => t.id !== id);
    setThreads(updatedThreads);
    localStorage.setItem(getThreadsKey(userSession), JSON.stringify(updatedThreads));
    if (activeThreadId === id) {
      if (updatedThreads.length > 0) {
        setActiveThreadId(updatedThreads[0].id);
      } else {
        setActiveThreadId(null);
      }
      setActiveCitations([]);
    }
  };

  const clearAllThreads = () => {
    setThreads([]);
    setActiveThreadId(null);
    localStorage.removeItem(getThreadsKey(userSession));
    setActiveCitations([]);
    setErrorMessage(null);
  };

  const handleClearChat = () => {
    if (activeThreadId) {
      deleteThread(activeThreadId);
    } else {
      setActiveCitations([]);
      setErrorMessage(null);
    }
  };

  const logout = async () => {
    setUserSession(null);
    localStorage.removeItem("aura_session");
    try {
      await logoutServerAction();
    } catch (err) {
      console.error("Error logging out on server:", err);
    }
    const defaultProfile: StudentProfile = {
      name: "",
      branch: "B.Tech (ICT)",
      year: "3rd Year",
      semester: "Semester V",
      interests: "Artificial Intelligence, competitive coding",
    };
    setStudentProfile(defaultProfile);
    localStorage.setItem(profileKey, JSON.stringify(defaultProfile));
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
    threads,
    activeThreadId,
    setActiveThreadId,
    startNewChat,
    deleteThread,
    clearAllThreads,
    studentProfile,
    saveProfile,
    handleMicClick,
    handleSendMessage,
    handleClearChat,
    userSession,
    logout,
  };
}
