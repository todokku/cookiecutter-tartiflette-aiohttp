import json

from typing import Any, Dict, Optional, Tuple

from aiohttp.http_exceptions import HttpBadRequest

__all__ = ("extract_graphql_params",)


async def _graphql_request_parser(
    request: "aiohttp.web.Request",
) -> Dict[str, Any]:
    """
    Parses a request from an application/graphql content type request.
    :param request: incoming aiohttp request
    :type request: aiohttp.web.Request
    :return: GraphQL params extracted from the request
    :rtype: Dict[str, Any]
    """
    return {"query": await request.text()}


async def _json_request_parser(
    request: "aiohttp.web.Request",
) -> Dict[str, Any]:
    """
    Parses a request from an application/json content type request.
    :param request: incoming aiohttp request
    :type request: aiohttp.web.Request
    :return: GraphQL params extracted from the request
    :rtype: Dict[str, Any]
    :raise HttpBadRequest: if the body is an invalid JSON
    """
    try:
        return await request.json()
    except Exception:
        raise HttpBadRequest(message="POST body sent invalid JSON.")


async def _form_request_parser(
    request: "aiohttp.web.Request",
) -> Dict[str, Any]:
    """
    Parses a request from an application/x-www-form-urlencoded or
    multipart/form-data content type request.
    :param request: incoming aiohttp request
    :type request: aiohttp.web.Request
    :return: GraphQL params extracted from the request
    :rtype: Dict[str, Any]
    """
    return await request.post()


_REQUEST_PARSERS = {
    "application/graphql": _graphql_request_parser,
    "application/json": _json_request_parser,
    "application/x-www-form-urlencoded": _form_request_parser,
    "multipart/form-data": _form_request_parser,
}


async def _parse_request(request: "aiohttp.web.Request") -> Dict[str, Any]:
    """
    Parses a GraphQL request depending on the request content type.
    :param request: incoming aiohttp request
    :type request: aiohttp.web.Request
    :return: GraphQL params extracted from the request
    :rtype: Dict[str, Any]
    """
    request_parser = _REQUEST_PARSERS.get(request.content_type)
    if request_parser:
        return await request_parser(request)
    return {}


def _parse_graphql_params(
    body_data: Dict[str, Any], url_data: Dict[str, Any]
) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validates and extracts GraphQL params from the query string and/or the body
    request.
    :param body_data: data extracted from the body request
    :param url_data: data extracted from the query string
    :type body_data: Dict[str, Any]
    :type url_data: Dict[str, Any]
    :return: a tuple containing the query, variables and operation name
    :rtype: Tuple[str, Optional[Dict[str, Any]], Optional[str]]
    :raise HttpBadRequest: if the filled in variables are invalid JSON
    """
    query = url_data.get("query") or body_data.get("query")
    if not isinstance(query, str):
        query = None

    variables = url_data.get("variables") or body_data.get("variables")
    if variables and isinstance(variables, str):
        try:
            variables = json.loads(variables)
        except Exception:
            raise HttpBadRequest("Variables are invalid JSON.")
    elif not isinstance(variables, dict):
        variables = None

    operation_name = url_data.get("operationName") or body_data.get(
        "operationName"
    )
    if not isinstance(operation_name, str):
        operation_name = None

    return (query, variables, operation_name)


async def extract_graphql_params(
    request: "aiohttp.web.Request",
) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
    """
    Parses and extracts GraphQL params from a request.
    :param request: incoming aiohttp request
    :type request: aiohttp.web.Request
    :return: a tuple containing the query, variables and operation name
    :rtype: Tuple[str, Optional[Dict[str, Any]], Optional[str]]
    """
    return _parse_graphql_params(await _parse_request(request), request.query)
