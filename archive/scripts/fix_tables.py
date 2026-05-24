import asyncio
from db.session import engine
from shared.database.base import Base

import models.user
import models.api_key
import models.audit_log
import models.batch
import models.request
import models.response
import models.settings

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("All tables created successfully.")

asyncio.run(main())
