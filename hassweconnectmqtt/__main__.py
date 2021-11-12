import argparse
from io import FileIO
import logging
from typing import List

from weconnect import addressable, weconnect
from weconnect.elements.battery_status import BatteryStatus

import paho.mqtt.client as mqtt
import time

from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.parking_position import ParkingPosition
from weconnect.elements.plug_status import PlugStatus
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.access_status import AccessStatus

from hassweconnectmqtt.component.binary import Binary
from hassweconnectmqtt.component.device import Device
from hassweconnectmqtt.component.sensor import Sensor

logging.basicConfig(level=logging.INFO)

LOGGER = logging.getLogger(__name__)


def main():
    observers: List[VehicleObserver] = []

    parser = argparse.ArgumentParser(prog='hass-weconnect-mqtt')

    parser.add_argument('--broker', type=str,
                        help='Address of MQTT broker', required=True)
    parser.add_argument('-u', '--username', type=str,
                        help='Username of We Connect ID account', required=True)
    parser.add_argument('-p', '--password', type=str,
                        help='Password of We Connect ID account', required=True)
    parser.add_argument('-i', '--interval', type=int,
                        help='API request interval', default=300, required=False)
    parser.add_argument('--images', type=str, default=None, required=False)
    

    args = parser.parse_args()

    client = mqtt.Client()
    client.connect(args.broker)
    client.loop_start()

    connection = weconnect.WeConnect(
        args.username, args.password, updateAfterLogin=False, loginOnInit=False)
    connection.login()
    connection.update()

    for vin, vehicle in connection.vehicles.items():
        del vin
        observer = VehicleObserver(vehicle, client, args.images)
        observers.append(observer)

    try:
        while True:
            connection.update(updateCapabilities=False, updatePictures=False)
            LOGGER.info("update")
            time.sleep(args.interval)
    except BaseException as e:
        LOGGER.error(e)

    for observer in observers:
        observer.close()
    
    client.loop_stop()
    client.disconnect()


class VehicleObserver:
    def __init__(self, vehicle: weconnect.Vehicle, client, imageSaveFolder=None) -> None:
        self.vehicle = vehicle

        if imageSaveFolder is not None:
            vehicle.updatePictures()

            f = FileIO(f"{imageSaveFolder}{vehicle.vin.value}.png", 'w')
            self.vehicle.pictures['car'].value.save(f, 'PNG')

        for v in vehicle.statuses.keys():
            LOGGER.info(v)

        self.access_status = vehicle.statuses.get('accessStatus')
        self.battery_status = vehicle.statuses.get('batteryStatus')
        self.charging_status = vehicle.statuses.get('chargingStatus')
        self.climatisation_status = vehicle.statuses.get('climatisationStatus')
        self.parking_position = vehicle.statuses.get('parkingPosition')
        self.plug_status = vehicle.statuses.get('plugStatus')        

        self.sensors = {}
        self.binaries = {}
        self.client = client

        self.device = Device(vehicle.nickname.value, "Volkswagen",
                             vehicle.model.value, vehicle.vin.value)

        self.addSensor(self.vehicle.vin, "VIN")

        if isinstance(self.access_status, AccessStatus):
            self.addSensor(self.access_status.overallStatus, "Access")

        if isinstance(self.battery_status, BatteryStatus):
            self.addSensor(self.battery_status.currentSOC_pct, "Battery percentage", "battery", "%")
            self.addSensor(self.battery_status.cruisingRangeElectric_km, "Range", unit_of_measurement="km")

        if isinstance(self.charging_status, ChargingStatus):
            self.addBinary(self.charging_status.chargingState, "Charge state", [ChargingStatus.ChargingState.CHARGING], [], "battery_charging")
            self.addSensor(self.charging_status.chargeMode, "Charge mode")
            self.addSensor(self.charging_status.chargePower_kW, "Charge power", "power", "W")
            self.addSensor(self.charging_status.chargeRate_kmph, "Charge rate", unit_of_measurement="kmph")

        if isinstance(self.climatisation_status, ClimatizationStatus):
            self.addSensor(self.climatisation_status.remainingClimatisationTime_min, "Remaining climatisation time", unit_of_measurement="minutes")
            self.addBinary(self.climatisation_status.climatisationState, "Climatisation", [ClimatizationStatus.ClimatizationState.COOLING, ClimatizationStatus.ClimatizationState.HEATING, ClimatizationStatus.ClimatizationState.VENTILATION], [], "power")

        if isinstance(self.parking_position, ParkingPosition):
            self.addSensor(self.parking_position.latitude, "Parking Latitude")
            self.addSensor(self.parking_position.longitude, "Parking Longitude")

        if isinstance(self.plug_status, PlugStatus):
            self.addBinary(self.plug_status.plugConnectionState, "Plug", [PlugStatus.PlugConnectionState.CONNECTED], [], "plug")
            self.addBinary(self.plug_status.plugLockState, "Plug lock", [PlugStatus.PlugLockState.LOCKED], [], "lock")

    def addSensor(self, attribute: addressable.AddressableAttribute, name, device_class=None, unit_of_measurement=None):
        address, id = self.get_ids(attribute)

        sensor = Sensor(self.client, id, name, self.device,
                        device_class, unit_of_measurement)
        sensor.publish_config()
        sensor.available = attribute.enabled

        self.sensors[address] = sensor
        self.setSensor(attribute)
        attribute.addObserver(self.on_sensor, addressable.AddressableLeaf.ObserverEvent.ALL)

    def addBinary(self, attribute: addressable.AddressableAttribute, name: str, enable_value: list = [True], disable_value: list = [False], device_class: str = None):
        address, id = self.get_ids(attribute)

        binary = Binary(self.client, id, name, self.device,
                        device_class, enable_value, disable_value)
        binary.publish_config()
        binary.available = attribute.enabled

        self.binaries[address] = binary
        self.setBinary(attribute)
        attribute.addObserver(self.on_binary, addressable.AddressableLeaf.ObserverEvent.ALL)

    def get_ids(self, attribute: addressable.AddressableAttribute):
        address = attribute.getLocalAddress()
        id = self.get_unique_id(address)

        return (address, id)

    def get_unique_id(self, address):
        return f"{self.vehicle.vin}_{address}"

    def setSensor(self, attribute: addressable.AddressableAttribute):
        address = attribute.getLocalAddress()
        sensor: Sensor = self.sensors[address]

        value = attribute.value

        if type(value) == AccessStatus.OverallState:
            value = value.name

        if type(value) == ChargingStatus.ChargingState:
            if value in [ChargingStatus.ChargingState.OFF, ChargingStatus.ChargingState.READY_FOR_CHARGING, ChargingStatus.ChargingState.ERROR]:
                value = "off"
            else:
                value = value.value

        if type(value) == ChargingStatus.ChargeMode:
            value = value.value

        sensor.available = attribute.enabled
        sensor.publish_state(value)
        LOGGER.info(f"sensor: {sensor._unique_id}")

    def on_sensor(self, element, flags):
        self.setSensor(element)

    def setBinary(self, attribute: addressable.AddressableAttribute):
        address = attribute.getLocalAddress()
        binary: Binary = self.binaries[address]

        value = attribute.value

        binary.available = attribute.enabled
        binary.set_state(value)
        LOGGER.info(f"binary: {binary._unique_id}")

    def on_binary(self, element, flags):
        self.setBinary(element)

    def close(self):
        for sensor in self.sensors.values():
            sensor.available = False
        
        for binary in self.binaries.values():
            binary.available = False
    


if __name__ == '__main__':
    main()
