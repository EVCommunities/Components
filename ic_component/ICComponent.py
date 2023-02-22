# Copyright 2023 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>
#            Ville Heikkilä <ville.heikkila@tuni.fi>

import asyncio
from datetime import datetime, timedelta
from typing import Any, cast, List, Optional, Union

from tools.components import AbstractSimulationComponent
from tools.exceptions.messages import MessageError
from tools.messages import BaseMessage
from tools.tools import FullLogger, load_environmental_variables, log_exception
from tools.datetime_tools import to_utc_datetime_object

from ic_component.energy_check import EnergyCheck
from ic_component.power_info import PowerInfo
from ic_component.station_data import StationData
from ic_component.user_data import UserData
from messages.car_metadata_message import CarMetaDataMessage
from messages.StationState_message import StationStateMessage
from messages.user_state_message import UserStateMessage
from messages.PowerRequirement_message import PowerRequirementMessage
from messages.car_state_message import CarStateMessage
from messages.requirements_warning_message import RequirementsWarningMessage

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
MAX_POWER = "MAX_POWER"
TOTAL_MAX_POWER = "TOTAL_MAX_POWER"

USER_STATE_TOPIC = "USER_STATE_TOPIC"
CAR_STATE_TOPIC = "CAR_STATE_TOPIC"
CAR_METADATA_TOPIC = "CAR_METADATA_TOPIC"
STATION_STATE_TOPIC = "STATION_STATE_TOPIC"
POWER_OUTPUT_TOPIC = "POWER_OUTPUT_TOPIC"
POWER_REQUIREMENT_TOPIC = "POWER_REQUIREMENT_TOPIC"
REQUIREMENTS_WARNING_TOPIC = "REQUIREMENTS_WARNING_TOPIC"

TIMEOUT = 1.0

class ICComponent(AbstractSimulationComponent):
    # The constructor for the component class.
    def __init__(
        self,
        total_max_power: float
    ):

        # Initialize the AbstractSimulationComponent using the values from the environmental variables.
        # This will initialize various variables including the message client for message bus access.

        super().__init__()

        # Set the object variables for the extra parameters.
        self._users: List[UserData] = []
        self._stations: List[StationData] = []
        self._total_max_power = total_max_power

        self._total_user_count = 0
        self._total_station_count = 0

        self._car_metadata_received = False
        self._station_state_received = False
        self._user_state_received = False
        self._car_state_received = False
        self._power_requirement_message_sent = False

        self._epoch_car_metadata_count = 0
        self._epoch_station_state_count = 0
        self._epoch_user_state_count = 0
        self._epoch_car_state_count = 0
        self._used_total_power = 0.0

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
            (POWER_REQUIREMENT_TOPIC, str, "PowerRequirementTopic"),
            (REQUIREMENTS_WARNING_TOPIC, str, "Requirements.Warning")
        )

        self._power_requirement_topic = cast(str, environment[POWER_REQUIREMENT_TOPIC])
        self._requirements_warning_topic = cast(str, environment[REQUIREMENTS_WARNING_TOPIC])

        # receive topic
        self._other_topics = [
            "Init.User.CarMetadata",
            "User.UserState",
            "User.CarState",
            "StationStateTopic"
        ]

        if self.start_message is not None:
            users = self.start_message.get('ProcessParameters', {}).get('UserComponent', {}).keys()
            stations = self.start_message.get('ProcessParameters', {}).get('StationComponent', {}).keys()
            LOGGER.info("START MESSAGE")
            LOGGER.info(f"Users: {users}")
            LOGGER.info(f"Stations: {stations}")
            self._total_user_count = len(users)
            self._total_station_count = len(stations)

    def clear_epoch_variables(self) -> None:
        """Clears all the variables that are used to store information about the received input within the
           current epoch. This method is called automatically after receiving an epoch message for a new epoch.
           NOTE: this method should be overwritten in any child class that uses epoch specific variables
        """
        self._epoch_station_state_count = 0
        self._epoch_user_state_count = 0
        self._epoch_car_state_count = 0
        self._used_total_power = 0.0

        self._station_state_received = False
        self._user_state_received = False
        self._car_state_received = False
        self._power_requirement_message_sent = False
        self._stations = []

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
        LOGGER.info(f"TOTAL AVAILABLE POWER: {self._total_max_power}")
        LOGGER.info("Process epoch")
        LOGGER.info(f"metadata count: {self._epoch_car_metadata_count}")
        LOGGER.info(f"total user count: {self._total_user_count}")

        if self._epoch_car_metadata_count == self._total_user_count:
            self._car_metadata_received = True
            LOGGER.info(f"All Car Metadata Received: {self._car_metadata_received}")

        if self._epoch_station_state_count == self._total_station_count:
            self._station_state_received = True
            LOGGER.info(f"All Station State Received: {self._stations}")

        if self._epoch_user_state_count == self._total_user_count:
            self._user_state_received = True
            LOGGER.info("All User State Received")

        if not self._power_requirement_message_sent and (
            self._car_metadata_received and self._station_state_received and self._user_state_received
        ):
            await self._send_power_requirement_message()
            self._power_requirement_message_sent = True

        if self._epoch_car_state_count == self._total_user_count:
            self._car_state_received = True

        return self._power_requirement_message_sent and self._car_state_received

    async def all_messages_received_for_epoch(self) -> bool:
        return True

    async def general_message_handler(self, message_object: Union[BaseMessage, Any], message_routing_key: str) -> None:
        LOGGER.info("message handler.")

        if isinstance(message_object, CarMetaDataMessage):
            message_object = cast(CarMetaDataMessage, message_object)
            carMetaDatainfo = UserData(
                user_id=message_object.user_id,
                user_name=message_object.user_name,
                user_component_name=message_object.source_process_id,
                station_id=message_object.station_id,
                state_of_charge=message_object.state_of_charge,
                car_battery_capacity=message_object.car_battery_capacity,
                car_model=message_object.car_model,
                car_max_power=message_object.car_max_power
            )
            if carMetaDatainfo.user_id in [user.user_id for user in self._users]:
                LOGGER.warning(f"Received second metadata for user {carMetaDatainfo.user_id}")
                return

            self._users.append(carMetaDatainfo)
            LOGGER.info(f"Number of users with metadata: {len(self._users)}")
            self._epoch_car_metadata_count = self._epoch_car_metadata_count + 1
            await self.start_epoch()

        elif isinstance(message_object, StationStateMessage):
            message_object = cast(StationStateMessage, message_object)
            stationInfo = StationData(
                station_id=message_object.station_id,
                max_power=message_object.max_power
            )
            if stationInfo.station_id in [station.station_id for station in self._stations]:
                LOGGER.warning(f"Received second data for station {stationInfo.station_id}")
                return

            self._stations.append(stationInfo)
            LOGGER.info(f"Number of stations with data: {len(self._stations)}")
            self._epoch_station_state_count = self._epoch_station_state_count + 1
            await self.start_epoch()

        elif isinstance(message_object, UserStateMessage):
            message_object = cast(UserStateMessage, message_object)
            LOGGER.info(f"user state: {message_object}")
            LOGGER.info(f"USER STATE MESSAGE: {self._user_state_received}")

            if message_object.user_id not in [user.user_id for user in self._users]:
                LOGGER.error(f"Received an user state message for a user without metadata: {message_object.user_id}")
                # TODO: figure out what to do in this case:
                return

            for user in self._users:
                if user.user_id == message_object.user_id:
                    user.target_state_of_charge = message_object.target_state_of_charge
                    user.target_time = message_object.target_time
                    user.arrival_time = message_object.arrival_time
                    user.required_energy = user.car_battery_capacity * (user.target_state_of_charge - user.state_of_charge) / 100
                    LOGGER.info(str(user))
                    break

            self._epoch_user_state_count = self._epoch_user_state_count + 1
            await self.start_epoch()

        elif isinstance(message_object, CarStateMessage):
            message_object = cast(CarStateMessage, message_object)
            LOGGER.info(f"car state: {message_object}")

            if message_object.user_id not in [user.user_id for user in self._users]:
                LOGGER.error(f"Received a car state message for a user without data: {message_object.user_id}")
                # TODO: figure out what to do in this case:
                return

            for user in self._users:
                if user.user_id == message_object.user_id:
                    user.state_of_charge = message_object.state_of_charge
                    break

            LOGGER.info(f"car_state_received: {self._car_state_received}")
            self._epoch_car_state_count = self._epoch_car_state_count + 1
            await self.start_epoch()

        else:
            LOGGER.debug(f"Received unknown message from {message_routing_key}: {message_object}")

    async def _send_power_requirement_message(self):
        LOGGER.info("power requirement message initiated")
        connected_users: List[UserData] = []

        if self._latest_epoch_message is None:
            await self.send_error_message("Tried to calculate power distribution before any epoch messages had arrived")
            return
        start_time = to_utc_datetime_object(self._latest_epoch_message.start_time)
        end_time = to_utc_datetime_object(self._latest_epoch_message.end_time)
        epoch_length = (end_time - start_time).seconds

        # check if all user requirements can be fulfilled
        energy_check = self._calculate_energy_check()
        LOGGER.info(f"Energy check: {energy_check}")
        if (
            energy_check is not None and
            len(energy_check.affected_users) > 0 and
            energy_check.total_available_energy < energy_check.total_required_energy and
            energy_check.total_required_energy > 0.0
        ):
            energy_percentage = 100 * energy_check.total_available_energy / energy_check.total_required_energy
            LOGGER.info(f"Sending a requirements warning message: {energy_percentage}")
            await self._send_warning_message(
                energy_percentage=energy_percentage,
                users=energy_check.affected_users
            )
            # for now, after sending the warning message just continue as normal

        for user in self._users:
            arrival_time = to_utc_datetime_object(user.arrival_time)
            target_time = to_utc_datetime_object(user.target_time)
            if start_time >= arrival_time and end_time <= target_time:
                connected_users.append(user)
        connected_users = sorted(connected_users, key=lambda user: (user.target_time, -user.required_energy))
        LOGGER.info(f"Connected_users: {connected_users}")

        power_requirements = self._calculate_power_requirements(connected_users, start_time)

        for power_info in power_requirements:
            powerRequirementForStation = float(0.0)
            LOGGER.info(f"POWER REQ: {power_info}")

            if power_info.user_id != 0:
                if self._used_total_power < self._total_max_power:
                    LOGGER.info("IN CONDITION")
                    LOGGER.info("EPOCH MESSAGE")
                    LOGGER.info("START TIME")
                    LOGGER.info(f"epoch_length: {epoch_length}")

                    if power_info.target_state_of_charge > power_info.state_of_charge:
                        powerRequirementForStation = min(
                            power_info.station_max_power,
                            power_info.car_max_power,
                            self._total_max_power - self._used_total_power,
                            power_info.required_energy / (epoch_length / 3600)
                        )
                        self._used_total_power = self._used_total_power + powerRequirementForStation
                    LOGGER.info(f"power to station '{power_info.station_id}': {powerRequirementForStation}")

            await self._send_single_power_requirement_message(power_info, powerRequirementForStation)

        LOGGER.info(f"Allocated {self._used_total_power} power (maximum: {self._total_max_power}) in epoch {self._latest_epoch}")

    def _calculate_power_requirements(self, connected_users: List[UserData], start_time: datetime):
        """Calculates and returns the power requirements for each station."""
        power_requirements: List[PowerInfo] = []
        empty_power_requirements: List[PowerInfo] = []

        for station in self._stations:
            LOGGER.info(f"STATION LOGGER: {station}")
            isConnected = False
            for user in connected_users:
                if user.station_id == station.station_id:
                    isConnected = True
                    LOGGER.info(str(start_time))
                    LOGGER.info(str(user.arrival_time))
                    powerInfo = PowerInfo(
                        user_id=user.user_id,
                        station_id=user.station_id,
                        station_max_power=station.max_power,
                        car_max_power=user.car_max_power,
                        state_of_charge=user.state_of_charge,
                        target_state_of_charge=user.target_state_of_charge,
                        required_energy=user.required_energy,
                        target_time=user.target_time
                    )
                    power_requirements.append(powerInfo)
            if not isConnected:
                empty_power_requirements.append(PowerInfo(user_id=0, station_id=station.station_id))

        power_requirements = sorted(power_requirements, key=lambda power_info: (power_info.target_time, -power_info.required_energy))
        LOGGER.info(f"power_requirements: {power_requirements}")

        power_requirements = power_requirements + empty_power_requirements
        LOGGER.info(f"power_requirements: {power_requirements}")

        return power_requirements

    async def _send_single_power_requirement_message(self, power_info: PowerInfo, power_requirement: float) -> None:
        """Publishes one power requirement message."""
        try:
            power_requirement_message = self._message_generator.get_message(
                PowerRequirementMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                StationId = power_info.station_id,
                UserId = power_info.user_id,
                Power = power_requirement
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._power_requirement_topic,
                message_bytes= power_requirement_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating result message.")

    async def _send_warning_message(self, energy_percentage: float, users: List[str]) -> None:
        """Publishes requirements warning message."""
        try:
            requirements_warning_message = self._message_generator.get_message(
                RequirementsWarningMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                AvailableEnergy=energy_percentage,
                AffectedUsers=users
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._requirements_warning_topic,
                message_bytes= requirements_warning_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            log_exception(message_error)
            await self.send_error_message("Internal error when creating requirements warning message.")

    def _calculate_energy_check(self) -> Optional[EnergyCheck]:
        """Calculates and returns the required and available energy for the rest of the simulation."""
        if self._latest_epoch_message is None:
            return None

        total_available_energy: float = 0.0
        current_start_time = to_utc_datetime_object(self._latest_epoch_message.start_time)
        end_time = to_utc_datetime_object(self._latest_epoch_message.end_time)
        epoch_length = (end_time - current_start_time).seconds
        # the following assumes the target times are in ISO-8601 string format
        latest_target_time = to_utc_datetime_object(max([user.target_time for user in self._users]))

        while current_start_time < latest_target_time:
            p_tot_epoch: float = 0.0
            current_end_time = current_start_time + timedelta(seconds=epoch_length)
            for user in self._users:
                # only include users who are connected to a station the entire epoch
                if (
                    to_utc_datetime_object(user.arrival_time) <= current_start_time and
                    to_utc_datetime_object(user.target_time) >= current_end_time
                ):
                    p_tot_epoch += min(user.car_max_power, self._get_station_max_power(user.station_id))

            total_available_energy += (epoch_length / 3600) * min(self._total_max_power, p_tot_epoch)
            current_start_time = current_end_time

        # determine user as affected if they are currently at a station and are not yet at their target capacity
        return EnergyCheck(
            total_available_energy=total_available_energy,
            total_required_energy=sum([user.required_energy for user in self._users]),
            affected_users=[
                user.user_component_name
                for user in self._users
                if (
                    user.arrival_time <= self._latest_epoch_message.start_time and
                    user.target_time >= self._latest_epoch_message.end_time and
                    user.state_of_charge < user.target_state_of_charge
                )
            ]
        )

    def _get_station_max_power(self, station_id: str) -> float:
        station_power = [
            station.max_power
            for station in self._stations
            if station.station_id == station_id
        ]
        if station_power:
            return station_power[0]
        return 0.0


def create_component() -> ICComponent:
    LOGGER.info("create IC component")
    environment_variables = load_environmental_variables(
        (TOTAL_MAX_POWER, float, 0.0)
    )
    total_max_power = cast(float, environment_variables[TOTAL_MAX_POWER])

    return ICComponent(
        total_max_power = total_max_power
    )


async def start_component():
    """
    Creates and starts a IC component.
    """
    # A general exception handler that should catch any unhandled error that would otherwise crash the program.
    # Having this might be especially useful when testing components in large simulations and some component(s)
    # crash without giving any output.
    #
    # Note, that any exceptions thrown in async functions will not be caught here.
    # Instead they should get logged as warnings but otherwise should not crash the component.
    try:
        LOGGER.debug("start ic component")
        ic_component = create_component()

        # The component will only start listening to the message bus once the start() method has been called.
        await ic_component.start()

        # Wait in the loop until the component has stopped itself.
        while not ic_component.is_stopped:
            await asyncio.sleep(TIMEOUT)

    except BaseException as error:  # pylint: disable=broad-except
        log_exception(error)
        LOGGER.info("Component will now exit.")


if __name__ == "__main__":
    asyncio.run(start_component())
