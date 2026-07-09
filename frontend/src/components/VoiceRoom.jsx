import { useEffect, useRef, useState } from "react";
import { Room, RoomEvent, Track } from "livekit-client";
import { getLiveKitToken } from "../api";
import ChatTranscript from "./ChatTranscript";
import { MicIcon, WaveIcon } from "./Icons";

const STATES = {
  idle: { label: "Ready", detail: "Tap the mic to start a voice session" },
  connecting: { label: "Connecting…", detail: "Joining LiveKit room" },
  connected: { label: "Waiting for agent", detail: "Agent is joining the room" },
  listening: { label: "Live", detail: "Speak naturally — you can interrupt anytime" },
  error: { label: "Error", detail: "" },
};

const IS_MOBILE = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

const MIC_CAPTURE_OPTIONS = {
  channelCount: 1,
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: !IS_MOBILE,
};

async function applyMicEchoCancellation(room) {
  const pub = room.localParticipant.getTrackPublication(Track.Source.Microphone);
  const mediaTrack = pub?.track?.mediaStreamTrack;
  if (mediaTrack?.applyConstraints) {
    await mediaTrack.applyConstraints({
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: !IS_MOBILE,
    });
  }
}

function upsertTranscript(messages, segment, role) {
  const idx = messages.findIndex((m) => m.id === segment.id);
  const entry = {
    id: segment.id,
    role,
    text: segment.text,
    final: segment.final,
  };
  if (idx >= 0) {
    const next = [...messages];
    next[idx] = entry;
    return next;
  }
  return [...messages, entry];
}

export default function VoiceRoom({ onSessionLiveChange }) {
  const [state, setState] = useState("idle");
  const [detail, setDetail] = useState(STATES.idle.detail);
  const [messages, setMessages] = useState([]);
  const roomRef = useRef(null);
  const audioRef = useRef(null);

  function setVoiceState(key, extraDetail) {
    setState(key);
    setDetail(extraDetail ?? STATES[key]?.detail ?? "");
  }

  function attachAudio(track, label) {
    if (track.kind !== Track.Kind.Audio || !audioRef.current) return;
    const el = track.attach();
    el.autoplay = true;
    el.playsInline = true;
    el.setAttribute("playsinline", "true");
    el.setAttribute("webkit-playsinline", "true");
    el.volume = IS_MOBILE ? 0.5 : 0.85;
    el.id = `audio-${label}`;
    audioRef.current.appendChild(el);
  }

  function handleTranscription(segments, participant) {
    if (!participant) return;
    const role = participant.isLocal ? "user" : "agent";
    setMessages((prev) =>
      segments.reduce((acc, segment) => upsertTranscript(acc, segment, role), prev),
    );
  }

  async function connect() {
    try {
      setVoiceState("connecting");
      setMessages([]);
      const { token, url, room: roomName } = await getLiveKitToken();

      if (audioRef.current) audioRef.current.innerHTML = "";

      const room = new Room({
        audioCaptureDefaults: MIC_CAPTURE_OPTIONS,
      });
      roomRef.current = room;

      room.on(RoomEvent.Connected, () => {
        setVoiceState("connected", `Room ${roomName} — agent incoming`);
      });

      room.on(RoomEvent.ParticipantConnected, (p) => {
        if (!p.isLocal) {
          setVoiceState("listening", "Agent ready — ask me anything");
          p.audioTrackPublications.forEach((pub) => {
            if (pub.track) attachAudio(pub.track, p.identity);
          });
        }
      });

      room.on(RoomEvent.TrackSubscribed, (track, _pub, participant) => {
        if (!participant.isLocal) attachAudio(track, participant.identity);
      });

      room.on(RoomEvent.TranscriptionReceived, handleTranscription);

      room.on(RoomEvent.Disconnected, () => {
        setVoiceState("idle");
      });

      await room.startAudio();
      await room.connect(url, token);
      await room.localParticipant.setMicrophoneEnabled(true, MIC_CAPTURE_OPTIONS);
      await applyMicEchoCancellation(room);
    } catch (err) {
      setVoiceState("error", err.message);
      console.error(err);
    }
  }

  async function disconnect() {
    if (roomRef.current) await roomRef.current.disconnect();
    roomRef.current = null;
    setVoiceState("idle");
  }

  const isLive = state === "listening" || state === "connected" || state === "connecting";
  const statusLabel = state === "error" ? "Error" : STATES[state]?.label ?? "Ready";

  useEffect(() => {
    onSessionLiveChange?.(isLive);
  }, [isLive, onSessionLiveChange]);

  return (
    <>
      <ChatTranscript messages={messages} isLive={isLive} />

      <div className="voice-panel">
        <div className="voice-orb-wrap" data-state={state}>
          <div className="voice-orb-ring" />
          <button
            type="button"
            className="voice-orb"
            onClick={() => connect()}
            disabled={isLive}
            aria-label={isLive ? "Session active" : "Start voice session"}
          >
            {state === "listening" ? <WaveIcon /> : <MicIcon />}
          </button>
        </div>

        <div className="status-row">
          <span
            className={`status-dot ${
              state === "listening"
                ? "status-dot--live"
                : state === "connecting" || state === "connected"
                  ? "status-dot--connecting"
                  : state === "error"
                    ? "status-dot--error"
                    : ""
            }`}
          />
          <span className="status-label">{statusLabel}</span>
        </div>
        <p className="status-detail">{detail}</p>

        {isLive && (
          <button type="button" className="btn btn-ghost disconnect-btn" onClick={disconnect}>
            End session
          </button>
        )}

        <div ref={audioRef} style={{ display: "none" }} aria-hidden />
      </div>
    </>
  );
}
