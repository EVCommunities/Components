# Copyright 2023 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Dataclass for holding power information during simulation."""

from dataclasses import dataclass


@dataclass
class PowerInfo:
    """Dataclass for holding power information"""
    user_id: int
    station_id: str
    station_max_power: float = 0.0
    car_max_power: float = 0.0
    state_of_charge: float = 0.0
    target_state_of_charge: float = 0.0
    required_energy: float = 0.0
    target_time: str = "2023-01-01T00:00:00.000Z"
