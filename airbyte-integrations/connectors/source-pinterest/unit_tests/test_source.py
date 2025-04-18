#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

from unittest.mock import MagicMock, patch

import pytest
from source_pinterest.source import SourcePinterest

from airbyte_cdk.utils import AirbyteTracedException


def test_check_connection(requests_mock, test_config):
    requests_mock.get("https://api.pinterest.com/v5/boards", status_code=200)
    source = SourcePinterest()
    logger_mock = MagicMock()
    assert source.check_connection(logger_mock, test_config) == (True, None)


def test_check_wrong_date_connection(wrong_date_config):
    source = SourcePinterest()
    logger_mock = MagicMock()
    with pytest.raises(AirbyteTracedException) as e:
        source.check_connection(logger_mock, wrong_date_config)
    assert e.value.message == "Entered `Start Date` wrong_date_format does not match format YYYY-MM-DD"


def test_check_connection_expired_token(requests_mock, test_config):
    requests_mock.post("https://api.pinterest.com/v5/oauth/token", status_code=401)
    source = SourcePinterest()
    logger_mock = MagicMock()
    assert source.check_connection(logger_mock, test_config) == (
        False,
        "Unable to connect to stream boards - 401 Client Error: None " "for url: https://api.pinterest.com/v5/oauth/token",
    )


def test_get_authenticator(test_config):
    source = SourcePinterest()
    auth = source.get_authenticator(test_config)
    expected = test_config.get("refresh_token")
    assert auth._refresh_token == expected


def test_invalid_account_id(wrong_account_id_config):
    source = SourcePinterest()
    logger_mock = MagicMock()

    with patch("source_pinterest.source.AdAccountValidationStream") as MockStream:
        instance = MockStream.return_value
        instance.read_records.return_value = []

        with pytest.raises(AirbyteTracedException) as e:
            source.check_connection(logger_mock, wrong_account_id_config)

        expected_error = f"Invalid ad_account_id: {wrong_account_id_config['account_id']}. No data returned from Pinterest API."
        assert e.value.message == expected_error
