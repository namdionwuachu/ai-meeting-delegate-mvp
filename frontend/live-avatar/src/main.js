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
    try {
      const resp = await fetch(config.audio_url);
      const arrayBuffer = await resp.arrayBuffer();
      const audioCtx = new AudioContext({ sampleRate: 24000 });
      const decoded = await audioCtx.decodeAudioData(arrayBuffer);
      
      // Create MediaStream from audio buffer
      const source = audioCtx.createBufferSource();
      source.buffer = decoded;
      const destination = audioCtx.createMediaStreamDestination();
      source.connect(destination);
      
      // Publish as LiveKit audio track
      const { LocalAudioTrack } = await import('livekit-client');
      const audioTrack = new LocalAudioTrack(
        destination.stream.getAudioTracks()[0],
        undefined,
        false
      );
      await room.localParticipant.publishTrack(audioTrack);
      
      // Start playing
      source.start();
      status.textContent = "Speaking…";
      
      source.onended = async () => {
        await room.localParticipant.unpublishTrack(audioTrack);
        status.textContent = "Listening…";
      };
    } catch (err) {
      console.error("[LIPSYNC] Error:", err);
    }
  }
}
start().catch((err) => {
  console.error("LiveAvatar failed", err);
  status.textContent = `Failed: ${err.message}`;
});