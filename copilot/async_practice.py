import asyncio
import time

import httpx
import os

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8001",
)

def normalize_result(result):
    if isinstance(result, TimeoutError):
        return {
            "status": "timeout",
            "data": None,
            "reason": "Request exceeded its deadline",
        }
    elif isinstance(result, httpx.HTTPStatusError):
        return {
            "status": "error",
            "data": None,
            "reason": "API returned an unsuccessful HTTP response",
            "http_status": result.response.status_code,
        }
    elif isinstance(result, Exception):
        return {
            "status": "error",
            "data": None,
            "reason": str(result),
        }

    else:
        return {
            "status": "success",
            "data": result,
            "reason": None,
        }


async def fetch_inverters(client):
    return await get_json_with_retry(
        client,
        f"{API_BASE_URL}/inverters"
        
    )
    
async def fetch_alarms(client):
    return await get_json_with_retry(
        client,
        f"{API_BASE_URL}/alarms"
    )
    


async def search_manual(alarms):
    print(f"Manual: searching for {alarms['alarm_name']}")
    await asyncio.sleep(4)
    print("Manual: finished")
    return {"explanation": "Axis movement may be obstructed."}

async def investigate_alarms(client):
    alarms_data = await fetch_alarms(client)
    manual_search = await asyncio.wait_for(
        search_manual(alarms_data),
        timeout=10,
    )
    return {
        "alarms_data": alarms_data,
        "manual_search": manual_search
    }
    
async def get_json_with_retry(client, url, max_attempts=3):
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    
    for attempt in range(1, max_attempts + 1):
        response = await client.get(url)
        
        if response.status_code == 503 and attempt < max_attempts:
            await asyncio.sleep(0.1)
            continue
        
        response.raise_for_status()
        return response.json()
    
    
async def main():
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=5.0) as client:
        inverters_data, alarms_data = await asyncio.gather(
            fetch_inverters(client),
            investigate_alarms(client),
            return_exceptions=True
        )
    
    inverter_result = normalize_result(inverters_data)
    alarm_result = normalize_result(alarms_data)
    
    print(inverter_result)
    print(alarm_result)
    elapsed = time.perf_counter() - start
    print(f"Elapsed: {elapsed:.2f} seconds")
    
if __name__ == "__main__":
    asyncio.run(main())