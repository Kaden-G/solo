"""LLM provider abstraction — Claude and OpenAI, switchable via config."""

from abc import ABC, abstractmethod

import yaml


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """Send a prompt to the LLM and return the text response."""


class ClaudeProvider(LLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model

    def generate(self, prompt: str, system: str | None = None) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o"):
        import openai

        self.client = openai.OpenAI()
        self.model = model

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content


def get_provider(config_path: str = "config.yml") -> LLMProvider:
    """Factory: return the LLM provider specified in config."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    llm = config["llm"]
    provider_name = llm["provider"]

    if provider_name == "claude":
        return ClaudeProvider(model=llm["claude"]["model"])
    elif provider_name == "openai":
        return OpenAIProvider(model=llm["openai"]["model"])
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
