# CivicEye

AI-powered civic infrastructure operations showcase for portfolio demos.

## What it shows

- AI image and video detection for road damage
- Realtime operations and repair routing
- District risk analytics and executive reporting
- Map-based incident intelligence
- Seeded demo mode for stable local presentation

## Run locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Validation

```bash
npm run build
npm run typecheck
```

## Demo flows

1. Home page hero and live preview
2. AI upload and detection reveal
3. Operations live command center
4. Operations map and analytics
5. Executive dashboard / field queue

## Portfolio screenshots

- Hero section with live preview
- Architecture showcase section
- AI upload result reveal
- Operations live dashboard
- Operations map fallback / GIS view
- Analytics dashboard cards

## Notes

- The app includes seeded demo data so the presentation stays polished even if backend services are offline.
- The map route uses a full Mapbox view when a token is available and a seeded fallback when it is not.
