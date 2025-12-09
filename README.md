# GreenSpace – Dublin Footpaths & Parks Explorer

GreenSpace is a small Django + PostGIS web app that helps users explore **parks, playgrounds and walking routes** around Dublin.

It focuses on **walkable, family-friendly and accessible routes**:

- Find parks within a chosen radius of your location.
- Show footpaths around you, with an **“accessible only”** filter.
- Search parks and playgrounds by name.
- Find your **nearest playground**.
- Manage your own **personal playgrounds** (create/update/delete).
- Report **accessibility issues** (e.g. broken pavements, blocked ramps) on any route.

The app is built for the Web Mapping & Location-Based Services module and runs either:

- Using **Docker** (Postgres + Django + Nginx), or  
- Directly on your machine with Python + Postgres.

---

## 1. Project structure (top-level)

```text
greenspace/
├─ api/                 # Django views, URLs, migrations
├─ server/              # Django project settings (DJANGO_SETTINGS_MODULE=server.settings)
├─ templates/
│   └─ index.html       # Main map UI (Leaflet + Bootstrap + JS)
├─ static/
│   └─ img/
│       └─ bg-city.jpg  # Background image used by the homepage
├─ data/
│   ├─ dcc_parks.geojson
│   ├─ osm_footways.geojson
│   └─ osm_playgrounds.geojson
├─ docker-compose.yml
├─ dockerfile
├─ nginx.conf
├─ manage.py
├─ requirements.txt
└─ README.md            # This file
2. Features overview
The UI is a single page (templates/index.html) with:

Leaflet map

Base map from OpenStreetMap tiles.

User location marker (via “Use my location” or by clicking on the map).

Controls at the top:

Use my location – set map to your browser geolocation.

Radius (m) – search radius in metres.

Find Parks – GET /api/parks/within?lat=&lng=&radius_m=.

Nearest Playground – GET /api/playgrounds/nearest.

Show Footpaths in Radius – GET /api/access/routes/within.

Optional “Accessible routes only” toggle maps to accessible_only=true.

Clear Map – removes layers and resets status.

Search panel:

Search parks by name → /api/parks/search?q=...

Search playgrounds by name → /api/playgrounds/search?q=...

Personal Playground CRUD:

POST /api/playgrounds – create.

PATCH /api/playgrounds/<id> – update name.

DELETE /api/playgrounds/<id>/delete – delete.

Frontend fields: Name, Lat, Lng, ID.

Accessibility issue reports:

Button on each route popup: “Report accessibility issue”

Opens a Bootstrap modal.

POST /api/access/issues with:

route_id

issue_type (broken pavement, blocked ramp, etc.)

description

lat/lng taken from the user marker.

Backend tables: walking_routes, access_issues.

3. Requirements
You can run the project in two ways:

Option A – Using Docker (recommended for fresh setup)
Windows 10/11

Docker Desktop installed and running

WSL2 backend enabled (Docker Desktop will guide you)

You do not need to install Postgres separately for this option.

Option B – Without Docker (local Python)
Python 3.12 (or 3.11+)

PostgreSQL with PostGIS enabled

A database called greenspace

Default user/password expected: postgres / postgres

git or a ZIP of the project

If your credentials differ, you can edit server/settings.py (DATABASES section) or override via environment variables.

4. Getting the code (ZIP)
Download the project ZIP (e.g. greenspace-main.zip) from the source (GitHub / Moodle / OneDrive).

Extract it somewhere, for example:

text
Copy code
C:\Users\<your-name>\Projects\greenspace\
You should see manage.py, docker-compose.yml, api/, server/, templates/, etc inside that folder.

5. Running with Docker (Option A – recommended)
5.1 Start Docker Desktop
Open Docker Desktop and make sure it is running.

Wait until it shows that the Docker Engine is running and healthy.

5.2 Build and start the containers
Open PowerShell in the project folder:

powershell
Copy code
cd "C:\Users\<your-name>\Projects\greenspace"

docker compose up --build
This will:

Build the web image using dockerfile (Django + Gunicorn).

Start a Postgres + PostGIS container (db).

Start an Nginx container (nginx) that proxies to Django.

The first build may take a few minutes as Python dependencies are installed.

When everything is up, you should see log output from db, web and nginx.

5.3 One-time: apply migrations (inside the web container)
Open a second PowerShell window and run:

powershell
Copy code
cd "C:\Users\<your-name>\Projects\greenspace"
docker compose exec web bash
Inside the container:

bash
Copy code
cd /app

# Tell Django that the spatial tables (parks, playgrounds, walking_routes, access_issues)
# already exist (we manage them directly in Postgres), so don't try to re-create them:
python manage.py migrate api 0001_initial --fake

# Apply the rest of the Django migrations (auth, admin, sessions, etc.)
python manage.py migrate
If this completes without errors, the Django schema is ready.

⚠️ Note: the actual spatial tables (parks, playgrounds, walking_routes, access_issues)
are created in Postgres directly (SQL), not by Django models. See §7 for details.

5.4 Open the app in a browser
With docker compose up --build still running, open:

http://localhost:8080

You should see:

The GreenSpace UI with the bg-city.jpg background.

A map centered roughly on Dublin.

All the controls at the top (Use my location, Find Parks, etc.).

The playground management card at the bottom.

Keep the docker compose up window open; stopping it will stop the app.

To shut everything down cleanly:

powershell
Copy code
cd "C:\Users\<your-name>\Projects\greenspace"
docker compose down
6. Running without Docker (Option B – local Python)
If you prefer to run directly on your laptop:

6.1 Install dependencies
Install Python 3.12.

Install PostgreSQL with PostGIS extension.

Create a database greenspace and a user postgres with password postgres (or adjust settings later).

6.2 Create and activate a virtual environment
From PowerShell in the project folder:

powershell
Copy code
cd "C:\Users\<your-name>\Projects\greenspace"

python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
6.3 Create PostGIS tables (if not there already)
Connect to Postgres using psql:

powershell
Copy code
psql -U postgres -d greenspace
In psql run:

sql
Copy code
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS parks (
    id        SERIAL PRIMARY KEY,
    name      TEXT,
    category  TEXT,
    area_ha   DOUBLE PRECISION,
    geom      geometry(MultiPolygon, 4326)
);

CREATE TABLE IF NOT EXISTS playgrounds (
    id     SERIAL PRIMARY KEY,
    name   TEXT,
    source TEXT,
    geom   geometry(Point, 4326)
);

CREATE TABLE IF NOT EXISTS walking_routes (
    id            SERIAL PRIMARY KEY,
    name          TEXT,
    source        TEXT,
    surface       TEXT,
    smoothness    TEXT,
    is_accessible BOOLEAN,
    geom          geometry(LineString, 4326)
);

CREATE TABLE IF NOT EXISTS access_issues (
    id          SERIAL PRIMARY KEY,
    route_id    INTEGER REFERENCES walking_routes(id) ON DELETE CASCADE,
    issue_type  TEXT,
    description TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    geom        geometry(Point, 4326)
);
Exit psql with \q.

6.4 Apply Django migrations
Back in your virtualenv:

powershell
Copy code
cd "C:\Users\<your-name>\Projects\greenspace"
.\.venv\Scripts\activate

python manage.py migrate api 0001_initial --fake
python manage.py migrate
6.5 Run the development server
powershell
Copy code
python manage.py runserver
Then open:

http://127.0.0.1:8000

The UI and functionality are the same as in the Docker setup.

7. Spatial data (parks, routes, playgrounds)
The database schema is designed for PostGIS, and the app expects the following tables:

parks

playgrounds

walking_routes

access_issues

The schema creation is described in §6.3 (or equivalent inside Docker with docker compose exec db bash).

The sample data files live under data/:

data/dcc_parks.geojson

data/osm_footways.geojson

data/osm_playgrounds.geojson

If the database is empty, the app UI will still work, but:

Searches and “Find Parks” / “Show Footpaths” will return no features.

You can still create your own playgrounds and access issues.

To import the sample data, you can use tools like:

QGIS → “Import layer to PostGIS…”

ogr2ogr (from GDAL) with commands targeting the greenspace database and the correct geometry column + SRID 4326.

This import step is optional for running the code.
For local testing during development I imported these GeoJSON files into the parks, playgrounds and walking_routes tables.

8. API endpoints (summary)
Some key endpoints used by the frontend:

Health:

GET /api/health

Parks:

GET /api/parks/within?lat=&lng=&radius_m=

GET /api/parks/search?q=

GET /api/parks/containing?lat=&lng=

Playgrounds:

GET /api/playgrounds/nearest?lat=&lng=&limit=1

GET /api/playgrounds/search?q=

POST /api/playgrounds (create)

PATCH /api/playgrounds/<int:pk> (update name)

DELETE /api/playgrounds/<int:pk>/delete (delete)

GET /api/playgrounds/<int:pk>/get (fetch one)

Walking routes:

GET /api/routes/intersecting_park?park_id=

GET /api/routes/within?lat=&lng=&radius_m=

GET /api/access/routes/within?lat=&lng=&radius_m=&accessible_only=true|false

Accessibility issues:

POST /api/access/issues → create a new reported issue

GET /api/access/issues/near?lat=&lng=&radius_m= → list issues near a point