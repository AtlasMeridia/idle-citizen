---
title: Sensitive credentials file in repo root
labels: [security, urgent]
created: 2025-12-24
---

## Issue

A file `values.md` exists in the repo root containing:
- Anthropic API key
- Ghost Content API key
- Site URLs

This file appears in git status as untracked but should NOT be committed.

## Recommendation

1. Delete `values.md` from the repo root
2. If these were meant as reference, store them in a `.env` file or password manager
3. Consider rotating the exposed API keys as a precaution (especially the Anthropic key)

## Note

Discovered during session 36 while reviewing git status.

## Resolution (Session 37)

File has been removed from the repo root. Issue resolved.
