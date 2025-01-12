#!/bin/bash

if ! command -v python3 &> /dev/null
then
    echo "Python não encontrado! Certifique-se de que o Python esteja instalado."
    exit 1
fi

python3 main.py