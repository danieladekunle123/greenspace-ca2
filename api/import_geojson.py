import json
from pathlib import Path
from django.conf import settings
from django.db import connection

DATA_DIR = settings.BASE_DIR / "data"


def load_parks():
    path = DATA_DIR / "dcc_parks.geojson"
    print(f"Loading parks from {path}")
    with path.open() as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        cur.execute("TRUNCATE parks RESTART IDENTITY;")
        for feat in gj.get("features", []):
            geom = feat.get("geometry")
            if not geom:
                continue
            geom_json = json.dumps(geom)

            props = feat.get("properties") or {}
            name = (
                props.get("name")
                or props.get("NAME")
                or "Park"
            )
            category = (
                props.get("category")
                or props.get("CATEGORY")
                or ""
            )
            area_ha = (
                props.get("area_ha")
                or props.get("AREA_HA")
            )

            cur.execute(
                """
                INSERT INTO parks (name, category, area_ha, geom)
                VALUES (%s, %s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
                """,
                [name, category, area_ha, geom_json],
            )
    print("Parks loaded.")


def load_playgrounds():
    path = DATA_DIR / "osm_playgrounds.geojson"
    print(f"Loading playgrounds from {path}")
    with path.open() as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        cur.execute("TRUNCATE playgrounds RESTART IDENTITY;")
        for feat in gj.get("features", []):
            geom = feat.get("geometry")
            if not geom:
                continue
            geom_json = json.dumps(geom)

            props = feat.get("properties") or {}
            name = (
                props.get("name")
                or props.get("NAME")
                or "Playground"
            )

            cur.execute(
                """
                INSERT INTO playgrounds (name, source, geom)
                VALUES (%s, %s,
                        ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
                """,
                [name, "OSM", geom_json],
            )
    print("Playgrounds loaded.")


def load_routes():
    path = DATA_DIR / "osm_footways.geojson"
    print(f"Loading walking routes from {path}")
    with path.open() as f:
        gj = json.load(f)

    with connection.cursor() as cur:
        # if there are any access_issues already, truncate them too so FK doesn't block us
        cur.execute("TRUNCATE access_issues RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE walking_routes RESTART IDENTITY;")

        for feat in gj.get("features", []):
            geom = feat.get("geometry")
            if not geom:
                continue

            # Only accept LineString/MultiLineString. Skip Polygons etc.
            gtype = geom.get("type")
            if gtype not in ("LineString", "MultiLineString"):
                continue

            geom_json = json.dumps(geom)

            props = feat.get("properties") or {}
            name = props.get("name") or props.get("NAME") or ""
            surface = props.get("surface") or ""
            smoothness = props.get("smoothness") or ""

            # Very simple heuristic for is_accessible
            is_accessible = surface in ("paved", "asphalt", "concrete") and smoothness in (
                "good",
                "excellent",
                "very_good",
            )

            # ST_LineMerge will handle MultiLineString -> LineString in many cases.
            cur.execute(
                """
                INSERT INTO walking_routes
                  (name, source, surface, smoothness, is_accessible, geom)
                VALUES
                  (%s, %s, %s, %s, %s,
                   ST_SetSRID(ST_LineMerge(ST_GeomFromGeoJSON(%s)), 4326))
                """,
                [name, "OSM", surface, smoothness, is_accessible, geom_json],
            )
    print("Walking routes loaded.")


def run():
    print("Starting GeoJSON import...")
    load_parks()
    load_playgrounds()
    load_routes()
    print("All data loaded.")
