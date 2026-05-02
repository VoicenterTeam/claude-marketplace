# Skill: `lead-tracker`

Track which marketing campaign or web page generated an inbound call using the Voicenter Lead Tracker JavaScript SDK.

> Source: [`plugins/voicenter-api/skills/lead-tracker/SKILL.md`](../../../plugins/voicenter-api/skills/lead-tracker/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **Incoming** · Transport: **Browser JS SDK**

---

## When to use this skill

- Track which Google Ads / Facebook / UTM campaign drove a phone call
- Replace a static phone number on a landing page with a dynamic tracking number (DID)
- Add a click-to-call button tied to a specific visitor session
- Pass GCLID / FBCLID into Voicenter for offline call conversion tracking
- Identify which page or ad source the caller was on before they called
- Build call attribution for marketing analytics

---

## How it works

1. Visitor lands on your page from an ad / social / direct source.
2. The Lead Tracker SDK calls Voicenter and gets a **dynamic DID** assigned to this session.
3. The DID replaces your static phone number on the page.
4. When the visitor calls the DID, Voicenter links the call to the visitor's session data.
5. The CDR for that call contains the visitor info in `CustomData` — full attribution.

The DID pool is provisioned by Voicenter; concurrent visitors get different DIDs. Returning visitors within the cache window get the same DID (stored in `localStorage`).

---

## Setup

```html
<script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
```

Then initialize:

```javascript
VC_DID_TRACKER.init(
  'YOUR_TOKEN_FROM_VOICENTER',
  { name: 'Visitor', utm_source: 'google' },
  { text: ['.phone-number'], href: ['#call-btn'], call: ['.click-to-call'] }
);
```

Environment:

```env
VOICENTER_LEAD_TRACKER_TOKEN=your_did_pool_token_here
```

The token is **client-side**, scoped only to a DID pool — exposing it in HTML is by design.

---

## `init()` arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `token` | String | ✅ | DID-pool token from Voicenter |
| `visitorInfo` | Object | ❌ | Any data to associate with this session (UTM, GCLID, etc.) |
| `actions` | Object | ❌ | DOM selectors to update with the assigned DID |
| `actions.text` | String[] | ❌ | Selectors whose `innerText` is replaced with the DID |
| `actions.href` | String[] | ❌ | Selectors whose `href` becomes `tel:<DID>` |
| `actions.call` | String[] | ❌ | Selectors that trigger a `tel:` call when clicked |

---

## Examples

### Replace a phone number + click-to-call

```html
<p class="phone-display">03-123-4567</p>
<button class="call-btn">Call Us Now</button>

<script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
<script>
VC_DID_TRACKER.init(
  'YOUR_TOKEN',
  { name: 'Visitor' },
  { text: ['.phone-display'], call: ['.call-btn'] }
);
</script>
```

### Pass UTM and click IDs

```javascript
const params = new URLSearchParams(window.location.search);
VC_DID_TRACKER.init('YOUR_TOKEN', {
  utm_source: params.get('utm_source') ?? 'direct',
  utm_campaign: params.get('utm_campaign'),
  utm_medium: params.get('utm_medium'),
  gclid: params.get('gclid'),
  fbclid: params.get('fbclid'),
  page: window.location.href,
});
```

### Get the DID programmatically

```javascript
VC_DID_TRACKER.init('YOUR_TOKEN', { name: 'Visitor' })
  .then(function(did) {
    console.log('Assigned DID:', did);
    gtag('event', 'phone_number_shown', { did });
  });
```

### Full landing page

```html
<!DOCTYPE html>
<html>
<head><title>Landing Page</title></head>
<body>
  <h1>Contact Us</h1>
  <p>Call us: <span class="tracking-number">Loading...</span></p>
  <a href="#" class="call-link">Click to Call</a>
  <button class="call-btn">Call Now</button>

  <script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
  <script>
    const params = new URLSearchParams(window.location.search);
    VC_DID_TRACKER.init(
      'YOUR_VOICENTER_TOKEN',
      {
        utm_source: params.get('utm_source') ?? 'direct',
        utm_campaign: params.get('utm_campaign'),
        gclid: params.get('gclid'),
        page: window.location.href,
      },
      { text: ['.tracking-number'], href: ['.call-link'], call: ['.call-btn'] }
    );
  </script>
</body>
</html>
```

### React hook

```typescript
import { useEffect } from 'react';

declare const VC_DID_TRACKER: {
  init: (token: string, visitorInfo?: object, actions?: object) => Promise<string>;
};

export function useLeadTracker(token: string) {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js';
    script.onload = () => {
      const params = new URLSearchParams(window.location.search);
      VC_DID_TRACKER.init(
        token,
        {
          utm_source: params.get('utm_source') ?? 'direct',
          utm_campaign: params.get('utm_campaign'),
          page: window.location.href,
        },
        { text: ['.tracking-phone'], href: ['.phone-link'] }
      );
    };
    document.body.appendChild(script);
    return () => { document.body.removeChild(script); };
  }, [token]);
}
```

---

## How visitor data appears downstream

Every key in `visitorInfo` is stored against the call. After the call ends:

| Where | Field |
|---|---|
| [CDR Notification](../cdr-notification/README.md) | `CustomData` — `utm_source`, `utm_campaign`, `gclid`, `page`, … |
| [Call Log](../call-log/README.md) | Include `CustomData` in the `fields` array to retrieve it |
| [External Layer](../external-layer/README.md) | Use the DID dialed (`DATA.DID`) plus your DID-pool mapping to know which campaign |

This closes the attribution loop from ad click → CDR → revenue.

---

## Tips & best practices

- The `token` maps to a **pool of DIDs**. Voicenter provisions the pool size — make sure it can absorb your concurrent traffic.
- The DID is cached in **`localStorage`** — returning visitors within the expiry window get the same number.
- Pass **`gclid`** and **`fbclid`** to enable offline call conversion uploads.
- Entirely **client-side** — no server code required.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `VC_DID_TRACKER is not defined` | Script blocked or not loaded | Check CSP, network tab |
| Same DID for every visitor | Pool is too small or cache is hitting | Ask Voicenter to expand the pool |
| Visitor info missing in CDR | `init()` not called before render | Call `init()` early in the page lifecycle |
| `tel:` link does not work on desktop | Browser without a tel handler | Provide a fallback CTA |

---

## Related skills

- [CDR Notification](../cdr-notification/README.md) — receives `visitorInfo` in `CustomData`
- [External Layer](../external-layer/README.md) — can route differently per campaign DID
- [Call Log](../call-log/README.md) — query historical attribution via `CustomData`
