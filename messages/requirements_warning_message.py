"""
Message class for warning messages which are sent in cases where some of the energy requirements cannot be fulfilled
"""

# Copyright 2023 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

from __future__ import annotations
from typing import Any, Dict, List, Optional

from tools.exceptions.messages import MessageValueError
from tools.messages import AbstractResultMessage


class RequirementsWarningMessage(AbstractResultMessage):
    CLASS_MESSAGE_TYPE = "RequirementsWarning"
    MESSAGE_TYPE_CHECK = True

    MESSAGE_ATTRIBUTES = {
        "AvailableEnergy": "available_energy",
        "AffectedUsers": "affected_users"
    }
    OPTIONAL_ATTRIBUTES = []
    QUANTITY_BLOCK_ATTRIBUTES = {}
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}
    TIMESERIES_BLOCK_ATTRIBUTES = []

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
    def available_energy(self) -> float:
        """Returns the available energy in percentages."""
        return self.__available_energy

    @property
    def affected_users(self) -> List[str]:
        """Returns the available energy in percentages."""
        return self.__affected_users

    @available_energy.setter
    def available_energy(self, percentage: int | float | str):
        if self._check_available_energy(percentage):
            self.__available_energy = float(percentage)
        else:
            raise MessageValueError(f"'{percentage}' is not a floating point value between 0 and 100")

    @affected_users.setter
    def affected_users(self, user_list: List[str]):
        if self._check_affected_users(user_list):
            self.__affected_users = user_list
        else:
            raise MessageValueError(f"'{user_list}' is not a non-empty list of strings representing users")

    # provide a new implementation for the "test of message equality" function
    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, RequirementsWarningMessage) and
            self.available_energy == other.available_energy and
            self.affected_users == other.affected_users
        )

    @classmethod
    def _check_available_energy(cls, percentage: int | float | str) -> bool:
        try:
            float_percentage = float(percentage)
            return 0.0 <= float_percentage <= 100.0
        except ValueError:
            return False

    @classmethod
    def _check_affected_users(cls, user_list: List[str]) -> bool:
        return len(user_list) > 0 and all(len(user) > 0 for user in user_list)

    # Provide a new implementation for the class method from_json method
    # Only the return type should be changed here
    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Optional[RequirementsWarningMessage]:
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


RequirementsWarningMessage.register_to_factory()
