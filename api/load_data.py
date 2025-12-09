import os
import json
from django.db import connection

DATA_DIR = "/app/data"  # this is where the files are inside the container


def load_parks():
    path = os.path.join(DATA_DIR, "dcc_parks.geojson")
    print(f"Loading parks from {path}")
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        for feat in gj.get("features", []):
            props = feat.get("properties") or {}
            name = props.get("name") or props.get("NAME") or "Park"
            category = props.get("category") or props.get("TYPE")
            area_ha = props.get("area_ha") or props.get("AREA_HA")

            geom_json = json.dumps(feat["geometry"])
            cur.execute(
                """
                INSERT INTO parks (name, category, area_ha, geom)
                VALUES (%s, %s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
                """,
                [name, category, area_ha, geom_json],
            )


def load_playgrounds():
    path = os.path.join(DATA_DIR, "osm_playgrounds.geojson")
    print(f"Loading playgrounds from {path}")
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        for feat in gj.get("features", []):
            props = feat.get("properties") or {}
            name = props.get("name") or "Playground"
            source = props.get("source") or "OSM"

            geom_json = json.dumps(feat["geometry"])
            cur.execute(
                """
                INSERT INTO playgrounds (name, source, geom)
                VALUES (%s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
                """,
                [name, source, geom_json],
            )


def load_routes():
    path = os.path.join(DATA_DIR, "osm_footways.geojson")
    print(f"Loading walking routes from {path}")
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        for feat in gj.get("features", []):
            props = feat.get("properties") or {}
            name = props.get("name")
            source = props.get("source") or "OSM"
            surface = props.get("surface")
            smoothness = props.get("smoothness")
            is_accessible = props.get("is_accessible")

            # cheap way to coerce truthy/falsy to bool or None
            if isinstance(is_accessible, str):
                is_accessible = is_accessible.lower() in ("true", "t", "yes", "1")

            geom_json = json.dumps(feat["geometry"])
            cur.execute(
                """
                INSERT INTO walking_routes
                  (name, source, surface, smoothness, is_accessible, geom)
                VALUES (%s, %s, %s, %s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
                """,
                [name, source, surface, smoothness, is_accessible, geom_json],
            )


def main():
    print("Starting data load...")
    load_parks()
    print("Parks loaded.")
    load_playgrounds()
    print("Playgrounds loaded.")
    load_routes()
    print("Walking routes loaded.")
    print("Done.")


if __name__ == "__main__":
    main()
