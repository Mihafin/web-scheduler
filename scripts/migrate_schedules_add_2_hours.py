#!/usr/bin/env python3
"""
Одноразовая миграция: сдвинуть date_from / date_to у всех расписаний на +2 часа (абсолютное время в UTC).

Запуск (из корня репозитория):
  python3 scripts/migrate_schedules_add_2_hours.py var/data.sqlite

Сделайте копию БД перед запуском. После миграции включите новую логику отображения на фронте (UTC-метки студии).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, timezone


def parse_iso_utc(s: str) -> datetime:
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def to_iso_z(dt: datetime) -> str:
    u = dt.astimezone(timezone.utc)
    base = u.strftime("%Y-%m-%dT%H:%M:%S")
    if u.microsecond:
        ms = u.microsecond // 1000
        base += f".{ms:03d}"
    return base + "Z"


def main() -> int:
    p = argparse.ArgumentParser(description="schedules: +2 hours to date_from/date_to")
    p.add_argument("db", help="path to SQLite file (e.g. var/data.sqlite)")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="only print rows that would change",
    )
    args = p.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, date_from, date_to FROM schedules ORDER BY id")
        rows = cur.fetchall()
        updates: list[tuple[str, str, int]] = []
        for sid, df, dt in rows:
            try:
                nf = to_iso_z(parse_iso_utc(df) + timedelta(hours=2))
                nt = to_iso_z(parse_iso_utc(dt) + timedelta(hours=2))
            except (ValueError, TypeError) as e:
                print(f"id={sid}: skip parse error: {e}", file=sys.stderr)
                continue
            if nf != df or nt != dt:
                updates.append((nf, nt, sid))
                if args.dry_run:
                    print(f"id={sid}\n  {df} -> {nf}\n  {dt} -> {nt}")

        if args.dry_run:
            print(f"Would update {len(updates)} row(s).")
            return 0

        for nf, nt, sid in updates:
            cur.execute(
                "UPDATE schedules SET date_from = ?, date_to = ? WHERE id = ?",
                (nf, nt, sid),
            )
        conn.commit()
        print(f"Updated {len(updates)} schedule row(s).")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
