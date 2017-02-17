#!/bin/bash

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace

NETWORKING_DPM_DIR=$DEST/networking-dpm
DPM_AGENT_CONF="etc/neutron/plugins/ml2/neutron_dpm_agent.conf"
#DPM_AGENT_CONF="${Q_PLUGIN_CONF_PATH}/dpm_agent.ini"
DPM_AGENT_BINARY="${NEUTRON_BIN_DIR}/neutron-dpm-agent"

# check for service enabled
if is_service_enabled q-dpm-agt; then

    if [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
        # Set up system services
        # no-op
        :

    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        setup_develop $NETWORKING_DPM_DIR


    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        # Configure after the other layer 1 and 2 services have been configured

        # Uses oslo config generator to generate core sample configuration files
        (cd $NETWORKING_DPM_DIR && exec ./tools/generate_config_file_samples.sh)

        if [ -f "$NETWORKING_DPM_DIR/$DPM_AGENT_CONF.sample" ]; then
            cp "$NETWORKING_DPM_DIR/$DPM_AGENT_CONF.sample" /$DPM_AGENT_CONF
        fi

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize and start the template service
        run_process q-dpm-agt "$DPM_AGENT_BINARY --config-file $NEUTRON_CONF --config-file /$DPM_AGENT_CONF"
    fi

    if [[ "$1" == "unstack" ]]; then
        # Shut down template services
        stop_process q-dpm-agt
    fi

    if [[ "$1" == "clean" ]]; then
        # Remove state and transient data
        # Remember clean.sh first calls unstack.sh
        # no-op
        :
    fi
fi

# Restore xtrace
$XTRACE