import isodate

durations = [
    "PT59S",    # 59s
    "PT1M",     # 60s
    "PT1M1S",   # 61s
    "PT2M59S",  # 179s
    "PT3M",     # 180s
    "PT3M1S",   # 181s
    "PT1H",     # 3600s
    "P1DT1H",   # 1 day 1 hour
]

print(f"{'ISO':<10} | {'Seconds':<10} | {'<=60s':<6} | {'<=180s':<6}")
print("-" * 45)

for d in durations:
    try:
        dt = isodate.parse_duration(d)
        sec = dt.total_seconds()
        print(f"{d:<10} | {sec:<10} | {sec<=60!s:<6} | {sec<=180!s:<6}")
    except Exception as e:
        print(f"{d:<10} | Error: {e}")
