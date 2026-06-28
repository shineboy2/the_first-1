import asyncio
import sys
from pathlib import Path
sys.path.insert(0, "/home/docker/my-distributed-app/the_first-1/response-network/api")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from db.session import async_session
from models.request_type import RequestType
from models.request_type_parameter import RequestTypeParameter

async def main():
    async with async_session() as db:
        result = await db.execute(select(RequestType).options(selectinload(RequestType.parameters)))
        request_types = result.scalars().all()
        for rt in request_types:
            if rt.name == "search_passengers":
                rt.elasticsearch_query_template = {
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"first_name": "{{first_name}}"}},
                                {"match": {"last_name": "{{last_name}}"}}
                            ]
                        }
                    }
                }
                rt.available_indices = ["customers"]
                if not rt.parameters:
                    db.add_all([
                        RequestTypeParameter(request_type_id=rt.id, name="first_name", description="First Name", parameter_type="string", is_required=True, placeholder_key="first_name"),
                        RequestTypeParameter(request_type_id=rt.id, name="last_name", description="Last Name", parameter_type="string", is_required=True, placeholder_key="last_name")
                    ])
                print("Fixed search_passengers")
            elif rt.name == "search_reservations":
                rt.elasticsearch_query_template = {
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"booking_id": "{{booking_id}}"}}
                            ]
                        }
                    }
                }
                rt.available_indices = ["bookings"]
                if not rt.parameters:
                    db.add_all([
                        RequestTypeParameter(request_type_id=rt.id, name="booking_id", description="Booking ID", parameter_type="string", is_required=True, placeholder_key="booking_id")
                    ])
                print("Fixed search_reservations")

        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())
