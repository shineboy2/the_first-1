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
            print(f"Type: {rt.name} (Execution: {rt.execution_method})")
            if not rt.parameters:
                print("  No parameters defined!")
            for param in rt.parameters:
                print(f"  - Param: {param.name} ({param.parameter_type})")
            print()

if __name__ == "__main__":
    asyncio.run(main())
