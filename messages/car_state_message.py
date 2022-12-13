# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>

from __future__ import annotations
from typing import Any, Dict, Optional

from tools.exceptions.messages import MessageError, MessageValueError
from tools.messages import AbstractResultMessage


class CarStateMessage(AbstractResultMessage):
    CLASS_MESSAGE_TYPE = "CarState"
    MESSAGE_TYPE_CHECK = True

    USER_ID_ATTRIBUTE = "UserId"
    USER_ID_PROPERTY = "user_id"

    STATION_ID_ATTRIBUTE = "StationId"
    STATION_ID_PROPERTY = "station_id"

    #Added
    STATE_OF_CHARGE_ATTRIBUTE = "StateOfCharge"
    STATE_OF_CHARGE_PROPERTY = "state_of_charge"


    # all attributes specific that are added to the AbstractResult should be introduced here
    MESSAGE_ATTRIBUTES = {
        USER_ID_ATTRIBUTE: USER_ID_PROPERTY,
        STATION_ID_ATTRIBUTE: STATION_ID_PROPERTY,
        STATE_OF_CHARGE_ATTRIBUTE: STATE_OF_CHARGE_PROPERTY
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
    def station_id(self) -> str:
        return self.__station_id
    @property
    def state_of_charge(self) -> float:
        return self.__state_of_charge      

    @user_id.setter
    def user_id(self, user_id: int):
        if self._check_user_id(user_id):
            self.__user_id = user_id
        else:
            raise MessageValueError(f"Invalid value for UserId: {user_id}")

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

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, CarStateMessage) and
            self.user_id == other.user_id and 
            self.station_id == other.station_id and 
            self.state_of_charge == other.state_of_charge
        )

    @classmethod
    def _check_user_id(cls, user_id: int) -> bool:
        return isinstance(user_id, int)

    @classmethod
    def _check_station_id(cls, station_id: str) -> bool:
        return isinstance(station_id, str)

    @classmethod
    def _check_state_of_charge(cls, state_of_charge: float) -> bool:
        return isinstance(state_of_charge, float)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Optional[CarStateMessage]:
        try:
            message_object = cls(**json_message)
            return message_object
        except (TypeError, ValueError, MessageError):
            return None

CarStateMessage.register_to_factory()
