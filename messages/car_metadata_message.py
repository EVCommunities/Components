# Copyright 2022 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>

from __future__ import annotations
from typing import Any, Dict, Optional

from tools.exceptions.messages import MessageError, MessageValueError
from tools.messages import AbstractResultMessage


class CarMetaDataMessage(AbstractResultMessage):
    CLASS_MESSAGE_TYPE = "CarMetaData"
    MESSAGE_TYPE_CHECK = True


    USER_ID_ATTRIBUTE = "UserId"
    USER_ID_PROPERTY = "user_id"

    USER_NAME_ATTRIBUTE = "UserName"
    USER_NAME_PROPERTY = "user_name"

    STATION_ID_ATTRIBUTE = "StationId"
    STATION_ID_PROPERTY = "station_id"

    #Added
    STATE_OF_CHARGE_ATTRIBUTE = "StateOfCharge"
    STATE_OF_CHARGE_PROPERTY = "state_of_charge"

    CAR_BATTERY_CAPACITY_ATTRIBUTE = "CarBatteryCapacity"
    CAR_BATTERY_CAPACITY_PROPERTY = "car_battery_capacity"

    CAR_MODEL_ATTRIBUTE = "CarModel"
    CAR_MODEL_PROPERTY = "car_model"

    #Added
    CAR_MAX_POWER_ATTRIBUTE = "CarMaxPower"
    CAR_MAX_POWER_PROPERTY = "car_max_power"



    # all attributes specific that are added to the AbstractResult should be introduced here
    MESSAGE_ATTRIBUTES = {
        USER_ID_ATTRIBUTE: USER_ID_PROPERTY,
        USER_NAME_ATTRIBUTE: USER_NAME_PROPERTY,
        STATION_ID_ATTRIBUTE: STATION_ID_PROPERTY,
        STATE_OF_CHARGE_ATTRIBUTE: STATE_OF_CHARGE_PROPERTY,
        CAR_BATTERY_CAPACITY_ATTRIBUTE: CAR_BATTERY_CAPACITY_PROPERTY,
        CAR_MODEL_ATTRIBUTE: CAR_MODEL_PROPERTY,
        CAR_MAX_POWER_ATTRIBUTE: CAR_MAX_POWER_PROPERTY

    }
    # list all attributes that are optional here (use the JSON attribute names)
    OPTIONAL_ATTRIBUTES = []

    # all attributes that are using the Quantity block format should be listed here
    QUANTITY_BLOCK_ATTRIBUTES = {}

    # all attributes that are using the Quantity array block format should be listed here
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}

    # all attributes that are using the Time series block format should be listed here
    TIMESERIES_BLOCK_ATTRIBUTES = []

    # always include these definitions to update the full list of attributes to these class variables
    # no need to modify anything here
    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = {
        **AbstractResultMessage.QUANTITY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_BLOCK_ATTRIBUTES
    }
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL = {
        **AbstractResultMessage.QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_ARRAY_BLOCK_ATTRIBUTES
    }
    TIMESERIES_BLOCK_ATTRIBUTES_FULL = (
        AbstractResultMessage.TIMESERIES_BLOCK_ATTRIBUTES_FULL +
        TIMESERIES_BLOCK_ATTRIBUTES
    )

    @property
    def user_id(self) -> int:
        return self.__user_id
    @property
    def user_name(self) -> str:
        return self.__user_name
    @property
    def station_id(self) -> str:
        return self.__station_id
    @property
    def state_of_charge(self) -> float:
        return self.__state_of_charge      
    @property
    def car_battery_capacity(self) -> float:
        return self.__car_battery_capacity
    @property
    def car_model(self) -> str:
        return self.__car_model
    @property
    def car_max_power(self) -> float:
        return self.__car_max_power



    @user_id.setter
    def user_id(self, user_id: int):
        if self._check_user_id(user_id):
            self.__user_id = user_id
        else:
            raise MessageValueError(f"Invalid value for UserId: {user_id}")

    @user_name.setter
    def user_name(self, user_name: str):
        if self._check_user_name(user_name):
            self.__user_name = user_name
        else:
            raise MessageValueError(f"Invalid value for UserName: {user_name}")

    @station_id.setter
    def station_id(self, station_id: str):
        if self._check_station_id(station_id):
            self.__station_id = station_id
        else:
            raise MessageValueError(f"Invalid value for StationId: {station_id}")

    @state_of_charge.setter
    def state_of_charge(self, state_of_charge: float):
        if self._check_state_of_charge(state_of_charge):
            self.__state_of_charge = state_of_charge
        else:
            raise MessageValueError(f"Invalid value for StateOfCharge: {state_of_charge}")

    @car_battery_capacity.setter
    def car_battery_capacity(self, car_battery_capacity: float):
        if self._check_car_battery_capacity(car_battery_capacity):
            self.__car_battery_capacity = car_battery_capacity
        else:
            raise MessageValueError(f"Invalid value for CarBatteryCapacity: {car_battery_capacity}")

    @car_model.setter
    def car_model(self, car_model: str):
        if self._check_car_model(car_model):
            self.__car_model = car_model
        else:
            raise MessageValueError(f"Invalid value for CarModel: {car_model}")

    @car_max_power.setter
    def car_max_power(self, car_max_power: float):
        if self._check_car_max_power(car_max_power):
            self.__car_max_power = car_max_power
        else:
            raise MessageValueError(f"Invalid value for CarMaxPower: {car_max_power}")

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, CarMetaDataMessage) and
            self.user_id == other.user_id and 
            self.user_name == other.user_name  and 
            self.station_id == other.station_id and 
            self.state_of_charge == other.state_of_charge and 
            self.car_battery_capacity == other.car_battery_capacity and 
            self.car_model == other.car_model and 
            self.car_max_power == other.car_max_power
        )

    @classmethod
    def _check_user_id(cls, user_id: int) -> bool:
        return isinstance(user_id, int)

    @classmethod
    def _check_user_name(cls, user_name: str) -> bool:
        return isinstance(user_name, str)

    @classmethod
    def _check_station_id(cls, station_id: str) -> bool:
        return isinstance(station_id, str)

    @classmethod
    def _check_state_of_charge(cls, state_of_charge: float) -> bool:
        return isinstance(state_of_charge, float)

    @classmethod
    def _check_car_battery_capacity(cls, car_battery_capacity: float) -> bool:
        return isinstance(car_battery_capacity, float)

    @classmethod
    def _check_car_model(cls, car_model: str) -> bool:
        return isinstance(car_model, str)

    @classmethod
    def _check_car_max_power(cls, car_max_power: float) -> bool:
        return isinstance(car_max_power, float)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Optional[CarMetaDataMessage]:
        try:
            message_object = cls(**json_message)
            return message_object
        except (TypeError, ValueError, MessageError):
            return None

CarMetaDataMessage.register_to_factory()