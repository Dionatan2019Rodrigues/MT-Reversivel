"""ponto de entrada do simulador de máquina de turing reversível.

uso: python simulador.py < entrada-quintupla.txt
"""

from __future__ import annotations

import sys

from parser import parse_input
from simulador_reversivel import SimuladorReversivel
from visualizador import Visualizador


def _configurar_encoding() -> None:
    """configura stdout e stderr para utf-8 no windows."""
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


def main() -> None:
    """lê a entrada, parseia a MT e inicia o simulador com a GUI."""
    _configurar_encoding()

    linhas = sys.stdin.read().strip().split('\n')
    mt = parse_input(linhas)

    visualizador = Visualizador()

    simulador = SimuladorReversivel(
        mt,
        callback=visualizador.enviar_evento,
        controlador=visualizador,
    )

    visualizador.configurar(simulador)
    visualizador.iniciar()


if __name__ == '__main__':
    main()