from time import sleep

import dpath.util as dp
from colorama import Fore
from gps import gps, client, WATCH_ENABLE, WATCH_NEWSTYLE, MPS_TO_KNOTS

from .sensor import Sensor


class GpsdSensor(Sensor):
    """ Class for the communication and collections of gps data coming from the gpsd daemon. """

    def __init__(self, name, filters):
        """ Create a new sensor based on the GPSd protocol. Filter response sentences by the topic list passed
        as argument, each topic follows this pattern: "<object>/.../<attribute>".
        Available objects and attributes names can be found here: https://gpsd.gitlab.io/gpsd/gpsd_json.html.
        The wildcard '*' can be used to gather all the available data in the sub-path.\n
        :param name: The sensor displayable name.
        :param filters: A list of topics to watch in response sentences.
        """
        super().__init__(name, filters)
        self.session = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
        self.start()

    @staticmethod
    def unwrap_report(report):
        """ Unwrap the given report and export the class. Unwrapping means converting a dictionary
        wrapper into a dictionary. \n
        :param report: The report as a wrapped dictionary.
        :return: A dictionary tree with the report class as the root and the rest as a sub-tree.
        """
        def unwrap(wrapped_dict):
            output = {}
            for attr in wrapped_dict:
                if not isinstance(wrapped_dict[attr], client.dictwrapper): output[attr] = wrapped_dict[attr]
                else: output[attr] = unwrap(wrapped_dict[attr])
            return output
        unwrapped_dict = unwrap(report)
        report_class = unwrapped_dict['class']
        del unwrapped_dict['class']
        return {report_class: unwrapped_dict}

    def copy_report(self, report, path):
        """ Copy the given gpsd report into the data variable of the sensor in the given path. \n
        :param report: The report as a gps library client dictwrapper.
        :param path: The destination path of the data tree. The path can contain wildcards.
        """
        for path, value in dp.search(report, path, yielded=True):
            if dp.search(report, f'{path}/*'): self.copy_report(report, f'{path}/*')
            else: self.set(path, value)

    def start_daemon(self, tries):
        """ Try to start the gpsd service for the given number of tries by querying it. \n
        :param tries: The number of tries after giving up.
        :return: True if the daemon has been started successfully, false otherwise.
        """
        for i in range(tries):
            # TODO: Implement a standard print function
            print(f"{Fore.RED}[{self.getName()}] GPSD is not running, trying staring the service... [{i+1}]{Fore.RESET}")
            try:
                self.session = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
                print(f"{Fore.GREEN}[{self.getName()}]GPSD daemon started successfully!{Fore.RESET}")
                return True
            except ConnectionRefusedError: sleep(5)
        return False

    def run(self):
        """ Main routine of the thread. Get and filter gpsd reports. """
        while True:
            if 'TPV/speed' in self and self['TPV/speed']: self.set('TPV/speed', self['TPV/speed'] * MPS_TO_KNOTS)
            try:
                report = GpsdSensor.unwrap_report(self.session.next())
                for path in self.filters: self.copy_report(report, path)
            except KeyError: pass
            except StopIteration:
                if not self.start_daemon(5): return
