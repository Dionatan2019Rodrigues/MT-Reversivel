from dataclasses import dataclass
from collections import defaultdict
import re
import sys


@dataclass(frozen=True)
class Regra:
    id: int
    estado_atual: str
    simbolo_lido: str
    proximo_estado: str
    simbolo_escrito: str
    movimento: str

def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        linhas = [
            linha.strip()
            for linha in arquivo
            if linha.strip()
        ]

    # Primeira linha
    qtd_estados, qtd_entrada, qtd_fita, qtd_transicoes = \
        map(int, linhas[0].split())

    # Conjuntos
    estados = linhas[1].split()
    alfabeto_entrada = linhas[2].split()
    alfabeto_fita = linhas[3].split()

    # Regex para:
    # (1,0)=(2,$,R)
    padrao = re.compile(
        r"^\(([^,]+),([^)]+)\)=\(([^,]+),([^,]+),([^)]+)\)$"
    )

    regras = []

    inicio = 4
    fim = inicio + qtd_transicoes

    for numero, linha in enumerate(
        linhas[inicio:fim],
        start=1
    ):
        linha = linha.replace(" ", "")

        resultado = padrao.match(linha)

        if resultado is None:
            raise ValueError(
                f"Transição inválida: {linha}"
            )

        estado, lido, novo_estado, escrito, movimento = \
            resultado.groups()

        movimento = movimento.upper()

        regras.append(
            Regra(
                numero,
                estado,
                lido,
                novo_estado,
                escrito,
                movimento
            )
        )

    # Palavra fica depois das transições
    palavra = linhas[fim]

    # Algumas verificações
    if len(estados) != qtd_estados:
        raise ValueError(
            "Quantidade de estados incorreta."
        )

    if len(alfabeto_entrada) != qtd_entrada:
        raise ValueError(
            "Quantidade de símbolos de entrada incorreta."
        )

    if len(alfabeto_fita) != qtd_fita:
        raise ValueError(
            "Quantidade de símbolos da fita incorreta."
        )

    if len(regras) != qtd_transicoes:
        raise ValueError(
            "Quantidade de transições incorreta."
        )

    return (
        estados,
        alfabeto_entrada,
        alfabeto_fita,
        regras,
        palavra
    )


class MaquinaTuringReversivel:

    def __init__(
        self,
        estados,
        alfabeto_fita,
        regras,
        palavra,
        branco="B"
    ):
        self.estados = estados
        self.alfabeto_fita = alfabeto_fita
        self.branco = branco

        # Convenção utilizada para este arquivo
        self.estado_inicial = estados[0]
        self.estado_final = estados[-1]

        self.estado = self.estado_inicial
        self.cabeca = 0

        # --------------------------
        # FITA 1 - trabalho
        # --------------------------

        self.fita = defaultdict(
            lambda: self.branco
        )

        for posicao, simbolo in enumerate(palavra):
            self.fita[posicao] = simbolo

        self.palavra_original = palavra

        # --------------------------
        # FITA 2 - histórico
        # --------------------------

        self.historico = []

        # --------------------------
        # FITA 3 - saída
        # --------------------------

        self.fita_saida = None

        self.regras_por_chave = {}
        self.regras_por_id = {}

        for regra in regras:

            chave = (
                regra.estado_atual,
                regra.simbolo_lido
            )

            # Verifica determinismo
            if chave in self.regras_por_chave:
                raise ValueError(
                    f"Máquina não determinística em {chave}"
                )

            self.regras_por_chave[chave] = regra
            self.regras_por_id[regra.id] = regra


    def deslocamento(self, movimento):

        if movimento == "R":
            return 1

        if movimento == "L":
            return -1

        return 0


    def mostrar_fita(self):

        posicoes = [
            posicao
            for posicao, simbolo in self.fita.items()
            if simbolo != self.branco
        ]

        if not posicoes:
            return ""

        inicio = min(posicoes)
        fim = max(posicoes)

        return "".join(
            self.fita[i]
            for i in range(inicio, fim + 1)
        )


    def passo_frente(self):

        simbolo = self.fita[self.cabeca]

        chave = (
            self.estado,
            simbolo
        )

        regra = self.regras_por_chave.get(chave)

        if regra is None:
            return False

        # ------------------------
        # GRAVA HISTÓRICO
        # ------------------------

        self.historico.append(regra.id)

        # Escreve na fita
        self.fita[self.cabeca] = \
            regra.simbolo_escrito

        # Move a cabeça
        self.cabeca += self.deslocamento(
            regra.movimento
        )

        # Troca o estado
        self.estado = regra.proximo_estado

        return True


    def executar(self, max_passos=100000):

        passos = 0

        print("\n--- EXECUÇÃO PARA FRENTE ---")

        while self.estado != self.estado_final:

            if passos >= max_passos:
                raise RuntimeError(
                    "Número máximo de passos atingido."
                )

            print(
                f"Passo {passos:3} | "
                f"Estado {self.estado} | "
                f"Fita {self.mostrar_fita()} | "
                f"Histórico {self.historico}"
            )

            executou = self.passo_frente()

            if not executou:
                print("Nenhuma transição disponível.")
                break

            passos += 1

        print(
            f"\nEstado alcançado: {self.estado}"
        )

        # ======================================
        # ETAPA 2 DE BENNETT
        # COPIAR A SAÍDA
        # ======================================

        self.fita_saida = self.mostrar_fita()

        print(
            f"Saída copiada: {self.fita_saida}"
        )

        return passos


    def passo_tras(self):

        if not self.historico:
            return False

        # Retira a última transição executada
        id_regra = self.historico.pop()

        regra = self.regras_por_id[id_regra]

        # ---------------------------------
        # DESFAZ O MOVIMENTO
        # ---------------------------------

        self.cabeca -= self.deslocamento(
            regra.movimento
        )

        # Verificação de segurança
        if (
            self.fita[self.cabeca]
            != regra.simbolo_escrito
        ):
            raise RuntimeError(
                "Não foi possível inverter a transição."
            )

        # ---------------------------------
        # RESTAURA O SÍMBOLO ANTERIOR
        # ---------------------------------

        self.fita[self.cabeca] = \
            regra.simbolo_lido

        # ---------------------------------
        # RESTAURA O ESTADO ANTERIOR
        # ---------------------------------

        self.estado = regra.estado_atual

        return True


    def retroceder(self):

        passos = 0

        print("\n--- EXECUÇÃO REVERSA ---")

        while self.historico:

            print(
                f"Passo {passos:3} | "
                f"Estado {self.estado} | "
                f"Fita {self.mostrar_fita()} | "
                f"Histórico {self.historico}"
            )

            self.passo_tras()

            passos += 1

        print("\n--- CONFIGURAÇÃO FINAL ---")

        print(
            "Estado restaurado:",
            self.estado
        )

        print(
            "Entrada restaurada:",
            self.mostrar_fita()
        )

        print(
            "Histórico:",
            self.historico
        )

        print(
            "Saída preservada:",
            self.fita_saida
        )


def main():

    if len(sys.argv) < 2:
        print(
            "Uso: python maquina.py entrada-quintupla.txt"
        )
        return

    caminho = sys.argv[1]

    (
        estados,
        alfabeto_entrada,
        alfabeto_fita,
        regras,
        palavra
    ) = ler_arquivo(caminho)

    print("Estados:", estados)
    print("Alfabeto de entrada:", alfabeto_entrada)
    print("Alfabeto da fita:", alfabeto_fita)
    print("Palavra:", palavra)

    maquina = MaquinaTuringReversivel(
        estados,
        alfabeto_fita,
        regras,
        palavra
    )

    maquina.executar()

    maquina.retroceder()


if __name__ == "__main__":
    main()