import time
import logging

logger = logging.getLogger("security.audit")


async def audit_requests_middleware(
    request,
    call_next
):

    start = time.time()

    response = await call_next(request)

    duration = round(
        time.time() - start,
        3
    )

    logger.info(
        f"REQUEST "
        f"method={request.method} "
        f"path={request.url.path} "
        f"status={response.status_code} "
        f"time={duration}s"
    )

    return response