import { LiveAvatarSession, AgentEventsEnum } from "@heygen/liveavatar-web-sdk";

const params = new URLSearchParams(window.location.search);
const botId = params.get("bot_id");
const tokenUrl = params.get("token_url");

const video = document.getElementById("avatarVideo");
const audio = document.getElementById("audioPlayer");
const status = document.getElementById("status");

async function getConfig() {
  if (!botId || !tokenUrl) {
    throw new Error("Missing bot_id or token_url");
  }

  const resp = await fetch(
    `${decodeURIComponent(tokenUrl)}?bot_id=${botId}`
  );

  if (!resp.ok) {
    throw new Error(`Config fetch failed: ${resp.status}`);
  }

  return await resp.json();
}

async function start() {
  const config = await getConfig();

  console.log("Avatar config loaded", config);

  const sessionToken = config.session_token;

  if (!sessionToken) {
    throw new Error("Missing session_token");
  }

  status.textContent = "Connecting to LiveAvatar...";

  const session = new LiveAvatarSession({
    sessionToken,
  });

  session.on(
    AgentEventsEnum.VIDEO_STREAM_READY,
    (event) => {
      console.log("VIDEO_STREAM_READY", event);

      const stream = event?.stream || event;

      if (stream instanceof MediaStream) {
        video.srcObject = stream;
        video.style.display = "block";
        status.textContent = "Avatar connected";
      } else {
        console.error(
          "No MediaStream found in VIDEO_STREAM_READY",
          event
        );
      }
    }
  );

  session.on(
    AgentEventsEnum.AVATAR_SPEAK_STARTED,
    (event) => {
      console.log("AVATAR_SPEAK_STARTED", event);
      status.textContent = "Avatar speaking...";
    }
  );

  session.on(
    AgentEventsEnum.AVATAR_SPEAK_ENDED,
    (event) => {
      console.log("AVATAR_SPEAK_ENDED", event);
      status.textContent = "Avatar connected";
    }
  );

  console.log("Starting session...");

  await session.startSession();

  console.log("Session started");

  status.textContent = "Testing avatar speech...";

  setTimeout(() => {
    try {
      const textEventId = session.repeat(
        "Hello, this is a LiveAvatar text command test."
      );

      console.log(
        "repeat text event_id",
        textEventId
      );

      status.textContent =
        "Sent LiveAvatar text command";
    } catch (err) {
      console.error(
        "repeat text failed",
        err
      );

      status.textContent =
        `repeat text failed: ${err.message}`;
    }
  }, 3000);
}

start().catch((err) => {
  console.error("LiveAvatar failed", err);

  status.textContent =
    `LiveAvatar failed: ${err.message}`;

  setTimeout(() => {
    const botId = params.get("bot_id");
    const audioUrl = params.get("audio_url");
    const message = params.get("message");

    const staticUrl =
      "http://aidelegatemvpstack-avatar-static.s3-website-us-east-1.amazonaws.com/avatar.html"
      + (botId ? `?bot_id=${botId}` : "")
      + (audioUrl ? `&audio_url=${audioUrl}` : "")
      + (message ? `&message=${message}` : "");

    window.location.href = staticUrl;
  }, 10000);
});