const apiBase = document.getElementById('apiBase');
const question = document.getElementById('question');
const output = document.getElementById('output');
const player = document.getElementById('player');

async function callDelegate(mode) {
  const base = apiBase.value.replace(/\/$/, '');
  if (!base) throw new Error('Enter your API Gateway base URL');
  const resp = await fetch(`${base}/delegate/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      persona_id: 'namdi',
      meeting_id: 'test-ui',
      transcript: question.value,
      mode,
      output_mode: 'file'
    })
  });
  const data = await resp.json();
  output.textContent = JSON.stringify(data, null, 2);
  const audioUrl = data?.audio?.presigned_url || data?.audio?.audio_url;
  if (audioUrl) {
    player.src = audioUrl;
    player.play().catch(() => {});
  }
}

document.getElementById('askBtn').onclick = () => callDelegate('text').catch(e => output.textContent = e.message);
document.getElementById('voiceBtn').onclick = () => callDelegate('voice').catch(e => output.textContent = e.message);
