import os
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .models import SearchCriteria, SearchResponse
from .search import search_providers

# The Guardian search values the PCD procedure uses.
DHMO_PLAN_TYPE = "Managed Dental Care (DHMO/Prepaid)"
PRIMARY_CARE_DENTIST = "Primary Care Dentist"
DEFAULT_RADIUS_MILES = 50

app = FastAPI(
    title="PCD Provider Search (mock)",
    version="0.1.0",
    description="Mock of the Guardian PCD search for the WM5-MSG002 PCD dflows. "
                "Returns Primary Care Dentists within a radius of a zip code.",
)


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    # Open when PCD_MOCK_API_KEY is unset (local use); enforced once it is set.
    expected = os.environ.get("PCD_MOCK_API_KEY")
    if expected and not secrets.compare_digest(x_api_key or "", expected):
        raise HTTPException(status_code=401, detail="missing or invalid X-API-Key")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/pcd-providers", response_model=SearchResponse,
         dependencies=[Depends(require_api_key)])
def find_pcd_providers(
    zip_code: Annotated[str, Query(description="Employee's home zip code; ZIP+4 is accepted")],
    radius_miles: Annotated[int, Query(ge=1, le=250)] = DEFAULT_RADIUS_MILES,
    specialty: str = PRIMARY_CARE_DENTIST,
    plan_type: str = DHMO_PLAN_TYPE,
) -> SearchResponse:
    zip5 = zip_code.strip()[:5]
    if not (len(zip5) == 5 and zip5.isdigit()):
        raise HTTPException(status_code=422, detail="zip_code must be a 5-digit US zip code")

    providers = search_providers(zip5, radius_miles, specialty, plan_type)
    # An unknown zip is a data problem, not "no dentist nearby": it must not
    # turn into the service-area notice.
    if providers is None:
        raise HTTPException(status_code=404, detail="zip code %s is not in the mock data" % zip5)

    return SearchResponse(
        search=SearchCriteria(plan_type=plan_type, zip_code=zip5,
                              radius_miles=radius_miles, specialty=specialty),
        found=bool(providers),
        count=len(providers),
        pcd_ids=[p.pcd_id for p in providers],
        providers=providers,
    )
