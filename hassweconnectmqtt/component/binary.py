from typing import Any
import paho.mqtt.client as mqtt

from hassweconnectmqtt.component.component import Component
from hassweconnectmqtt.component.device import Device

BINARY_TYPE = "binary_sensor"

class Binary(Component):
    device_class: str

    enable_value: list
    disable_value: list

    def __init__(self, 
        client: mqtt.Client, 
        unique_id: str, 
        name: str,
        device: Device = None, 
        device_class: str = None,
        enable_value: list = [True],
        disable_value: list = [False],
        prefix: str = "homeassistant"
    ) -> None:
        super().__init__(client, unique_id, name, device=device, prefix=prefix)

        self.device_class = device_class
        self.enable_value = enable_value
        self.disable_value = disable_value

    @property
    def type(self) -> str:
        return BINARY_TYPE

    def get_config(self, config: object) -> object:
        if self.device_class is not None:
            config["device_class"] = self.device_class

        return config

    def set_state(self, state):
        payload = "OFF"

        if state in self.enable_value:
            payload = "ON"
        elif state in self.disable_value:
            payload = "OFF"

        self.publish_state(payload)