# Copyright 2022 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>

import asyncio
from typing import Any, cast, Union

from tools.components import AbstractSimulationComponent
from tools.exceptions.messages import MessageError
from tools.messages import BaseMessage
from tools.tools import FullLogger, load_environmental_variables, log_exception
from tools.datetime_tools import to_utc_datetime_object

# import all the required messages from installed libraries
from messages.car_metadata_message import CarMetaDataMessage
from messages.car_state_message import CarStateMessage
from messages.user_state_message import UserStateMessage
from messages.PowerOutput_message import PowerOutputMessage
from messages.requirements_warning_message import RequirementsWarningMessage


# initialize logging object for the module
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
ARRIVAL_TIME = "ARRIVAL_TIME"


USER_STATE_TOPIC = "USER_STATE_TOPIC"
CAR_STATE_TOPIC = "CAR_STATE_TOPIC"
CAR_METADATA_TOPIC = "CAR_METADATA_TOPIC"
REQUIREMENTS_WARNING_TOPIC = "REQUIREMENTS_WARNING_TOPIC"


# time interval in seconds on how often to check whether the component is still running
TIMEOUT = 1.0


class UserComponent(AbstractSimulationComponent):
    # The constructor for the component class.
    def __init__(
        self,
        user_id: int,
        user_name: str,
        station_id: str,
        state_of_charge: float,
        car_battery_capacity: float,
        car_model: str,
        car_max_power: float,
        target_state_of_charge: float,
        target_time: str,
        arrival_time: str
    ):

        # Initialize the AbstractSimulationComponent using the values from the environmental variables.
        # This will initialize various variables including the message client for message bus access.
        super().__init__()

        # Set the object variables for the extra parameters.
        self._user_id = user_id
        self._user_name = user_name
        self._station_id = station_id
        self._state_of_charge = state_of_charge
        self._car_battery_capacity = car_battery_capacity
        self._car_model = car_model
        self._car_max_power = car_max_power
        self._target_state_of_charge = target_state_of_charge
        self._target_time = target_time
        self._arrival_time = arrival_time

        self._car_metadata_sent = False
        self._user_state_sent = False
        self._power_output_received = False
        self._car_state_sent = False

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
            (USER_STATE_TOPIC, str, "User.UserState"),
            (CAR_STATE_TOPIC, str, "User.CarState"),
            (CAR_METADATA_TOPIC, str, "Init.User.CarMetadata"),
            (REQUIREMENTS_WARNING_TOPIC, str, "Requirements.Warning")
        )

        self._user_state_topic = cast(str, environment[USER_STATE_TOPIC])
        self._car_state_topic = cast(str, environment[CAR_STATE_TOPIC])
        self._car_metadata_topic = cast(str, environment[CAR_METADATA_TOPIC])
        self._requirements_warning_topic = cast(str, environment[REQUIREMENTS_WARNING_TOPIC])

        # The easiest way to ensure that the component will listen to all necessary topics
        # is to set the self._other_topics variable with the list of the topics to listen to.
        # Note, that the "SimState" and "Epoch" topic listeners are added automatically by the parent class.

        # receive topic
        self._other_topics = [
            "PowerOutputTopic",
            self._requirements_warning_topic
        ]

        # The base class contains several variables that can be used in the child class.
        # The variable list below is not an exhaustive list but contains the most useful variables.

        if self.start_message is not None:
            LOGGER.info("START MESSAGE")
            LOGGER.info(str(self.start_message.get("ProcessParameters", {}).get("UserComponent", {}).keys()))

        # Variables that should only be READ in the child class:
        # - self.simulation_id               the simulation id
        # - self.component_name              the component name
        # - self._simulation_state           either "running" or "stopped"
        # - self._latest_epoch               epoch number for the current epoch
        # - self._completed_epoch            epoch number for the latest epoch that has been completed
        # - self._latest_epoch_message       the latest epoch message as EpochMessage object

        # Variable for the triggering message ids where all relevant message ids should be appended.
        # The list is automatically cleared at the start of each epoch.
        # - self._triggering_message_ids

        # MessageGenerator object that can be used to generate the message objects:
        # - self._message_generator

        # RabbitmqClient object for communicating with the message bus:
        # - self._rabbitmq_client

    def clear_epoch_variables(self) -> None:
        """Clears all the variables that are used to store information about the received input within the
           current epoch. This method is called automatically after receiving an epoch message for a new epoch.
           NOTE: this method should be overwritten in any child class that uses epoch specific variables
        """
        self._user_state_sent = False
        self._car_state_sent = False
        self._power_output_received = False

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
        if not self._car_metadata_sent and self._latest_epoch == 1:
            await self._send_car_metadata_message()
            self._car_metadata_sent = True

        if not self._user_state_sent:
            await self._send_user_state_message()
            self._user_state_sent = True

            if self._latest_epoch_message is not None:  # this should always be True when we are here
                LOGGER.info(f"current epoch: {self._latest_epoch_message.start_time} - {self._latest_epoch_message.end_time}")
                LOGGER.info(f"car at station: {self._arrival_time} - {self._target_time}")
                if (
                    to_utc_datetime_object(self._latest_epoch_message.end_time) <= to_utc_datetime_object(self._arrival_time) or
                    to_utc_datetime_object(self._latest_epoch_message.start_time) >= to_utc_datetime_object(self._target_time)
                ):
                    LOGGER.info("Not in a station => setting power_output_received to True")
                    self._power_output_received = True

        if self._power_output_received and not self._car_state_sent:
            await self._send_car_state_message()
            self._car_state_sent = True

        # return True to indicate that the component is finished with the current epoch
        return self._user_state_sent and self._car_state_sent


    async def all_messages_received_for_epoch(self) -> bool:
        return True


    async def general_message_handler(self, message_object: Union[BaseMessage, Any], message_routing_key: str) -> None:

        LOGGER.info("message handler.")
        if isinstance(message_object, PowerOutputMessage):
            LOGGER.info("message handler.")
            message_object = cast(PowerOutputMessage, message_object)

            LOGGER.info(str(message_object))
            LOGGER.info(message_object.station_id)
            LOGGER.info(self._station_id)
            if message_object.station_id == self._station_id and message_object.user_id == self._user_id:
                if self._latest_epoch_message is None:
                    await self.send_error_message("Got PowerOutputMessage but there is no latest epoch message")
                    return
                if self._power_output_received:
                    LOGGER.warning(f"Already received PowerOutputMessage. Ignoring message from {message_object.source_process_id}")
                    return

                LOGGER.debug(f"Received PowerOutputMessage from {message_object.source_process_id}")
                epoch_length = (to_utc_datetime_object(self._latest_epoch_message.end_time) - to_utc_datetime_object(self._latest_epoch_message.start_time)).seconds
                LOGGER.info(f"epoch length: {epoch_length}")
                original_energy = (self._car_battery_capacity * self._state_of_charge) / 100  # in kWh
                LOGGER.info(f"ORIGINAL ENERGY: {original_energy}")
                new_energy = (message_object.power_output * epoch_length) / 3600  # in kWh
                LOGGER.info(f"New ENERGY: {new_energy}")
                new_total_energy = original_energy + new_energy
                LOGGER.info(f"New TOTAL ENERGY: {new_total_energy}")
                new_soc = (new_total_energy / self._car_battery_capacity) * 100
                new_soc = min(new_soc, 100.0)
                LOGGER.info(f"New SOC: {new_soc}")
                self._state_of_charge = new_soc
                LOGGER.info("PowerOUTPUT message processed")
                self._power_output_received = True
                await self.start_epoch()
            else:
                LOGGER.debug(f"Ignoring PowerOutputMessage from {message_object.source_process_id}")

        elif isinstance(message_object, RequirementsWarningMessage):
            LOGGER.info(
                f"Received requirements warning message: only {round(message_object.available_energy, 2)}%" +
                " of the required energy is available"
            )
            if (
                self._latest_epoch_message is not None and
                (
                    self._latest_epoch_message.end_time <= self._arrival_time or
                    self._latest_epoch_message.start_time >= self._target_time
                )
            ):
                LOGGER.info("Ignoring warning message due to not being at a charging station")
            elif self.component_name not in message_object.affected_users:
                LOGGER.info("I am not affected by the warning, so I am satisfied and will do nothing!")
            else:
                LOGGER.info("I am affected by the warning, I should probably do something!!")
                # TODO: add some kind of actual reaction to this case: requirements change? negotiations?

        else:
            LOGGER.debug(f"Received unknown message from {message_routing_key}: {message_object}")

    async def _send_user_state_message(self):
        LOGGER.info("user state message sent")
        try:
            user_state_message = self._message_generator.get_message(
                UserStateMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                UserId=self._user_id,
                TargetStateOfCharge=self._target_state_of_charge,
                TargetTime=self._target_time,
                ArrivalTime=self._arrival_time
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._user_state_topic,
                message_bytes= user_state_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating user state message.")

    async def _send_car_state_message(self):
        LOGGER.info("car state message sent")
        try:
            car_state_message = self._message_generator.get_message(
                CarStateMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                UserId=self._user_id,
                StationId=self._station_id,
                StateOfCharge=self._state_of_charge
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._car_state_topic,
                message_bytes= car_state_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating car state message.")

    async def _send_car_metadata_message(self):
        LOGGER.info("car metadata message sent")
        try:
            car_metadata_message = self._message_generator.get_message(
                CarMetaDataMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                UserId=self._user_id,
                UserName=self._user_name,
                StationId=self._station_id,
                StateOfCharge=self._state_of_charge,
                CarBatteryCapacity=self._car_battery_capacity,
                CarModel=self._car_model,
                CarMaxPower=self._car_max_power
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._car_metadata_topic,
                message_bytes= car_metadata_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating car metadata message.")

def create_component() -> UserComponent:
    """
    TODO: add proper description specific for this component.
    """
    LOGGER.info("create user component")
    # Read the parameters for the component from the environment variables.
    environment_variables = load_environmental_variables(
        (USER_ID, int, 0),
        (USER_NAME, str, ""),
        (STATION_ID, str, ""),
        (STATE_OF_CHARGE, float, 0.0),
        (CAR_BATTERY_CAPACITY, float, 0.0),
        (CAR_MODEL, str, ""),
        (CAR_MAX_POWER, float, 0.0),
        (TARGET_STATE_OF_CHARGE, float, 0.0),
        (TARGET_TIME, str, ""),
        (ARRIVAL_TIME, str, "")
    )


    # The cast function here is only used to help Python linters like pyright to recognize the proper type.
    # They are not necessary and can be omitted.
    user_id = cast(int, environment_variables[USER_ID])
    user_name = cast(str, environment_variables[USER_NAME])
    station_id = cast(str, environment_variables[STATION_ID])
    state_of_charge = cast(float, environment_variables[STATE_OF_CHARGE])
    car_battery_capacity = cast(float, environment_variables[CAR_BATTERY_CAPACITY])
    car_model = cast(str, environment_variables[CAR_MODEL])
    car_max_power = cast(float, environment_variables[CAR_MAX_POWER])
    target_state_of_charge = cast(float, environment_variables[TARGET_STATE_OF_CHARGE])
    target_time = cast(str, environment_variables[TARGET_TIME])
    arrival_time = cast(str, environment_variables[ARRIVAL_TIME])


    # Create and return a new SimpleComponent object using the values from the environment variables
    return UserComponent(
        user_id = user_id,
        user_name = user_name,
        station_id = station_id,
        state_of_charge = state_of_charge,
        car_battery_capacity = car_battery_capacity,
        car_model = car_model,
        car_max_power = car_max_power,
        target_state_of_charge = target_state_of_charge,
        target_time = target_time,
        arrival_time = arrival_time
    )

async def start_component():
    """
    Creates and starts a UserComponent component.
    """
    # A general exception handler that should catch any unhandled error that would otherwise crash the program.
    # Having this might be especially useful when testing components in large simulations and some component(s)
    # crash without giving any output.
    #
    # Note, that any exceptions thrown in async functions will not be caught here.
    # Instead they should get logged as warnings but otherwise should not crash the component.
    try:
        LOGGER.debug("start user component")
        user_component = create_component()

        # The component will only start listening to the message bus once the start() method has been called.
        await user_component.start()

        # Wait in the loop until the component has stopped itself.
        while not user_component.is_stopped:
            await asyncio.sleep(TIMEOUT)

    except BaseException as error:  # pylint: disable=broad-except
        log_exception(error)
        LOGGER.info("Component will now exit.")


if __name__ == "__main__":
    asyncio.run(start_component())
