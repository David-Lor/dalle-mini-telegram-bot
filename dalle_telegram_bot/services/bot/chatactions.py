from threading import Thread, Event, Lock
from collections import Counter
from typing import Dict

import telebot

from ...settings import Settings


class ActionManager:
    def __init__(self, action: str, bot: telebot.TeleBot, settings: Settings):
        self._action = action
        self._bot = bot
        self._settings = settings

        self._chatids_events: Dict[int, Event] = dict()
        self._chatids_counter = Counter()
        self._chatids_counter_lock = Lock()

    def start(self, chat_id: int):
        """Register a 'start' Action for a chat.
        If an action was not currently running for the chat, start it.
        In any case, increase the counter for the chat."""
        do_start = False
        with self._chatids_counter_lock:
            if not self.get_count(chat_id):
                do_start = True
            self.increase(chat_id)

        if do_start:
            self._start_action_thread(chat_id)

    def stop(self, chat_id: int):
        """Register a 'stop' Action for a chat.
        Decrease the counter; if just one action was running for the chat, stop it."""
        do_stop = False
        with self._chatids_counter_lock:
            if self.get_count(chat_id):
                if not self.decrease(chat_id):
                    do_stop = True

        if do_stop:
            self._stop_action_thread(chat_id)

    def get_count(self, chat_id: int) -> int:
        """Get current request count for a chat."""
        return self._chatids_counter[chat_id]

    def increase(self, chat_id: int) -> int:
        """Increase the request counter for a chat, and return the new value.
        The counter access should be locked while calling this method."""
        self._chatids_counter[chat_id] += 1
        return self.get_count(chat_id)

    def decrease(self, chat_id: int) -> int:
        """Decrease the request counter for a chat, and return the new value.
        If the new value is 0, remove the referenced that from the Counter.
        The counter access should be locked while calling this method."""
        self._chatids_counter[chat_id] -= 1
        current = self.get_count(chat_id)
        if current <= 0:
            del self._chatids_counter[chat_id]
        if current < 0:
            current = 0
        return current

    def _start_action_thread(self, chat_id: int):
        """Start the action thread. The chat_id MUST not be currently running any actions."""
        event = Event()
        thread = Thread(
            target=self._action_worker,
            kwargs=dict(
                chat_id=chat_id,
                event=event,
            ),
            name=f"TelegramBot-ActionWorker-{self._action}-{chat_id}",
            daemon=True
        )
        self._chatids_events[chat_id] = event
        thread.start()

    def _stop_action_thread(self, chat_id: int):
        """Stop the action thread for a chat_id. The chat_id MUST be currently running an action."""
        event = self._chatids_events.pop(chat_id)
        event.set()

    def _action_worker(self, chat_id: int, event: Event):
        # TODO Add timeout
        while not event.is_set():
            try:
                self._bot.send_chat_action(
                    chat_id=chat_id,
                    action=self._action,
                )
            # TODO Detect "bot blocked by user" and break in this case (call stop())
            except Exception:
                # TODO log
                pass
            event.wait(4.5)
