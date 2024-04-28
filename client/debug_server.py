import json
from fastapi import FastAPI

app = FastAPI(title="Debug Intermediary server")



@app.get("/init")
async def init():
    with open("./parties.json", "r", encoding="utf") as f:
        parties = json.loads("\n".join(f.readlines()))

    return {
        "auth_server": {"host": "127.0.0.1", "port": 7000},
        "backend_key": "",
        "intermediary_key": "",
        "parties": parties
    }
