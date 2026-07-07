import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TaskList from "../components/TaskList";
import VoiceRoom from "../components/VoiceRoom";
import { useAuth } from "../useAuth";

const CAPABILITIES = [
  "Book meetings",
  "Manage tasks",
  "Today's schedule",
];

export default function Assistant() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessionLive, setSessionLive] = useState(false);

  async function handleLogout() {
    try {
      await logout();
    } catch (e) {
      console.error(e);
    }
    navigate("/login", { replace: true });
  }

  return (
    <div className="shell">
      <div className="brand">
        <div className="brand-mark">🎙</div>
        <span className="brand-name">Voice Agent</span>
      </div>

      <div className="card">
        <header className="user-header">
          <div className="user-info">
            {user?.picture && <img src={user.picture} alt="" />}
            <div>
              <div className="name">{user?.name}</div>
              <div className="email">{user?.email}</div>
            </div>
          </div>
          <button type="button" className="btn btn-ghost" onClick={handleLogout}>
            Sign out
          </button>
        </header>

        <h2>Assistant</h2>
        <p className="subtitle">
          Your voice-powered helper for calendar and tasks.
        </p>

        <div className="chips">
          {CAPABILITIES.map((c) => (
            <span key={c} className="chip">
              {c}
            </span>
          ))}
        </div>

        <TaskList fastPoll={sessionLive} />

        <VoiceRoom onSessionLiveChange={setSessionLive} />
      </div>
    </div>
  );
}
