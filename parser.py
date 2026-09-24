"""parser do arquivo de entrada da máquina de turing."""

from __future__ import annotations

import re

from modelos import MTDefinition, Quintupla


def parse_input(linhas: list[str]) -> MTDefinition:
    """parseia as linhas da entrada padrão e retorna a definição da MT."""
    mt = MTDefinition()

    # linha 1: nº estados, nº símbolos entrada, nº símbolos fita, nº transições
    partes = linhas[0].split()
    mt.num_estados = int(partes[0])
    mt.num_simbolos_entrada = int(partes[1])
    mt.num_simbolos_fita = int(partes[2])
    mt.num_transicoes = int(partes[3])

    # linha 2: lista de estados
    mt.estados = [int(x) for x in linhas[1].split()]
    mt.estado_inicial = mt.estados[0]
    mt.estado_aceitacao = mt.estados[-1]  # último estado = aceitação

    # linha 3: alfabeto de entrada
    mt.alfabeto_entrada = linhas[2].split()

    # linha 4: alfabeto da fita
    mt.alfabeto_fita = linhas[3].split()

    # linhas seguintes: transições no formato (estado,símbolo)=(estado',símbolo',dir)
    padrao = re.compile(r'\((\d+),([^)]+)\)=\((\d+),([^,]+),([LR])\)')
    for i in range(mt.num_transicoes):
        linha = linhas[4 + i].strip()
        m = padrao.match(linha)
        if not m:
            raise ValueError(
                f"formato de transição inválido na linha {5 + i}: '{linha}'"
            )
        quintupla = Quintupla(
            estado_atual=int(m.group(1)),
            simbolo_lido=m.group(2),
            proximo_estado=int(m.group(3)),
            simbolo_escrito=m.group(4),
            direcao=m.group(5),
            indice=i,
        )
        mt.transicoes.append(quintupla)

    # última linha: cadeia de entrada
    mt.entrada = linhas[4 + mt.num_transicoes].strip()

    return mt
