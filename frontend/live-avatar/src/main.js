import { LiveAvatarSession, AgentEventsEnum } from "@heygen/liveavatar-web-sdk";

const params = new URLSearchParams(window.location.search);
const botId = params.get("bot_id");
const tokenUrl = params.get("token_url");

const video = document.getElementById("avatarVideo");
const audio = document.getElementById("audioPlayer");
const status = document.getElementById("status");

async function getConfig() {
  if (!botId || !tokenUrl) throw new Error("Missing bot_id or token_url");

  const resp = await fetch(`${decodeURIComponent(tokenUrl)}?bot_id=${botId}`);
  if (!resp.ok) throw new Error(`Config fetch failed: ${resp.status}`);

  return await resp.json();
}

async function start() {
  const config = await getConfig();

  console.log("Avatar config loaded", config);
  status.textContent = "Starting LiveAvatar...";

  const sessionToken =
    config.session_token ||
    config.sessionToken ||
    config.token;

  console.log("sessionToken type", typeof sessionToken, sessionToken?.slice?.(0, 20));

  if (!sessionToken || typeof sessionToken !== "string") {
    throw new Error("Missing or invalid LiveAvatar session token");
  }

  const session = new LiveAvatarSession();

  session.on(AgentEventsEnum.SESSION_STATE_UPDATED, (event) => {
    console.log("LiveAvatar state", event);
  });

  session.on(AgentEventsEnum.VIDEO_STREAM_READY, (event) => {
    console.log("Video stream ready", event);

    const stream = event?.stream || event;

    if (stream instanceof MediaStream) {
      video.srcObject = stream;
      status.textContent = "LiveAvatar connected";
    } else {
      console.error("No MediaStream found in VIDEO_STREAM_READY event", event);
    }
  });

  await session.startSession(sessionToken);

  if (config.audio_url) {
    audio.src = config.audio_url;
    await audio.play();
  }
}

start().catch((err) => {
  console.error("LiveAvatar failed", err);
  status.textContent = `LiveAvatar failed: ${err.message}`;
});
