import os
from collections.abc import Generator
import litellm
from reskilled import config as cfg

litellm.suppress_debug_info = True


def _set_env() -> str:
    c = cfg.load()
    if c.get("api_key") and c.get("env_var"):
        os.environ[c["env_var"]] = c["api_key"]
    return c["model"]


def complete(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return chat(messages, max_tokens=max_tokens)


def chat(messages: list[dict], max_tokens: int = 2048) -> str:
    model = _set_env()
    response = litellm.completion(model=model, messages=messages, max_tokens=max_tokens)
    return response.choices[0].message.content


def stream(prompt: str, system: str = "", max_tokens: int = 2048) -> Generator[str, None, None]:
    model = _set_env()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    for chunk in litellm.completion(model=model, messages=messages, max_tokens=max_tokens, stream=True):
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
