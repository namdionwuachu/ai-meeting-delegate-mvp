import { Room, RoomEvent, Track } from 'livekit-client';

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
  status.textContent = "Connecting to LiveAvatar...";

  if (!config.livekit_url || !config.livekit_token) {
    throw new Error("Missing LiveKit credentials");
  }

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

  if (config.audio_url) {
    audio.src = config.audio_url;
    audio.play().catch(err => console.warn("Autoplay blocked:", err));
  }
}

start().catch((err) => {
  console.error("LiveAvatar failed", err);
  status.textContent = `Failed: ${err.message}`;
});