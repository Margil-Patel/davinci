"use client";
import Image from "next/image";
import styles from "./page.module.css";
import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi! Ask me anything about your notes." },
  ]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [showTools, setShowTools] = useState(true);
  const [showBranding, setShowBranding] = useState(true);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleAsk = async () => {
    if (!query.trim()) return;
    const userMessage = { role: "user" as const, content: query };
    setMessages((msgs) => [...msgs, userMessage]);
    setLoading(true);
    setQuery("");
    
    try {
      const res = await fetch("http://localhost:5000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      
      const data = await res.json();
      const responseText = (data.answer || data.error || "No answer returned.")
        .replace(/<think>[\s\S]*?<\/think>/g, "")
        .trim();
      
      // Stop loading and start streaming
      setLoading(false);
      setStreaming(true);
      
      // Add streaming message
      setMessages((msgs) => [...msgs, { 
        role: "assistant", 
        content: "", 
        isStreaming: true 
      }]);
      
      // Simulate streaming effect
      let currentText = "";
      const words = responseText.split(' ');
      
      for (let i = 0; i < words.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 50)); // 50ms delay between words
        currentText += (i > 0 ? ' ' : '') + words[i];
        
        setMessages((msgs) => {
          const newMsgs = [...msgs];
          const lastMsg = newMsgs[newMsgs.length - 1];
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
            lastMsg.content = currentText;
          }
          return newMsgs;
        });
      }
      
      // Mark streaming as complete
      setMessages((msgs) => {
        const newMsgs = [...msgs];
        const lastMsg = newMsgs[newMsgs.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          lastMsg.isStreaming = false;
        }
        return newMsgs;
      });
      
    } catch (err) {
      const errorMessage = { role: "assistant" as const, content: "Error calling API." };
      setMessages((msgs) => [...msgs, errorMessage]);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading && !streaming) {
      handleAsk();
    }
  };

  const startNewChat = () => {
    setMessages([{ role: "assistant", content: "Hi! Ask me anything about your notes." }]);
  };

  return (
    <div className={styles.page} style={{ padding: 0, gap: 0 }}>
      <div className={styles.container}>
        <div className={`${styles.toolsSection} ${!showTools ? styles.hidden : ''}`}>
          <button onClick={() => setShowTools(false)} className={styles.closeButton}>
            &lt;
          </button>
          <div className={styles.toolsContent}>
            <h2 className={styles.toolsTitle}>Tools</h2>
            <div className={styles.toolsList}>
              <button className={styles.toolButton}>
                <span className={styles.toolIcon}>🔍</span>
                Data Search
              </button>
              <button className={styles.toolButton}>
                <span className={styles.toolIcon}>🔬</span>
                Data Research
              </button>
              <button className={styles.toolButton}>
                <span className={styles.toolIcon}>⚙️</span>
                Workflow
              </button>
            </div>
          </div>
        </div>
        {!showTools && (
          <button onClick={() => setShowTools(true)} className={`${styles.openButton} ${styles.left}`}>
            &gt;
          </button>
        )}
        <main className={styles.chatMain}>
          <div className={styles.chatWindow}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={
                  msg.role === "user"
                    ? styles.userMessage
                    : styles.assistantMessage
                }
              >
                {msg.content}
                {msg.isStreaming && <span className={styles.cursor}>|</span>}
              </div>
            ))}
            {loading && !streaming && (
              <div className={styles.assistantMessage}>
                <div className={styles.loadingAnimation}>
                  <div className={styles.loadingDot}></div>
                  <div className={styles.loadingDot}></div>
                  <div className={styles.loadingDot}></div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
          <div className={styles.inputArea}>
            <button
              onClick={startNewChat}
              className={styles.newChatButton}
              title="Start new chat"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 5V19M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Type your message..."
              disabled={loading || streaming}
              className={styles.chatInput}
            />
            <button
              onClick={handleAsk}
              disabled={loading || streaming || !query.trim()}
              className={styles.sendButton}
              aria-label="Send"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
              </svg>
            </button>
          </div>
        </main>
        <div className={`${styles.brandingSection} ${!showBranding ? styles.hidden : ''}`}>
          <button onClick={() => setShowBranding(false)} className={styles.closeButton}>
            &gt;
          </button>
          <div className={styles.brandingContent}>
            <div className={styles.logoContainer}>
              <div className={styles.logo}>
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <path d="M16 32C16 23.1634 23.1634 16 32 16C40.8366 16 48 23.1634 48 32C48 40.8366 40.8366 48 32 48" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  <path d="M32 48L40 40L32 32" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h1 className={styles.brandName}>Davinci</h1>
              <p className={styles.brandTagline}>Your AI Knowledge Assistant</p>
            </div>
            <div className={styles.brandingFeatures}>
              <div className={styles.feature}>
                <div className={styles.featureIcon}>🧠</div>
                <div className={styles.featureText}>
                  <h3>Smart Search</h3>
                  <p>Find answers in your documents instantly</p>
                </div>
              </div>
              <div className={styles.feature}>
                <div className={styles.featureIcon}>📚</div>
                <div className={styles.featureText}>
                  <h3>Knowledge Base</h3>
                  <p>Upload and organize your documents</p>
                </div>
              </div>
              <div className={styles.feature}>
                <div className={styles.featureIcon}>💬</div>
                <div className={styles.featureText}>
                  <h3>Natural Chat</h3>
                  <p>Ask questions in plain language</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        {!showBranding && (
          <button onClick={() => setShowBranding(true)} className={`${styles.openButton} ${styles.right}`}>
            &lt;
          </button>
        )}
      </div>
    </div>
  );
}
