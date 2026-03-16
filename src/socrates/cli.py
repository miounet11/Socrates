"""CLI entry point for Socrates."""

from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml
from pydantic import BaseModel, ValidationError

from socrates import Socrates
from socrates.config import find_config_path, load_config, write_default_config
from socrates.exceptions import ConfigurationError, ProviderError
from socrates.models import ContentDraft, ContentRequest, GenerationMode, ReviewReport

app = typer.Typer(
    help="Rubric-guided content generation for publishable drafts.",
    no_args_is_help=True,
)

FORCE_OPTION = typer.Option(False, "--force", help="Overwrite an existing config file.")
INPUT_PATH_ARGUMENT = typer.Argument(..., exists=True, readable=True, resolve_path=True)
JSON_OUTPUT_OPTION = typer.Option(False, "--json", help="Print JSON instead of a summary.")
MODE_OPTION = typer.Option(GenerationMode.AUTO, "--mode", case_sensitive=False)
FORMAT_OPTION = typer.Option("markdown", "--format", help="Output format: markdown or json.")
REQUEST_OPTION = typer.Option(
    ...,
    "--request",
    exists=True,
    readable=True,
    resolve_path=True,
    help="YAML request file used for the original generation.",
)


def _load_request(path: Path) -> ContentRequest:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise typer.BadParameter(f"Could not read request file: {exc}") from exc
    if not isinstance(raw, dict):
        raise typer.BadParameter("Request file must contain a YAML object.")
    try:
        return ContentRequest.model_validate(raw)
    except ValidationError as exc:
        raise typer.BadParameter(f"Invalid request file: {exc}") from exc


def _load_draft_markdown(path: Path) -> ContentDraft:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise typer.BadParameter(f"Could not read draft file: {exc}") from exc
    if not text:
        raise typer.BadParameter("Draft file is empty.")

    lines = [line for line in text.splitlines()]
    title = path.stem.replace("-", " ").replace("_", " ").title()
    body = text
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip() or title
        body = "\n".join(lines[1:]).strip()
    return ContentDraft(title=title, body=body)


def _client_from_workspace(start_path: Path | None = None) -> Socrates:
    return Socrates.from_config(start_path=start_path)


def _emit_json(model: BaseModel) -> None:
    typer.echo(model.model_dump_json(indent=2, exclude_none=True))


def _render_markdown_draft(draft: ContentDraft) -> str:
    pieces = [f"# {draft.title}", "", draft.body.strip()]
    if draft.summary:
        pieces.insert(2, f"*{draft.summary.strip()}*")
        pieces.insert(3, "")
    if draft.cta:
        pieces.extend(["", "> CTA", ">", f"> {draft.cta.strip()}"])
    return "\n".join(piece for piece in pieces if piece is not None)


def _render_review(report: ReviewReport) -> str:
    lines = [
        f"Publishability score: {report.publishability_score}",
        f"Passes: {'yes' if report.passes else 'no'}",
        "",
        report.summary,
    ]
    if report.findings:
        lines.extend(["", "Findings:"])
        for finding in report.findings:
            lines.append(
                f"- [{finding.severity}] {finding.category}: "
                f"{finding.evidence} -> {finding.recommendation}"
            )
    return "\n".join(lines)


@app.command()
def init(force: bool = FORCE_OPTION) -> None:
    """Create a starter `.socrates/config.toml`."""

    try:
        path = write_default_config(force=force)
    except ConfigurationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Wrote {path}")


@app.command()
def frame(
    input_path: Path = INPUT_PATH_ARGUMENT,
    json_output: bool = JSON_OUTPUT_OPTION,
) -> None:
    """Generate only the stage-1 content frame."""

    request = _load_request(input_path)
    try:
        client = _client_from_workspace(input_path.parent)
        frame_result = client.frame(request)
    except (ConfigurationError, ProviderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        _emit_json(frame_result)
        return

    typer.echo(json.dumps(frame_result.model_dump(mode="json"), indent=2))


@app.command()
def generate(
    input_path: Path = INPUT_PATH_ARGUMENT,
    mode: GenerationMode = MODE_OPTION,
    output_format: str = FORMAT_OPTION,
) -> None:
    """Generate content with auto-routing or an explicit mode."""

    request = _load_request(input_path)
    try:
        client = _client_from_workspace(input_path.parent)
        result = client.generate(request, mode=mode)
    except (ConfigurationError, ProviderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if output_format == "json":
        _emit_json(result)
        return
    if output_format != "markdown":
        raise typer.BadParameter("format must be either 'markdown' or 'json'")
    typer.echo(_render_markdown_draft(result.draft))


@app.command()
def review(
    draft_path: Path = INPUT_PATH_ARGUMENT,
    request_path: Path = REQUEST_OPTION,
    json_output: bool = JSON_OUTPUT_OPTION,
) -> None:
    """Run the review stage against an existing markdown draft."""

    request = _load_request(request_path)
    draft = _load_draft_markdown(draft_path)
    try:
        client = _client_from_workspace(request_path.parent)
        report = client.review(request, draft)
    except (ConfigurationError, ProviderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        _emit_json(report)
        return
    typer.echo(_render_review(report))


@app.command()
def doctor() -> None:
    """Inspect local config and provider readiness."""

    config = load_config()
    config_path = find_config_path()
    api_key_present = bool(config.provider.api_key)

    typer.echo(f"Config file: {config_path or 'not found'}")
    typer.echo(f"Provider: {config.provider.kind}")
    typer.echo(f"Base URL: {config.provider.base_url}")
    typer.echo(f"Default model: {config.models.default_model}")
    typer.echo(f"API key: {'present' if api_key_present else 'missing'}")

    if not api_key_present:
        raise typer.Exit(code=1)


def main() -> None:
    """Console script entry point."""

    app()


if __name__ == "__main__":
    main()
