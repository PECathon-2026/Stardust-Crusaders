import asyncio
import uvicorn
from .app import app, fixtures


async def main():
    admin = uvicorn.Server(
        uvicorn.Config(
            app, host="127.0.0.1", port=8765, access_log=False, log_level="warning"
        )
    )
    sandbox = uvicorn.Server(
        uvicorn.Config(
            fixtures, host="127.0.0.1", port=8766, access_log=False, log_level="warning"
        )
    )
    print("PrivacyLens: http://127.0.0.1:8765", flush=True)
    await asyncio.gather(admin.serve(), sandbox.serve())


if __name__ == "__main__":
    asyncio.run(main())
