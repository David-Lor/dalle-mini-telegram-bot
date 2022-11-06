from typing import Optional

import paho.mqtt.client as mqtt

from .common import Setupable
from .logger_abc import AbstractLogger
from ..settings import Settings


class Mqtt(Setupable, AbstractLogger):
    _mqtt: Optional[mqtt.Client]

    def __init__(self, settings: Settings):
        self._settings = settings
        self._mqtt = None
        if self._settings.mqtt_host:
            self._mqtt = mqtt.Client()

    def setup(self):
        if self._mqtt:
            self._mqtt.connect(
                host=self._settings.mqtt_host,
                port=self._settings.mqtt_port,
            )
            self._mqtt.loop_start()

    def teardown(self):
        if self._mqtt:
            self._mqtt.loop_stop()
            self._mqtt.disconnect()

    def log(self, data: str):
        topic = self._settings.mqtt_logs_topic_name
        if not self._mqtt or not topic:
            return

        # noinspection PyBroadException
        try:
            self._mqtt.publish(
                topic=topic,
                payload=data,
                qos=self._settings.mqtt_logs_qos,
            )
        except Exception:
            # TODO Log errors?
            pass
