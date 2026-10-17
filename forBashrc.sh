#!/bin/bash

# Some aliases and functions that are nice to have in a bashrc file

alias lpy="ps aux | grep -E '\.py($| )' | grep -v grep"

py() {
    if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then # Virtual environment is active, and usual executable exists
        "$VIRTUAL_ENV/bin/python" "$@"
    else
        command python3 "$@"
    fi
}

alias condaInit='eval "$(/home/$USER/miniconda3/bin/conda shell.bash hook)"'

globusInit() {
    # Start GLobus Connect Personal (GCP) so local device is endpoint
    /home/camden/Documents/Globus/globusconnectpersonal-3.2.8/globusconnectpersonal &

    # For tab completion
    if type globus > /dev/null 2>&1; then
        eval "$(globus --bash-completer)"
    fi

    # Activate venv with globus CLI installed
    source /home/camden/.globusVenv/bin/activate > /dev/null

    # Handy endpoint UUIDs
    export LOCAL="19101c2c-30a1-11f1-a72d-0afffe4617ab"
    export FIR="d6a86f93-b5de-4d26-ae5a-bcbec9cc6600"
    export FIR2="8dec4129-9ab4-451d-a45f-5b4b8471f7a3"
    export SOCKEYE="64a5c402-05c4-4607-bbad-46a9c2aebd98"
    export TRILLIUM="ad462f99-8436-42b4-adc6-3644e36c1b67"

    # Print login/session information
    echo "Local Globus endpoint initialized, and CLI is ready to be used. You are logged in as follows:"
    globus whoami -v
    globus session show
}
