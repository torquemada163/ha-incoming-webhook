"""Webhook server for incoming webhook integration."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .auth import create_auth_dependency
from .models import WebhookRequest, WebhookResponse, ErrorResponse
from .const import (
    DOMAIN,
    CONF_PORT,
    CONF_JWT_SECRET,
    ATTR_LAST_TRIGGERED_AT,
)

_LOGGER = logging.getLogger(__name__)


class WebhookServer:
    """FastAPI server for webhook handling running inside Home Assistant."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """
        Initialize webhook server.
        
        Args:
            hass: Home Assistant instance
            entry: Config entry for this integration
        """
        self.hass = hass
        self.entry = entry
        self.app: Optional[FastAPI] = None
        self.server: Optional[uvicorn.Server] = None
        self._server_task = None
        
    def _create_app(self) -> FastAPI:
        """
        Create FastAPI application with endpoints.
        
        Returns:
            Configured FastAPI application
        """
        app = FastAPI(
            title="Home Assistant Incoming Webhook",
            description="Secure webhook API for switch control",
            version="2.0.0",
        )
        
        # Get JWT secret from config for auth dependency
        config_data = self.hass.data[DOMAIN][self.entry.entry_id]["config"]
        jwt_secret = config_data[CONF_JWT_SECRET]
        verify_auth = create_auth_dependency(jwt_secret)
        
        @app.get("/")
        async def root():
            """Root endpoint - health check."""
            entities = self.hass.data[DOMAIN][self.entry.entry_id].get("entities", {})
            return {
                "name": "Incoming Webhook Integration",
                "version": "2.0.0",
                "status": "running",
                "switches_configured": len(entities)
            }
        
        @app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy"}
        
        @app.post("/webhook", response_model=WebhookResponse)
        async def webhook(
            request: WebhookRequest,
            jwt_payload: dict = Depends(verify_auth)
        ):
            """
            Main webhook endpoint for controlling switches.
            
            Args:
                request: Webhook request with switch_id, action, and optional attributes
                jwt_payload: Verified JWT payload (injected by auth dependency)
                
            Returns:
                WebhookResponse with operation result
            """
            return await self._handle_webhook(request)
        
        # Register exception handlers
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc: HTTPException):
            """Handle HTTP exceptions."""
            _LOGGER.warning(f"HTTP {exc.status_code}: {exc.detail}")
            
            error_response = ErrorResponse(
                error=exc.detail if isinstance(exc.detail, str) else "Error occurred",
                details=str(exc.detail) if not isinstance(exc.detail, str) else None
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump()
            )
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request, exc: Exception):
            """Handle unexpected exceptions."""
            _LOGGER.error(f"Unhandled exception: {exc}", exc_info=True)
            
            error_response = ErrorResponse(
                error="Internal server error",
                details="An unexpected error occurred"
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )
        
        return app
    
    async def _handle_webhook(self, request: WebhookRequest) -> WebhookResponse:
        """
        Handle incoming webhook request.
        
        Args:
            request: Validated webhook request
            
        Returns:
            WebhookResponse with operation result
            
        Raises:
            HTTPException: If switch not found or operation fails
        """
        switch_id = request.switch_id
        action = request.action
        custom_attributes = request.attributes or {}
        
        _LOGGER.info(f"Webhook called: switch_id={switch_id}, action={action}")
        
        # Get entities from hass.data
        entities = self.hass.data[DOMAIN][self.entry.entry_id].get("entities", {})
        
        # Find the entity
        entity = entities.get(switch_id)
        if not entity:
            _LOGGER.warning(f"Switch '{switch_id}' not found")
            raise HTTPException(
                status_code=404,
                detail=f"Switch '{switch_id}' is not configured"
            )
        
        try:
            # Perform the requested action
            if action == "on":
                await entity.async_turn_on()
                _LOGGER.debug(f"Switch {switch_id} turned on")
                
            elif action == "off":
                await entity.async_turn_off()
                _LOGGER.debug(f"Switch {switch_id} turned off")
                
            elif action == "toggle":
                await entity.async_toggle()
                _LOGGER.debug(f"Switch {switch_id} toggled")
            
            elif action == "status":
                # Just retrieve status, no state change
                _LOGGER.debug(f"Status check for {switch_id}")
            
            # Set custom attributes if provided
            if custom_attributes:
                await entity.async_set_custom_attributes(custom_attributes)
            
            # Get current state
            current_state =  "on" if entity.is_on else "off"
            attributes = entity.extra_state_attributes
            
            # Build response
            response = WebhookResponse(
                status="success",
                switch_id=switch_id,
                action=action,
                state=current_state,
                attributes=attributes
            )
            
            _LOGGER.info(
                f"Successfully processed {action} for {switch_id}, state={current_state}"
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            _LOGGER.error(f"Error processing webhook request: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    async def start(self) -> None:
        """Start FastAPI server as a background task."""
        config_data = self.hass.data[DOMAIN][self.entry.entry_id]["config"]
        port = config_data[CONF_PORT]
        
        _LOGGER.info(f"Starting webhook server on port {port}")
        
        try:
            # Pre-import uvicorn modules in executor to avoid blocking event loop
            def _import_uvicorn_modules():
                """Import uvicorn modules synchronously in executor."""
                import uvicorn.protocols.http.auto
                import uvicorn.protocols.websockets.auto
                import uvicorn.lifespan.on
            
            await self.hass.async_add_executor_job(_import_uvicorn_modules)
            
            # Create FastAPI app
            self.app = self._create_app()
            
            # Create Uvicorn server config
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=port,
                log_level="warning",  # Minimize logging spam
                access_log=False,     # Disable access logs
            )
            
            self.server = uvicorn.Server(config)
            
            # Start server in background task
            self._server_task = self.hass.async_create_task(
                self.server.serve()
            )
            
            _LOGGER.info(f"Webhook server started successfully on port {port}")
            
        except OSError as e:
            if "address already in use" in str(e).lower():
                _LOGGER.error(
                    f"Port {port} is already in use. "
                    f"Please choose a different port in integration settings."
                )
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to start webhook server: {e}", exc_info=True)
            raise
    
    async def stop(self) -> None:
        """Stop server gracefully."""
        if not self.server:
            return
        
        _LOGGER.info("Stopping webhook server...")
        
        try:
            # Signal server to stop
            self.server.should_exit = True
            
            # Cancel the server task gracefully
            if self._server_task and not self._server_task.done():
                self._server_task.cancel()
                
                try:
                    # Wait for task to finish with timeout
                    await asyncio.wait_for(self._server_task, timeout=5.0)
                except asyncio.CancelledError:
                    # This is expected when cancelling the task
                    _LOGGER.debug("Server task cancelled successfully")
                except asyncio.TimeoutError:
                    _LOGGER.warning("Server shutdown timed out, forcing stop")
                except Exception as e:
                    _LOGGER.error(f"Error during server shutdown: {e}")
            
            _LOGGER.info("Webhook server stopped successfully")
            
        except Exception as e:
            _LOGGER.error(f"Error stopping webhook server: {e}", exc_info=True)
