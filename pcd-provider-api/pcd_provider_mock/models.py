from pydantic import BaseModel


class Address(BaseModel):
    line1: str
    city: str
    state: str
    zip: str


class Provider(BaseModel):
    pcd_id: str
    provider_name: str
    practice_name: str
    specialty: str
    address: Address
    distance_miles: float


class SearchCriteria(BaseModel):
    plan_type: str
    zip_code: str
    radius_miles: int
    specialty: str


class SearchResponse(BaseModel):
    search: SearchCriteria
    found: bool
    count: int
    # The IDs alone, nearest first: the shape the preprocessing dflow reads as
    # `pcd_search.pcd_ids`.
    pcd_ids: list[str]
    providers: list[Provider]
