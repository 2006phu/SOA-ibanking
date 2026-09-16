import uuid
import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse


async def proxy_request(
    method: str,
    target_url: str,
    request: Request,
    user_id: str | None = None,
    user_email: str | None = None,
    timeout: float = 30.0,
) -> Response:
    """
    Forward HTTP request to downstream microservices using httpx.AsyncClient.
    Injects X-Correlation-ID for distributed tracing, and X-User-ID/X-User-Email
    for user context.
    """
    # Filter out client hop-by-hop headers
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    # Correlation ID injection
    correlation_id = (
        getattr(request.state, "correlation_id", None)
        or headers.get("X-Correlation-ID")
        or str(uuid.uuid4())
    )
    headers["X-Correlation-ID"] = correlation_id

    # User context injection
    effective_user_id = user_id or getattr(request.state, "user_id", None)
    if effective_user_id:
        headers["X-User-ID"] = str(effective_user_id)

    effective_email = user_email or getattr(request.state, "user_email", None)
    if effective_email:
        headers["X-User-Email"] = str(effective_email)

    effective_username = getattr(request.state, "user_username", None)
    if effective_username:
        headers["X-User-Name"] = str(effective_username)

    # Read body bytes
    body = await request.body()

    # Query parameters
    params = dict(request.query_params) if request.query_params else None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_response = await client.request(
                method=method,
                url=target_url,
                params=params,
                content=body,
                headers=headers,
            )

            # Strip hop-by-hop and encoding headers
            excluded_headers = {
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "connection",
            }
            resp_headers = {
                k: v for k, v in upstream_response.headers.items()
                if k.lower() not in excluded_headers
            }
            resp_headers["X-Correlation-ID"] = correlation_id

            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                headers=resp_headers,
                media_type=upstream_response.headers.get("content-type"),
            )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"detail": "Gateway Timeout: Upstream service did not respond in time."},
            headers={"X-Correlation-ID": correlation_id},
        )
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=503,
            content={"detail": f"Service Unavailable: Unable to communicate with upstream service ({str(exc)})."},
            headers={"X-Correlation-ID": correlation_id},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Gateway Error: {str(exc)}"},
            headers={"X-Correlation-ID": correlation_id},
        )
