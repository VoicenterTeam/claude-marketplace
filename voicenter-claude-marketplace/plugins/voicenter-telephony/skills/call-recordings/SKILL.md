---
description: Access and download call recordings from Voicenter
---

Help the developer **access, stream, or download call recordings** from Voicenter.

## What to do

1. If they have a `callId`, fetch the recording URL directly.
2. If they have a CDR record with `recordingUrl`, show how to stream or download it.
3. Offer to build a UI player embed or a bulk-download script as needed.

## API — Get recording URL by callId

**Endpoint:** `GET https://api.voicenter.com/v2/call/{callId}/recording`

**Response:**
```json
{
  "callId": "abc-123",
  "url": "https://recordings.voicenter.com/abc-123.mp3",
  "expiresAt": "2024-06-01T12:00:00Z",
  "duration": 270,
  "size": 2162688
}
```

The `url` is a **time-limited signed URL** — cache it only for the duration of the session.

## Example — TypeScript

```typescript
async function getRecordingUrl(token: string, callId: string): Promise<string> {
  const res = await fetch(`https://api.voicenter.com/v2/call/${callId}/recording`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) throw new Error('No recording found for this call');
  if (!res.ok) throw new Error(`Recording fetch failed: ${res.status}`);
  const { url } = await res.json();
  return url;
}

// Stream into a file (Node.js)
import { createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';

async function downloadRecording(token: string, callId: string, outputPath: string) {
  const url = await getRecordingUrl(token, callId);
  const res = await fetch(url);
  if (!res.ok) throw new Error('Download failed');
  await pipeline(res.body as any, createWriteStream(outputPath));
}
```

## HTML5 audio player embed

```html
<audio controls>
  <source src="SIGNED_RECORDING_URL" type="audio/mpeg" />
  Your browser does not support audio playback.
</audio>
```

Fetch the signed URL server-side, then pass it to the client to avoid exposing your API token.

## Bulk download script — Python

```python
import requests, os

def download_all_recordings(token, call_ids, output_dir="recordings"):
    os.makedirs(output_dir, exist_ok=True)
    for call_id in call_ids:
        r = requests.get(
            f"https://api.voicenter.com/v2/call/{call_id}/recording",
            headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code == 404:
            print(f"No recording for {call_id}")
            continue
        r.raise_for_status()
        signed_url = r.json()["url"]
        audio = requests.get(signed_url)
        audio.raise_for_status()
        with open(os.path.join(output_dir, f"{call_id}.mp3"), "wb") as f:
            f.write(audio.content)
        print(f"Saved {call_id}.mp3")
```

## Notes

- Signed URLs expire — always refetch before playback, don't store them long-term.
- Check your Voicenter account's recording retention policy; old calls may not have recordings.
- For compliance (PCI/GDPR), recordings can be deleted via `DELETE /v2/call/{callId}/recording`.
