"""LiveKit voice agent worker."""

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession
from livekit.plugins import groq

from app.config import AGENT_NAME, GROQ_LLM_MODEL
from app.database import init_db
from assistant import VoiceAssistant
from edge_tts_plugin import EdgeTTS

load_dotenv()
init_db()

server = AgentServer()


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
        tts=EdgeTTS(),
    )

    await session.start(room=ctx.room, agent=assistant)
    await session.generate_reply(
        instructions="Greet the user by name if you know it, and ask how you can help."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
