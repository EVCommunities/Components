# Copyright 2022 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Chalith Haputhantrige <chalith.haputhantrige@tuni.fi>

from __future__ import annotations
from typing import Any, Dict, Optional, Union

from tools.exceptions.messages import MessageError
from tools.messages import AbstractResultMessage


class StationStateMessage(AbstractResultMessage):
    """Description for the StationStateMessage class"""

    CLASS_MESSAGE_TYPE = "StationState"
    MESSAGE_TYPE_CHECK = True

    STATION_ID_ATTRIBUTE = "StationId"
    STATION_ID_PROPERTY = "station_id"

    MAX_POWER_ATTRIBUTE = "MaxPower"
    MAX_POWER_PROPERTY = "max_power"

    # all attributes specific that are added to the AbstractResult should be introduced here
    MESSAGE_ATTRIBUTES = {
        STATION_ID_ATTRIBUTE: STATION_ID_PROPERTY,
        MAX_POWER_ATTRIBUTE:MAX_POWER_PROPERTY
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

    # for each attributes added by this message type provide a property function to get the value of the attribute
    # the name of the properties must correspond to the names given in MESSAGE_ATTRIBUTES
    # template for one property:
    @property
    def station_id(self) -> str:
        return self.__station_id

    @property
    def max_power(self) -> float:
        return self.__max_power

    @station_id.setter
    def station_id(self, station_id: str):
        self.__station_id = station_id

    @max_power.setter
    def max_power(self, max_power: Union[int, float]):
        self.__max_power = float(max_power)

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, StationStateMessage) and
            self.station_id == other.station_id and
            self.max_power == other.max_power
        )

    @classmethod
    def _check_station_id(cls, station_id: str) -> bool:
        return isinstance(station_id, str)

    @classmethod
    def _check_max_power(cls, max_power: Union[int, float]) -> bool:
        return isinstance(max_power, (int, float))

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Optional[StationStateMessage]:
        """TODO: description for the from_json method"""
        try:
            message_object = cls(**json_message)
            return message_object
        except (TypeError, ValueError, MessageError):
            return None


StationStateMessage.register_to_factory()
