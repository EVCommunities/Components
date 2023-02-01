# Copyright 2023 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Dataclass for holding information about the current state of a station during simulation."""

from dataclasses import dataclass


@dataclass
class StationData:
    """Dataclass for holding station information"""
    station_id: str
    max_power: float
