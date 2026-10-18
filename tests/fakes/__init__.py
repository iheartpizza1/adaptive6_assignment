"""Test doubles. Re-exports only; each fake lives in its own module."""

from tests.fakes.fake_geo_ip import FakeGeoIp
from tests.fakes.fake_user_agent_lookup import FakeUserAgentLookup

__all__ = ["FakeGeoIp", "FakeUserAgentLookup"]
