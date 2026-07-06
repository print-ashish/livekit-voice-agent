"""LiveKit voice agent worker."""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession, JobExecutorType
from livekit.agents.voice.room_io import RoomOptions, TextOutputOptions
from livekit.plugins import groq

from app.config import AGENT_NAME, GROQ_LLM_MODEL, GROQ_TTS_MODEL, GROQ_TTS_VOICE
from app.database import init_db
from assistant import VoiceAssistant

load_dotenv()
init_db()

# Linux production defaults to PROCESS (subprocess per job) → OOM on Railway free tier.
# THREAD runs jobs in the main process (same as local `dev` on Windows).
# server = AgentServer(
#     job_executor_type=JobExecutorType.THREAD,
#     num_idle_processes=0,
#     initialize_process_timeout=60.0,
#     load_threshold=1.0,
# )

# from livekit.plugins import silero

# def prewarm(proc: agents.JobProcess):
#     proc.userdata["vad"] = silero.VAD.load()

server = AgentServer(
    job_executor_type=JobExecutorType.THREAD,
    num_idle_processes=0,
    initialize_process_timeout=60.0,
    load_threshold=1.0
)
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
    
        stt=groq.STT(model="whisper-large-v3-turbo"),
        llm=groq.LLM(model=GROQ_LLM_MODEL),
        tts=groq.TTS(model=GROQ_TTS_MODEL, voice=GROQ_TTS_VOICE),
        turn_detection="vad"
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
