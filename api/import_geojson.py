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
    from django.db import connection
    import json
    from pathlib import Path

    data_path = Path(__file__).resolve().parent.parent / "data" / "osm_footways.geojson"

    print(f"Loading walking routes from {data_path}")
    with connection.cursor() as cur:
        # IMPORTANT: truncate access_issues first (FK to walking_routes)
        cur.execute("TRUNCATE access_issues, walking_routes RESTART IDENTITY CASCADE;")

        with open(data_path, "r", encoding="utf-8") as f:
            gj = json.load(f)

        for feat in gj["features"]:
            geom = json.dumps(feat["geometry"])
            props = feat.get("properties") or {}

            name = props.get("name") or ""
            source = "OSM"
            surface = props.get("surface") or ""
            smoothness = props.get("smoothness") or ""
            is_accessible = (
                props.get("wheelchair") in ("yes", "designated", "permissive")
            )

            cur.execute(
                """
                INSERT INTO walking_routes (name, source, surface, smoothness, is_accessible, geom)
                VALUES (%s, %s, %s, %s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                );
                """,
                [name, source, surface, smoothness, is_accessible, geom],
            )

    print("Walking routes loaded.")



def run():
    print("Starting GeoJSON import...")
    load_parks()
    print("Parks loaded.")
    load_playgrounds()
    print("Playgrounds loaded.")
    load_routes()
    print("Walking routes loaded.")

