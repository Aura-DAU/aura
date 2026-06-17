# DAU PWA - Demo Script
This document provides the presenter with a structured script, setup checklist, and speech guidelines for the live demonstration of the DAU RAG Assistant.

---

## 🛠️ Demo Setup Checklist
Before starting the presentation, ensure the following are ready:
1. **Device:** A laptop connected to the projector, and a secondary mobile device (or simulated mobile frame in browser Chrome DevTools) to showcase PWA responsive layouts.
2. **Tab 1 (Main App):** The home screen of the DAU PWA with the Chat Assistant open.
3. **Tab 2 (Code/Data):** This file structure or the RAG pipeline architecture diagram (optional, for technical Q&A).
4. **Network:** Ensure active internet connection. Have a backup offline toggle ready to demonstrate offline caching.

---

## 🎤 Speech Script & Timeline

### ⏱️ 0:00 - 1:00 | Introduction & Context
* **Presenter Action:** Stand at the podium, show the home screen of the DAU PWA on the screen.
* **Script:**
  > *"Good morning/afternoon everyone. Today, we are excited to demonstrate the Dhirubhai Ambani University PWA, featuring our newly integrated, AI-powered RAG Assistant. 
  > 
  > Managing and navigating university information—ranging from academic policies and course syllabi to hostel rules and faculty contacts—has traditionally been a tedious process for students and administration alike. Our goal is to provide a single, highly reliable, and source-grounded assistant that answers any university-related query instantly, with 100% verified citations directly from our knowledge base."*

---

### ⏱️ 1:00 - 2:30 | Scenario 1: New Student & General Information
* **Presenter Action:** Open the chat console, type or paste the first query.
* **Query:** `"What is the vision of Dhirubhai Ambani University and when was it established?"`
* **Script:**
  > *"Let's start as an incoming freshman or visitor. We ask a fundamental question about the university. 
  > 
  > As you see, the assistant responds instantly. It tells us the exact founding date—August 6, 2001—and the core vision. But the most important part is at the bottom: **Sources Cited**. By clicking this source, the user is directed to the exact source page. This guarantees that our assistant does not hallucinate; it strictly relies on the verified documents in our system."*
* **Presenter Action:** Click the cited source to show the document. Then type the second query.
* **Query:** `"What is the policy regarding hostel curfews and guest entry?"`
* **Script:**
  > *"Now, let's look at campus life policies. We ask about hostel regulations. 
  > 
  > The system parses our indexed PDFs, extracts the precise section, and formats it as clear bullet points. No more downloading large manuals and scrolling to page 45; the student gets the answer instantly."*

---

### ⏱️ 2:30 - 4:00 | Scenario 2: Academic Curriculum & Electives
* **Presenter Action:** Reset chat or continue, type the next query.
* **Query:** `"What are the core subjects required in the B.Tech CSAI program?"`
* **Script:**
  > *"Next, let's step into the shoes of a student during registration. They want to know their required subjects for the CSAI program. 
  > 
  > The assistant displays the curriculum structure, breaking down the 17 institute core courses and 12 program core courses. It also lists elective slots."*
* **Presenter Action:** Follow up with a specific course query.
* **Query:** `"Is there a course on Trustworthy AI or Reinforcement Learning?"`
* **Script:**
  > *"If the student wants to verify a specific course code, the assistant cross-references the curriculum sheets and finds that PC-311 (Trustworthy AI) is in Semester V, and PC-312 (Reinforcement Learning) is in Semester VI. This ensures students can plan their terms with accurate data."*

---

### ⏱️ 4:00 - 5:00 | Scenario 3: Research & Faculty Contacts
* **Presenter Action:** Type the research query.
* **Query:** `"What are the research areas of Professor Abhishek Gupta and how do I contact him?"`
* **Script:**
  > *"Finally, let's look at research. A student wants to work on a project with a faculty member. They look up Professor Abhishek Gupta.
  > 
  > The system fetches his profile, lists his research areas in Signal Processing and Wireless Communications, and provides his email and phone extension. The student can now reach out immediately, with all the context they need."*

---

### ⏱️ 5:00 - 6:00 | Closing & Tech Stack Summary
* **Presenter Action:** Show the main slides or the system architecture summary.
* **Script:**
  > *"Under the hood, the system uses a state-of-the-art RAG pipeline powered by GPT-4o-mini, Qwen-Embedding, and a highly optimized vector database. We evaluated the assistant against a robust benchmark of 436 test questions spanning academics, policies, and faculty details, confirming excellent retrieval precision and citation consistency.
  > 
  > This assistant delivers reliable, source-backed value to our students, faculty, and administration. Thank you, and I am open to any questions!"*
