from threading import Thread, Event
from colorama import Style, Fore
from utils import TimeoutVar

from mqtt_sensor import MqttSensor
from gpsd_sensor import GpsdSensor

sensors_lut = {
    'accel': ['sensor/accel/#'],
    'gps': [],
    'wind': ['sensor/wind/#']
}


class SensorsProvider(Thread):

    def __init__(self):
        Thread.__init__(self, name="sensors_provider_thread", daemon=True)
        self.end_setup = Event()
        self.sensors = {
            'accel': MqttSensor('accel_sensor', [
                'sensor/accel/#'
            ]),
            'gps': GpsdSensor(),
            'wind': MqttSensor('wind_sensor', [
                'sensor/wind/#'
            ])
        }

    def run(self):
        for sensor in self.sensors.values():
            sensor.start()
            sensor.end_setup.wait(timeout=20)

        print(f"{Style.DIM}[{self.getName()}] Setup finished{Style.RESET_ALL}")
        self.end_setup.set()

        while True:
            for sensor in self.sensors.items():
                if not sensor[1].is_alive():
                    print(f"{Fore.YELLOW}[{self.getName()}]  Sensor dead, attempting recovery...{Fore.RESET}")
                    self.sensors[sensor[0]] = GpsdSensor if sensor[0] is 'gps' else MqttSensor(sensor[0], sensors_lut[sensor[0]])
                    self.sensors[sensor[0]].start()
                    self.sensors[sensor[0]].end_setup.wait(timeout=20)
                    if self.sensors[sensor[0]].end_setup.isSet():
                        print(f"{Fore.GREEN}[{self.getName()}]  Done recovery!{Fore.RESET}")

    def get_sensor(self, sensor_name):
        if sensor_name in self.sensors:
            return self.sensors[sensor_name]
        return None


if __name__ == "__main__":
    provider = SensorsProvider()
    provider.start()

    while True:
        pass