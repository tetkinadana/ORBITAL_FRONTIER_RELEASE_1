# ORBITAL FRONTIER

Telegram Mini App / React + Vite frontend with Python `aiogram 3` bot backend and SQLite game modules.

## Frontend (Windows / PowerShell)

```powershell
cd .\webapp
npm.cmd install
npm.cmd run build
npm.cmd run dev
```

To publish a test branch after a successful build:

```powershell
npx.cmd wrangler pages deploy dist --project-name orbital-frontier --branch preview-test
```

## Backend

Create `.env` from `.env.example`, fill in your bot token, install `requirements.txt`, then run `python main.py`.

## Important

Read `IMPLEMENTATION_STATUS.md` before publishing. The current frontend prototype stores player progress and currencies in browser `localStorage`; guilds and rewards are not yet protected by a shared authoritative API. Payment packs are display-only until a payment provider is connected. Back up the existing SQLite database before changing backend files.
