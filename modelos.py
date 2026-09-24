"""modelos para a máquina de turing reversível."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Quintupla:
    """regra clássica: (estado_atual, símbolo_lido) -> (próximo_estado, símbolo_escrito, direção)."""

    estado_atual: int
    simbolo_lido: str
    proximo_estado: int
    simbolo_escrito: str
    direcao: str  # 'L' ou 'R'
    indice: int = 0  # índice na lista original

    def __str__(self) -> str:
        return (
            f"({self.estado_atual},{self.simbolo_lido})"
            f"=({self.proximo_estado},{self.simbolo_escrito},{self.direcao})"
        )


@dataclass
class Quadrupla:
    """regra reversível de bennett, podendo ser do tipo ESCREVER ou MOVER."""

    estado_atual: int
    simbolo_lido: str
    proximo_estado: int
    simbolo_escrito: str | None  # none se tipo == 'MOVER'
    direcao: str | None          # none se tipo == 'ESCREVER'
    tipo: str                    # 'ESCREVER' ou 'MOVER'
    indice_quintupla: int = 0    # índice da quíntupla original correspondente

    def __str__(self) -> str:
        if self.tipo == 'ESCREVER':
            return (
                f"({self.estado_atual},{self.simbolo_lido})"
                f"→({self.proximo_estado},{self.simbolo_escrito}) [ESCREVER]"
            )
        return (
            f"({self.estado_atual},{self.simbolo_lido})"
            f"→({self.proximo_estado},{self.direcao}) [MOVER]"
        )


@dataclass
class MTDefinition:
    """definição completa de uma máquina de turing lida da entrada."""

    num_estados: int = 0
    num_simbolos_entrada: int = 0
    num_simbolos_fita: int = 0
    num_transicoes: int = 0
    estados: list[int] = field(default_factory=list)
    estado_inicial: int = 0
    estado_aceitacao: int = 0
    alfabeto_entrada: list[str] = field(default_factory=list)
    alfabeto_fita: list[str] = field(default_factory=list)
    transicoes: list[Quintupla] = field(default_factory=list)
    entrada: str = ""
