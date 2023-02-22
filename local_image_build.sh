#!/bin/bash
# Copyright 2023 Tampere University
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

docker build --tag ghcr.io/evcommunities/station-component:latest --file station_component.Dockerfile .
docker build --tag ghcr.io/evcommunities/user-component:latest --file user_component.Dockerfile .
docker build --tag ghcr.io/evcommunities/ic-component:latest --file ic_component.Dockerfile .
