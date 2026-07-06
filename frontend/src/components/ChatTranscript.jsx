import { useEffect, useRef } from "react";

export default function ChatTranscript({ messages, isLive }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span>Conversation</span>
        {isLive && <span className="chat-live">Live</span>}
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <p className="chat-empty">
            {isLive ? "Start speaking — your words will appear here." : "Connect to see the chat."}
          </p>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-bubble chat-bubble--${msg.role}${msg.final ? "" : " chat-bubble--interim"}`}
            >
              <span className="chat-role">{msg.role === "user" ? "You" : "Agent"}</span>
              <p>{msg.text}</p>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
