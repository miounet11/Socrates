from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from socrates.cli import app
from socrates.client import Socrates
from socrates.config import SocratesConfig
from tests.conftest import StubProvider

runner = CliRunner()


def test_init_writes_default_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert (tmp_path / ".socrates" / "config.toml").exists()


def test_generate_outputs_json(tmp_path: Path, monkeypatch, content_request) -> None:
    request_path = tmp_path / "request.yaml"
    request_path.write_text(content_request.model_dump_json(), encoding="utf-8")

    provider = StubProvider(
        [
            {
                "audience_pains": ["They lead with features, not pains."],
                "desired_takeaway": "Position around business friction.",
                "persuasion_triggers": ["Credible examples"],
                "credibility_requirements": ["Concrete examples"],
                "tone_rules": ["Be specific"],
                "anti_patterns": ["Do not say game-changing"],
                "core_angle": "Positioning should start with operational pain.",
            },
            {
                "title": "AI messaging fails when it skips the buyer problem",
                "body": "A draft body",
                "summary": None,
                "cta": None,
                "metadata": {},
            },
        ]
    )

    monkeypatch.setattr(
        "socrates.cli._client_from_workspace",
        lambda _path: Socrates(provider, config=SocratesConfig()),
    )

    result = runner.invoke(
        app,
        ["generate", str(request_path), "--mode", "guided", "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "guided"
    assert payload["draft"]["title"].startswith("AI messaging fails")


def test_presets_outputs_json() -> None:
    result = runner.invoke(app, ["presets", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert any(preset["key"] == "blog_post" for preset in payload)


def test_template_writes_yaml_file(tmp_path: Path) -> None:
    output_path = tmp_path / "request.yaml"

    result = runner.invoke(
        app,
        [
            "template",
            "blog_post",
            "--topic",
            "Custom topic",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    body = output_path.read_text(encoding="utf-8")
    assert "Custom topic" in body
    assert "content_type: blog_post" in body


def test_review_outputs_summary(tmp_path: Path, monkeypatch, content_request) -> None:
    request_path = tmp_path / "request.yaml"
    request_path.write_text(content_request.model_dump_json(), encoding="utf-8")
    draft_path = tmp_path / "draft.md"
    draft_path.write_text("# Draft\n\nThis is a game-changing message.", encoding="utf-8")

    provider = StubProvider(
        [
            {
                "publishability_score": 78,
                "summary": "Needs minor tightening.",
                "findings": [],
                "unsupported_claims": [],
                "repetition_flags": [],
                "ai_tone_flags": [],
                "passes": True,
            }
        ]
    )

    monkeypatch.setattr(
        "socrates.cli._client_from_workspace",
        lambda _path: Socrates(provider, config=SocratesConfig()),
    )

    result = runner.invoke(app, ["review", str(draft_path), "--request", str(request_path)])

    assert result.exit_code == 0
    assert "Publishability score:" in result.stdout
    assert "game-changing" in result.stdout
