#!/usr/bin/env python3
import dataclasses
import logging
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional

import dateutil.parser
import ovh
import ovh.exceptions

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


PROJECT_ENV_VARS = {
    "endpoint": "OVH_ENDPOINT",
    "application_key": "OVH_APP_KEY",
    "application_secret": "OVH_APP_SECRET",
    "consumer_key": "OVH_CONSUMER_KEY",
}

METRIC_NAME = "ovhcloud_publiccloud_usage"

USAGE_SCHEMA: Mapping[str, Any] = {
    "hourlyUsage": {
        "instance": {
            "tags": ["reference", "region"],
            "field": ["totalPrice"],
        },
        "instanceBandwidth": {
            "tags": ["region"],
            "field": ["totalPrice"],
        },
        "instanceOption": {
            "tags": ["reference", "region"],
            "field": ["totalPrice"],
        },
        "snapshot": {
            "tags": ["region"],
            "field": ["totalPrice"],
        },
        "storage": {
            "tags": ["bucketName", "region"],
            "field": ["totalPrice"],
        },
        "volume": {
            "tags": ["type", "region"],
            "field": ["totalPrice"],
        },
    },
    "monthlyUsage": {
        "instance": {
            "tags": ["reference", "region"],
            "field": ["totalPrice"],
        },
        "instanceOption": {
            "tags": ["reference", "region"],
            "field": ["totalPrice"],
        },
        "certification": {
            "tags": ["reference"],
            "field": ["totalPrice"],
        },
    },
    "resourcesUsage": [
        {
            "tags": ["type"],
            "field": ["totalPrice"],
        }
    ],
}


@dataclasses.dataclass(frozen=True)
class OVHConfig:
    endpoint: str
    application_key: str
    application_secret: str
    consumer_key: str


def load_env_config() -> OVHConfig:
    """Load required OVH environment variables."""
    missing = [
        var
        for attr, var in PROJECT_ENV_VARS.items()
        if not (value := os.environ.get(var))
    ]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return OVHConfig(
        endpoint=os.environ[PROJECT_ENV_VARS["endpoint"]],
        application_key=os.environ[PROJECT_ENV_VARS["application_key"]],
        application_secret=os.environ[PROJECT_ENV_VARS["application_secret"]],
        consumer_key=os.environ[PROJECT_ENV_VARS["consumer_key"]],
    )


def get_client(config: OVHConfig) -> ovh.Client:
    """Create an authenticated OVH client."""
    return ovh.Client(
        endpoint=config.endpoint,
        application_key=config.application_key,
        application_secret=config.application_secret,
        consumer_key=config.consumer_key,
    )


def safe_call(func, *args, **kwargs):
    """Wrap OVH API calls and log failures."""
    try:
        return func(*args, **kwargs)
    except ovh.exceptions.APIError as exc:
        logging.error("OVH API error calling %s: %s", func.__name__, exc)
    except Exception as exc:  # pragma: no cover
        logging.error("Unexpected error calling %s: %s", func.__name__, exc)
    return None


def sanitize_project_name(name: Optional[str]) -> str:
    """Normalize project description to avoid spaces in tags."""
    if not name:
        return "unknown"
    return name.replace(" ", "_")


def parse_timestamp(iso_value: str) -> int:
    """Convert ISO timestamp to nanoseconds since epoch."""
    parsed = dateutil.parser.parse(iso_value)
    return int(parsed.timestamp() * 1_000_000_000)


def format_point(
    tags: Mapping[str, Any],
    field_key: str,
    field_value: Any,
    timestamp_ns: int,
) -> str:
    """Construct a line protocol point from tags and a single field."""
    tag_set = ",".join(f"{k}={v}" for k, v in tags.items() if v is not None)
    return f"{METRIC_NAME},{tag_set} {field_key}={field_value:.0f} {timestamp_ns}"


def format_dict_usage(
    usage_data: Mapping[str, Any],
    category: str,
    schema: Mapping[str, Any],
    base_tags: Dict[str, Any],
    timestamp_ns: int,
) -> List[str]:
    """Format usage metrics for hourly/monthly schema sections."""
    points: List[str] = []
    for subcategory, specs in schema.items():
        entries = usage_data.get(subcategory)
        if not entries:
            continue
        for entry in entries:
            tags = dict(base_tags)
            tags.update({"category": category, "subcategory": subcategory})
            for tag in specs.get("tags", []):
                value = entry.get(tag)
                if value:
                    tags[tag] = value
            for field in specs.get("field", []):
                field_value = entry.get(field)
                if field_value is not None:
                    points.append(format_point(tags, field, field_value, timestamp_ns))
    return points


def format_list_usage(
    usage_entries: Iterable[Mapping[str, Any]],
    category: str,
    specs: Mapping[str, Any],
    base_tags: Dict[str, Any],
    timestamp_ns: int,
) -> List[str]:
    """Format usage metrics for list-style sections."""
    points: List[str] = []
    for entry in usage_entries:
        tags = dict(base_tags)
        tags["category"] = category
        for tag in specs.get("tags", []):
            value = entry.get(tag)
            if value:
                tags[tag] = value
        for field in specs.get("field", []):
            field_value = entry.get(field)
            if field_value is not None:
                points.append(format_point(tags, field, field_value, timestamp_ns))
    return points


def format_usage(
    project_id: str, project_name: str, current_usage: Mapping[str, Any]
) -> List[str]:
    """Convert raw OVH usage data into InfluxDB line protocol points."""
    measurement_tags = {"project_id": project_id, "project_name": project_name}
    last_update = current_usage.get("lastUpdate")
    if not last_update:
        logging.warning("Project %s has no lastUpdate timestamp", project_id)
        return []
    timestamp_ns = parse_timestamp(last_update)
    formatted_points: List[str] = []
    for category, schema in USAGE_SCHEMA.items():
        category_data = current_usage.get(category)
        if not category_data:
            continue
        if isinstance(schema, dict):
            formatted_points.extend(
                format_dict_usage(category_data, category, schema, measurement_tags, timestamp_ns)
            )
        elif isinstance(schema, list) and schema:
            formatted_points.extend(
                format_list_usage(
                    category_data,
                    category,
                    schema[0],
                    measurement_tags,
                    timestamp_ns,
                )
            )
    return formatted_points


def main() -> None:
    try:
        config = load_env_config()
    except RuntimeError as exc:
        logging.error(exc)
        return

    client = get_client(config)
    projects = safe_call(client.get, "/cloud/project") or []

    for project_id in projects:
        project_response = safe_call(client.get, f"/cloud/project/{project_id}")
        if not project_response or project_response.get("status") != "ok":
            logging.warning("Skipping project %s because it was not OK", project_id)
            continue
        description = sanitize_project_name(project_response.get("description"))
        usage = safe_call(client.get, f"/cloud/project/{project_id}/usage/current")
        if not usage:
            continue
        for line in format_usage(project_id, description, usage):
            print(line)


if __name__ == "__main__":
    main()
