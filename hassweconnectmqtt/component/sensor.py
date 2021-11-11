import paho.mqtt.client as mqtt

from hassweconnectmqtt.component.component import Component
from hassweconnectmqtt.component.device import Device

SENSOR_TYPE = "sensor"

class Sensor(Component):
    device_class: str
    unit_of_measurement: str

    def __init__(self, 
        client: mqtt.Client, 
        unique_id: str, 
        name: str,
        device: Device = None, 
        device_class: str = None,
        unit_of_measurement: str = None,
        prefix: str = "homeassistant"
    ) -> None:
        super().__init__(client, unique_id, name, device=device, prefix=prefix)

        self.device_class = device_class
        self.unit_of_measurement = unit_of_measurement

    @property
    def type(self) -> str:
        return SENSOR_TYPE

    def get_config(self, config: object) -> object:
        if self.device_class is not None:
            config["device_class"] = self.device_class

        if self.unit_of_measurement is not None:
            config["unit_of_measurement"] = self.unit_of_measurement

        return config
