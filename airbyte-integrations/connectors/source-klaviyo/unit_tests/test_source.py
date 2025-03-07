#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import logging

import pendulum
import pytest
from integration.config import KlaviyoConfigBuilder
from source_klaviyo.source import SourceKlaviyo

from airbyte_cdk.test.catalog_builder import CatalogBuilder
from airbyte_cdk.test.state_builder import StateBuilder


logger = logging.getLogger("airbyte")


def _source() -> SourceKlaviyo:
    catalog = CatalogBuilder().build()
    config = KlaviyoConfigBuilder().build()
    state = StateBuilder().build()
    return SourceKlaviyo(catalog, config, state)


@pytest.mark.parametrize(
    ("status_code", "is_connection_successful", "error_msg"),
    (
        (200, True, None),
        (
            400,
            False,
            ("Bad request. Please check your request parameters."),
        ),
        (
            403,
            False,
            ("Please provide a valid API key and make sure it has permissions to read specified streams."),
        ),
    ),
)
def test_check_connection(requests_mock, status_code, is_connection_successful, error_msg):
    requests_mock.register_uri(
        "GET",
        "https://a.klaviyo.com/api/metrics",
        status_code=status_code,
        json={"end": 1, "total": 1} if 200 >= status_code < 300 else {},
    )
    source = _source()
    success, error = source.check_connection(logger=logger, config={"api_key": "api_key"})
    assert success is is_connection_successful
    assert error == error_msg


def test_check_connection_unexpected_error(requests_mock):
    exception_info = "Something went wrong"
    requests_mock.register_uri("GET", "https://a.klaviyo.com/api/metrics", exc=Exception(exception_info))
    source = _source()
    success, error = source.check_connection(logger=logger, config={"api_key": "api_key"})
    assert success is False
    assert error == f"Unable to connect to stream metrics - {exception_info}"


def test_streams():
    source = _source()
    config = {"api_key": "some_key", "start_date": pendulum.datetime(2020, 10, 10).isoformat()}
    streams = source.streams(config)
    expected_streams_number = 11
    assert len(streams) == expected_streams_number

    # ensure only unique stream names are returned
    assert len({stream.name for stream in streams}) == expected_streams_number
