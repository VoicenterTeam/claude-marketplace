---
description: Track which marketing campaign or web page generated an inbound call using the Voicenter Lead Tracker JS SDK
---

Help the developer integrate the **Voicenter Lead Tracker** — a JavaScript SDK that assigns dynamic phone numbers (DIDs) to website visitors so you can track which ad, campaign, or landing page led to each incoming call.

## How it works

1. A visitor lands on your website from a Google Ad / Facebook / any source.
2. The Lead Tracker JS script calls Voicenter and gets a **dynamic DID** (virtual phone number) assigned to this visitor session.
3. The DID is displayed on the page in place of your static phone number.
4. When the visitor calls the DID, Voicenter links the call to that visitor's session data (UTM params, page URL, name, etc.).
5. The CDR for that call contains the visitor info — you know exactly which campaign generated it.

## Setup

Add the SDK script to your HTML `<body>`:

```html
<script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
```

Then initialize with your token and visitor info:

```javascript
VC_DID_TRACKER.init(
  'YOUR_TOKEN_FROM_VOICENTER',
  { name: 'John Doe', glid: 'gclid_param_from_url' },
  { text: ['.phone-number'], href: ['#call-btn'], call: ['.click-to-call'] }
);
```

## `init()` Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `token` | String | ✅ | Token provided by Voicenter — assigned to a pool of DIDs |
| `visitorInfo` | Object | ❌ | Any data to associate with this visitor (name, email, UTM params, GCLID, etc.) |
| `actions` | Object | ❌ | DOM selectors to update with the DID |
| `actions.text` | String[] | ❌ | Selectors whose `innerText` will be replaced with the DID |
| `actions.href` | String[] | ❌ | Selectors whose `href` will be set to `tel:<DID>` |
| `actions.call` | String[] | ❌ | Selectors that will trigger a `tel:` call when clicked |

## Examples

### Replace phone number text on the page

```html
<p class="phone-display">03-123-4567</p>

<script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
<script>
VC_DID_TRACKER.init(
  'YOUR_TOKEN',
  { name: 'Visitor' },
  { text: ['.phone-display'] }
);
// The text in .phone-display is now replaced with the visitor's assigned DID
</script>
```

### Click-to-call button

```html
<button class="call-me">Call Us Now</button>
<button id="callMe">📞 Speak to an agent</button>

<script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
<script>
VC_DID_TRACKER.init('YOUR_TOKEN', {}, { call: ['.call-me', '#callMe'] });
// Clicking either button dials the assigned DID via tel:
</script>
```

### Replace anchor `href`

```html
<a href="#" class="phone-link">Call us</a>

<script>
VC_DID_TRACKER.init('YOUR_TOKEN', {}, { href: ['.phone-link'] });
// href is now tel:<DID>
</script>
```

### Get the DID programmatically (no DOM action)

```html
<script>
VC_DID_TRACKER.init('YOUR_TOKEN', { name: 'Visitor' })
  .then(function(did) {
    console.log('Assigned DID:', did);
    // Store in your analytics, fire a custom GA event, etc.
  });
</script>
```

### Pass UTM / marketing parameters

```javascript
const urlParams = new URLSearchParams(window.location.search);

VC_DID_TRACKER.init('YOUR_TOKEN', {
  name: 'Visitor',
  utm_source: urlParams.get('utm_source'),
  utm_campaign: urlParams.get('utm_campaign'),
  utm_medium: urlParams.get('utm_medium'),
  gclid: urlParams.get('gclid'),
  fbclid: urlParams.get('fbclid'),
  page: window.location.href,
});
```

All `visitorInfo` fields are stored and associated with the call CDR — visible in the CDR Notification `CustomData`.

### Full example — landing page with tracking

```html
<!DOCTYPE html>
<html>
<head><title>My Landing Page</title></head>
<body>

  <h1>Contact Us</h1>
  <p>Call us: <span class="tracking-number">Loading...</span></p>
  <a href="#" class="call-link">📞 Click to Call</a>
  <button class="call-btn">Call Now</button>

  <script src="https://cdn.voicenter.co/cdn/Scripts/did_trace_worker/index.min.js"></script>
  <script>
    const params = new URLSearchParams(window.location.search);

    VC_DID_TRACKER.init(
      'YOUR_VOICENTER_TOKEN',
      {
        utm_source: params.get('utm_source') || 'direct',
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
  }, [token]);
}
```

## How the DID data appears in CDR

When a tracked call is made, the visitor info shows up in the CDR Notification `CustomData` field — you'll see your UTM params, page URL, and any other fields you passed into `visitorInfo`.

## Tips

- The `token` maps to a **pool of DIDs** in your Voicenter account. Each concurrent visitor on the page gets a unique DID from the pool. Contact Voicenter to configure the pool size for your expected traffic.
- The DID is cached in `localStorage` so returning visitors within the DID expiry window get the same number.
- Pass `gclid` (Google Click ID) and `fbclid` (Facebook Click ID) to connect offline call conversions back to your ad campaigns.
- Works on any HTML page — no server-side code required. The entire integration is client-side JS.
