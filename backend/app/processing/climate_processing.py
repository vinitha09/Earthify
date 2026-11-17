from datetime import date

def parse_power_response(response: dict, start: date, end: date, units: dict) -> dict:
    try:
        parameters = response["properties"]["parameter"]
        days = next(iter(parameters.values())).keys()
    except (KeyError, StopIteration) as exc:
        raise ValueError("NASA POWER returned an unexpected response") from exc
    rows = []
    for day in days:
        row = {"date": day}
        for name, values in parameters.items():
            value = values.get(day)
            row[name] = float(value) if isinstance(value, (int, float)) and value > -900 else None
        rows.append(row)
    return {"source": "NASA POWER Daily Point API", "time_standard": "UTC",
            "start": start.isoformat(), "end": end.isoformat(),
            "units": {name: units[name] for name in parameters}, "rows": rows,
            "missing_count": sum(v is None for row in rows for key, v in row.items() if key != "date")}


def aggregate_monthly_climate(climate: dict) -> list[dict]:
    months = {}
    for row in climate["rows"]:
        month = row["date"][:6]
        values = months.setdefault(month, {})
        for name in ("T2M", "PRECTOTCORR", "WS2M", "RH2M"):
            value = row.get(name)
            if value is not None:
                values.setdefault(name, []).append(value)
    return [
        {"month": f"{month[:4]}-{month[4:]}", **{
            name: round(sum(values) / len(values), 2)
            for name, values in factors.items() if values
        }}
        for month, factors in sorted(months.items())
    ]


