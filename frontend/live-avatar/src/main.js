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

  const session = new LiveAvatarSession();

  session.on(AgentEventsEnum.SESSION_STATE_UPDATED, (event) => {
    console.log("LiveAvatar state", event);
  });

  await session.startSession({
    sessionToken: config.session_token,
    onVideoReady: (stream) => {
      console.log("Video stream ready", stream);
      video.srcObject = stream;
      status.textContent = "LiveAvatar connected";
    },
  });

  if (config.audio_url) {
    audio.src = config.audio_url;
    await audio.play();
  }
}

start().catch((err) => {
  console.error("LiveAvatar failed", err);
  status.textContent = `LiveAvatar failed: ${err.message}`;
});
