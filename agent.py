"""LiveKit voice agent worker."""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession, JobExecutorType, inference
from livekit.agents.voice.room_io import RoomOptions, TextOutputOptions
from livekit.plugins import groq

from app.config import (
    AGENT_ENDPOINTING_MAX,
    AGENT_ENDPOINTING_MIN,
    AGENT_NAME,
    AGENT_PREEMPTIVE_TTS,
    AGENT_VAD_ACTIVATION,
    AGENT_VAD_MIN_SILENCE,
    GROQ_LLM_MODEL,
    GROQ_TTS_MODEL,
    GROQ_TTS_VOICE,
)
from app.database import init_db
from assistant import VoiceAssistant

load_dotenv()
init_db()

server = AgentServer(
    job_executor_type=JobExecutorType.THREAD,
    num_idle_processes=1,
    initialize_process_timeout=60.0,
    load_threshold=1.0,
)

TURN_HANDLING = {
    "turn_detection": "vad",
    "endpointing": {
        "min_delay": AGENT_ENDPOINTING_MIN,
        "max_delay": AGENT_ENDPOINTING_MAX,
    },
    "preemptive_generation": {
        "enabled": True,
        "preemptive_tts": AGENT_PREEMPTIVE_TTS,
    },
}


@server.rtc_session(agent_name=AGENT_NAME)
async def voice_agent(ctx: agents.JobContext):
    await ctx.connect()

    participant = await ctx.wait_for_participant()
    user_id_str = participant.attributes.get("user_id")
    if not user_id_str:
        raise ValueError("No user_id in participant attributes — user must be authenticated")

    user_id = int(user_id_str)
    assistant = VoiceAssistant(user_id=user_id)

    session = AgentSession(
        vad=inference.VAD(
            model="silero",
            activation_threshold=AGENT_VAD_ACTIVATION,
            min_silence_duration=AGENT_VAD_MIN_SILENCE,
        ),
        stt=groq.STT(model="whisper-large-v3-turbo", language="en"),
        llm=groq.LLM(model=GROQ_LLM_MODEL),
        tts=groq.TTS(model=GROQ_TTS_MODEL, voice=GROQ_TTS_VOICE),
        turn_handling=TURN_HANDLING,
    )

    await session.start(
        room=ctx.room,
        agent=assistant,
        room_options=RoomOptions(
            text_output=TextOutputOptions(sync_transcription=False),
        ),
    )
    await session.generate_reply(
        instructions="Greet the user by name if you know it, and ask how you can help."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
