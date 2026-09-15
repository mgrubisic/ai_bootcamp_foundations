"""
lares_llm - thin layer for calling Gemma/Gemini through the Gemini API.

Model names and quotas change from week to week; keeping that churn here
means the teaching cells stay clean.

    from lares_llm import set_key, ask, usage, which
    set_key(API_KEY)
    print(ask("Explain overfitting in one sentence."))
    usage()

    from lares_llm import call
    res = call(transcript, tools=[TOOL], task="agent")
    res["text"], res["tool_calls"]
"""
from __future__ import annotations

import random
import time

import requests

__all__ = ["ask", "call", "usage", "which", "reset", "set_key",
           "CHAINS", "LIMITS", "STATS", "LAST"]

# --- configuration: edit when quotas change or new models arrive -----------

# fallback chains per exercise; first entry is the default
CHAINS = {
    "chat":  ["gemma-4-31b-it", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
    "rag":   ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemma-4-31b-it"],
    "agent": ["gemma-4-31b-it", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
}

# copy from ai.dev/usage?tab=rate-limit if these change
LIMITS = {
    "gemma-4-31b-it":        {"rpm": 30, "tpm":  16_000, "rpd": 14_400},
    "gemini-3.1-flash-lite": {"rpm": 15, "tpm": 250_000, "rpd":     500},
    "gemini-3.5-flash-lite": {"rpm": 15, "tpm": 250_000, "rpd":     500},
}
_FALLBACK_LIMIT = {"rpm": 10, "tpm": 250_000, "rpd": 250}

BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_RETRY = {429, 500, 502, 503, 504}

API_KEY: str | None = None
STATS = {"requests": 0, "input": 0, "output": 0, "thoughts": 0, "failovers": 0}
LAST = {"model": None, "input": 0, "output": 0, "thoughts": 0, "seconds": 0.0}
_DEAD: set[str] = set()      # 404 or daily quota gone - retrying will not help


def set_key(key: str) -> None:
    global API_KEY
    API_KEY = key


def reset() -> None:
    """Clear dead models and counters. Useful when restarting an exercise."""
    _DEAD.clear()
    for k in STATS:
        STATS[k] = 0


def which(task: str = "chat") -> str:
    """Which model would be used right now for this exercise."""
    chain = CHAINS.get(task, CHAINS["chat"])
    return next((m for m in chain if m not in _DEAD), chain[0])


def call(contents: list[dict], *, tools: list[dict] | None = None,
         system: str | None = None, json_schema: dict | None = None,
         search: bool = False, thinking: bool = False,
         task: str = "chat", model: str | None = None, temperature: float = 0.0,
         max_tokens: int = 1000, tries: int = 3, verbose: bool = True) -> dict:
    """
    Send a request; on failure move to the next model in the chain.

    Returns: text, thinking, tool_calls, sources, model, finish, ok, error.
    """
    if not API_KEY:
        raise RuntimeError("No API_KEY. Call set_key(...) first.")

    gc = {"temperature": temperature, "maxOutputTokens": max_tokens,
          "thinkingConfig": {"thinkingLevel": "high" if thinking else "minimal"}}
    if json_schema:
        gc["responseMimeType"] = "application/json"
        gc["responseSchema"] = json_schema

    body: dict = {"contents": contents, "generationConfig": gc}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    blocks = ([{"functionDeclarations": tools}] if tools else []) \
        + ([{"google_search": {}}] if search else [])
    if blocks:
        body["tools"] = blocks

    chain = [model] if model else CHAINS.get(task, CHAINS["chat"])
    chain = [m for m in chain if m not in _DEAD] or list(chain)
    err = "unknown"

    for i, mdl in enumerate(chain):
        if i:
            STATS["failovers"] += 1
            if verbose:
                print(f"  -> switching to {mdl}")

        for attempt in range(1, tries + 1):
            t0 = time.time()
            r = requests.post(f"{BASE}/{mdl}:generateContent",
                              params={"key": API_KEY}, json=body, timeout=120)
            if r.status_code == 200:
                return _parse(r.json(), mdl, time.time() - t0)

            err = f"{mdl}: HTTP {r.status_code} {r.text[:120]}"
            if verbose:
                print(f"  {mdl}: HTTP {r.status_code}")

            # 404 or daily quota: waiting will not help, drop the model
            if r.status_code == 404 or (r.status_code == 429
                                        and "perday" in r.text.lower()):
                _DEAD.add(mdl)
                break
            if r.status_code not in _RETRY or attempt == tries:
                break

            base = 6.0 if r.status_code == 503 else 1.0    # 503 lasts longer
            wait = min(45, base * 2 ** (attempt - 1)) * (0.5 + random.random())
            if verbose:
                print(f"     waiting {wait:.1f}s")
            time.sleep(wait)

    return {"text": f"[all models failed: {err}]", "thinking": "", "tool_calls": [],
            "sources": [], "model": None, "finish": "ERROR", "ok": False, "error": err}


def _parse(j: dict, mdl: str, secs: float) -> dict:
    u = j.get("usageMetadata") or {}
    LAST.update(model=mdl, input=u.get("promptTokenCount", 0),
                output=u.get("candidatesTokenCount", 0),
                thoughts=u.get("thoughtsTokenCount", 0), seconds=secs)
    STATS["requests"] += 1
    for k in ("input", "output", "thoughts"):
        STATS[k] += LAST[k]

    cands = j.get("candidates") or []
    if not cands:
        return {"text": "[no answer - most likely a safety filter]", "thinking": "",
                "tool_calls": [], "sources": [], "model": mdl,
                "finish": "NO_CANDIDATES", "ok": False, "error": None}

    c = cands[0]
    # one pass: reasoning parts carry "thought": true and must stay out of text
    text, thought, calls = [], [], []
    for p in (c.get("content") or {}).get("parts") or []:
        if "functionCall" in p:
            calls.append({"name": p["functionCall"].get("name", ""),
                          "args": p["functionCall"].get("args") or {}})
        elif "text" in p:
            (thought if p.get("thought") else text).append(p["text"])

    meta = c.get("groundingMetadata")        # only present when search=True
    return {"text": "".join(text).strip(), "thinking": "".join(thought).strip(),
            "tool_calls": calls, "model": mdl, "finish": c.get("finishReason", "?"),
            "ok": True, "error": None,
            "sources": [ch["web"] for ch in (meta.get("groundingChunks") or [])
                        if ch.get("web")] if meta else []}


def ask(prompt: str, **kw) -> str:
    """One prompt -> text. Everything else behaves like call()."""
    res = call([{"role": "user", "parts": [{"text": prompt}]}], **kw)
    if res["finish"] == "MAX_TOKENS":
        return res["text"] + "\n\n[TRUNCATED -> raise max_tokens]"
    return res["text"]


def usage(label: str = "last call") -> None:
    l, s = LAST, STATS
    print(f"  {label + ':':20s} {str(l['model'] or '-'):24s} "
          f"in {l['input']:>7,}  out {l['output']:>6,}  thinking {l['thoughts']:>6,}"
          f"  {l['seconds']:.1f}s")
    print(f"  {'total:':20s} {str(s['requests']) + ' calls':24s} "
          f"in {s['input']:>7,}  out {s['output']:>6,}  thinking {s['thoughts']:>6,}"
          + (f"   ({s['failovers']} failovers)" if s["failovers"] else ""))
    if l["model"]:
        lim = LIMITS.get(l["model"], _FALLBACK_LIMIT)
        tot = max(1, l["input"] + l["output"] + l["thoughts"])   # thinking counts too
        print(f"  limits {l['model']}: rpm={lim['rpm']} tpm={lim['tpm']:,} "
              f"rpd={lim['rpd']:,}  -> ~{min(lim['rpm'], lim['tpm'] // tot)} calls/min")
    if _DEAD:
        print(f"  models dropped: {', '.join(sorted(_DEAD))}")
