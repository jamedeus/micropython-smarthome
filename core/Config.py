import re
import gc
import time
import logging
import network
from random import randrange
from machine import Pin, Timer, RTC
import requests
import SoftwareTimer
from Group import Group
from api_keys import ipgeo_key
from hardware_classes import hardware_classes
from util import (
    is_device,
    is_sensor,
    is_device_or_sensor,
    reboot,
    print_with_timestamp,
    read_wifi_credentials_from_disk
)

# Set name for module's log lines
log = logging.getLogger("Config")

# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)


def instantiate_hardware(name, **kwargs):
    '''Takes name (device1, sensor2, etc) and dict of config params,
    instantiates correct driver class and returns instance.
    '''
    if is_device(name) and kwargs['_type'] not in hardware_classes['devices']:
        raise ValueError(f'Unsupported device type "{kwargs["_type"]}"')
    if is_sensor(name) and kwargs['_type'] not in hardware_classes['sensors']:
        raise ValueError(f'Unsupported sensor type "{kwargs["_type"]}"')
    if not is_device_or_sensor(name):
        raise ValueError(
            f'Invalid name "{name}", must start with "device" or "sensor"'
        )

    # Remove schedule rules (unexpected arg)
    del kwargs['schedule']

    # Import correct module, instantiate class
    if is_device(name):
        module = __import__(hardware_classes['devices'][kwargs['_type']])
    else:
        module = __import__(hardware_classes['sensors'][kwargs['_type']])
    cls = getattr(module, module.__name__)
    return cls(name, **kwargs)


class Config():
    '''Takes dict parsed from config.json, sets up node, peripherals, and
    scheduled rule changes based on config file settings.

    Makes API calls to set system clock and get local sunrise/sunset times used
    in schedule rules (uses GPS coordinates in config file if present).

    Instantiates correct driver for all devices and sensors specified in config
    file, creates callback timers for each scheduled rule change.

    Public attributes:
      devices:           List of device driver instances
      sensors:           List of device sensor instances
      schedule_keywords: Dict with keywords as keys, HH:MM timestamps as values

    Public methods:
      find:              Takes device or sensor ID, returns matching instance
      get_status:        Generates status dict returned by status API endpoint
      reload_schedule_rules: Updates sunrise/sunset times from API and creates
                         scheduled rule change callback timers for next day

    Optional delay_setup argument used in unit tests to prevent automatically
    running all methods (allows checking state in between each method).
    '''

    def __init__(self, conf, delay_setup=False):
        print_with_timestamp("Instantiating config object...")
        log.info("Instantiating config object...")
        log.debug("Config file: %s", conf)

        # Save metadata parameters (included in status object used by frontend)
        self._metadata = conf["metadata"]
        # Add key for timestamp of next schedule rule reload (between 3-4 am)
        self._metadata["_reload_time"] = ""

        # Device and sensor instances, populated by _instantiate_peripherals
        self.devices = []
        self.sensors = []

        # Group instances, populated by _build_groups
        self.groups = []

        # Stores IrBlaster instance if configured
        self.ir_blaster = None

        # Nested schedule rules dict with device and sensor IDs (device1,
        # sensor2, etc) as keys, dict of timestamp-rule pairs as values
        self.schedule = {}

        # Dictionairy of keyword-timestamp pairs, used for schedule rules
        self.schedule_keywords = {'sunrise': '00:00', 'sunset': '00:00'}
        self.schedule_keywords.update(conf["schedule_keywords"])

        # Parse all device and sensor sections into dict attributes, removed
        # after device and sensor lists populated by _instantiate_peripherals
        self._device_configs = {device: config for device, config in conf.items()
                                if is_device(device)}
        self._sensor_configs = {sensor: config for sensor, config in conf.items()
                                if is_sensor(sensor)}
        if "ir_blaster" in conf:
            self._ir_blaster_config = conf["ir_blaster"]

        if not delay_setup:
            self._setup()

    def _setup(self):
        '''Entrypoint, calls methods to set up node at boot. Runs automatically
        when class instantiated unless delay_setup arg passed (unit tests).
        '''

        # Connect to wifi, hit APIs for current time, sunrise/sunset timestamps
        self._api_calls()
        gc.collect()

        # Instantiate each config in self._device_configs and self._sensor_configs
        # as appropriate class, add to self.devices and self.sensors respectively
        self._instantiate_peripherals()

        # Create timers for all schedule rules expiring in next 24 hours
        self._build_queue()

        # Map relationships between sensors ("triggers") and devices ("targets")
        # Must run after _build_queue to prevent sensors turning devices on/off
        # before correct scheduled rule applied
        self._build_groups()

        # Start timer to build schedule rule queue for next 24 hours around 3 am
        self._start_reload_schedule_rules_timer()

        log.info("Finished instantiating config")

    def _start_reload_schedule_rules_timer(self):
        '''Schedules callback timer for a random time between 3:00-4:00 am.
        Updates sunrise/sunset times, regenerates schedule rule epoch times for
        next day, and creates callback timer for each scheduled rule change.
        '''

        # Get current epoch time + time tuple
        epoch = time.time()
        now = time.localtime(epoch)

        # Get epoch time of 3:00 am tomorrow
        # Only need to increment day, weekday etc will roll over correctly
        # Timezone (last arg) is none (required for cpython test environment)
        next_reload = time.mktime(
            (now[0], now[1], now[2] + 1, 3, 0, 0, now[6], now[7], -1)
        )

        # Calculate milliseconds until reload, add random 0-60 minute delay to
        # stagger API calls (prevent all nodes hitting endpoint simultaneously)
        adjust = randrange(3600)
        ms_until_reload = (next_reload - epoch + adjust) * 1000

        # Get HH:MM timestamp of next reload, write to log
        reload_time = time.localtime(next_reload + adjust)
        self._metadata["_reload_time"] = f"{reload_time[3]}:{reload_time[4]}"
        log.info(
            "Reload_schedule_rules callback scheduled for %s am",
            self._metadata["_reload_time"]
        )

        # Add timer to queue
        SoftwareTimer.timer.create(
            ms_until_reload,
            self.reload_schedule_rules,
            "reload_schedule_rules"
        )

    def _instantiate_peripherals(self):
        '''Populates self.devices and self.sensors lists by instantiating
        config sections from self._device_configs and self._sensor_configs.
        Can only be called once on startup.
        '''

        # Prevent calling again after setup complete
        if self.devices or self.sensors:
            raise RuntimeError("Peripherals already instantiated")

        # Instantiate all configs in _device_configs (populates self.devices)
        self._instantiate_devices(self._device_configs)

        # Instantiate all configs in _sensor_configs (populates self.sensors)
        self._instantiate_sensors(self._sensor_configs)

        # Instantiate IR Blaster if configured (max 1 due to driver limitation)
        # IR Blaster is not a Device subclass, has no schedule rules, and is
        # only triggered by API calls (can use ApiTarget to add to Group)
        if "_ir_blaster_config" in self.__dict__:
            from IrBlaster import IrBlaster
            self.ir_blaster = IrBlaster(
                int(self._ir_blaster_config["pin"]),
                self._ir_blaster_config["target"]
            )
            del self._ir_blaster_config

        # Delete device and sensor config dicts
        del self._device_configs
        del self._sensor_configs
        gc.collect()

    def _instantiate_devices(self, conf):
        '''Takes dict with device IDs (device1, device2, etc) as keys, device
        config dicts as values. Instantiates appropriate hardware driver class
        with params for each device and adds instance to self.devices list.
        '''
        log.debug("Instantiating devices")
        for device in sorted(conf):
            # Add device's schedule rules to dict
            self.schedule[device] = conf[device]["schedule"]

            try:
                # Instantiate device with appropriate class
                instance = instantiate_hardware(device, **conf[device])

                # Add instance to config.devices
                self.devices.append(instance)
            except AttributeError:
                log.critical(
                    "Failed to instantiate %s (%s), params: %s",
                    device, conf[device]['_type'], conf[device]
                )
                print_with_timestamp(
                    f"ERROR: Failed to instantiate {device} ({conf[device]['_type']}"
                )
            except ValueError:
                log.critical(
                    "Failed to instantiate %s, unsupported device type %s",
                    device, conf[device]['_type']
                )
                print_with_timestamp(
                    f"ERROR: Failed to instantiate {device}, unsupported device type {conf[device]['_type']}"
                )

        log.debug("Finished instantiating device instances")

    def _instantiate_sensors(self, conf):
        '''Takes dict with sensor IDs (sensor1, sensor2, etc) as keys, sensor
        config dicts as values. Instantiates appropriate hardware driver class
        with params for each sensor and adds instance to self.sensors list.
        '''
        log.debug("Instantiating sensors")
        for sensor in sorted(conf):
            # Add sensor's schedule rules to dict
            self.schedule[sensor] = conf[sensor]["schedule"]

            try:
                # Find device instances for each ID in targets list
                targets = [t for t in (
                    self.find(target) for target in conf[sensor]["targets"]
                ) if t]

                # Replace targets list with list of instances
                conf[sensor]['targets'] = targets

                # Instantiate sensor with appropriate class
                instance = instantiate_hardware(sensor, **conf[sensor])

                # Add sensor instance to triggered_by list of each target
                for t in targets:
                    t.triggered_by.append(instance)

                # Add instance to config.sensors
                self.sensors.append(instance)
            except AttributeError:
                log.critical(
                    "Failed to instantiate %s (%s), params: %s",
                    sensor, conf[sensor]['_type'], conf[sensor]
                )
                print_with_timestamp(
                    f"ERROR: Failed to instantiate {sensor} ({conf[sensor]['_type']}"
                )
            except ValueError:
                log.critical(
                    "Failed to instantiate %s, unsupported sensor type %s",
                    sensor, conf[sensor]['_type']
                )
                print_with_timestamp(
                    f"ERROR: Failed to instantiate {sensor}, unsupported sensor type {conf[sensor]['_type']}"
                )

        log.debug("Finished instantiating sensor instances")

    def _build_groups(self):
        '''Maps relationships between sensors (triggers) and devices (targets).
        Multiple sensors with identical targets are merged into a single Group
        instance (can also contain 1 sensor with 1 or more target). Groups will
        check condition of all sensors when refresh method is called and turn
        devices on or off when conditions change.
        '''
        log.debug("Building groups")

        # Prevent calling again after setup complete
        if self.groups:
            raise RuntimeError("Peripherals already instantiated")

        sensor_list = self.sensors.copy()

        while len(sensor_list) > 0:
            # Get first sensor in sensor_list, add to group list
            s = sensor_list.pop(0)
            group = [s]

            # Find all sensors with identical targets, add to group list
            for i in sensor_list:
                if i.targets == s.targets:
                    group.append(i)

            # Delete all sensors in group from sensor_list
            for i in group:
                try:
                    del sensor_list[sensor_list.index(i)]
                except ValueError:
                    pass

            # Instantiate group object from list of sensors
            instance = Group("group" + str(len(self.groups) + 1), group)
            self.groups.append(instance)

            # Pass instance to each member's group attributes, allows members
            # to access group methods (sensors call refresh when triggered)
            for sensor in instance.triggers:
                sensor.group = instance
                # Add Sensor's post-action routines (if any), each routine will
                # run after group turns targets on/off
                sensor.add_routines()

            for device in instance.targets:
                device.group = instance

        log.debug("Finished building %s groups", len(self.groups))

    def get_status(self):
        '''Returns dict with metadata and current status of all devices and
        sensors. Called by status API endpoint, frontend polls every 5 seconds
        and uses response to update react state.
        '''

        # Populate template from class attributes
        status_dict = {
            "metadata": self._metadata,
            "devices": {},
            "sensors": {}
        }

        # Add schedule keywords to metadata
        status_dict["metadata"]["schedule_keywords"] = self.schedule_keywords

        # Add bool that tells frontend if IR Blaster is configured
        status_dict["metadata"]["ir_blaster"] = bool(self.ir_blaster)

        # Add IR targets if IR Blaster configured
        if self.ir_blaster:
            status_dict["metadata"]["ir_targets"] = self.ir_blaster.target

        # Iterate devices, add get_status return value, add schedule rules
        for i in self.devices:
            status_dict["devices"][i.name] = i.get_status()
            status_dict["devices"][i.name]["schedule"] = self.schedule[i.name]

        # Iterate sensors, add get_status return value, add schedule rules
        for i in self.sensors:
            status_dict["sensors"][i.name] = i.get_status()
            status_dict["sensors"][i.name]["schedule"] = self.schedule[i.name]

        return status_dict

    def _api_calls(self):
        '''Connects to wifi (if not connected), sets system clock and
        sunrise/sunset times with values received from API.
        '''

        # Auto-reboot if startup doesn't complete in 1 min (prevents API calls
        # hanging, timer canceled at bottom of function once calls complete).
        reboot_timer.init(period=60000, mode=Timer.ONE_SHOT, callback=reboot)

        # Turn onboard LED on, indicates setup in progress
        led.value(1)

        # Connect to wifi
        wlan = network.WLAN(network.WLAN.IF_STA)
        wlan.active(True)
        if not wlan.isconnected():
            credentials = read_wifi_credentials_from_disk()
            log.debug("Attempting to connect to %s", credentials['ssid'])
            wlan.connect(credentials["ssid"], credentials["password"])

            # Wait until finished connecting before proceeding
            while not wlan.isconnected():
                continue
            print_with_timestamp(f"Successfully connected to {credentials['ssid']}")
            log.debug("Successfully connected to %s", credentials['ssid'])

        failed_attempts = 0

        # Ensure enough free ram for API response
        gc.collect()

        # Set system clock and sunrise/sunset times with timestamps from ipgeo API
        # Determines timezone by IP address unless config file contains GPS coords
        # Retry up to 5 times if API call fails, reboot after 5th failure
        while True:
            try:
                log.debug("Getting system time from ipgeolocation.io API...")
                # Use GPS coordinates if present, otherwise rely on IP lookup
                url = f"https://api.ipgeolocation.io/astronomy?apiKey={ipgeo_key}"
                if "gps" in self._metadata:
                    log.debug("Using GPS coordinates from config file")
                    url += f"&lat={self._metadata['gps']['lat']}&long={self._metadata['gps']['lon']}"

                response = requests.get(url, timeout=5)

                # Parse time parameters
                hour, minute, second = response.json()["current_time"].split(":")
                second, millisecond = second.split(".")

                # Parse date parameters
                year, month, day = map(int, response.json()["date"].split("-"))

                # Set RTC (uses different parameter order than time.localtime)
                RTC().datetime(
                    (year, month, day, 0, int(hour), int(minute), int(second), int(millisecond))
                )
                log.debug("System clock set")

                # Set sunrise/sunset times
                self.schedule_keywords["sunrise"] = response.json()["sunrise"]
                self.schedule_keywords["sunset"] = response.json()["sunset"]
                log.debug(
                    "Received sunrise time = %s, sunset time = %s",
                    self.schedule_keywords["sunrise"],
                    self.schedule_keywords["sunset"]
                )
                response.close()
                break

            # Issue with response object
            except KeyError:
                print_with_timestamp(
                    f'ERROR (ipgeolocation.io): {response.json()["message"]}'
                )
                log.error(
                    'ERROR (ipgeolocation.io): %s', response.json()["message"]
                )
                reboot()

            # Network issue
            except OSError:
                print_with_timestamp("Failed to set system time, retrying...")
                log.error("Failed to set system time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5:
                    log.critical(
                        "Failed to set system time 5 times, reboot triggered"
                    )
                    reboot()
                time.sleep_ms(1500)  # If failed, wait 1.5 seconds before retrying
                gc.collect()  # Free up memory before retrying

        log.info(
            "Finished API calls (timestamp may look weird due to system clock change)"
        )

        # Stop timer once API calls finish
        reboot_timer.deinit()

        # Turn off LED to confirm setup completed successfully
        led.value(0)

    def _convert_rules(self, rules):
        '''Takes dict of schedule rules with HH:MM timestamps, returns dict of
        same rules with unix epoch timestamps for next time rule should run.
        Called every day between 3-4 am (epoch times only work once).
        '''

        # Create empty dict to store new schedule rules
        result = {}

        # Replace keywords with timestamp from dict, timestamps convert to epoch below
        for keyword, timestamp in self.schedule_keywords.items():
            if keyword in rules:
                rules[timestamp] = rules[keyword]
                del rules[keyword]

        # Get rule start times, sort chronologically
        schedule = list(rules)
        schedule.sort()

        # Get epoch time in current timezone
        epoch = time.time()
        # Get time tuple in current timezone
        now = time.localtime(epoch)

        for rule in schedule:
            # Skip unconverted keywords
            if not re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", rule):
                continue

            # Get epoch time by substituting rule hour and minute into current date params
            # Timezone (last arg) is none (required for cpython test environment)
            hour, minute = rule.split(":")
            params = (now[0], now[1], now[2], int(hour), int(minute), 0, now[6], now[7], -1)
            trigger_time = time.mktime(params)

            # Add to results: Key = unix timestamp, value = rule from original dict
            result[trigger_time] = rules[rule]
            # Add same rule with timestamp 24 hours earlier (expired rules must
            # exist, current_rule determined by finding first non-expired rule)
            result[trigger_time - 86400] = rules[rule]
            # Add same rule with timestamp 24 hours later (moves rules that have
            # already expired today to tomorrow, eg rules after midnight)
            result[trigger_time + 86400] = rules[rule]

        # Get chronological list of rule timestamps
        schedule = []
        for rule in result:
            schedule.append(rule)
        schedule.sort()

        # Find current scheduled rule (last rule with timestamp before current time)
        for rule in schedule:
            if epoch > rule:
                current = rule
            # Found
            else:
                break

        # Delete all expired rules except current
        for rule in schedule:
            if not rule == current:
                del result[rule]
            else:
                break

        # Return the finished dictionairy
        return result

    def _build_queue(self):
        '''Iterates all devices and sensors, converts schedule rule HH:MM times
        to unix epoch times, creates callback timers to change rules at correct
        times, and sets correct current scheduled_rule for each instance.
        '''
        log.debug("Building schedule rule queue for all devices and sensors")

        # Delete all existing schedule rule timers to avoid conflicts
        SoftwareTimer.timer.cancel("scheduler")

        for instance, rules in self.schedule.items():
            # Convert HH:MM timestamps to unix epoch timestamp of next run
            # Copy avoids overwriting schedule keywords with HH:MM in original
            epoch_rules = self._convert_rules(rules.copy())

            # Get target instance (skip if unable to find)
            instance = self.find(instance)
            if not instance:
                continue

            # No rules: set default_rule as scheduled_rule, skip to next instance
            if len(epoch_rules) == 0:
                # Set current_rule and scheduled_rule (returns False if invalid)
                if not instance.set_rule(instance.default_rule, True):
                    # Disable instance if default invalid (prevent unpredictable behavior)
                    log.critical(
                        "%s invalid default rule (%s), disabling instance",
                        instance.name, instance.default_rule
                    )
                    instance.current_rule = "disabled"
                    instance.scheduled_rule = "disabled"
                    instance.default_rule = "disabled"
                    instance.disable()
                continue

            # Get list of timestamps, sort chronologically
            # First item in queue is current scheduled rule
            queue = []
            for j in epoch_rules:
                queue.append(j)
            queue.sort()

            # Set current_rule and scheduled_rule (returns False if invalid)
            if not instance.set_rule(epoch_rules[queue.pop(0)], True):
                # Fall back to default_rule if scheduled rule is invalid
                log.error(
                    "%s scheduled rule invalid, falling back to default rule",
                    instance.name
                )
                if not instance.set_rule(instance.default_rule, True):
                    # Disable instance if default invalid (prevent unpredictable behavior)
                    log.critical(
                        "%s invalid default rule (%s), disabling instance",
                        instance.name, instance.default_rule
                    )
                    instance.current_rule = "disabled"
                    instance.scheduled_rule = "disabled"
                    instance.default_rule = "disabled"
                    instance.disable()

            # Clear target's queue
            instance.rule_queue = []

            # Populate target's queue with chronological rule values
            for k in queue:
                instance.rule_queue.append(epoch_rules[k])

            # Get epoch time in current timezone
            epoch = time.time()

            # Create timers for all epoch_rules
            for k in queue:
                milliseconds = (k - epoch) * 1000
                SoftwareTimer.timer.create(
                    milliseconds,
                    instance.next_rule,
                    "scheduler"
                )
                gc.collect()

        print_with_timestamp("Finished building schedule rule queue")
        log.debug(
            "Finished building queue, total timers = %s",
            len(SoftwareTimer.timer.queue)
        )

    def find(self, target):
        '''Takes ID (device1, sensor2, etc), returns instance or False.'''
        if is_device(target):
            for i in self.devices:
                if i.name == target:
                    return i
            log.debug("Config.find: Unable to find %s", target)
            return False

        if is_sensor(target):
            for i in self.sensors:
                if i.name == target:
                    return i
            log.debug("Config.find: Unable to find %s", target)
            return False

        log.debug("Config.find: Unable to find %s", target)
        return False

    def reload_schedule_rules(self):
        '''Called by timer between 3-4 am every day, updates sunrise/sunset
        times and generates schedule rule epoch timestamps for next day.
        '''
        print_with_timestamp("Reloading schedule rules...")
        log.info("Callback: Reloading schedule rules")
        # Updated sunrise/sunset times, set system clock (fix daylight savings)
        self._api_calls()
        gc.collect()

        # Create timers for all schedule rules expiring in next 24 hours
        self._build_queue()

        # Set timer to run again tomorrow between 3-4 am
        self._start_reload_schedule_rules_timer()
