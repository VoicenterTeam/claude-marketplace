/**
 * Click2Call: ring my cell first, then bridge to the office.
 *
 * Flow:
 *   Leg 1 — Voicenter dials MY_CELL. I answer.
 *   Leg 2 — Voicenter dials MY_OFFICE and bridges both legs.
 *
 * Env vars:
 *   VOICENTER_API_CODE — API token from Voicenter back office
 *   MY_CELL            — your cell in E.164 without `+` (e.g. 972501234567)
 *   MY_OFFICE          — office number or SIP extension (e.g. 97237654321 or SIP123)
 *
 * Run:
 *   VOICENTER_API_CODE=xxx MY_CELL=972500000000 MY_OFFICE=97237654321 \
 *     npx tsx call-cell-and-office.ts
 */

const C2C_URL = 'https://api.voicenter.com/ForwardDialer/click2call.aspx';

const CODE = process.env.VOICENTER_API_CODE ?? 'REPLACE_WITH_API_CODE';
const MY_CELL = process.env.MY_CELL ?? 'REPLACE_WITH_CELL_E164';
const MY_OFFICE = process.env.MY_OFFICE ?? 'REPLACE_WITH_OFFICE_NUMBER_OR_SIP';

interface Click2CallResponse {
  ERRORCODE: number;
  ERRORMESSAGE: string;
  CALLID: string;
}

async function callCellThenOffice(): Promise<Click2CallResponse> {
  const res = await fetch(C2C_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code: CODE,
      phone: MY_CELL,
      target: MY_OFFICE,
      action: 'call',
      format: 'json',
      record: 'false',
      phonemaxdialtime: 30,
      targetmaxdialtime: 30,
    }),
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: Click2CallResponse = await res.json();
  if (data.ERRORCODE !== 0) {
    throw new Error(`Click2Call error ${data.ERRORCODE}: ${data.ERRORMESSAGE}`);
  }
  return data;
}

callCellThenOffice()
  .then((r) => console.log('Call started, CALLID:', r.CALLID))
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
