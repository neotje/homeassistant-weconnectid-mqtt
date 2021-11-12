import paho.mqtt.client as mqtt
import json
from hassweconnectmqtt.component.device import Device

import logging
LOGGER = logging.getLogger(__name__)


class Component:
    _available: bool = True

    _unique_id: str
    _prefix: str
    _client: mqtt.Client
    _name: str

    device: Device

    def __init__(self, client: mqtt.Client, unique_id: str, name: str, device: Device = None, prefix: str = "homeassistant") -> None:
        self._unique_id = unique_id
        self._prefix = prefix
        self._client = client
        self._name = name
        self.device = device

    @property
    def type(self) -> str:
        return "component"

    @property
    def base_topic(self) -> str:
        return f"{self._prefix}/{self.type}/{self._unique_id}"

    @property
    def availability_topic(self):
        return f"{self.base_topic}/available"

    @property
    def config_topic(self):
        return f"{self.base_topic}/config"

    @property
    def state_topic(self):
        return f"{self.base_topic}/state"

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, value: bool):
        self._set_available(value)

    def _set_available(self, available: bool):
        payload = "offline"

        if available:
            payload = "online"

        self._available = available

        self._client.publish(self.availability_topic, payload, retain=True)

    def get_base_config(self) -> object:
        config = {
            "availability_topic": self.availability_topic,
            "name": self._name,
            "state_topic": self.state_topic,
            "unique_id": self._unique_id
        }

        if self.device is not None:
            config["device"] = self.device.to_object()

        return config

    def get_config(self, config: object) -> object:
        return config

    def publish_config(self):
        base = self.get_base_config()
        config = self.get_config(base)
        LOGGER.debug(config)
        self._client.publish(
            self.config_topic, json.dumps(config), retain=True)

    def publish_state(self, state):
        payload: str = ""

        if type(state) == object:
            payload = json.dumps(state)
        else:
            payload = str(state)

        self._client.publish(self.state_topic, payload)
