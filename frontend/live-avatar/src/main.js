import { Room, RoomEvent, Track } from "livekit-client";

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

  if (!config.livekit_url || !config.livekit_token) {
    throw new Error("Missing livekit_url or livekit_token");
  }

  status.textContent = "Connecting to LiveAvatar...";

  const room = new Room();

  room.on(RoomEvent.TrackSubscribed, (track) => {
    if (track.kind === Track.Kind.Video) {
      track.attach(video);
      video.style.display = "block";
      status.textContent = "Avatar connected";
    }
    if (track.kind === Track.Kind.Audio) {
      track.attach(audio);
    }
  });

  room.on(RoomEvent.Disconnected, () => {
    status.textContent = "Disconnected";
  });

  await room.connect(config.livekit_url, config.livekit_token);
  status.textContent = "Connected — waiting for avatar...";
}

start().catch((err) => {
  console.error("LiveAvatar failed", err);
  status.textContent = `LiveAvatar failed: ${err.message}`;

  // Fallback to static avatar with audio
  setTimeout(() => {
    const audioUrl = config?.audio_url || params.get("audio_url");
    const message = config?.message || params.get("message");

    window.location.href =
      "http://aidelegatemvpstack-avatar-static.s3-website-us-east-1.amazonaws.com/avatar.html" +
      (botId ? `?bot_id=${botId}` : "") +
      (audioUrl ? `&audio_url=${encodeURIComponent(audioUrl)}` : "") +
      (message ? `&message=${encodeURIComponent(message)}` : "");
  }, 10000);
});