# Copyright 2023 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Dataclass for holding information about the required and available energy"""

from dataclasses import dataclass
from typing import List


@dataclass
class EnergyCheck:
    """Dataclass for holding energy information"""
    total_required_energy: float
    total_available_energy: float
    affected_users: List[str]
