import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/inverters")
async def get_inverters():
    await asyncio.sleep(3)
    return {"energy_kwh": 1500}

@app.get("/alarms")
async def get_alarms():
    await asyncio.sleep(2)
    return {"alarm_name": "Axis Blocked"}