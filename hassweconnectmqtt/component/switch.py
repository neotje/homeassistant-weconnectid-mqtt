from enum import Enum
import paho.mqtt.client as mqtt
from weconnect.addressable import AddressableAttribute, AddressableLeaf

from hassweconnectmqtt.component.component import Component
from hassweconnectmqtt.component.device import Device

import time

import logging
LOGGER = logging.getLogger(__name__)

SWITCH_TYPE = "switch"

class Switch(Component):
    def __init__(self, 
        client: mqtt.Client, 
        unique_id: str, 
        name: str,
        status: AddressableAttribute,
        device: Device = None,
        enable_value: list = [True],
        disable_value: list = [False],
        prefix: str = "homeassistant"
    ) -> None:
        super().__init__(client, unique_id, name, device=device, prefix=prefix)
        self.enable_value = enable_value
        self.disable_value = disable_value
        self.status = status
        self.status.addObserver(self._observer, AddressableLeaf.ObserverEvent.ALL)

        self._client.message_callback_add(self.command_topic, self._on_command)
        self._client.subscribe(self.command_topic)

        self.lastCommand = time.time()

    @property
    def type(self) -> str:
        return SWITCH_TYPE

    @property
    def command_topic(self):
        return f"{self.base_topic}/command"

    def _on_command(self, client, userdata, msg: mqtt.MQTTMessage):
        self.lastCommand = time.time()

    def _observer(self, element: AddressableAttribute, flags):
        if time.time() - self.lastCommand > 300:
            self.set_state(element.value)
        else:
            if flags & AddressableLeaf.ObserverEvent.VALUE_CHANGED:
                self.set_state(element.value)
                

    def get_config(self, config: object) -> object:
        config["command_topic"] = self.command_topic

        return config

    def set_state(self, state):
        payload = "OFF"

        if state in self.enable_value:
            payload = "ON"
        elif state in self.disable_value:
            payload = "OFF"

        self.publish_state(payload)

    def on_command(self, callback):
        def subscribeCallback(client, userdata, msg: mqtt.MQTTMessage):
            payload = msg.payload.decode()

            if payload == "ON":
                callback(True)
            elif payload == "OFF":
                callback(False)

            self.publish_state(payload)
        
        self._client.message_callback_add(self.command_topic, subscribeCallback)
        self._client.subscribe(self.command_topic)
