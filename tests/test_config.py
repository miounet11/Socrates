from pathlib import Path

from socrates.config import load_config


def test_load_config_reads_file_and_env_override(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / ".socrates"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        """
[provider]
kind = "openai-compatible"
api_key = "from-file"
base_url = "https://example.com/v1"

[models]
default_model = "model-from-file"
frame_model = ""
outline_model = ""
draft_model = ""
review_model = ""
temperature = 0.4

[generation]
fallback_to_prompt_json = true
timeout_seconds = 45.0
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("SOCRATES_MODEL", "model-from-env")

    config = load_config(tmp_path)

    assert config.provider.api_key == "from-file"
    assert config.provider.base_url == "https://example.com/v1"
    assert config.models.default_model == "model-from-env"
    assert config.models.temperature == 0.4

