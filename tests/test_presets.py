from socrates.models import GenerationMode
from socrates.presets import build_request_from_preset, find_preset, list_presets


def test_list_presets_contains_expected_keys() -> None:
    keys = [preset.key for preset in list_presets()]
    assert "blog_post" in keys
    assert "content_calendar" in keys
    assert "brand_narrative" in keys


def test_find_preset_normalizes_hyphens() -> None:
    preset = find_preset("linkedin-long-post")
    assert preset is not None
    assert preset.key == "linkedin_long_post"
    assert preset.recommended_mode == GenerationMode.GUIDED


def test_build_request_from_preset_uses_defaults() -> None:
    request = build_request_from_preset("value_prop")
    assert request.platform == "web"
    assert request.content_type == "value_prop"
    assert request.include_cta is True
    assert request.constraints


def test_build_request_from_preset_accepts_overrides() -> None:
    request = build_request_from_preset(
        "blog_post",
        topic="Custom topic",
        audience="Custom audience",
        goal="Custom goal",
    )
    assert request.topic == "Custom topic"
    assert request.audience == "Custom audience"
    assert request.goal == "Custom goal"

