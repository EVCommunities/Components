# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>

import asyncio
from typing import Any, cast, Set, Union

from tools.components import AbstractSimulationComponent
from tools.exceptions.messages import MessageError
from tools.messages import BaseMessage
from tools.tools import FullLogger, load_environmental_variables, log_exception

from messages.car_metadata_message import CarMetaDataMessage
from messages.StationState_message import StationStateMessage
from messages.user_state_message import UserStateMessage
from messages.PowerRequirement_message import PowerRequirementMessage
from messages.car_state_message import CarStateMessage

LOGGER = FullLogger(__name__)

# set the names of the used environment variables to Python variables
USER_ID = "USER_ID"
USER_NAME = "USER_NAME"
STATION_ID = "STATION_ID"
STATE_OF_CHARGE = "STATE_OF_CHARGE"
CAR_BATTERY_CAPACITY = "CAR_BATTERY_CAPACITY"
CAR_MODEL = "CAR_MODEL"
CAR_MAX_POWER = "CAR_MAX_POWER"
TARGET_STATE_OF_CHARGE = "TARGET_STATE_OF_CHARGE"
TARGET_TIME = "TARGET_TIME"
MAX_POWER = "MAX_POWER"

USER_STATE_TOPIC = "USER_STATE_TOPIC"
CAR_STATE_TOPIC = "CAR_STATE_TOPIC"
CAR_METADATA_TOPIC = "CAR_METADATA_TOPIC"
STATION_STATE_TOPIC = "STATION_STATE_TOPIC"
POWER_OUTPUT_TOPIC = "POWER_OUTPUT_TOPIC"
POWER_REQUIREMENT_TOPIC = "POWER_REQUIREMENT_TOPIC"

TIMEOUT = 1.0

class ICComponent(AbstractSimulationComponent):
    # The constructor for the component class.
    def __init__(
        self,
        users: list,
        stations: list
        ):

        # Initialize the AbstractSimulationComponent using the values from the environmental variables.
        # This will initialize various variables including the message client for message bus access.    
        
        super().__init__()

        # Set the object variables for the extra parameters.
        self._users = users
        self._stations= stations
        self._car_metadata_received = False
        self._station_state_received = False
        self._user_state_received = False
        self._car_state_received = False

        # Add checks for the parameters if necessary
        # and set initialization error if there is a problem with the parameters.
        # if <some_check_for_the_parameters>:
        #     # add appropriate error message
        #     self.initialization_error = "There was a problem with the parameters"
        #     LOGGER.error(self.initialization_error)

        # variables to keep track of the components that have provided input within the current epoch
        # and to keep track of the current sum of the input values


        # Load environmental variables for those parameters that were not given to the constructor.
        # In this template the used topics are set in this way with given default values as an example.
        # fix topic names
        
        environment = load_environmental_variables(
            (POWER_REQUIREMENT_TOPIC, str, "PowerRequirementTopic")
        )

        self._power_requirement_topic = cast(str, environment[POWER_REQUIREMENT_TOPIC])

        #recieve topic
        self._other_topics = [
            "Init.User.CarMetadata",
            "User.UserState",
            "User.CarState",
            "StationStateTopic"
        ]

        if self.start_message is not None:
            LOGGER.info("START MESSAGE")
            LOGGER.info(self.start_message.get("ProcessParameters", {}).get("UserComponent", {}).keys())
            LOGGER.info(self.start_message.get("ProcessParameters", {}).get("StationComponent", {}).keys())

    def clear_epoch_variables(self) -> None:
        """Clears all the variables that are used to store information about the received input within the
           current epoch. This method is called automatically after receiving an epoch message for a new epoch.
           NOTE: this method should be overwritten in any child class that uses epoch specific variables
        """
    async def process_epoch(self) -> bool:
        """
        Process the epoch and do all the required calculations.
        Assumes that all the required information for processing the epoch is available.
        Returns False, if processing the current epoch was not yet possible.
        Otherwise, returns True, which indicates that the epoch processing was fully completed.
        This also indicated that the component is ready to send a Status Ready message to the Simulation Manager.
        NOTE: this method should be overwritten in any child class.
        TODO: add proper description specific for this component.
        """
        # Modify with Conditions
        ## Add the send message functions
        
        # TODO : Implement logic for sending messages

        #Modify
        # return True to indicate that the component is finished with the current epoch
        return False

    async def all_messages_received_for_epoch(self) -> bool:
        return True

    async def general_message_handler(self, message_object: Union[BaseMessage, Any], message_routing_key: str) -> None:

        LOGGER.info("message handler.")
        if isinstance(message_object, CarMetaDataMessage):
            message_object = cast(CarMetaDataMessage, message_object)
            self._car_metadata_received = True
        elif isinstance(message_object, StationStateMessage):
            message_object = cast(StationStateMessage, message_object)
            self._station_state_received = True
        elif isinstance(message_object, UserStateMessage):
            message_object = cast(UserStateMessage, message_object)
            self._user_state_received = True
        elif isinstance(message_object, CarStateMessage):
            message_object = cast(CarStateMessage, message_object)
            self._car_state_received = True
        else:
            LOGGER.debug("Received unknown message from {message_routing_key}: {message_object}")


    async def _send_power_requirement_message(self):
        LOGGER.info("power requirement message sent")
        try:
            power_requirement_message = self._message_generator.get_message(
                PowerRequirementMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                #TODO: implement station id logic
                StationId=1,
                TargetTime=self._target_time
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._power_requirement_topic,
                message_bytes= power_requirement_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating result message.")

# TODO: Implement create and start component