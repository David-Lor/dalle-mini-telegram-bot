import time
from threading import Thread, Event, Lock
from collections import Counter
from typing import Dict

import telebot

from ...utils import exception_is_bot_blocked_by_user
from ...logger import logger, get_request_id
from ...settings import Settings


class ActionManager:
    def __init__(self, action: str, timeout: float, bot: telebot.TeleBot, settings: Settings):
        self._action = action
        self._timeout = timeout
        self._bot = bot
        self._settings = settings

        self._chatids_events: Dict[int, Event] = dict()
        self._chatids_counter = Counter()
        self._chatids_counter_lock = Lock()

    def start(self, chat_id: int):
        """Register a 'start' Action for a chat.
        If no action was currently running for the chat, start it.
        In all cases, increase the counter for the chat."""
        do_start = False
        with self._chatids_counter_lock:
            if self._chatids_counter[chat_id] == 0:
                do_start = True
            self.increase(chat_id)

        if do_start:
            # run the start outside the counter lock
            self._start_action_thread(chat_id)

    def stop(self, chat_id: int):
        """Register a 'stop' Action for a chat.
        Decrease the counter; if just one action was running for the chat, stop it."""
        do_stop = False
        with self._chatids_counter_lock:
            if self._chatids_counter[chat_id] != 0:
                if self.decrease(chat_id) == 0:
                    do_stop = True

        if do_stop:
            # run the stop outside the counter lock
            self._stop_action_thread(chat_id)

    def increase(self, chat_id: int) -> int:
        """Increase the request counter for a chat, and return the new value.
        The counter access should be locked while calling this method."""
        self._chatids_counter[chat_id] += 1
        return self._chatids_counter[chat_id]

    def decrease(self, chat_id: int) -> int:
        """Decrease the request counter for a chat, and return the new value.
        If the new value is 0, remove the referenced that from the Counter.
        The counter access should be locked while calling this method."""
        self._chatids_counter[chat_id] -= 1

        current = self._chatids_counter[chat_id]
        if current < 0:
            current = 0
        if current == 0:
            del self._chatids_counter[chat_id]

        return current

    def _start_action_thread(self, chat_id: int):
        """Start the action thread. The chat_id MUST not be currently running any actions."""
        event = Event()
        self._chatids_events[chat_id] = event
        request_id = get_request_id()

        Thread(
            target=self._action_worker,
            kwargs=dict(
                request_id=request_id,
                chat_id=chat_id,
                event=event,
            ),
            name=f"TelegramBot-ActionWorker-{self._action}-{chat_id}",
            daemon=True
        ).start()

    def _stop_action_thread(self, chat_id: int):
        """Stop the action thread for a chat_id. The chat_id MUST be currently running an action."""
        event = self._chatids_events.pop(chat_id, None)
        if event:
            event.set()

    def _action_worker(self, request_id: str, chat_id: int, event: Event):
        with logger.contextualize(request_id=request_id, chat_id=chat_id, chat_action=self._action):
            start = time.time()
            while not event.is_set():
                try:
                    logger.trace("Sending chat action...")
                    self._bot.send_chat_action(
                        chat_id=chat_id,
                        action=self._action,
                    )
                    logger.debug("Chat action sent")

                except Exception as ex:
                    if exception_is_bot_blocked_by_user(ex):
                        logger.info("Bot blocked by user, stopping chat action")
                        self._stop_action_thread(chat_id)
                        return
                    logger.opt(exception=ex).warning("Chat action failed delivery")

                elapsed = time.time() - start
                if elapsed >= self._timeout:
                    logger.bind(elapsed_time_seconds=round(elapsed, 3)).warning("Chat action timed out")
                    self._stop_action_thread(chat_id)
                    return

                event.wait(4.5)

            logger.debug("Chat action finalized")
