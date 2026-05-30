from fastapi.responses import JSONResponse
from fastapi import status

import logging

logger = logging.getLogger(__name__)

def add_exception_handlers(app):

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request,
        exc
    ):

        logger.exception(
            "Unhandled exception"
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Error interno del servidor"
            }
        )