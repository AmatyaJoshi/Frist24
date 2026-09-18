#!/bin/sh
# One-shot model puller. Runs against the already-healthy `ollama` service.
set -eu
MODEL="${OLLAMA_MODEL:-llama3.1:8b}"
FALLBACK="${OLLAMA_FALLBACK_MODEL:-mistral}"

echo "[ollama-pull] waiting for $OLLAMA_HOST ..."
i=0
until ollama list >/dev/null 2>&1; do
  i=$((i+1)); [ "$i" -gt 60 ] && { echo "[ollama-pull] server not reachable"; exit 1; }
  sleep 2
done

if ollama list | awk '{print $1}' | grep -qx "$MODEL"; then
  echo "[ollama-pull] $MODEL already present"; exit 0
fi

echo "[ollama-pull] pulling $MODEL (several GB on first run) ..."
if ollama pull "$MODEL"; then
  echo "[ollama-pull] done: $MODEL"; exit 0
fi

echo "[ollama-pull] $MODEL failed, trying fallback $FALLBACK ..."
ollama pull "$FALLBACK" && echo "[ollama-pull] done: $FALLBACK"
