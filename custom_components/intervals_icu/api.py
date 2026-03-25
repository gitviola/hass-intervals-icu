"""Intervals.icu API client."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

import aiohttp

API_BASE_URL = "https://intervals.icu"


class IntervalsIcuApiError(Exception):
    """Raised when the Intervals.icu API returns an unexpected response."""


class IntervalsIcuAuthError(IntervalsIcuApiError):
    """Raised when authentication with Intervals.icu fails."""


class IntervalsIcuConnectionError(IntervalsIcuApiError):
    """Raised when communication with Intervals.icu fails."""


class IntervalsIcuApiClient:
    """Thin async client for Intervals.icu API endpoints used by this integration."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._auth = aiohttp.BasicAuth(login="API_KEY", password=api_key)

    async def get_athlete(self, athlete_id: str) -> dict[str, Any]:
        """Fetch the athlete profile object."""
        data = await self._request_json("GET", f"/api/v1/athlete/{athlete_id}")
        if not isinstance(data, dict):
            raise IntervalsIcuApiError("Unexpected athlete response format")
        return data

    async def get_athlete_summary(self, athlete_id: str) -> list[dict[str, Any]]:
        """Fetch summary rows used for fitness/fatigue/form sensors."""
        data = await self._request_json(
            "GET", f"/api/v1/athlete/{athlete_id}/athlete-summary.json"
        )
        if not isinstance(data, list):
            raise IntervalsIcuApiError("Unexpected athlete summary response format")
        return [row for row in data if isinstance(row, dict)]

    async def get_wellness_record(self, athlete_id: str, record_id: str) -> dict[str, Any]:
        """Fetch a wellness record by record id (typically an ISO date string)."""
        data = await self._request_json(
            "GET", f"/api/v1/athlete/{athlete_id}/wellness/{quote(record_id, safe='')}"
        )
        if not isinstance(data, dict):
            raise IntervalsIcuApiError("Unexpected wellness record response format")
        return data

    async def list_wellness_records(
        self,
        athlete_id: str,
        *,
        oldest: str | None = None,
        newest: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch wellness records for a date range."""
        params: dict[str, Any] = {}
        if oldest:
            params["oldest"] = oldest
        if newest:
            params["newest"] = newest

        data = await self._request_json(
            "GET",
            f"/api/v1/athlete/{athlete_id}/wellness.json",
            params=params or None,
        )
        if not isinstance(data, list):
            raise IntervalsIcuApiError("Unexpected wellness list response format")
        return [row for row in data if isinstance(row, dict)]

    async def update_wellness_record(
        self,
        athlete_id: str,
        record_date: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Partially update a wellness record for a date."""
        data = await self._request_json(
            "PUT",
            f"/api/v1/athlete/{athlete_id}/wellness/{quote(record_date, safe='')}",
            json_body=payload,
        )
        if not isinstance(data, dict):
            raise IntervalsIcuApiError("Unexpected wellness update response format")
        return data

    async def _request_json(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
    ) -> Any:
        """Run an authenticated request and parse JSON response."""
        url = f"{API_BASE_URL}{path}"

        try:
            async with self._session.request(
                method,
                url,
                auth=self._auth,
                params=params,
                json=json_body,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status in (401, 403):
                    raise IntervalsIcuAuthError("Authentication failed")

                if response.status >= 400:
                    body = await response.text()
                    raise IntervalsIcuApiError(
                        f"API request failed ({response.status}): {body[:200]}"
                    )

                try:
                    return await response.json(content_type=None)
                except aiohttp.ContentTypeError as err:
                    body = await response.text()
                    raise IntervalsIcuApiError(
                        f"API returned non-JSON response: {body[:200]}"
                    ) from err

        except asyncio.TimeoutError as err:
            raise IntervalsIcuConnectionError("Request to Intervals.icu timed out") from err
        except aiohttp.ClientError as err:
            raise IntervalsIcuConnectionError(
                "Network error while contacting Intervals.icu"
            ) from err
