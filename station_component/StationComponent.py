# Copyright 2022 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Chalith Haputhantrige <chalith.haputhantrige@tuni.fi>

import asyncio
import traceback
import random
from typing import Any, cast, Set, Optional, Union

from tools.components import AbstractSimulationComponent
from tools.exceptions.messages import MessageError
from tools.messages import BaseMessage
from tools.tools import FullLogger, load_environmental_variables, log_exception

from messages.StationState_message import StationStateMessage
from messages.PowerOutput_message import PowerOutputMessage
from messages.PowerRequirement_message import PowerRequirementMessage


LOGGER = FullLogger(__name__)

STATION_ID = "STATION_ID"
MAX_POWER = "MAX_POWER"
INPUT_COMPONENTS = "INPUT_COMPONENTS"

STATION_STATE_TOPIC = "STATION_STATE_TOPIC"
POWER_OUTPUT_TOPIC = "POWER_OUTPUT_TOPIC"

TIMEOUT = 1.0

class StationComponent(AbstractSimulationComponent):


    def __init__(self,station_id: str, max_power:int):
        
        super().__init__()

        self._station_id = station_id
        self._max_power = max_power


        self._station_state = False
        self._power_requirement_recevied = False
        self._power_required = None
        self._power_output = 0.0

    
        environment = load_environmental_variables(
            (STATION_STATE_TOPIC, str, "StationStateTopic"),
             (POWER_OUTPUT_TOPIC, str, "PowerOutputTopic")
        )
        self._station_state_topic = cast(str, environment[STATION_STATE_TOPIC])
        self._power_output_topic = cast(str, environment[POWER_OUTPUT_TOPIC])

        # The easiest way to ensure that the component will listen to all necessary topics
        # is to set the self._other_topics variable with the list of the topics to listen to.
        # Note, that the "SimState" and "Epoch" topic listeners are added automatically by the parent class.
        self._other_topics = ["PowerRequirementTopic"]


    def clear_epoch_variables(self) -> None:
        self._station_state = False
        self._power_requirement_recevied = False
        self._power_required = None

    async def process_epoch(self) -> bool:

        if not (self._station_state):
            await self._send_stationstate_message()
            self._station_state = True

        if (self._power_requirement_recevied):
            await self._send_poweroutput_message()
            return True
        
        return False
        

    
    async def _send_stationstate_message(self):
        """
        Sends a intial station state  message to the IC
        """
        try:
            stationstate_message = self._message_generator.get_message(
                StationStateMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                StationId=self._station_id,
                MaxPower=self._max_power
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._station_state_topic,
                message_bytes=stationstate_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating result message.")

    async def _send_poweroutput_message(self):
        """
        Sends a powerout message to given user topic
        """
        try:
            poweroutput_message = self._message_generator.get_message(
                PowerOutputMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                StationId=self._station_id,
                PowerOutput=self._power_output
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._power_output_topic,
                message_bytes=poweroutput_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating result message.")

    async def all_messages_received_for_epoch(self) -> bool:
        return True

    async def general_message_handler(self, message_object: Union[BaseMessage, Any],
                                      message_routing_key: str) -> None:
        LOGGER.info("message handler.")
        if isinstance(message_object, PowerRequirementMessage):
            message_object = cast(PowerRequirementMessage, message_object)
            LOGGER.info(message_object)
            if(message_object.station_id == self._station_id):
                LOGGER.debug(f"Received PowerRequirementMessage from {message_object.source_process_id}")
                self._power_output = float(message_object.power)
                self._power_requirement_recevied = True
                await self.start_epoch()
            else:
                LOGGER.debug(f"Ignoring PowerRequirementMessage from {message_object.source_process_id}")
        else:
            LOGGER.debug("Received unknown message from {message_routing_key}: {message_object}")


def create_component() -> StationComponent:

    LOGGER.debug("create")
    environment_variables = load_environmental_variables(
        (STATION_ID, str, ""),  
        (MAX_POWER, str, "")  
    )
    station_id = cast(str, environment_variables[STATION_ID])
    max_power = cast(str, environment_variables[MAX_POWER])


    return StationComponent(
        station_id=station_id,
        max_power=max_power,
    )


async def start_component():
    try:
        LOGGER.debug("start")
        station_component = create_component()
        await station_component.start()

        while not station_component.is_stopped:
            await asyncio.sleep(TIMEOUT)

    except BaseException as error:  # pylint: disable=broad-except
        log_exception(error)
        LOGGER.info("Component will now exit.")




if __name__ == "__main__":
    asyncio.run(start_component())
