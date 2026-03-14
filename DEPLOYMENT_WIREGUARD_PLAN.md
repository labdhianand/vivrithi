# Deployment and WireGuard Plan

## Problem

The hackathon requires a publicly accessible application, but the available Docling GPU host is reachable only over WireGuard at `10.2.36.58`.

That means:

- users must not need VPN access
- the GPU should remain private
- the backend still needs a private route to the GPU

## Recommended Hackathon Topology

### Public Backend on a WireGuard-Capable VM

```text
Internet User
  -> HTTPS
  -> Public VM
     -> Frontend
     -> Backend API
     -> SQLite / persistent disk
     -> WireGuard client
        -> moslabserver (10.2.36.58)
           -> Docling GPU worker
```

## Why This Is the Right Tradeoff

- simplest operationally for the hackathon
- no inbound exposure for the GPU machine
- no custom queueing system required
- public judges can access the app directly
- the backend can keep the current SSH-based orchestration code

## Components

### Public VM

Responsibilities:

- serve frontend or reverse-proxy frontend
- run FastAPI backend
- terminate TLS with Caddy or Nginx
- join the WireGuard network
- hold environment variables for:
  - Tavily
  - LandingAI
  - Docling remote connection settings

### GPU Host

Responsibilities:

- stay private on WireGuard
- run Docling inside the remote Python environment
- accept SSH only from the backend VM

### Frontend Hosting Choice

Option A:

- host frontend on the same public VM

Option B:

- host frontend on Vercel
- point it to the public backend URL

For hackathon reliability, Option A is simpler because there is only one public deployable to validate.

## Backend Configuration

Required environment variables:

- `DOCLING_REMOTE_HOST=10.2.36.58`
- `DOCLING_REMOTE_PORT=22`
- `DOCLING_REMOTE_USERNAME=moslab`
- `DOCLING_REMOTE_PASSWORD=<secret>`
- `DOCUMENT_PROCESSING_BACKEND=docling_remote`
- `DOCUMENT_BATCH_MAX_CONCURRENCY=4`

Recommended batch settings for the A100 80GB:

- `DOCLING_REMOTE_PAGE_BATCH_SIZE=128`
- `DOCLING_REMOTE_LAYOUT_BATCH_SIZE=128`
- `DOCLING_REMOTE_OCR_BATCH_SIZE=96`
- `DOCLING_REMOTE_TABLE_BATCH_SIZE=4`

## Security Notes

- Do not expose the GPU host directly to the public internet.
- Limit SSH ingress to the backend VM only.
- Store the SSH password or key only on the backend host.
- Keep WireGuard keys off the frontend runtime if the frontend is separated.

## Fallback Architecture

If the backend must stay on Railway or Render and cannot join WireGuard:

1. Public backend writes conversion jobs to a queue or database.
2. A WireGuard-connected agent polls those jobs over outbound HTTPS.
3. The agent runs Docling on the private GPU.
4. The agent posts results back to the backend.

This is more production-friendly, but slower to implement than the VM approach.

## Demo-Day Runbook

1. Start WireGuard on the public backend VM.
2. Confirm `10.2.36.58` is reachable from the backend VM.
3. Verify `nvidia-smi` on the GPU host.
4. Start backend and frontend.
5. Upload OneDrive sample documents and process the case.
6. Keep one completed case in the database as a fallback walkthrough, but do not depend on seeding for the main demo.
