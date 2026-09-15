"""
lares_llm - minimal helper for calling Gemma/Gemini through the Gemini API.

    from lares_llm import set_key, ask, usage
    set_key(API_KEY)
    print(ask("Explain overfitting in one sentence."))
    usage()
"""
import time

import requests

# --- configuration: edit when quotas change or new models arrive -----------

# if the first model fails, the next one is tried.
# each student has their own key, so daily limits are not the problem -
# what decides the order is which model is actually answering today.
CHAINS = {
    "chat":  ["gemma-4-31b-it", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
    "agent": ["gemma-4-31b-it", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
    # big prompts need TPM; gemma has only 16K, so it is no use here
    "rag":   ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
}

# copy from ai.dev/usage?tab=rate-limit if these change
LIMITS = {
    "gemma-4-31b-it":        {"rpm": 30, "tpm":  16_000, "rpd": 14_400},
    "gemini-3.1-flash-lite": {"rpm": 15, "tpm": 250_000, "rpd":     500},
    "gemini-3.5-flash-lite": {"rpm": 15, "tpm": 250_000, "rpd":     500},
}

BASE = "https://generativelanguage.googleapis.com/v1beta/models"
API_KEY = None
STATS = {"requests": 0, "input": 0, "output": 0, "thoughts": 0}
LAST = {"model": None, "input": 0, "output": 0, "thoughts": 0, "seconds": 0.0}


def set_key(key):
    global API_KEY
    API_KEY = key


def which(task="chat"):
    """Which model this exercise starts with."""
    return CHAINS.get(task, CHAINS["chat"])[0]


def call(contents, *, tools=None, system=None, json_schema=None, search=False,
         thinking=False, task="chat", model=None, temperature=0.0,
         max_tokens=1000, tries=5, verbose=True):
    """Send a request. Retry on server errors, then try the next model."""
    config = {"temperature": temperature, "maxOutputTokens": max_tokens,
              "thinkingConfig": {"thinkingLevel": "high" if thinking else "minimal"}}
    if json_schema:
        config["responseMimeType"] = "application/json"
        config["responseSchema"] = json_schema

    body = {"contents": contents, "generationConfig": config}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if tools:
        body["tools"] = [{"functionDeclarations": tools}]
    elif search:
        body["tools"] = [{"google_search": {}}]

    for mdl in ([model] if model else CHAINS.get(task, CHAINS["chat"])):
        for attempt in range(tries):
            start = time.time()
            r = requests.post(f"{BASE}/{mdl}:generateContent",
                              params={"key": API_KEY}, json=body, timeout=120)
            if r.status_code == 200:
                return _parse(r.json(), mdl, time.time() - start)

            if verbose:
                print(f"  {mdl}: HTTP {r.status_code} {r.text[:100]}")
            if r.status_code not in (429, 500, 502, 503, 504):
                break            # our request is wrong; retrying will not help
            time.sleep(5)        # server is busy or we are too fast

    return {"text": "[all models failed]", "thinking": "", "tool_calls": [],
            "sources": [], "model": None, "finish": "ERROR"}


def _parse(response, mdl, seconds):
    used = response.get("usageMetadata", {})
    LAST.update(model=mdl, input=used.get("promptTokenCount", 0),
                output=used.get("candidatesTokenCount", 0),
                thoughts=used.get("thoughtsTokenCount", 0), seconds=seconds)
    STATS["requests"] += 1
    for key in ("input", "output", "thoughts"):
        STATS[key] += LAST[key]

    candidate = response["candidates"][0]
    text, thinking, tool_calls = [], [], []
    for part in candidate["content"]["parts"]:
        if "functionCall" in part:
            tool_calls.append(part["functionCall"])
        elif part.get("thought"):        # reasoning, not the answer
            thinking.append(part["text"])
        else:
            text.append(part["text"])

    grounding = candidate.get("groundingMetadata", {})
    return {"text": "".join(text).strip(), "thinking": "".join(thinking).strip(),
            "tool_calls": tool_calls, "model": mdl,
            "finish": candidate.get("finishReason"),
            "sources": [c["web"] for c in grounding.get("groundingChunks", [])
                        if "web" in c]}


def ask(prompt, **kw):
    """One prompt -> text."""
    return call([{"role": "user", "parts": [{"text": prompt}]}], **kw)["text"]


def usage(label="last call"):
    """Print what the last call cost, and the running total."""
    limit = LIMITS.get(LAST["model"], {"rpm": 10, "tpm": 250_000, "rpd": 250})
    tokens = max(1, LAST["input"] + LAST["output"] + LAST["thoughts"])
    print(f"  {label}: {LAST['model']}  in {LAST['input']}  out {LAST['output']}"
          f"  thinking {LAST['thoughts']}  {LAST['seconds']:.1f}s")
    print(f"  total: {STATS['requests']} calls  in {STATS['input']}"
          f"  out {STATS['output']}  thinking {STATS['thoughts']}")
    print(f"  limits: rpm={limit['rpm']} tpm={limit['tpm']:,} rpd={limit['rpd']:,}"
          f"  -> at {tokens} tokens/call you can do {min(limit['rpm'], limit['tpm'] // tokens)} calls/min")