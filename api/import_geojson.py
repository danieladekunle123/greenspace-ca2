import json
from pathlib import Path
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_parks():
    path = DATA_DIR / "dcc_parks.geojson"
    print(f"Loading parks from {path}")
    with path.open("r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        # Optional: clear existing
        cur.execute("DELETE FROM parks;")

        for feat in gj["features"]:
            props = feat.get("properties", {})
            geom = json.dumps(feat["geometry"])

            name = props.get("name") or props.get("NAME") or "Park"
            category = props.get("category") or props.get("CATEGORY")
            area_ha = props.get("area_ha") or props.get("AREA_HA")

            cur.execute(
                """
                INSERT INTO parks(name, category, area_ha, geom)
                VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
                """,
                [name, category, area_ha, geom],
            )
    print("Parks loaded.")


def load_playgrounds():
    path = DATA_DIR / "osm_playgrounds.geojson"
    print(f"Loading playgrounds from {path}")
    with path.open("r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        cur.execute("DELETE FROM playgrounds;")

        for feat in gj["features"]:
            props = feat.get("properties", {})
            geom = json.dumps(feat["geometry"])

            name = props.get("name") or "Playground"
            source = props.get("source") or "OSM"

            cur.execute(
                """
                INSERT INTO playgrounds(name, source, geom)
                VALUES (%s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));
                """,
                [name, source, geom],
            )
    print("Playgrounds loaded.")


def load_routes():
    path = BASE_DIR / "data" / "osm_footways.geojson"
    print(f"Loading walking routes from {path}")
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        # Clear existing rows
        cur.execute("TRUNCATE walking_routes RESTART IDENTITY;")

        count_total = 0
        count_inserted = 0
        count_skipped = 0

        for feat in gj.get("features", []):
            count_total += 1
            geom = feat.get("geometry")
            props = feat.get("properties", {}) or {}

            if not geom:
                count_skipped += 1
                continue

            geom_type = geom.get("type")
            # Only accept true LineStrings; skip Polygons, MultiLineStrings, etc.
            if geom_type != "LineString":
                count_skipped += 1
                continue

            name = props.get("name") or ""
            surface = props.get("surface")
            smoothness = props.get("smoothness")

            # simple heuristic for accessibility flag
            is_accessible = False
            if surface in ("asphalt", "concrete"):
                if smoothness in ("good", "excellent", "very_good"):
                    is_accessible = True

            cur.execute(
                """
                INSERT INTO walking_routes(name, source, surface, smoothness, is_accessible, geom)
                VALUES (
                  %s,
                  %s,
                  %s,
                  %s,
                  %s,
                  ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)
                );
                """,
                [
                    name,
                    "osm",
                    surface,
                    smoothness,
                    is_accessible,
                    json.dumps(geom),
                ],
            )
            count_inserted += 1

    print(f"Walking routes: total={count_total}, inserted={count_inserted}, skipped={count_skipped}")



def run():
    print("Starting GeoJSON import...")
    load_parks()
    print("Parks loaded.")
    load_playgrounds()
    print("Playgrounds loaded.")
    load_routes()
    print("Walking routes loaded.")

