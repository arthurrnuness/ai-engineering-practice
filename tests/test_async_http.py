import asyncio

import httpx

import pytest

from copilot.async_practice import (
    fetch_inverters,
    investigate_alarms,
    normalize_result,
)


def test_alarm_failure_preserves_inverter_result():
    def fake_api(request):
        if request.url.path == "/inverters":
            return httpx.Response(
                200,
                json={"energy_kwh": 1500},
            )

        if request.url.path == "/alarms":
            return httpx.Response(
                503,
                json={"detail": "Alarm service unavailable"},
            )

        raise AssertionError(f"Unexpected request: {request.url}")

    async def run_scenario():
        transport = httpx.MockTransport(fake_api)

        async with httpx.AsyncClient(transport=transport) as client:
            results = await asyncio.gather(
                fetch_inverters(client),
                investigate_alarms(client),
                return_exceptions=True,
            )

        return [normalize_result(result) for result in results]

    inverter_result, alarm_result = asyncio.run(run_scenario())

    assert inverter_result["status"] == "success"
    assert inverter_result["data"] == {"energy_kwh": 1500}

    assert alarm_result["status"] == "error"
    assert alarm_result["http_status"] == 503
    
def test_both_api_failures_are_reported():
    def fake_api(request):
        if request.url.path == "/inverters":
            return httpx.Response(
                500,
                json={"energy_kwh": 1500},
            )

        if request.url.path == "/alarms":
            return httpx.Response(
                503,
                json={"detail": "Alarm service unavailable"},
            )

        raise AssertionError(f"Unexpected request: {request.url}")

    async def run_scenario():
        transport = httpx.MockTransport(fake_api)

        async with httpx.AsyncClient(transport=transport) as client:
            results = await asyncio.gather(
                fetch_inverters(client),
                investigate_alarms(client),
                return_exceptions=True,
            )

        return [normalize_result(result) for result in results]
    
    

    inverter_result, alarm_result = asyncio.run(run_scenario())

    assert inverter_result["status"] == "error"
    assert inverter_result["http_status"] == 500

    assert alarm_result["status"] == "error"
    assert alarm_result["http_status"] == 503
    
def test_inverter_request_recovers_after_two_failures():
    attempts = []

    def fake_api(request):
        attempts.append(request.url.path)

        if len(attempts) < 3:
            return httpx.Response(503)

        return httpx.Response(
            200,
            json={"energy_kwh": 1500},
        )

    async def run_scenario():
        transport = httpx.MockTransport(fake_api)

        async with httpx.AsyncClient(transport=transport) as client:
            return await fetch_inverters(client)

    result = asyncio.run(run_scenario())

    assert result == {"energy_kwh": 1500}
    assert len(attempts) == 3
    
def test_inverter_request_after_three_failures():
    attempts = []

    def fake_api(request):
        attempts.append(request.url.path)

        return httpx.Response(
            503,
            json={"detail": "Alarm service unavailable"},
        )

    async def run_scenario():
        transport = httpx.MockTransport(fake_api)

        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_inverters(client)

    asyncio.run(run_scenario())

    assert len(attempts) == 3