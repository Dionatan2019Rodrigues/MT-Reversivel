"""fita infinita para a máquina de turing."""

from __future__ import annotations


class Fita:
    """fita infinita implementada com dicionário (posição -> símbolo)."""

    def __init__(self, conteudo: str = '', branco: str = 'B'):
        self.branco = branco
        self.celulas: dict[int, str] = {}
        self.posicao: int = 0

        # inicializar com conteúdo, se fornecido
        for i, caractere in enumerate(conteudo):
            self.celulas[i] = caractere

    def ler(self) -> str:
        """lê o símbolo na posição atual do cabeçote."""
        return self.celulas.get(self.posicao, self.branco)

    def escrever(self, simbolo: str) -> None:
        """escreve um símbolo na posição atual do cabeçote."""
        if simbolo == self.branco:
            self.celulas.pop(self.posicao, None)
        else:
            self.celulas[self.posicao] = simbolo

    def mover(self, direcao: str) -> None:
        """move o cabeçote: 'R' -> +1, 'L' -> -1."""
        self.posicao += 1 if direcao == 'R' else -1

    def esta_limpa(self) -> bool:
        """verifica se a fita contém apenas brancos."""
        return all(v == self.branco for v in self.celulas.values())

    def conteudo_str(self) -> str:
        """retorna o conteúdo da fita como string contígua."""
        if not self.celulas:
            return ''
        pos_min = min(self.celulas.keys())
        pos_max = max(self.celulas.keys())
        return ''.join(
            self.celulas.get(i, self.branco)
            for i in range(pos_min, pos_max + 1)
        )

    def __str__(self) -> str:
        if not self.celulas:
            return f"[{self.branco}]  ^(pos={self.posicao})"

        pos_min = min(min(self.celulas.keys()), self.posicao)
        pos_max = max(max(self.celulas.keys()), self.posicao)
        partes = []
        for i in range(pos_min, pos_max + 1):
            simbolo = self.celulas.get(i, self.branco)
            if i == self.posicao:
                partes.append(f"[{simbolo}]")
            else:
                partes.append(f" {simbolo} ")
        return ''.join(partes)
