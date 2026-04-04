
def format_protocol(rows):
    header = "COUNT TIME_MS DIR STEP"
    lines = [header]

    for r in rows:
        lines.append(
            f"{r['COUNT']:05d} {r['TIME_MS']:06d} {r['DIR']} {r['STEP']}"
        )

    return "\n".join(lines)
