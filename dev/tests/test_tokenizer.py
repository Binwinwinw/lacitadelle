import tokenizer


class _FakeEncoding:
    def encode(self, text: str) -> list[int]:
        return [1, 2, 3]


class _FakeTiktoken:
    def encoding_for_model(self, model: str) -> _FakeEncoding:
        if model != "known-model":
            raise KeyError(model)
        return _FakeEncoding()


def test_count_tokens_uses_tiktoken_for_known_model(monkeypatch):
    monkeypatch.setattr(
        tokenizer.importlib,
        "import_module",
        lambda name: _FakeTiktoken(),
    )

    assert tokenizer.count_tokens("some text", "known-model") == 3


def test_count_tokens_uses_character_fallback_when_tiktoken_is_missing(
    monkeypatch,
):
    def missing_module(name: str):
        raise ImportError(name)

    monkeypatch.setattr(tokenizer.importlib, "import_module", missing_module)

    assert tokenizer.count_tokens("abcdefgh", "local-model") == 2
    assert tokenizer.count_tokens("", "local-model") == 0


def test_count_tokens_uses_character_fallback_for_unknown_model(monkeypatch):
    monkeypatch.setattr(
        tokenizer.importlib,
        "import_module",
        lambda name: _FakeTiktoken(),
    )

    assert tokenizer.count_tokens("abcdefgh", "Ornith-1.5-9B.gguf") == 2
