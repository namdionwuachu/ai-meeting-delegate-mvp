import json
import os
import traceback
import boto3
dynamodb = boto3.resource("dynamodb")
from datetime import datetime, timezone
from urllib.parse import quote
from persona.persona_loader import load_persona
from persona.examples_loader import load_examples
from persona.rag_retriever import retrieve_context
from persona.response_generator import generate_delegate_response
from policy.decision_rules import check_policy
from policy.confidence import score_confidence
from policy.output_guardrails import check_output
from policy.escalation import escalate
from voice.voice_router import synthesize_voice
from audit.audit_writer import write_audit_record
from meeting.output_media import start_audio_output, start_output_media


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }


def handler(event, context):
    """Main API Lambda for POST /delegate/respond."""
    try:
        # ── Realtime meeting invocation (async from realtime_handler) ──
        if event.get("source") == "realtime":
            transcript = event.get("transcript", "")
            bot_id = event.get("bot_id")
            meeting_id = event.get("meeting_id", "realtime-session")
            persona_id = "namdi"
            
            print(f"[REALTIME] transcript={transcript!r} bot_id={bot_id!r}")

            if not transcript or not bot_id:
                print(f"[REALTIME] Early return — missing transcript or bot_id")
                return

            policy = check_policy(transcript, source="INPUT")
            if policy["decision"] == "block":
                return

            persona = load_persona(persona_id)
            rag_context = retrieve_context(transcript, persona_id)
            examples = load_examples(persona_id, policy.get("intent", "general"))
            generation = generate_delegate_response(
                question=transcript,
                persona=persona,
                rag_context=rag_context,
                examples=examples,
                policy=policy,
            )
            answer = generation["text"]

            output_policy = check_output(answer, source="OUTPUT")
            if output_policy["decision"] == "block":
                return

            audio_result = synthesize_voice(
                text=answer,
                voice_profile_id=os.environ.get("DEFAULT_VOICE_PROFILE_ID", "namdi-v1"),
                meeting_id=meeting_id,
                output_mode="file",
            )

            
            audio_url = (
                (audio_result or {}).get("audio_url")
                or (audio_result or {}).get("url")
                or (audio_result or {}).get("presigned_url")
            )
            
            print(f"[REALTIME] audio_result={audio_result} audio_url={audio_url!r}")
            

            avatar_result = None

            if audio_url and bot_id:
                result = start_audio_output(bot_id=bot_id, audio_url=audio_url)
                print(f"[REALTIME] start_audio_output result={result}")

                avatar_base_url = os.environ.get("AVATAR_STATIC_URL", "")
                encoded_audio = quote(audio_url, safe="")
                encoded_message = quote(answer[:180], safe="")
                liveavatar_ok = False
                           
                try:
                    from avatar.liveavatar_client import create_session_token
                    import time

                    session = create_session_token()
                    if session.get("created"):
                        table = dynamodb.Table(os.environ["SESSIONS_TABLE"])
                        table.put_item(Item={
                            "meeting_id": bot_id,
                            "event_ts": "liveavatar_token",
                            "session_token": session["session_token"],
                            "audio_url": audio_url,
                            "message": answer[:180],
                            "ttl": int(time.time()) + 300,
                        })

                        avatar_api_url = os.environ.get("AVATAR_TOKEN_API_URL", "")
                        avatar_url = (
                            f"{avatar_base_url}/live/index.html"
                            f"?bot_id={bot_id}"
                            f"&token_url={quote(avatar_api_url, safe='')}"
                        
                        )
                        print(f"[REALTIME] avatar_url_length={len(avatar_url)} avatar_url={avatar_url[:200]!r}")
                        avatar_result = start_output_media(
                            bot_id=bot_id,
                            webpage_url=avatar_url,
                        )
                      
                        print(f"[REALTIME] liveavatar avatar_result={avatar_result}")
                        liveavatar_ok = True
                        # ── LiveKit audio publish for lip-sync ──────────────────
                        # Send audio to LiveAvatar via LiveKit REST API
                        # Avoids livekit SDK numpy dependency issues in Lambda
                        try:
                            import requests as req_lib
                            import base64
                            import json as _json

                            avatar_api_url = os.environ.get("AVATAR_TOKEN_API_URL", "")

                            # Get LiveKit credentials
                            token_resp = req_lib.get(
                                f"{avatar_api_url}?bot_id={bot_id}",
                                timeout=15,
                            )
                            token_data = token_resp.json()
                            lk_url = token_data.get("livekit_url")
                            lk_token = token_data.get("livekit_token")
                            ws_url = token_data.get("ws_url")

                            if lk_url and lk_token:
                                # Fetch MP3 from S3
                                audio_resp = req_lib.get(audio_url, timeout=15)
                                mp3_b64 = base64.b64encode(audio_resp.content).decode("utf-8")

                                # Send audio via LiveKit data channel REST API
                                lk_http_url = lk_url.replace("wss://", "https://").replace("ws://", "http://")
                                data_payload = _json.dumps({
                                    "type": "agent.speak",
                                    "audio": mp3_b64,
                                }).encode("utf-8")

                                data_b64 = base64.b64encode(data_payload).decode("utf-8")

                                send_resp = req_lib.post(
                                    f"{lk_http_url}/twirp/livekit.RoomService/SendData",
                                    json={
                                        "room": token_data.get("room_name", ""),
                                        "data": data_b64,
                                        "kind": 0,
                                    },
                                    headers={
                                        "Authorization": f"Bearer {lk_token}",
                                        "Content-Type": "application/json",
                                    },
                                    timeout=15,
                                )
                                print(f"[REALTIME] livekit_send_data status={send_resp.status_code} response={send_resp.text[:200]}")

                        except Exception as lk_err:
                            import traceback as tb
                            print(f"[REALTIME] livekit_publish_failed type={type(lk_err).__name__} error={str(lk_err)!r} traceback={tb.format_exc()}")
                        

                    else:
                        raise Exception(f"LiveAvatar token failed: {session}")

                except Exception as e:
                    print(f"[REALTIME] liveavatar_failed fallback_to_static error={str(e)}")

                if not liveavatar_ok and avatar_base_url:
                    avatar_url = (
                        f"{avatar_base_url}/avatar.html"
                        f"?audio_url={encoded_audio}"
                        f"&message={encoded_message}"            
                    )
                    print(f"[REALTIME] avatar_url={avatar_url!r}")
                    
                    avatar_result = start_output_media(
                        bot_id=bot_id,
                        webpage_url=avatar_url,
                    )
                    print(f"[REALTIME] static avatar_result={avatar_result}")
                       
                    
            return {
                "ok": True,
                "source": "realtime",
                "audio_url": audio_url,
                "avatar_result": avatar_result,
            }

        # ── Existing HTTP API flow below ──
        if event.get("httpMethod") == "GET":
            return _response(200, {"status": "ok", "service": "ai-meeting-delegate"})

        body = json.loads(event.get("body") or "{}") if "body" in event else event
        transcript = body.get("transcript") or body.get("question")
        persona_id = body.get("persona_id", "namdi")
        meeting_id = body.get("meeting_id", "local-demo")
        mode = body.get("mode", "text")

        if not transcript:
            return _response(400, {"error": "transcript or question is required"})
        
        

        policy = check_policy(transcript, source="INPUT")
        if policy["decision"] == "block":
            answer = "I am not authorised to answer that on behalf of the human owner. I will escalate it for direct review."
            escalation = escalate({
                "meeting_id": meeting_id,
                "persona_id": persona_id,
                "transcript": transcript,
                "policy": policy,
                "answer": answer,
            })
            audit = write_audit_record({
                "meeting_id": meeting_id,
                "persona_id": persona_id,
                "transcript": transcript,
                "decision": "block",
                "answer": answer,
                "policy": policy,
                "escalation": escalation,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            return _response(200, {"decision": "block", "text": answer, "policy": policy, "escalation": escalation, "audit": audit})

        persona = load_persona(persona_id)
        rag_context = retrieve_context(transcript, persona_id)
        examples = load_examples(persona_id, policy.get("intent", "general"))

        generation = generate_delegate_response(
            question=transcript,
            persona=persona,
            rag_context=rag_context,
            examples=examples,
            policy=policy,
        )
        answer = generation["text"]

        output_policy = check_output(answer, source="OUTPUT")
        if output_policy["decision"] == "block":
            answer = "I should not answer that directly. I will flag this for the human owner."
            policy["output_guardrail"] = output_policy
            policy["escalation_required"] = True

        confidence = score_confidence(rag_context=rag_context, examples=examples, policy=policy)
        decision = "speak" if confidence >= 0.7 and policy["decision"] == "allow" and output_policy["decision"] == "allow" else "cautious"
        escalation = None
        if policy.get("escalation_required", False):
            escalation = escalate({
                "meeting_id": meeting_id,
                "persona_id": persona_id,
                "transcript": transcript,
                "decision": decision,
                "policy": policy,
                "confidence": confidence,
                "draft_answer": answer,
            }, subject="AI Delegate review required")

        audio_result = None
        if mode in ["voice", "voice_only", "voice_avatar"]:
            audio_result = synthesize_voice(
                text=answer,
                voice_profile_id=body.get("voice_profile_id") or os.environ.get("DEFAULT_VOICE_PROFILE_ID", "namdi-v1"),
                meeting_id=meeting_id,
                output_mode=body.get("output_mode", "file"),
            )

        audit = write_audit_record({
            "meeting_id": meeting_id,
            "persona_id": persona_id,
            "transcript": transcript,
            "decision": decision,
            "answer": answer,
            "confidence": confidence,
            "policy": policy,
            "rag_context": rag_context,
            "examples": examples,
            "audio": audio_result,
            "generation": generation,
            "output_policy": output_policy,
            "escalation": escalation,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        return _response(200, {
            "decision": decision,
            "text": answer,
            "confidence": confidence,
            "policy": policy,
            "generation": generation,
            "audio": audio_result,
            "output_policy": output_policy,
            "escalation": escalation,
            "audit": audit,
        })

    except Exception as exc:
        print(traceback.format_exc())
        return _response(500, {"error": str(exc)})# Fri 12 Jun 2026 00:01:22 BST
