#  Copyright (c) 2020 Matteo Carnelos.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from threading import Timer


class TimeoutVar:
    """
    Class for the creation of variables with timeout.

    A timeout variable auto resets itself to a default value if it's not changed after the set timeout time.
    In this case the default value represent the unavailable state of the gps data.
    """

    def __init__(self, default, timeout_sec):
        """ Set options and initialize variable to it's default value. """
        self.actual = default
        self.default = default
        self.timeout_sec = timeout_sec
        self.timeout_timer = None

    def set_value(self, value):
        """ Set the value of the variable and reset the timeout timer. """
        self.actual = value
        if self.actual != self.default:
            if self.timeout_timer is not None: self.timeout_timer.cancel()
            self.timeout_timer = Timer(self.timeout_sec, self.set_value, [self.default])
            self.timeout_timer.start()
    
    def is_default(self):
        """ Tell if the variable value is the default one. """
        return self.actual == self.default
