import asyncio
import os
from pathlib import Path
import uvicorn
from .app import app, fixtures


async def main():
    # A moved checkout or a direct launch must also have a usable temp folder.
    runtime_temp = Path(__file__).resolve().parents[1] / ".runtime" / "tmp"
    runtime_temp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(runtime_temp)
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
