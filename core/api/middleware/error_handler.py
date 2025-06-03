"""
"""
    """Middleware for handling exceptions across all endpoints."""
        """Process request and handle any exceptions."""
            logger.warning(f"Pydantic validation error: {e.errors()}")
            
            # Format validation errors for frontend consumption
            formatted_errors = []
            for error in e.errors():
                location = " → ".join(str(loc) for loc in error.get("loc", []))
                message = error.get("msg", "Validation error")
                formatted_errors.append(f"{location}: {message}")
            
            error_response = ErrorResponse(
                error="ValidationError",
                message=", ".join(formatted_errors),
                details={
                    "path": str(request.url.path),
                    "validation_errors": e.errors()
                },
            )
            return JSONResponse(status_code=422, content=error_response.dict())

        except Exception:


            pass
            # Handle other validation errors
            logger.warning(f"Validation error: {str(e)}")
            error_response = ErrorResponse(
                error="ValidationError",
                message=str(e),
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=400, content=error_response.dict())

        except Exception:


            pass
            # Handle permission errors
            logger.warning(f"Permission error: {str(e)}")
            error_response = ErrorResponse(
                error="PermissionError",
                message="You don't have permission to perform this action",
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=403, content=error_response.dict())

        except Exception:


            pass
            # Handle not found errors
            logger.warning(f"Not found error: {str(e)}")
            error_response = ErrorResponse(
                error="NotFoundError",
                message=str(e),
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=404, content=error_response.dict())

        except Exception:


            pass
            # Handle timeout errors
            logger.error(f"Timeout error: {str(e)}")
            error_response = ErrorResponse(
                error="TimeoutError",
                message="Request timed out",
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=504, content=error_response.dict())

        except Exception:


            pass
            # Handle all other exceptions
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

            # In production, don't expose internal errors
            error_response = ErrorResponse(
                error="InternalServerError",
                message="An internal error occurred",
                details={
                    "path": str(request.url.path),
                    "traceback": (traceback.format_exc() if logger.level <= logging.DEBUG else None),
                },
            )
            return JSONResponse(status_code=500, content=error_response.dict())

def handle_api_error(error: Exception, status_code: int = 500) -> JSONResponse:
    """
    """
            "type": error_type,
            "traceback": (traceback.format_exc() if logger.level <= logging.DEBUG else None),
        },
    )

    return JSONResponse(status_code=status_code, content=error_response.dict())
