# Copyright 2022 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ali Mehraj <ali.mehraj@tuni.fi>

from __future__ import annotations
from typing import Any, Dict, Optional

from tools.exceptions.messages import MessageError, MessageValueError
from tools.messages import AbstractResultMessage
# Confirm usage
from datetime import datetime

class UserStateMessage(AbstractResultMessage):
    CLASS_MESSAGE_TYPE = "UserState"
    MESSAGE_TYPE_CHECK = True

    USER_ID_ATTRIBUTE = "UserId"
    USER_ID_PROPERTY = "user_id"

    #Modified from TARGET_BATTERY
    TARGET_STATE_OF_CHARGE_ATTRIBUTE = "TargetStateOfCharge"
    TARGET_STATE_OF_CHARGE_PROPERTY = "target_state_of_charge"

    #Modified from LEAVING_TIME
    TARGET_TIME_ATTRIBUTE = "TargetTime"
    TARGET_TIME_PROPERTY = "target_time"

    MESSAGE_ATTRIBUTES = {
        USER_ID_ATTRIBUTE: USER_ID_PROPERTY,
        TARGET_STATE_OF_CHARGE_ATTRIBUTE: TARGET_STATE_OF_CHARGE_PROPERTY,
        TARGET_TIME_ATTRIBUTE: TARGET_TIME_PROPERTY
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
    def target_state_of_charge(self) -> float:
        return self.__target_state_of_charge

    @property
    def target_time(self) -> str:
        return self.__target_time  

    @user_id.setter
    def user_id(self, user_id: int):
        if self._check_user_id(user_id):
            self.__user_id = user_id
        else:
            raise MessageValueError(f"Invalid value for UserId: {user_id}")

    @target_state_of_charge.setter
    def target_state_of_charge(self, target_state_of_charge: float):
        if self._check_target_state_of_charge(target_state_of_charge):
            self.__target_state_of_charge = target_state_of_charge
        else:
            raise MessageValueError(f"Invalid value for TargetStateOfCharge: {target_state_of_charge}")

    @target_time.setter
    def target_time(self, target_time: str):
        if self._check_target_time(target_time):
            self.__target_time = target_time
        else:
            raise MessageValueError(f"Invalid value for TargetStateOfCharge: {target_time}")

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, UserStateMessage) and
            self.user_id == other.user_id and 
            self.target_state_of_charge == other.target_state_of_charge and 
            self.target_time == other.target_time
        )

    @classmethod
    def _check_user_id(cls, user_id: int) -> bool:
        return isinstance(user_id, int)

    @classmethod
    def _check_target_state_of_charge(cls, target_state_of_charge: float) -> bool:
        return isinstance(target_state_of_charge, float)

    @classmethod
    def _check_target_time(cls, target_time: str) -> bool:
        return isinstance(target_time, str)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Optional[UserStateMessage]:
        try:
            message_object = cls(**json_message)
            return message_object
        except (TypeError, ValueError, MessageError):
            return None

UserStateMessage.register_to_factory()
