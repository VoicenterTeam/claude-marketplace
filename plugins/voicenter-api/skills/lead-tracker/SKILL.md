---
description: Track which marketing campaign or web page generated an inbound call using the Voicenter Lead Tracker JS SDK
---

Help the developer integrate the **Voicenter Lead Tracker** — a JavaScript SDK that assigns dynamic phone numbers (DIDs) to website visitors to track which ad, campaign, or landing page led to each incoming call.

## When to use this skill

Use this skill when the user wants to:
- Track which Google Ads / Facebook / UTM campaign generated a phone call
- Replace a static phone number on a landing page with a dynamic tracking number
- Add a click-to-call button that is tied to a specific visitor session
- Pass Google Click ID (GCLID) or Facebook Click ID (FBCLID) to offline call conversion tracking
- Know which page or source a caller was on before they called
- Build call attribution for marketing analytics

## Environment Variables

```env
VOICENTER_LEAD_TRACKER_TOKEN=your_did_pool_token_here
# Token is provided by Voicenter and is tied to a pool of DIDs configured for your account
```

## How it works

1. Visitor lands on your page from a Google Ad / social / direct source.
2. The Lead Tracker SDK calls Voicenter and gets a **dynamic DID** (virtual number) assigned to this visitor session.
3. The DID replaces your static phone number on the page.
4. When the visitor calls the DID, Voicenter links the call to their session data (UTM params, page URL, GCLID, etc.).
5. The CDR for that call contains the visitor info in `CustomData` — you know exactly which campaign generated it.

## Setup

Add the SDK script to your HTML `<body>`:

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

## `init()` Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `token` | String | ✅ | Token from Voicenter — maps to a pool of DIDs |
| `visitorInfo` | Object | ❌ | Any data to associate with this visitor session (name, email, UTM params, GCLID, etc.) |
| `actions` | Object | ❌ | DOM selectors to update automatically with the assigned DID |
| `actions.text` | String[] | ❌ | Selectors whose `innerText` will be replaced with the DID |
| `actions.href` | String[] | ❌ | Selectors whose `href` will be set to `tel:<DID>` |
| `actions.call` | String[] | ❌ | Selectors that trigger a `tel:` call when clicked |

## Examples

### Replace phone number text + click-to-call button

```html
<p class="phone-display">03-123-4567</p>
<button class="call-btn">Call Us Now</button>

<script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
<script>
VC_DID_TRACKER.init(
  'YOUR_TOKEN',
  { name: 'Visitor' },
  {
    text: ['.phone-display'],
    call: ['.call-btn'],
  }
);
</script>
```

### Pass UTM and click ID parameters

```javascript
const urlParams = new URLSearchParams(window.location.search);

VC_DID_TRACKER.init('YOUR_TOKEN', {
  utm_source: urlParams.get('utm_source') ?? 'direct',
  utm_campaign: urlParams.get('utm_campaign'),
  utm_medium: urlParams.get('utm_medium'),
  gclid: urlParams.get('gclid'),
  fbclid: urlParams.get('fbclid'),
  page: window.location.href,
});
```

### Get the DID programmatically (no DOM update)

```javascript
VC_DID_TRACKER.init('YOUR_TOKEN', { name: 'Visitor' })
  .then(function(did) {
    console.log('Assigned DID:', did);
    // Store in analytics, fire a custom GA event, etc.
    gtag('event', 'phone_number_shown', { did });
  });
```

### Full landing page example

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
      {
        text: ['.tracking-number'],
        href: ['.call-link'],
        call: ['.call-btn'],
      }
    );
  </script>
</body>
</html>
```

## TypeScript / React Integration

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
        {
          text: ['.tracking-phone'],
          href: ['.phone-link'],
        }
      );
    };
    document.body.appendChild(script);
    return () => { document.body.removeChild(script); };
  }, [token]);
}
```

## How visitor data appears in CDR

All `visitorInfo` fields are stored and associated with the call CDR. In the **CDR Notification** webhook, your UTM params, GCLID, and page URL will appear inside the `CustomData` field — enabling full offline call conversion attribution.

## Tips

- The `token` maps to a **pool of DIDs** in your Voicenter account. Each concurrent visitor on the page gets a unique DID from the pool. Contact Voicenter to configure the pool size based on your expected concurrent traffic.
- The DID is cached in **`localStorage`** so returning visitors within the DID expiry window get the same tracking number.
- Pass **`gclid`** (Google Click ID) and **`fbclid`** (Facebook Click ID) to connect offline call conversions back to your ad campaigns.
- This is entirely **client-side** — no server-side code is required.

## Related Skills

- **CDR Notification** — Receives the `visitorInfo` data in `CustomData` after the tracked call ends
- **External Layer** — Can use the DID from Lead Tracker to route calls differently per campaign
