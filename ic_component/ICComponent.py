# Copyright 2022 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>

import asyncio
from typing import Any, cast, Set, Union
from operator import itemgetter

from tools.components import AbstractSimulationComponent
from tools.exceptions.messages import MessageError
from tools.messages import BaseMessage
from tools.tools import FullLogger, load_environmental_variables, log_exception
from tools.datetime_tools import to_utc_datetime_object

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
ARRIVAL_TIME = "ARRIVAL_TIME"
MAX_POWER = "MAX_POWER"
USERS = "USERS"
STATIONS = "STATIONS"
TOTAL_MAX_POWER = "TOTAL_MAX_POWER"

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
        stations: list,
        total_max_power: float
        ):

        # Initialize the AbstractSimulationComponent using the values from the environmental variables.
        # This will initialize various variables including the message client for message bus access.    
        
        super().__init__()

        # Set the object variables for the extra parameters.
        self._users = users
        self._stations = stations
        self._total_max_power = total_max_power

        self._total_user_count = 0
        self._total_station_count = 0

        self._car_metadata_received = False
        self._station_state_received = False
        self._user_state_received = False
        self._car_state_received = False

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
            LOGGER.info(len(self.start_message.get("ProcessParameters", {}).get("UserComponent", {}).keys()))
            LOGGER.info(len(self.start_message.get("ProcessParameters", {}).get("StationComponent", {}).keys()))
            self._total_user_count = len(self.start_message.get("ProcessParameters", {}).get("UserComponent", {}).keys())
            self._total_station_count = len(self.start_message.get("ProcessParameters", {}).get("StationComponent", {}).keys())

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
        LOGGER.info("TOTAL AVAILABLE POWER")
        LOGGER.info(self._total_max_power)
        LOGGER.info("Process epoch")
        LOGGER.info(self._epoch_car_metadata_count)
        LOGGER.info(self._total_user_count)
        if(self._epoch_car_metadata_count == self._total_user_count):
            self._car_metadata_received = True
            LOGGER.info("All Car Metadata Received")
            LOGGER.info(self._car_metadata_received)

        if(self._epoch_station_state_count == self._total_station_count and self._car_metadata_received == True):
            self._station_state_received = True
            LOGGER.info("All Station State Received")

        if(self._epoch_user_state_count == self._total_user_count and self._station_state_received == True):
            self._user_state_received = True
            LOGGER.info("All User State Received")
            await self._send_power_requirement_message()

        if(self._epoch_car_state_count == self._total_user_count and self._user_state_received == True):
            self._car_state_received = True
            return True
        

        #Modify
        # return True to indicate that the component is finished with the current epoch
        return False

    async def all_messages_received_for_epoch(self) -> bool:
        return True

    async def general_message_handler(self, message_object: Union[BaseMessage, Any], message_routing_key: str) -> None:

        LOGGER.info("message handler.")
        if isinstance(message_object, CarMetaDataMessage):
            message_object = cast(CarMetaDataMessage, message_object)
            carMetaDatainfo = { "userId": message_object.user_id, "userName": message_object.user_name, "stationId": message_object.station_id, "stateOfCharge": message_object.state_of_charge, "carBatteryCapacity": message_object.car_battery_capacity, "carModel": message_object.car_model, "carMaxPower": message_object.car_max_power}
            #carMetaDatainfo = (message_object.user_id, message_object.user_name, message_object.station_id, message_object.state_of_charge, message_object.car_battery_capacity, message_object.car_model, message_object.car_max_power)
            self._users.append(carMetaDatainfo)
            LOGGER.info(len(self._users))
            self._epoch_car_metadata_count = self._epoch_car_metadata_count + 1
            await self.start_epoch()
        elif isinstance(message_object, StationStateMessage):
            message_object = cast(StationStateMessage, message_object)
            stationInfo = { "stationId": message_object.station_id, "maxPower": message_object.max_power}
            #stationInfo = (message_object.station_id, message_object.max_power)
            self._stations.append(stationInfo)
            LOGGER.info(len(self._stations))
            self._epoch_station_state_count = self._epoch_station_state_count + 1
            await self.start_epoch()
        elif isinstance(message_object, UserStateMessage):
            message_object = cast(UserStateMessage, message_object)
            LOGGER.info(message_object)
            LOGGER.info("USER STATE MESSAGE")
            LOGGER.info(self._user_state_received)
            for u in self._users:
                if u['userId'] == message_object.user_id:
                    u['targetStateOfCharge'] = message_object.target_state_of_charge
                    u['targetTime'] = message_object.target_time
                    u['arrivalTime'] = message_object.arrival_time
                    u['requiredEngery'] = u['carBatteryCapacity'] * (u['targetStateOfCharge'] - u['stateOfCharge'])/100
                    LOGGER.info(u)
            self._epoch_user_state_count = self._epoch_user_state_count + 1
            await self.start_epoch()
        elif isinstance(message_object, CarStateMessage):
            message_object = cast(CarStateMessage, message_object)
            LOGGER.info(message_object)
            for u in self._users:
                if u['userId'] == message_object.user_id:
                    u['stateOfCharge'] = message_object.state_of_charge
            LOGGER.info(self._car_state_received)
            self._epoch_car_state_count = self._epoch_car_state_count + 1
            await self.start_epoch()
        else:
            LOGGER.debug("Received unknown message from {message_routing_key}: {message_object}")


    async def _send_power_requirement_message(self):
        LOGGER.info("power requirement message initiated")
        power_requirement = []
        #self._users = sorted(self._users, key=itemgetter('targetTime'), reverse=False)
        
        self._users = sorted(self._users, key=lambda k: (k['targetTime'], -k['requiredEngery']))
        LOGGER.info(self._users)

        for s in self._stations:
            station_power = s['maxPower']
            powerInfo = { "userId": "N/A", "stationId" : s['stationId'] }
            for u in self._users:
                if(u['stationId'] == s['stationId']):
                    LOGGER.info(to_utc_datetime_object(self._latest_epoch_message.start_time))
                    LOGGER.info(to_utc_datetime_object(u['arrivalTime']))
                    if(to_utc_datetime_object(self._latest_epoch_message.start_time) >= to_utc_datetime_object(u['arrivalTime']) and to_utc_datetime_object(self._latest_epoch_message.end_time) <= to_utc_datetime_object(u['targetTime'])):
                        powerInfo = { "userId": u['userId'], "stationId" : u['stationId'], "stationMaxPower": float(station_power), "carMaxPower": u['carMaxPower'], "stateOfCharge": u['stateOfCharge'], "targetStateOfCharge": u['targetStateOfCharge'], "requiredEngery": u['requiredEngery']}
            power_requirement.append(powerInfo)

        # for u in self._users:
        #     station_power = 0.0
        #     for s in self._stations:
        #         if(u['stationId'] == s['stationId']):
        #             station_power = s['maxPower']
        #     powerInfo = { "userId": u['userId'], "stationId" : u['stationId'], "stationMaxPower": float(station_power), "carMaxPower": u['carMaxPower'], "stateOfCharge": u['stateOfCharge'], "targetStateOfCharge": u['targetStateOfCharge'], "requiredEngery": u['requiredEngery']}
        #     power_requirement.append(powerInfo)
        LOGGER.info(power_requirement)

        for p in power_requirement:
            LOGGER.info("POWER REQ")
            powerRequirementForStation = float(0.0)
            if(self._used_total_power < self._total_max_power and p['userId']!= "N/A"):
                
                LOGGER.info("IN CONDITION")
                LOGGER.info("EPOCH MESSAGE")
                LOGGER.info("START TIME")
                LOGGER.info((to_utc_datetime_object(self._latest_epoch_message.end_time) - to_utc_datetime_object(self._latest_epoch_message.start_time)).seconds)
                if(p['targetStateOfCharge'] > p['stateOfCharge']):
                    powerRequirementForStation = min(p['stationMaxPower'], p['carMaxPower'], self._total_max_power - self._used_total_power, (p['requiredEngery'] / (to_utc_datetime_object(self._latest_epoch_message.end_time) - to_utc_datetime_object(self._latest_epoch_message.start_time)).seconds) * 3600)
                    #powerRequirementForStation = min(p['stationMaxPower'], p['carMaxPower'], self._total_max_power - self._used_total_power, p['requiredEngery'] / (to_utc_datetime_object(self._latest_epoch_message.end_time) - to_utc_datetime_object(self._latest_epoch_message.start_time)).seconds)
                    self._used_total_power = self._used_total_power + powerRequirementForStation                     
                LOGGER.info(powerRequirementForStation)  
                
            try:
                power_requirement_message = self._message_generator.get_message(
                        PowerRequirementMessage,
                        EpochNumber=self._latest_epoch,
                        TriggeringMessageIds=self._triggering_message_ids,
                        StationId = p['stationId'],
                        Power = powerRequirementForStation
                )

                await self._rabbitmq_client.send_message(
                    topic_name=self._power_requirement_topic,
                    message_bytes= power_requirement_message.bytes()
                )            

            except (ValueError, TypeError, MessageError) as message_error:
                # When there is an exception while creating the message, it is in most cases a serious error.
                log_exception(message_error)
                await self.send_error_message("Internal error when creating result message.")



def create_component() -> ICComponent:
    LOGGER.info("create IC component")
    environment_variables = load_environmental_variables(
        (USERS, list, []),   
        (STATIONS, list, []),
        (TOTAL_MAX_POWER, float, 0.0)
    )
    users = cast(list, environment_variables[USERS])
    stations = cast(list, environment_variables[STATIONS])
    total_max_power = cast(float, environment_variables[TOTAL_MAX_POWER])

    return ICComponent(
        users = users,
        stations = stations,
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