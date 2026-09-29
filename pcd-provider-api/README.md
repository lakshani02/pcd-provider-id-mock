# PCD Provider Search (mock)

A stand-in for the Guardian PCD search (`guardiananytime.com/fpapp/search`) that the
WM5-MSG002 "PCD PROVIDER-ID IS REQUIRED" process uses to find a Primary Care Dentist
for Managed Dental Care (MDG) and FCW Dental. It lets the PCD dflows look up a
provider ID instead of carrying it in the input JSON, until real Guardian access exists.

It mirrors the manual search: plan type **Managed Dental Care (DHMO/Prepaid)**, the
employee's **zip code**, **50 miles**, specialty **Primary Care Dentist**.

This is a separate project from the data engine: its own dependencies, image and
deployment. Nothing in `src/` imports it.

## Endpoint

`GET /api/v1/pcd-providers`

| Query parameter | Required | Default | Notes |
|---|---|---|---|
| `zip_code` | yes | | 5 digits; ZIP+4 (`75201-1234`) is accepted |
| `radius_miles` | no | `50` | 1 to 250 |

The plan type (Managed Dental Care (DHMO/Prepaid)) and specialty (Primary Care Dentist) are
fixed; the response echoes them under `search`.

Response (nearest first):

```json
{
  "search": {"plan_type": "Managed Dental Care (DHMO/Prepaid)", "zip_code": "75201",
             "radius_miles": 50, "specialty": "Primary Care Dentist"},
  "found": true,
  "count": 3,
  "pcd_ids": ["PCD0012345", "PCD0012346", "PCD0023456"],
  "providers": [
    {"pcd_id": "PCD0012345", "provider_name": "Dr. Maria Lopez",
     "practice_name": "Uptown Family Dental", "specialty": "Primary Care Dentist",
     "address": {"line1": "2501 N Harwood St", "city": "Dallas", "state": "TX", "zip": "75201"},
     "distance_miles": 0.3}
  ]
}
```

`pcd_ids` has the same shape as the preprocessing dflow's `pcd_search.pcd_ids`.

| Status | Meaning |
|---|---|
| `200`, `found: true` | One or more providers in range. Use the first ID |
| `200`, `found: false` | No provider in range: the PCD is not available (the service-area case) |
| `404` | The zip code isn't in the mock data. This is a data problem, not "no provider", so it must not produce the service-area notice |
| `422` | The zip code isn't 5 digits |
| `401` | An API key is configured and `X-API-Key` is missing or wrong |

`GET /health` returns `{"status": "ok"}`. Interactive docs are at `/docs`.

## Test zip codes

| Zip | Place | Result |
|---|---|---|
| `75201` | Dallas, TX | Found: `PCD0012345` first (the ID the PCD sample inputs use) |
| `75001` | Addison, TX | Found: `PCD0012346` first |
| `76102` | Fort Worth, TX | Found: `PCD0023456` first |
| `77002` | Houston, TX | Found: `PCD0034567` |
| `78701` | Austin, TX | Found: `PCD0045678` |
| `10001` | New York, NY | Found: `PCD0056789` |
| `79843` | Marfa, TX | **Not found**: no dentist within 50 miles |
| `82001` | Cheyenne, WY | **Not found** |
| any other | | `404` |

The data lives in `pcd_provider_mock/data/`: `zip_centroids.json` (zip to coordinates) and
`providers.json` (dentists with coordinates). Distance is straight-line miles from the zip
centre. To use a different data set without rebuilding, mount a folder holding both files and
set `PCD_MOCK_DATA_DIR` to it.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8080` | Port the container listens on |
| `PCD_MOCK_API_KEY` | unset | When set, every search must send it as `X-API-Key`. Leave unset only for local use |
| `PCD_MOCK_DATA_DIR` | bundled `data/` | Folder holding `zip_centroids.json` and `providers.json` |

## Run locally

From this folder, with Python 3.13:

```bash
pip install .
uvicorn pcd_provider_mock.main:app --port 8095
curl "http://localhost:8095/api/v1/pcd-providers?zip_code=75201"
```

## Run with Docker

Next to the data engine's local stack, on its shared network (run `make docker-start-infra`
first). The URL is `http://pcd-provider-mock:8080` from a containerised processor, or
`http://localhost:8095` from a processor running on the host:

```bash
docker compose -f mock-services/pcd-provider-api/docker-compose.yml up -d --build
```

On its own:

```bash
docker build -t pcd-provider-mock mock-services/pcd-provider-api
docker run -p 8095:8080 -e PCD_MOCK_API_KEY=<key> pcd-provider-mock
```

## Deploying

The image is self-contained and stateless: one container, no database, a health check on
`/health`. For a shared environment:

1. Build and push the image to the registry the data engine uses (ACR/ECR).
2. Run it as its own Deployment and Service (one replica is enough), with the liveness and
   readiness probes on `GET /health` and port `8080`.
3. **Set `PCD_MOCK_API_KEY`** from a secret, and store the same key as a workspace secret for
   the dflow, so the dflow sends `X-API-Key: ${wsecret:PCD_MOCK_API_KEY}`.
4. Give the dflow the Service's in-cluster URL.

This is a mock and holds fake providers only. Replace it with the real Guardian integration
before any production use.
