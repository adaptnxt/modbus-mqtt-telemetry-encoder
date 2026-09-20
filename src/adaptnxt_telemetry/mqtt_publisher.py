"""
Resilient MQTT Telemetry Publisher with offline-safety and connection monitoring.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

import logging
from typing import Callable, Optional

logger = logging.getLogger("adaptnxt_telemetry.mqtt")


class ResilientMqttPublisher:
    """Wrapper around MQTT publishing that surfaces connection states to the pipeline."""

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "adaptnxt-edge-publisher",
        username: Optional[str] = None,
        password: Optional[str] = None,
        keepalive: int = 60,
        mock_mode: bool = False
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keepalive = keepalive
        self.mock_mode = mock_mode

        self.is_connected = False
        self._mock_published_messages = []
        self._client = None

        if not self.mock_mode:
            self._init_client()

    def _init_client(self) -> None:
        try:
            import paho.mqtt.client as mqtt
            # Support both paho-mqtt v1 and v2 CallbackAPIVersion if available
            try:
                self._client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
            except AttributeError:
                self._client = mqtt.Client(client_id=self.client_id)

            if self.username:
                self._client.username_pw_set(self.username, self.password)

            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
        except ImportError:
            logger.warning("paho-mqtt not installed. Switching to mock mode.")
            self.mock_mode = True

    def _on_connect(self, client, userdata, flags, rc=None, *args, **kwargs) -> None:
        # Paho v2 passes reason_code as rc or inside flags
        code = getattr(rc, "value", rc) if rc is not None else 0
        if code == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker %s:%s", self.broker_host, self.broker_port)
        else:
            self.is_connected = False
            logger.error("Failed to connect to MQTT broker, return code: %s", code)

    def _on_disconnect(self, client, userdata, *args, **kwargs) -> None:
        self.is_connected = False
        rc = args[0] if args else kwargs.get("reason_code", 0)
        logger.warning("Disconnected from MQTT broker (code: %s)", rc)

    def connect(self) -> bool:
        """Attempts connection to the broker."""
        if self.mock_mode:
            self.is_connected = True
            return True

        try:
            self._client.connect(self.broker_host, self.broker_port, self.keepalive)
            self._client.loop_start()
            return True
        except Exception as e:
            logger.error("Connection attempt failed: %s", e)
            self.is_connected = False
            return False

    def publish(self, topic: str, payload_str: str, qos: int = 1) -> bool:
        """Publishes a payload. Returns True if successfully sent, False if offline."""
        if self.mock_mode:
            if self.is_connected:
                self._mock_published_messages.append({"topic": topic, "payload": payload_str})
                return True
            return False

        if not self.is_connected:
            return False

        try:
            info = self._client.publish(topic, payload_str, qos=qos)
            info.wait_for_publish(timeout=2.0)
            return info.is_published()
        except Exception as e:
            logger.error("Publish failed: %s", e)
            return False

    def disconnect(self) -> None:
        """Stops the client loop and disconnects gracefully."""
        self.is_connected = False
        if not self.mock_mode and self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
