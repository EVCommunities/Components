# Copyright 2023 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Dataclass for holding information about the current state of a user during simulation."""

from dataclasses import dataclass


@dataclass
class UserData:
    """Dataclass for holding user information"""
    # metadata attributes
    user_id: int
    user_name: str
    station_id: str
    state_of_charge: float
    car_battery_capacity: float
    car_model: str
    car_max_power: float

    # attributes for the user requirements
    target_state_of_charge: float = 0.0
    required_energy: float = 0.0
    arrival_time: str = "2023-01-01T00:00:00.000Z"
    target_time: str = "2023-01-01T00:00:00.000Z"
