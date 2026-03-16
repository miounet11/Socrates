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
from socrates.presets import build_request_from_preset, list_presets
from socrates.site_automation import (
    DEFAULT_LOCALES,
    DEFAULT_STATE_PATH,
    DEFAULT_TOPICS_PER_RUN,
    generate_daily_site_content,
)

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
OUTPUT_PATH_OPTION = typer.Option(
    None,
    "--output",
    resolve_path=True,
    help="Write the YAML template to a file instead of stdout.",
)
PUBLISH_DIR_OPTION = typer.Option(
    Path("site"),
    "--publish-dir",
    resolve_path=True,
    help="Static site directory to update with generated library pages.",
)
STATE_FILE_OPTION = typer.Option(
    DEFAULT_STATE_PATH,
    "--state-file",
    resolve_path=True,
    help="State file used to avoid publishing the same topic twice.",
)
TOPICS_PER_RUN_OPTION = typer.Option(
    DEFAULT_TOPICS_PER_RUN,
    "--topics-per-run",
    min=1,
    max=5,
    help="How many topic seeds to publish in one run.",
)
LOCALES_OPTION = typer.Option(
    ",".join(DEFAULT_LOCALES),
    "--locales",
    help="Comma-separated locales to publish, for example en-US,zh-CN.",
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


def _parse_site_locales(raw_locales: str) -> tuple[str, ...]:
    supported = set(DEFAULT_LOCALES)
    locales = tuple(dict.fromkeys(part.strip() for part in raw_locales.split(",") if part.strip()))
    if not locales:
        raise typer.BadParameter("At least one locale must be provided.")

    invalid = [locale for locale in locales if locale not in supported]
    if invalid:
        valid = ", ".join(DEFAULT_LOCALES)
        raise typer.BadParameter(
            f"Unsupported locale(s): {', '.join(invalid)}. Supported locales: {valid}."
        )
    return locales


def _emit_json(model: BaseModel) -> None:
    typer.echo(model.model_dump_json(indent=2, exclude_none=True))


def _emit_data_json(data: object) -> None:
    typer.echo(json.dumps(data, indent=2))


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


def _render_presets_table() -> str:
    rows = ["Preset | Mode | Platform | Summary", "--- | --- | --- | ---"]
    for preset in list_presets():
        rows.append(
            f"{preset.key} | {preset.recommended_mode.value} | "
            f"{preset.platform} | {preset.summary}"
        )
    return "\n".join(rows)


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
def presets(
    json_output: bool = JSON_OUTPUT_OPTION,
) -> None:
    """List built-in content presets and their recommended modes."""

    preset_list = list_presets()
    if json_output:
        _emit_data_json([preset.model_dump(mode="json") for preset in preset_list])
        return
    typer.echo(_render_presets_table())


@app.command()
def template(
    preset: str = typer.Argument(..., help="Preset key, for example blog_post."),
    topic: str | None = typer.Option(None, "--topic", help="Override the preset topic."),
    audience: str | None = typer.Option(
        None,
        "--audience",
        help="Override the preset audience.",
    ),
    goal: str | None = typer.Option(None, "--goal", help="Override the preset goal."),
    output_path: Path | None = OUTPUT_PATH_OPTION,
) -> None:
    """Generate a starter YAML request from a built-in preset."""

    try:
        request = build_request_from_preset(
            preset,
            topic=topic,
            audience=audience,
            goal=goal,
        )
    except KeyError as exc:
        typer.echo(f"Unknown preset: {preset}", err=True)
        raise typer.Exit(code=1) from exc

    payload = yaml.safe_dump(
        request.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        allow_unicode=False,
    )
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
        typer.echo(f"Wrote {output_path}")
        return
    typer.echo(payload.rstrip())


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


@app.command("site-generate")
def site_generate(
    publish_dir: Path = PUBLISH_DIR_OPTION,
    state_file: Path = STATE_FILE_OPTION,
    topics_per_run: int = TOPICS_PER_RUN_OPTION,
    locales: str = LOCALES_OPTION,
    json_output: bool = JSON_OUTPUT_OPTION,
) -> None:
    """Generate evergreen website library pages and rebuild sitemap/indexes."""

    selected_locales = _parse_site_locales(locales)
    publish_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = _client_from_workspace(Path.cwd())
        summary = generate_daily_site_content(
            client,
            publish_dir=publish_dir,
            state_path=state_file,
            topics_per_run=topics_per_run,
            locales=selected_locales,
        )
    except (ConfigurationError, ProviderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if json_output:
        _emit_json(summary)
        return

    typer.echo(
        "Generated "
        f"{len(summary.generated_seed_keys)} topic(s), "
        f"{len(summary.generated_pages)} page(s), "
        f"skipped {len(summary.skipped_seed_keys)} topic(s)."
    )
    if summary.generated_pages:
        typer.echo("Pages:")
        for page in summary.generated_pages:
            typer.echo(f"- {page}")


def main() -> None:
    """Console script entry point."""

    app()


if __name__ == "__main__":
    main()
