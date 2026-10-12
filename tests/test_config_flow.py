"""Tests for the HRA Renovasjon config flow."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.hra_renovasjon.const import (
    CONF_ADDRESS,
    CONF_AGREEMENT_GUID,
    DOMAIN,
)

from .conftest import ADDRESS, AGREEMENT_GUID, SEARCH_URL, make_entry


async def _start(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    return result


async def test_user_flow_creates_entry(hass, aioclient_mock):
    aioclient_mock.get(SEARCH_URL, json=[{"agreementGuid": AGREEMENT_GUID}])
    result = await _start(hass)

    with patch(
        "custom_components.hra_renovasjon.async_setup_entry", return_value=True
    ) as mock_setup:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ADDRESS: ADDRESS}
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == ADDRESS
    assert result2["data"] == {CONF_ADDRESS: ADDRESS, CONF_AGREEMENT_GUID: AGREEMENT_GUID}
    assert result2["result"].unique_id == AGREEMENT_GUID
    assert len(mock_setup.mock_calls) == 1

    # The address goes to the API as the `query` parameter.
    _, url, _, _ = aioclient_mock.mock_calls[0]
    assert url.query["query"] == ADDRESS


async def test_vague_address_takes_first_match(hass, aioclient_mock):
    """Documented behaviour: several matches silently pick data[0]."""
    aioclient_mock.get(
        SEARCH_URL,
        json=[{"agreementGuid": AGREEMENT_GUID}, {"agreementGuid": "other-guid"}],
    )
    result = await _start(hass)

    with patch("custom_components.hra_renovasjon.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ADDRESS: "Storgata"}
        )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_AGREEMENT_GUID] == AGREEMENT_GUID


async def test_already_configured_aborts(hass, aioclient_mock):
    """Regression (0.1.14): the abort was swallowed and shown as cannot_connect."""
    make_entry(hass)
    aioclient_mock.get(SEARCH_URL, json=[{"agreementGuid": AGREEMENT_GUID}])
    result = await _start(hass)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )

    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_no_match_shows_cannot_connect(hass, aioclient_mock):
    """The API answers 200 [] for an unknown address."""
    aioclient_mock.get(SEARCH_URL, json=[])
    result = await _start(hass)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: "Finnes ikke 99"}
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_http_error_shows_cannot_connect(hass, aioclient_mock):
    aioclient_mock.get(SEARCH_URL, status=500)
    result = await _start(hass)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_can_retry_after_error(hass, aioclient_mock):
    aioclient_mock.get(SEARCH_URL, status=500)
    result = await _start(hass)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result2["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(SEARCH_URL, json=[{"agreementGuid": AGREEMENT_GUID}])
    with patch("custom_components.hra_renovasjon.async_setup_entry", return_value=True):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {CONF_ADDRESS: ADDRESS}
        )

    assert result3["type"] == FlowResultType.CREATE_ENTRY
