# Nepali Movies

A mobile-first Nepali movie discovery and streaming interface that uses YouTube embeds and preserves original creator attribution.

Live app: https://apps.laxmannepal.com.np/Nepali-Movies/

## Architecture

- Static frontend suitable for GitHub Pages
- Movie metadata stored as JSON
- YouTube embeds for playback; no downloading or re-hosting
- GitHub Actions for scheduled catalog maintenance
- Local recommendation/watch-history algorithm
- PWA-ready responsive UI

## Data automation

The catalog updater can use `YOUTUBE_API_KEY` as a GitHub Actions secret. Without the secret, the app remains functional with the checked-in catalog and manual seed data.
