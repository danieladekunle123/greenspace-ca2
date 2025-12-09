import json
import os

from django.conf import settings
from django.db import connection

DATA_DIR = settings.BASE_DIR / "data"


def load_parks():
    path = DATA_DIR / "dcc_parks.geojson"
    print(f"Loading parks from {path}")

    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        # Start fresh
        cur.execute("TRUNCATE parks RESTART IDENTITY CASCADE;")

        for feat in gj.get("features", []):
            geom = feat.get("geometry")
            if not geom:
                continue

            props = feat.get("properties") or {}
            name = props.get("name") or props.get("fullname") or "Park"
            category = props.get("type") or props.get("category")
            area_ha = (
                props.get("area_ha")
                or props.get("area_ha_calc")
                or props.get("area_ha_calc_1")
            )

            cur.execute(
                """
                INSERT INTO parks (name, category, area_ha, geom)
                VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
                """,
                [name, category, area_ha, json.dumps(geom)],
            )

    print("Parks loaded.")


def load_playgrounds():
    path = DATA_DIR / "osm_playgrounds.geojson"
    print(f"Loading playgrounds from {path}")

    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        cur.execute("TRUNCATE playgrounds RESTART IDENTITY CASCADE;")

        for feat in gj.get("features", []):
            geom = feat.get("geometry")
            if not geom:
                continue

            props = feat.get("properties") or {}
            name = props.get("name") or "Playground"
            source = "OSM"

            cur.execute(
                """
                INSERT INTO playgrounds (name, source, geom)
                VALUES (%s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
                """,
                [name, source, json.dumps(geom)],
            )

    print("Playgrounds loaded.")


def load_routes():
    path = DATA_DIR / "osm_footways.geojson"
    print(f"Loading walking routes from {path}")

    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        # Because access_issues has a FK to walking_routes, truncate both with CASCADE
        cur.execute(
            "TRUNCATE access_issues, walking_routes RESTART IDENTITY CASCADE;"
        )

        inserted = 0
        skipped = 0

        for feat in gj.get("features", []):
            geom = feat.get("geometry")
            if not geom:
                skipped += 1
                continue

            gtype = geom.get("type")
            # Only load pure LineString; skip Polygons, MultiLineStrings, etc.
            if gtype != "LineString":
                skipped += 1
                continue

            props = feat.get("properties") or {}
            name = props.get("name") or "Footpath"
            source = "OSM"
            surface = props.get("surface")
            smoothness = props.get("smoothness")

            # Simple heuristic: treat "paved / asphalt / concrete" etc. as accessible
            surface_lower = (surface or "").lower()
            smooth_lower = (smoothness or "").lower()
            is_accessible = any(
                key in surface_lower
                for key in ["paved", "asphalt", "concrete", "paving_stones", "tactile"]
            ) and ("bad" not in smooth_lower and "very_bad" not in smooth_lower)

            cur.execute(
                """
                INSERT INTO walking_routes
                  (name, source, surface, smoothness, is_accessible, geom)
                VALUES
                  (%s, %s, %s, %s, %s,
                   ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
                """,
                [
                    name,
                    source,
                    surface,
                    smoothness,
                    is_accessible,
                    json.dumps(geom),
                ],
            )
            inserted += 1

    print(f"Walking routes loaded. Inserted={inserted}, skipped_non_lines={skipped}")


def run():
    print("Starting GeoJSON import...")
    load_parks()
    load_playgrounds()
    load_routes()
    print("All data imported.")
