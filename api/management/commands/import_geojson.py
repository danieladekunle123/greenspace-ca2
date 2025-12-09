import json, os
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

def insert_geojson_features(table, json_path, name_field=None, source=""):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    feats = data["features"]
    with connection.cursor() as cur:
        for ft in feats:
            geom = json.dumps(ft["geometry"])
            props = ft.get("properties", {}) or {}

            if table == "parks":
                name = props.get(name_field or "name") or props.get("Name") or "Park"
                category = props.get("category") or props.get("Category")
                area_ha = props.get("area_ha") or props.get("Area_Ha") or None
                cur.execute("""
                WITH g AS (
                    SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS g
                ),
                norm AS (
                    SELECT ST_Multi(g) AS geom
                    FROM g
                    WHERE g IS NOT NULL
                )
                INSERT INTO parks(name, category, area_ha, geom)
                SELECT %s, %s, %s, geom FROM norm;
                """, [geom, name, category, area_ha])

            # --- Playgrounds ---
            elif table == "playgrounds":
                name = props.get(name_field or "name") or "Playground"
                cur.execute("""
                WITH g AS (
                    SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS g
                )
                INSERT INTO playgrounds(name, source, geom)
                SELECT %s, %s, g
                FROM g
                WHERE g IS NOT NULL;
                """, [geom, name, source])

            # --- Walking Routes ---
            elif table == "walking_routes":
                name = props.get(name_field or "name") or props.get("highway") or "Footway"

                surface = props.get("surface") 
                smoothness = props.get("smoothness")  

                accessible = None  
                good_surfaces = {"paved", "asphalt", "concrete"}
                good_smoothness = {"excellent", "good"}

                if surface in good_surfaces and smoothness in good_smoothness:
                    accessible = True
                elif surface is not None or smoothness is not None:
                    accessible = False

                cur.execute("""
                WITH g AS (
                    SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS g
                ),
                norm AS (
                    SELECT CASE
                    WHEN GeometryType(g) IN ('LINESTRING','MULTILINESTRING')
                        THEN ST_LineMerge(ST_Multi(g))
                    WHEN GeometryType(g) IN ('POLYGON','MULTIPOLYGON')
                        THEN ST_Multi(ST_Boundary(g))
                    ELSE NULL
                    END AS geom
                    FROM g
                )
                INSERT INTO walking_routes(name, source, surface, smoothness, is_accessible, geom)
                SELECT %s, %s, %s, %s, %s, geom
                FROM norm
                WHERE geom IS NOT NULL;
                """, [geom, name, source, surface, smoothness, accessible])


class Command(BaseCommand):
    help = "Import GeoJSON files into PostGIS"

    def add_arguments(self, parser):
        parser.add_argument("--parks", default="data/dcc_parks.geojson")
        parser.add_argument("--playgrounds", default="data/osm_playgrounds.geojson")
        parser.add_argument("--routes", default="data/osm_footways.geojson")

    def handle(self, *args, **opts):
        base = settings.BASE_DIR
        parks = os.path.join(base, opts["parks"])
        pg = os.path.join(base, opts["playgrounds"])
        rt = os.path.join(base, opts["routes"])

        insert_geojson_features("parks", parks, name_field="name", source="DCC Parks")
        insert_geojson_features("playgrounds", pg, name_field="name", source="OSM")
        insert_geojson_features("walking_routes", rt, name_field="name", source="OSM")

        self.stdout.write(self.style.SUCCESS("Imported parks, playgrounds, routes"))
