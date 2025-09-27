# app/api/websocket.py - Complete WebSocket implementation
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
    Request,
    Query,
)
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List, Set
import json
import asyncio
import logging
import time
from datetime import datetime

from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/ws", tags=["websocket"], redirect_slashes=False)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.campaign_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_meta: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, campaign_id: str, user_id: str):
        """Accept a WebSocket connection and register it"""
        await websocket.accept()

        if campaign_id not in self.campaign_connections:
            self.campaign_connections[campaign_id] = set()
        self.campaign_connections[campaign_id].add(websocket)

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        self.connection_meta[websocket] = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
        }
        logger.info(f"WebSocket connected: user={user_id}, campaign={campaign_id}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_meta:
            meta = self.connection_meta[websocket]
            campaign_id = meta.get("campaign_id")
            user_id = meta.get("user_id")

            if campaign_id and campaign_id in self.campaign_connections:
                self.campaign_connections[campaign_id].discard(websocket)
                if not self.campaign_connections[campaign_id]:
                    del self.campaign_connections[campaign_id]

            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            del self.connection_meta[websocket]
            logger.info(
                f"WebSocket disconnected: user={user_id}, campaign={campaign_id}"
            )

    async def send_to_campaign(self, message: str, campaign_id: str):
        """Send a message to all connections for a specific campaign"""
        if campaign_id in self.campaign_connections:
            disconnected = set()
            for connection in self.campaign_connections[campaign_id].copy():
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send message: {e}")
                    disconnected.add(connection)

            for connection in disconnected:
                self.disconnect(connection)

    async def broadcast_to_campaign(self, data: dict, campaign_id: str):
        """Broadcast structured data to all connections for a campaign"""
        message = json.dumps(data)
        await self.send_to_campaign(message, campaign_id)


# Global connection manager instance
manager = ConnectionManager()


# Main WebSocket endpoint - this will be accessible at /api/ws
@router.websocket("")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """Main WebSocket endpoint for real-time updates"""
    from app.core.security import verify_token

    user_id = None
    campaign_id = "general"

    try:
        # Verify token
        if not token:
            await websocket.close(code=1008, reason="Missing token")
            return

        try:
            payload = verify_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token payload")
                return
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Accept connection
        await manager.connect(websocket, campaign_id, user_id)

        # Send initial connection message
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "WebSocket connected successfully",
            }
        )

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages with timeout for keepalive
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)

                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    # Handle different message types
                    if message_type == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                    elif message_type == "subscribe_campaign":
                        new_campaign_id = message.get("campaign_id")
                        if new_campaign_id:
                            # Update the campaign subscription
                            manager.disconnect(websocket)
                            campaign_id = new_campaign_id
                            await manager.connect(websocket, campaign_id, user_id)
                            await websocket.send_json(
                                {
                                    "type": "subscribed",
                                    "campaign_id": campaign_id,
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                    else:
                        # Echo unknown messages for debugging
                        await websocket.send_json(
                            {
                                "type": "echo",
                                "original": message,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )

                except json.JSONDecodeError:
                    await websocket.send_json(
                        {"type": "error", "message": "Invalid JSON format"}
                    )

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json(
                    {"type": "keepalive", "timestamp": datetime.utcnow().isoformat()}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


@router.websocket("/campaign/{campaign_id}")
async def websocket_campaign_endpoint(
    websocket: WebSocket, campaign_id: str, token: str = Query(None)
):
    """WebSocket endpoint for campaign-specific updates"""
    from app.core.security import verify_token

    user_id = None

    try:
        # Verify token
        if not token:
            await websocket.close(code=1008, reason="Missing token")
            return

        try:
            payload = verify_token(token)
            user_id = payload.get("user_id")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Connect to specific campaign
        await manager.connect(websocket, campaign_id, user_id)

        # Send welcome message
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "campaign_id": campaign_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Connected to campaign {campaign_id} updates",
            }
        )

        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)

                try:
                    message = json.loads(data)
                    # Handle ping/pong
                    if message.get("type") == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json(
                    {"type": "keepalive", "timestamp": datetime.utcnow().isoformat()}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for campaign {campaign_id}")
    except Exception as e:
        logger.error(f"WebSocket error for campaign {campaign_id}: {e}")
    finally:
        manager.disconnect(websocket)


# Helper function to send campaign updates
async def send_campaign_update(campaign_id: str, update_data: dict):
    """Send update to all connections watching a campaign"""
    await manager.broadcast_to_campaign(
        {
            "type": "campaign_update",
            "campaign_id": campaign_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
        campaign_id,
    )
