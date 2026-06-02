from __future__ import annotations

import json
import mmap
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_RANGE = (date(2023, 1, 1), date(2025, 12, 31))
NEW_COLLECTION_RANGES = {
    "destructive_earthquake": (date(2026, 2, 16), date(2026, 2, 22)),
    "super_typhoon": (date(2026, 3, 8), date(2026, 3, 17)),
    "extreme_rainstorm": (date(2026, 4, 20), date(2026, 4, 26)),
}

DATE_RE = re.compile(rb"20\d\d-\d\d-\d\d")
DEPLOYMENT_PREFIX = b'"deployment_id": "'
COLLECTION_DATE_PREFIX = b'"collection_date": "'
MEASUREMENT_PERIOD_PREFIX = b'"measurement_period": "'
OLD_HISTORICAL_RANGE = b"2023-01-01/2023-12-31"
NEW_HISTORICAL_RANGE = b"2023-01-01/2025-12-31"


def extract_string(line: bytes, prefix: bytes) -> bytes:
    start = line.find(prefix)
    if start == -1:
        raise ValueError(f"Missing field prefix: {prefix!r}")
    start += len(prefix)
    end = line.find(b'"', start)
    if end == -1:
        raise ValueError(f"Missing closing quote for field prefix: {prefix!r}")
    return line[start:end]


def parse_date(value: bytes) -> date:
    return date.fromisoformat(value.decode("ascii"))


def distribute_date(index: int, count: int, target_range: tuple[date, date]) -> date:
    start, end = target_range
    if count == 1:
        return start
    span_days = (end - start).days
    return start + timedelta(days=(index * span_days) // (count - 1))


def target_range_for(scenario: str, measurement_period: str) -> tuple[date, date]:
    if measurement_period == "historical":
        return HISTORICAL_RANGE
    if measurement_period == "new_collection":
        return NEW_COLLECTION_RANGES[scenario]
    raise ValueError(f"Unsupported measurement period: {measurement_period}")


def inclusive_dates(target_range: tuple[date, date]) -> list[str]:
    start, end = target_range
    return [
        (start + timedelta(days=offset)).isoformat()
        for offset in range((end - start).days + 1)
    ]


def cell_info_paths() -> list[Path]:
    return sorted(ROOT.glob("*/*/*/*/cell_info.jsonl"))


def business_user_paths() -> list[Path]:
    return sorted(ROOT.glob("*/*/*/*/business_users.jsonl"))


def profile_paths() -> list[Path]:
    return sorted(ROOT.glob("*/*/*/*/resource_profile.json"))


def scenario_for(path: Path) -> str:
    return path.relative_to(ROOT).parts[0]


def build_deployment_date_map() -> dict[bytes, tuple[date, date]]:
    records: dict[tuple[str, str], list[tuple[bytes, date]]] = defaultdict(list)
    for path in cell_info_paths():
        scenario = scenario_for(path)
        with path.open("rb") as source:
            for line in source:
                deployment_id = extract_string(line, DEPLOYMENT_PREFIX)
                measurement_period = extract_string(line, MEASUREMENT_PERIOD_PREFIX).decode(
                    "ascii"
                )
                collection_date = parse_date(extract_string(line, COLLECTION_DATE_PREFIX))
                records[(scenario, measurement_period)].append(
                    (deployment_id, collection_date)
                )

    deployment_dates: dict[bytes, tuple[date, date]] = {}
    for (scenario, measurement_period), deployments in sorted(records.items()):
        target_range = target_range_for(scenario, measurement_period)

        for index, (deployment_id, old_date) in enumerate(deployments):
            new_date = distribute_date(index, len(deployments), target_range)
            if deployment_id in deployment_dates:
                raise ValueError(f"Duplicate deployment ID: {deployment_id!r}")
            deployment_dates[deployment_id] = (old_date, new_date)

        print(
            f"{scenario:24} {measurement_period:14} "
            f"records={len(deployments):4} "
            f"range={target_range[0].isoformat()}/{target_range[1].isoformat()}"
        )
    return deployment_dates


def replace_line_dates(
    line: bytes, deployment_dates: dict[bytes, tuple[date, date]], cache: dict
) -> tuple[bytes, int]:
    deployment_id = extract_string(line, DEPLOYMENT_PREFIX)
    try:
        old_collection_date, new_collection_date = deployment_dates[deployment_id]
    except KeyError as exc:
        raise ValueError(f"Unknown deployment ID: {deployment_id!r}") from exc
    delta = new_collection_date - old_collection_date

    def replace(match: re.Match[bytes]) -> bytes:
        key = (delta.days, match.group())
        replacement = cache.get(key)
        if replacement is None:
            replacement = (parse_date(match.group()) + delta).isoformat().encode("ascii")
            cache[key] = replacement
        return replacement

    return DATE_RE.subn(replace, line)


def update_jsonl_in_place(
    paths: list[Path], deployment_dates: dict[bytes, tuple[date, date]]
) -> tuple[int, int]:
    line_count = 0
    replacement_count = 0
    cache: dict[tuple[int, bytes], bytes] = {}
    for path in paths:
        with path.open("r+b") as target:
            with mmap.mmap(target.fileno(), 0, access=mmap.ACCESS_WRITE) as mapped:
                offset = 0
                while offset < len(mapped):
                    next_offset = mapped.find(b"\n", offset)
                    if next_offset == -1:
                        next_offset = len(mapped)
                    else:
                        next_offset += 1
                    line = mapped[offset:next_offset]
                    updated, count = replace_line_dates(line, deployment_dates, cache)
                    if len(updated) != len(line):
                        raise ValueError(f"Date replacement changed line length: {path}")
                    mapped[offset:next_offset] = updated
                    line_count += 1
                    replacement_count += count
                    offset = next_offset
                mapped.flush()
        path.touch()
    return line_count, replacement_count


def count_business_periods(paths: list[Path]) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for path in paths:
        scenario = scenario_for(path)
        with path.open("rb") as source:
            for line in source:
                measurement_period = extract_string(
                    line, MEASUREMENT_PERIOD_PREFIX
                ).decode("ascii")
                counts[(scenario, measurement_period)] += 1
    return counts


def update_business_users_in_place(paths: list[Path]) -> tuple[int, int]:
    period_counts = count_business_periods(paths)
    period_indexes: Counter[tuple[str, str]] = Counter()
    line_count = 0
    replacement_count = 0
    cache: dict[tuple[int, bytes], bytes] = {}
    for path in paths:
        scenario = scenario_for(path)
        with path.open("r+b") as target:
            with mmap.mmap(target.fileno(), 0, access=mmap.ACCESS_WRITE) as mapped:
                offset = 0
                while offset < len(mapped):
                    next_offset = mapped.find(b"\n", offset)
                    if next_offset == -1:
                        next_offset = len(mapped)
                    else:
                        next_offset += 1
                    line = mapped[offset:next_offset]
                    measurement_period = extract_string(
                        line, MEASUREMENT_PERIOD_PREFIX
                    ).decode("ascii")
                    key = (scenario, measurement_period)
                    target_date = distribute_date(
                        period_indexes[key],
                        period_counts[key],
                        target_range_for(scenario, measurement_period),
                    )
                    old_date = parse_date(extract_string(line, COLLECTION_DATE_PREFIX))
                    delta = target_date - old_date

                    def replace(match: re.Match[bytes]) -> bytes:
                        cache_key = (delta.days, match.group())
                        replacement = cache.get(cache_key)
                        if replacement is None:
                            replacement = (
                                parse_date(match.group()) + delta
                            ).isoformat().encode("ascii")
                            cache[cache_key] = replacement
                        return replacement

                    updated, count = DATE_RE.subn(replace, line)
                    if len(updated) != len(line):
                        raise ValueError(f"Date replacement changed line length: {path}")
                    mapped[offset:next_offset] = updated
                    period_indexes[key] += 1
                    line_count += 1
                    replacement_count += count
                    offset = next_offset
                mapped.flush()
        path.touch()
    return line_count, replacement_count


def update_resource_profiles() -> int:
    updated_count = 0
    array_re = re.compile(
        rb'("collection_dates": \[\r?\n)(.*?)(\r?\n      \])', re.DOTALL
    )
    for path in profile_paths():
        scenario = scenario_for(path)
        raw = path.read_bytes()
        raw, historical_count = re.subn(
            OLD_HISTORICAL_RANGE, NEW_HISTORICAL_RANGE, raw
        )
        if historical_count not in (0, 1):
            raise ValueError(f"Unexpected historical range count in {path}")
        line_break = b"\r\n" if b"\r\n" in raw else b"\n"
        entries = inclusive_dates(NEW_COLLECTION_RANGES[scenario])
        rendered_entries = line_break.join(
            b'        "' + item.encode("ascii") + b'"' + (b"," if index < len(entries) - 1 else b"")
            for index, item in enumerate(entries)
        )
        raw, collection_count = array_re.subn(
            lambda match: match.group(1) + rendered_entries + match.group(3), raw
        )
        if collection_count != 1:
            raise ValueError(f"Expected one collection_dates array in {path}")
        path.write_bytes(raw)
        updated_count += 1
    return updated_count


def update_metadata() -> None:
    path = ROOT / "metadata.json"
    raw = path.read_bytes()
    line_break = "\r\n" if b"\r\n" in raw else "\n"
    trailing_line_break = raw.endswith((b"\r\n", b"\n"))
    metadata = json.loads(raw.decode("utf-8"))
    historical_range = "/".join(item.isoformat() for item in HISTORICAL_RANGE)

    for scenario, scenario_metadata in metadata["disaster_scenarios"].items():
        scenario_metadata["historical_date_range"] = historical_range
        scenario_metadata["new_collection_dates"] = inclusive_dates(
            NEW_COLLECTION_RANGES[scenario]
        )

    metadata["measurement_periods"]["historical"]["date_range"] = historical_range
    metadata["measurement_periods"]["new_collection"]["scenario_dates"] = {
        scenario: inclusive_dates(NEW_COLLECTION_RANGES[scenario])
        for scenario in metadata["measurement_periods"]["new_collection"][
            "scenario_dates"
        ]
    }

    rendered = json.dumps(metadata, ensure_ascii=False, indent=2)
    if trailing_line_break:
        rendered += "\n"
    path.write_bytes(rendered.replace("\n", line_break).encode("utf-8"))


def main() -> None:
    deployment_dates = build_deployment_date_map()
    cell_lines, cell_replacements = update_jsonl_in_place(
        cell_info_paths(), deployment_dates
    )
    business_lines, business_replacements = update_business_users_in_place(
        business_user_paths()
    )
    profile_count = update_resource_profiles()
    update_metadata()
    print(
        "updated "
        f"deployments={len(deployment_dates)}, "
        f"cell_lines={cell_lines}, "
        f"business_lines={business_lines}, "
        f"date_replacements={cell_replacements + business_replacements}, "
        f"profiles={profile_count}, metadata=1"
    )


if __name__ == "__main__":
    main()
