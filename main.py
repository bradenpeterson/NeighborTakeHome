from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
from collections import defaultdict


class VehicleRequest(BaseModel):
    length: int
    quantity: int


class Listing(BaseModel):
    id: str
    location_id: str
    length: int
    width: int
    price_in_cents: int


class LocationResponse(BaseModel):
    location_id: str
    listing_ids: List[str]
    total_price_in_cents: int


app = FastAPI()

# Load listings once
with open("listings.json", "r") as f:
    listings_data = [Listing(**l) for l in json.load(f)]


def evaluate_location(vehicles: List[VehicleRequest], loc_listings: List[Listing]):
    chosen = []
    total_price = 0

    for v in vehicles:
        valid_listings = [
            l for l in loc_listings
            if l.length >= v.length and l.width >= 10
        ]

        if len(valid_listings) < v.quantity:
            return False, [], 0

        valid_listings.sort(key=lambda x: x.price_in_cents)
        selected = valid_listings[:v.quantity]

        chosen.extend([l.id for l in selected])
        total_price += sum(l.price_in_cents for l in selected)

    return True, chosen, total_price


def find_possible_combinations(listings: List[Listing], vehicles: List[VehicleRequest]) -> List[LocationResponse]:
    locations = defaultdict(list)
    for listing in listings:
        locations[listing.location_id].append(listing)

    results = []
    for location_id, loc_listings in locations.items():
        valid, listing_ids, total_price = evaluate_location(vehicles, loc_listings)
        if valid:
            results.append(LocationResponse(
                location_id=location_id,
                listing_ids=listing_ids,
                total_price_in_cents=total_price
            ))

    return sorted(results, key=lambda x: x.total_price_in_cents)


@app.post("/", response_model=List[LocationResponse])
async def find_storage(vehicles: List[VehicleRequest]):
    total_quantity = sum(v.quantity for v in vehicles)
    if total_quantity > 5:
        raise HTTPException(status_code=400, detail="Total quantity of vehicles cannot exceed 5")

    return find_possible_combinations(listings_data, vehicles)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
