"""
lares_llm - shared layer for calling models (AI Bootcamp, Thursday).

Why it exists: model names, quotas and parameters change from week to week,
and different models have different bottlenecks. This is pulled OUT of the
teaching cells so those changes happen in one place.

Usage in a notebook:

    from lares_llm import ask, usage, which
    print(ask("Explain overfitting in one sentence.", task="chat"))
    usage()

For the agent:

    from lares_llm import call
    res = call(transcript, tools=[TOOL], task="agent")
    res["text"], res["tool_calls"]
"""
from __future__ import annotations

import random
import time

import requests

__all__ = ["ask", "call", "usage", "which", "CHAINS", "LIMITS",
           "STATS", "LAST", "set_key", "reset", "supports"]

# ---------------------------------------------------------------------------
# configuration - the only place to edit when quotas change
# ---------------------------------------------------------------------------

# fallback chains per exercise; first entry is the default
# order follows the BOTTLENECK of that exercise, not model "quality"
CHAINS = {
    # short prompts, many calls -> requests per day matter
    "chat":  ["gemma-4-31b-it", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
    # document in context -> tokens per minute matter
    "rag":   ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemma-4-31b-it"],
    # long context + tool calling + many calls -> RPD and tools matter
    "agent": ["gemma-4-31b-it", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
}

# copy from ai.dev/usage?tab=rate-limit if these change
LIMITS = {
    "gemma-4-31b-it":           {"rpm": 30, "tpm":  16_000, "rpd": 14_400},
    "gemini-3.1-flash-lite":    {"rpm": 15, "tpm": 250_000, "rpd":     500},
    "gemini-3.5-flash-lite":    {"rpm": 15, "tpm": 250_000, "rpd":     500},
    "gemini-3.6-flash":         {"rpm":  5, "tpm": 250_000, "rpd":      20},
}
_DEFAULT_LIMIT = {"rpm": 10, "tpm": 250_000, "rpd": 250}

# "thinking" control differs by model family:
#   Gemini 2.5 -> thinkingBudget: 0 (can be switched off)
#   Gemini 3.x -> thinkingLevel: "MINIMAL" (cannot be fully off)
#   Gemma      -> not supported at all
# start from a guess and step down if the API rejects it
_THINKING: dict[str, dict | None] = {}

BASE = "https://generativelanguage.googleapis.com/v1beta/models"
API_KEY: str | None = None

STATS = {"requests": 0, "input": 0, "output": 0, "thoughts": 0, "failovers": 0}
LAST = {"model": None, "input": 0, "output": 0, "thoughts": 0, "seconds": 0.0}
_DEAD: set[str] = set()          # models that returned 404 or used up the daily quota
_NO_SYSTEM: set[str] = set()     # models without a systemInstruction field (e.g. Gemma)
_NO_JSON: set[str] = set()       # models without native JSON mode


def set_key(key: str) -> None:
    global API_KEY
    API_KEY = key


def reset() -> None:
    """Clear state (dead models, counters). Useful when restarting an exercise."""
    _DEAD.clear()
    _NO_SYSTEM.clear()
    _NO_JSON.clear()
    _THINKING.clear()
    for k in STATS:
        STATS[k] = 0


def which(task: str = "chat") -> str:
    """Which model would be used right now for this exercise."""
    for m in CHAINS.get(task, CHAINS["chat"]):
        if m not in _DEAD:
            return m
    return CHAINS.get(task, CHAINS["chat"])[0]


def _guess_thinking(model: str) -> dict | None:
    if model in _THINKING:
        return _THINKING[model]
    if model.startswith("gemma"):
        cfg = None
    elif "-2.5-" in model:
        cfg = {"thinkingBudget": 0}
    else:
        cfg = {"thinkingLevel": "MINIMAL"}
    _THINKING[model] = cfg
    return cfg


def _degrade_thinking(model: str) -> bool:
    """Model rejected the thinking config. Step down. True if there is more to try."""
    cfg = _THINKING.get(model)
    if not cfg:
        return False
    lvl = cfg.get("thinkingLevel")
    if lvl and lvl.isupper():
        _THINKING[model] = {"thinkingLevel": lvl.lower()}
    else:
        _THINKING[model] = None
    return True


# ---------------------------------------------------------------------------
# core: one call, with failover along the chain
# ---------------------------------------------------------------------------


def call(contents: list[dict], *, tools: list[dict] | None = None,
         extra_tools: list[dict] | None = None, system: str | None = None,
         json_schema: dict | None = None,
         task: str = "chat", model: str | None = None, temperature: float = 0.0,
         max_tokens: int = 4096, tries_per_model: int = 3,
         verbose: bool = True) -> dict:
    """
    Send a request; on failure switch to the next model in the chain.

    Returns a dict: text, tool_calls, model, finish, ok, error.
    """
    if not API_KEY:
        return {"text": "", "tool_calls": [], "model": None, "finish": "NO_KEY",
                "ok": False, "error": "No API_KEY. Call set_key(...)."}

    chain = [model] if model else [m for m in CHAINS.get(task, CHAINS["chat"])]
    chain = [m for m in chain if m not in _DEAD] or chain
    t0 = time.time()
    last_err = "nepoznato"

    for idx, mdl in enumerate(chain):
        if idx > 0:
            STATS["failovers"] += 1
            if verbose:
                print(f"  -> switching to {mdl}")

        attempt = 0
        while attempt < tries_per_model:
            attempt += 1
            gc = {"temperature": temperature, "maxOutputTokens": max_tokens}
            think = _guess_thinking(mdl)
            if think:
                gc["thinkingConfig"] = dict(think)
            local_contents = contents
            if system:
                if mdl in _NO_SYSTEM:
                    # no systemInstruction field -> prepend to the first user turn
                    local_contents = [{"role": "user",
                                       "parts": [{"text": system + "\n\n"}]}] + contents
            if json_schema is not None and mdl not in _NO_JSON:
                gc["responseMimeType"] = "application/json"
                gc["responseSchema"] = json_schema

            body: dict = {"contents": local_contents, "generationConfig": gc}
            if system and mdl not in _NO_SYSTEM:
                body["systemInstruction"] = {"parts": [{"text": system}]}
            tool_blocks = []
            if tools:
                tool_blocks.append({"functionDeclarations": tools})
            if extra_tools:                    # e.g. [{"google_search": {}}]
                tool_blocks.extend(extra_tools)
            if tool_blocks:
                body["tools"] = tool_blocks

            try:
                r = requests.post(f"{BASE}/{mdl}:generateContent",
                                  params={"key": API_KEY}, json=body, timeout=120)
            except Exception as exc:                       # network
                last_err = f"{type(exc).__name__}: {exc}"
                if verbose:
                    print(f"  {mdl}: {last_err}")
                break

            txt = r.text.lower()

            # --- 404: model does not exist on this key -> mark dead, move on ---
            if r.status_code == 404:
                _DEAD.add(mdl)
                last_err = f"{mdl}: 404, does not exist"
                if verbose:
                    print(f"  {mdl}: 404 (does not exist)")
                break

            # --- daily quota / billing: waiting does NOT help -> dead, move on ---
            _DAY = ("per day", "per_day", "perday", "requestsperday",
                    "billing", "plan and billing")
            if r.status_code == 429 and any(k in txt for k in _DAY):
                _DEAD.add(mdl)
                last_err = f"{mdl}: daily quota exhausted"
                if verbose:
                    print(f"  {mdl}: daily quota exhausted")
                break

            # --- 400 for systemInstruction: model has no such field, fold it in ---
            _SYS_ERR = ("system", "systeminstruction", "developer instruction",
                        "system_instruction")
            if (r.status_code == 400 and system and mdl not in _NO_SYSTEM
                    and any(k in txt.replace("_", " ") for k in _SYS_ERR)):
                _NO_SYSTEM.add(mdl)
                if verbose:
                    print(f"  {mdl}: no systemInstruction field -> folding into the prompt")
                attempt -= 1
                continue

            # --- 400 for JSON mode: fall back to asking for JSON in the prompt ---
            if (r.status_code == 400 and json_schema is not None
                    and mdl not in _NO_JSON
                    and ("responsemimetype" in txt.replace("_", "")
                         or "responseschema" in txt.replace("_", "")
                         or "json" in txt)):
                _NO_JSON.add(mdl)
                if verbose:
                    print(f"  {mdl}: no native JSON mode -> asking for JSON in the prompt")
                attempt -= 1
                continue

            # --- 400 due to thinking parameter: step down, retry same model ---
            if r.status_code == 400 and ("think" in txt or "budget" in txt):
                if _degrade_thinking(mdl):
                    if verbose:
                        print(f"  {mdl}: thinking config rejected -> stepping down")
                    attempt -= 1                          # does not count as an attempt
                    continue
                last_err = f"{mdl}: 400 {r.text[:120]}"
                break

            # --- 503 overload / 5xx / per-minute 429: wait and retry ---
            if r.status_code in (429, 500, 502, 503, 504):
                if attempt >= tries_per_model:
                    last_err = f"{mdl}: HTTP {r.status_code} after {attempt} attempts"
                    if verbose:
                        print(f"  {mdl}: HTTP {r.status_code}, giving up on this model")
                    break
                base = 6.0 if r.status_code == 503 else 1.0   # 503 lasts longer
                wait = min(45, base * 2 ** (attempt - 1)) * (0.5 + random.random())
                if verbose:
                    print(f"  {mdl}: HTTP {r.status_code}, waiting {wait:.1f}s")
                time.sleep(wait)
                continue

            if r.status_code >= 400:
                last_err = f"{mdl}: HTTP {r.status_code} {r.text[:150]}"
                if verbose:
                    print(f"  {mdl}: HTTP {r.status_code}")
                break

            # --- success ---
            return _parse(r.json(), mdl, time.time() - t0)

    return {"text": f"[all models failed: {last_err}]", "tool_calls": [],
            "model": None, "finish": "ERROR", "ok": False, "error": last_err}


def _parse(j: dict, mdl: str, secs: float) -> dict:
    u = j.get("usageMetadata", {}) or {}
    LAST.update(model=mdl, input=u.get("promptTokenCount", 0),
                output=u.get("candidatesTokenCount", 0),
                thoughts=u.get("thoughtsTokenCount", 0), seconds=secs)
    STATS["requests"] += 1
    STATS["input"] += LAST["input"]
    STATS["output"] += LAST["output"]
    STATS["thoughts"] += LAST["thoughts"]

    cands = j.get("candidates") or []
    if not cands:
        return {"text": "[no answer - most likely a safety filter]", "tool_calls": [],
                "model": mdl, "finish": "NO_CANDIDATES", "ok": False, "error": None}

    c = cands[0]
    parts = (c.get("content") or {}).get("parts", []) or []
    text = "".join(p.get("text", "") for p in parts if "text" in p)
    calls = [{"name": p["functionCall"].get("name", ""),
              "args": p["functionCall"].get("args", {}) or {}}
             for p in parts if "functionCall" in p]

    meta = c.get("groundingMetadata") or {}
    return {"text": text.strip(), "tool_calls": calls, "raw_parts": parts,
            "model": mdl, "finish": c.get("finishReason", "?"), "ok": True,
            "error": None,
            "sources": [{"title": (ch.get("web") or {}).get("title", "?"),
                         "uri": (ch.get("web") or {}).get("uri", "")}
                        for ch in (meta.get("groundingChunks") or []) if ch.get("web")],
            "queries": meta.get("webSearchQueries") or []}


def supports(model: str | None = None) -> dict:
    """What we have learned about this model so far, from actual API responses."""
    m = model or which("chat")
    return {"model": m, "alive": m not in _DEAD,
            "systemInstruction": m not in _NO_SYSTEM,
            "native_json": m not in _NO_JSON,
            "thinking": _THINKING.get(m, "unknown")}


# ---------------------------------------------------------------------------
# convenience
# ---------------------------------------------------------------------------


def ask(prompt: str, *, task: str = "chat", **kw) -> str:
    """One prompt -> text. Everything else behaves like call()."""
    res = call([{"role": "user", "parts": [{"text": prompt}]}], task=task, **kw)
    if res["finish"] == "MAX_TOKENS":
        return res["text"] + "\n\n[TRUNCATED: finishReason=MAX_TOKENS -> raise max_tokens]"
    return res["text"]


def usage(label: str = "last call") -> None:
    l, s = LAST, STATS
    lim = LIMITS.get(l["model"], _DEFAULT_LIMIT)
    print(f"  {label + ':':20s} {str(l['model'] or '-'):24s} "
          f"in {l['input']:>7,}  out {l['output']:>6,}  thinking {l['thoughts']:>6,}"
          f"  {l['seconds']:.1f}s")
    print(f"  {'total:':20s} {str(s['requests']) + ' calls':24s} "
          f"in {s['input']:>7,}  out {s['output']:>6,}  thinking {s['thoughts']:>6,}"
          + (f"   ({s['failovers']} failovers)" if s["failovers"] else ""))
    if l["model"]:
        tot = max(1, l["input"] + l["output"])
        print(f"  limits {l['model']}: rpm={lim['rpm']} tpm={lim['tpm']:,} "
              f"rpd={lim['rpd']:,}  -> ~{lim['tpm'] // tot} such calls/min")
    if _DEAD:
        print(f"  models dropped: {', '.join(sorted(_DEAD))}")
