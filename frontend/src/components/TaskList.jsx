import { useEffect, useRef, useState } from "react";
import { getTasks } from "../api";

export default function TaskList({ fastPoll = false }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const knownIdsRef = useRef(new Set());
  const [newIds, setNewIds] = useState(new Set());

  useEffect(() => {
    let cancelled = false;

    async function loadTasks() {
      try {
        const data = await getTasks();
        if (cancelled) return;

        const nextTasks = data.tasks ?? [];
        const nextIds = new Set(nextTasks.map((task) => task.id));
        const added = new Set(
          [...nextIds].filter((id) => !knownIdsRef.current.has(id)),
        );
        knownIdsRef.current = nextIds;

        setTasks(nextTasks);
        setError("");
        if (added.size > 0) {
          setNewIds(added);
          setTimeout(() => {
            if (!cancelled) setNewIds(new Set());
          }, 1200);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadTasks();
    const intervalMs = fastPoll ? 1500 : 4000;
    const timer = setInterval(loadTasks, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [fastPoll]);

  return (
    <section className="task-panel">
      <div className="task-header">
        <span>Tasks</span>
        {fastPoll && <span className="task-live">Live</span>}
      </div>

      {loading && tasks.length === 0 ? (
        <p className="task-empty">Loading tasks…</p>
      ) : error ? (
        <p className="task-empty task-empty--error">{error}</p>
      ) : tasks.length === 0 ? (
        <p className="task-empty">No open tasks yet. Ask the agent to add one.</p>
      ) : (
        <ul className="task-list">
          {tasks.map((task) => (
            <li
              key={task.id}
              className={`task-item ${newIds.has(task.id) ? "task-item--new" : ""}`}
            >
              <span className="task-check" aria-hidden />
              <span className="task-text">{task.text}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
