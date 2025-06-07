"""
"""
T = TypeVar("T")
S = TypeVar("S")

class Service(ABC):
    """
    """
        """Initialize the service (synchronous)."""
        """Initialize the service asynchronously."""
        """Release resources held by the service (synchronous)."""
        """Release resources held by the service asynchronously."""
    """
    """
        """
        """
        """
        """
        """
        """
    """
    """
        """Initialize the enhanced service registry."""

    def register(self, service: T) -> T:
        """
        """
            logger.warning(f"Service {service_type.__name__} is already registered")
            return service

        # Register the service
        self._services.append(service)
        self._service_ids.add(service_id)

        # Also register by concrete type if not already registered
        if service_type not in self._service_by_type:
            self._service_by_type[service_type] = service

        # Register by each base class/interface that it implements
        for base_class in service_type.__mro__[1:]:  # Skip the class itself
            if base_class not in (object, ABC) and base_class not in self._service_by_type:
                self._service_by_type[base_class] = service

        return service

    def register_factory(
        self, service_type: Type[T], factory: Union[ServiceFactory[T], Callable[[], T]]
    ) -> ServiceFactory[T]:
        """
        """

        return factory

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        """
        """
        """
            raise ValueError(f"Required service of type {service_type.__name__} not found")
        return service

    def unregister(self, service: Any) -> bool:
        """
        """
            return True
        else:
            logger.warning(f"Service {service_type.__name__} is not registered")
            return False

    def has_service(self, service_type: Type[T]) -> bool:
        """
        """
        """
        """
        logger.info(f"Initializing {len(self._services)} services asynchronously")

        for service in self._services:
            service_name = service.__class__.__name__

            # Check if the service supports async initialization
            if hasattr(service, "initialize_async") and callable(service.initialize_async):
                # Create tasks for async initialization
                task = asyncio.create_task(self._initialize_service_async(service, service_name))
                initialization_tasks.append(task)
            elif hasattr(service, "initialize") and callable(service.initialize):
                # For synchronous initialize methods, run in thread pool
                loop = asyncio.get_running_loop()
                task = asyncio.create_task(self._initialize_service_sync(service, service_name, loop))
                initialization_tasks.append(task)

        # Wait for all initialization tasks to complete
        results = await asyncio.gather(*initialization_tasks, return_exceptions=True)

        # Process results and collect errors
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                service_name, error = result
                if error:
                    errors[service_name] = error

        if errors:
            logger.warning(f"Service initialization completed with {len(errors)} errors")
        else:
            logger.info("All services initialized successfully")

        return errors

    async def _initialize_service_async(self, service: Any, service_name: str) -> tuple[str, Optional[str]]:
        """
        """
            return service_name, None
        except Exception:

            pass
            error_msg = f"Failed to initialize service {service_name} asynchronously: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    async def _initialize_service_sync(
        self, service: Any, service_name: str, loop: asyncio.AbstractEventLoop
    ) -> tuple[str, Optional[str]]:
        """
        """
            return service_name, None
        except Exception:

            pass
            error_msg = f"Failed to initialize service {service_name} in thread pool: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    def initialize_all(self) -> Dict[str, str]:
        """
        """
        logger.info(f"Initializing {len(self._services)} services")

        for service in self._services:
            service_name = service.__class__.__name__
            if hasattr(service, "initialize") and callable(service.initialize):
                try:

                    pass
                    service.initialize()
                except Exception:

                    pass
                    error_msg = f"Failed to initialize service {service_name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors[service_name] = error_msg
                    # Don't re-raise, we want to try initializing all services

        if errors:
            logger.warning(f"Service initialization completed with {len(errors)} errors")
        else:
            logger.info("All services initialized successfully")

        return errors

    async def close_all_async(self) -> Dict[str, str]:
        """
        """
            if hasattr(service, "close_async") and callable(service.close_async):
                task = asyncio.create_task(self._close_service_async(service, service_name))
                closure_tasks.append(task)
            elif hasattr(service, "close") and callable(service.close):
                loop = asyncio.get_running_loop()
                task = asyncio.create_task(self._close_service_sync(service, service_name, loop))
                closure_tasks.append(task)

        # Wait for all closure tasks to complete
        results = await asyncio.gather(*closure_tasks, return_exceptions=True)

        # Process results and collect errors
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                service_name, error = result
                if error:
                    errors[service_name] = error

        # Reset registry state
        self._reset_registry()

        if errors:
            logger.warning(f"Service closure completed with {len(errors)} errors")
        else:
            logger.info("All services closed successfully")

        return errors

    async def _close_service_async(self, service: Any, service_name: str) -> tuple[str, Optional[str]]:
        """
        """
            return service_name, None
        except Exception:

            pass
            error_msg = f"Failed to close service {service_name} asynchronously: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    async def _close_service_sync(
        self, service: Any, service_name: str, loop: asyncio.AbstractEventLoop
    ) -> tuple[str, Optional[str]]:
        """
        """
            return service_name, None
        except Exception:

            pass
            error_msg = f"Failed to close service {service_name} in thread pool: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    def close_all(self) -> Dict[str, str]:
        """
        """
            if hasattr(service, "close") and callable(service.close):
                try:

                    pass
                    service.close()
                except Exception:

                    pass
                    error_msg = f"Failed to close service {service_name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors[service_name] = error_msg

        # Reset registry state
        self._reset_registry()

        if errors:
            logger.warning(f"Service registry closed with {len(errors)} errors")
        else:
            logger.info("All services closed successfully")

        return errors

    def _reset_registry(self) -> None:
        """
        """
        """
        """
        """
        """
    """
    """
    """Register a service with the global registry."""
    """Get a service from the global registry by type."""
    """Get a required service from the global registry by type."""
    """Register a service factory with the global registry."""