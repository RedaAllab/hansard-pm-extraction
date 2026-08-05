import json

from hansard_pm_extraction.export import (
    build_contributions_df,
    build_tenures_df,
    write_data_readme,
    write_schema_json,
)


def _write_ndjson(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


CONTRIBUTION_RECORD = {
    "_pm_name": "Rishi Sunak",
    "_pm_party": "Conservative",
    "MemberId": 4483,
    "ItemId": 1,
    "ContributionExtId": "abc",
    "ContributionTextFull": "Hello.",
    "HansardSection": "hs_Para",
    "DebateSection": "Engagements",
    "DebateSectionId": 1,
    "DebateSectionExtId": "abc-debate",
    "SittingDate": "2023-01-25T00:00:00",
    "Section": "Commons Chamber",
    "House": "Commons",
    "OrderInDebateSection": 1,
    "DebateSectionOrder": 1,
    "_ingested_at": "2026-08-05T00:00:00+00:00",
}

TENURE_RECORD = {
    "pm_name": "Rishi Sunak",
    "member_id": 4483,
    "party": "Conservative",
    "tenure_start": "2022-10-25T00:00:00",
    "tenure_end": "2024-07-05T00:00:00",
}


def test_build_contributions_df_dedups_by_contribution_ext_id(tmp_path):
    contrib_dir = tmp_path / "contributions"
    _write_ndjson(contrib_dir / "Rishi_Sunak.ndjson", [CONTRIBUTION_RECORD, CONTRIBUTION_RECORD])
    df = build_contributions_df(contrib_dir)
    assert len(df) == 1


def test_build_contributions_df_renames_columns(tmp_path):
    contrib_dir = tmp_path / "contributions"
    _write_ndjson(contrib_dir / "Rishi_Sunak.ndjson", [CONTRIBUTION_RECORD])
    df = build_contributions_df(contrib_dir)
    assert set(df.columns) == {
        "pm_name",
        "pm_party",
        "member_id",
        "item_id",
        "contribution_ext_id",
        "contribution_text",
        "hansard_section",
        "debate_section",
        "debate_section_id",
        "debate_section_ext_id",
        "sitting_date",
        "section",
        "house",
        "order_in_debate_section",
        "debate_section_order",
        "ingested_at",
    }


def test_build_contributions_df_raises_on_empty_dir(tmp_path):
    contrib_dir = tmp_path / "contributions"
    contrib_dir.mkdir()
    try:
        build_contributions_df(contrib_dir)
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError:
        pass


def test_build_tenures_df_parses_null_tenure_end(tmp_path):
    path = tmp_path / "pm_tenures.ndjson"
    record = {**TENURE_RECORD, "tenure_end": None}
    _write_ndjson(path, [record])
    df = build_tenures_df(path)
    assert df["tenure_end"].isna().all()


def test_write_schema_json_records_row_count_and_dtypes(tmp_path):
    contrib_dir = tmp_path / "contributions"
    _write_ndjson(contrib_dir / "Rishi_Sunak.ndjson", [CONTRIBUTION_RECORD])
    df = build_contributions_df(contrib_dir)
    out_path = tmp_path / "schema.json"
    write_schema_json({"pm_contributions": df}, out_path)
    schema = json.loads(out_path.read_text())
    assert schema["pm_contributions"]["row_count"] == 1
    assert "pm_name" in schema["pm_contributions"]["columns"]


def test_write_data_readme_lists_pm_names(tmp_path):
    contrib_dir = tmp_path / "contributions"
    _write_ndjson(contrib_dir / "Rishi_Sunak.ndjson", [CONTRIBUTION_RECORD])
    contributions = build_contributions_df(contrib_dir)

    tenures_path = tmp_path / "pm_tenures.ndjson"
    _write_ndjson(tenures_path, [TENURE_RECORD])
    tenures = build_tenures_df(tenures_path)

    out_path = tmp_path / "data_README.md"
    write_data_readme(contributions, tenures, "2023-01-25", out_path)
    text = out_path.read_text()
    assert "Rishi Sunak" in text
    assert "Corpus cutoff date: 2023-01-25" in text
