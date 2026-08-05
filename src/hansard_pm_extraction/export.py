"""Convert staged NDJSON into the versioned parquet corpus, with the
data_README.md and schema.json every export ships per CLAUDE.md §4.

Usage:
    python -m hansard_pm_extraction.export
"""

import datetime as dt
import json
import logging
from pathlib import Path

import pandas as pd

from hansard_pm_extraction.config import CORPUS_DIR, RAW_DIR
from hansard_pm_extraction.http import configure_logging
from hansard_pm_extraction.io_utils import read_ndjson

log = logging.getLogger("hansard_pm_extraction.export")

PM_TENURES_PATH = RAW_DIR / "pm_tenures.ndjson"
CONTRIBUTIONS_DIR = RAW_DIR / "contributions"

CONTRIBUTIONS_COLUMNS = {
    "_pm_name": "pm_name",
    "_pm_party": "pm_party",
    "MemberId": "member_id",
    "ItemId": "item_id",
    "ContributionExtId": "contribution_ext_id",
    "ContributionTextFull": "contribution_text",
    "HansardSection": "hansard_section",
    "DebateSection": "debate_section",
    "DebateSectionId": "debate_section_id",
    "DebateSectionExtId": "debate_section_ext_id",
    "SittingDate": "sitting_date",
    "Section": "section",
    "House": "house",
    "OrderInDebateSection": "order_in_debate_section",
    "DebateSectionOrder": "debate_section_order",
    "_ingested_at": "ingested_at",
}

TENURES_COLUMNS = {
    "pm_name": "pm_name",
    "party": "pm_party",
    "member_id": "member_id",
    "tenure_start": "tenure_start",
    "tenure_end": "tenure_end",
}


def build_contributions_df(contributions_dir: Path = CONTRIBUTIONS_DIR) -> pd.DataFrame:
    records = []
    for path in sorted(contributions_dir.glob("*.ndjson")):
        records.extend(read_ndjson(path))
    if not records:
        raise FileNotFoundError(f"No contribution NDJSON files found under {contributions_dir}")

    df = pd.DataFrame(records)[list(CONTRIBUTIONS_COLUMNS)].rename(columns=CONTRIBUTIONS_COLUMNS)
    df["sitting_date"] = pd.to_datetime(df["sitting_date"])
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    df = df.drop_duplicates(subset=["contribution_ext_id"])
    return df.sort_values(["pm_name", "sitting_date", "order_in_debate_section"]).reset_index(
        drop=True
    )


def build_tenures_df(pm_tenures_path: Path = PM_TENURES_PATH) -> pd.DataFrame:
    records = read_ndjson(pm_tenures_path)
    df = pd.DataFrame(records)[list(TENURES_COLUMNS)].rename(columns=TENURES_COLUMNS)
    df["tenure_start"] = pd.to_datetime(df["tenure_start"])
    df["tenure_end"] = pd.to_datetime(df["tenure_end"])
    return df


def _dtype_name(series: pd.Series) -> str:
    return str(series.dtype)


def write_schema_json(tables: dict[str, pd.DataFrame], path) -> None:
    schema = {
        name: {
            "columns": {col: _dtype_name(df[col]) for col in df.columns},
            "row_count": len(df),
        }
        for name, df in tables.items()
    }
    path.write_text(json.dumps(schema, indent=2))


def write_data_readme(
    contributions: pd.DataFrame, tenures: pd.DataFrame, cutoff_date: str, path
) -> None:
    generated_at = dt.datetime.now(dt.UTC).isoformat()
    lines = [
        "# Data README",
        "",
        f"Generated: {generated_at}",
        f"Corpus cutoff date: {cutoff_date}",
        "",
        "## pm_contributions.parquet",
        "",
        f"Row count: {len(contributions)}",
        "",
        "| Column | Type | Description |",
        "|---|---|---|",
        "| pm_name | string | PM speaking, resolved via Members API tenure window |",
        "| pm_party | string | PM's party at time of speech (from Members API `latestParty`) |",
        "| member_id | int64 | Members API member id |",
        "| item_id | int64 | Hansard contribution item id |",
        "| contribution_ext_id | string | Hansard external contribution id (unique, dedup key) |",
        "| contribution_text | string | Full contribution text |",
        "| hansard_section | string | Hansard structural tag |",
        "| debate_section | string | Debate title; 'Engagements' identifies PMQs |",
        "| debate_section_id | int64 | Hansard debate section id |",
        "| debate_section_ext_id | string | Hansard external debate section id |",
        "| sitting_date | datetime64[ns] | Date of the sitting |",
        "| section | string | Chamber section (Commons Chamber) |",
        "| house | string | House (Commons only, by extraction scope) |",
        "| order_in_debate_section | int64 | Contribution order within the debate section |",
        "| debate_section_order | int64 | Debate section order within the sitting |",
        "| ingested_at | datetime64[ns] | Ingestion timestamp (UTC) |",
        "",
        f"Categorical values, `pm_name`: {sorted(contributions['pm_name'].unique().tolist())}",
        f"Categorical values, `house`: {sorted(contributions['house'].unique().tolist())}",
        "",
        "## pm_tenures.parquet",
        "",
        f"Row count: {len(tenures)}",
        "",
        "| Column | Type | Description |",
        "|---|---|---|",
        "| pm_name | string | Commonly known PM name |",
        "| pm_party | string | Party at time of tenure |",
        "| member_id | int64 | Members API member id |",
        "| tenure_start | datetime64[ns] | Date appointed PM |",
        "| tenure_end | datetime64[ns] (nullable) | Date tenure ended; null for the sitting PM |",
        "",
        "See PHASE0_SCOPING.md for how these tenure windows and the cutoff date were decided.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main(cutoff_date: str | None = None) -> None:
    configure_logging(RAW_DIR.parent.parent / "logs")
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    contributions = build_contributions_df()
    tenures = build_tenures_df()
    cutoff_date = cutoff_date or contributions["sitting_date"].max().date().isoformat()

    contributions.to_parquet(CORPUS_DIR / "pm_contributions.parquet", index=False)
    tenures.to_parquet(CORPUS_DIR / "pm_tenures.parquet", index=False)

    write_schema_json(
        {"pm_contributions": contributions, "pm_tenures": tenures}, CORPUS_DIR / "schema.json"
    )
    write_data_readme(contributions, tenures, cutoff_date, CORPUS_DIR / "data_README.md")

    log.info(
        "Exported %d contributions, %d PM tenures -> %s (cutoff %s)",
        len(contributions),
        len(tenures),
        CORPUS_DIR,
        cutoff_date,
    )


if __name__ == "__main__":
    main()
