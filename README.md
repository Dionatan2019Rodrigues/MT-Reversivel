# Simulador de Máquina de Turing Reversível

**Teoria da Computação — Trabalho 1**

Simulador de uma Máquina de Turing Reversível baseada no modelo de 3 fitas proposto por Charles H. Bennett (1973).

---

## Sumário

1. [Problematização](#1-problematização)
2. [Máquina de Turing Reversível](#2-máquina-de-turing-reversível)
3. [Solução de Bennett](#3-solução-de-bennett)
4. [Estágios de Execução](#4-estágios-de-execução)
5. [Estrutura do Projeto](#5-estrutura-do-projeto)
6. [Execução](#6-execução)
7. [Formato de Entrada](#7-formato-de-entrada)
8. [Funcionamento](#8-funcionamento)
9. [Exemplo Completo](#9-exemplo-completo)

---

## 1. Problematização

Na computação tradicional, quando uma Máquina de Turing executa um passo, ela **sobrescreve** o símbolo anterior na fita. Essa informação é permanentemente perdida. Se quiséssemos "voltar no tempo" e desfazer a computação, não saberíamos qual símbolo estava ali antes.

Essa perda de informação tem uma consequência física direta: pelo **Princípio de Landauer**, toda operação logicamente irreversível (como apagar um bit) dissipa uma quantidade mínima de energia na forma de calor. Isso significa que computadores tradicionais possuem um **limite termodinâmico fundamental** de eficiência energética.

A pergunta central que Bennett se fez foi:

> *"É possível realizar qualquer computação de forma completamente reversível, sem destruir informação — e, portanto, sem dissipar energia?"*

A resposta é **sim**, e o modelo que ele propôs prova que qualquer função computável por uma MT padrão também pode ser computada por uma MT reversível, com um custo relativamente pequeno em tempo e espaço.

---

## 2. Máquina de Turing Reversível

Uma **Máquina de Turing Reversível** é uma MT na qual cada configuração possui **no máximo um predecessor**. Ou seja, dado qualquer estado da máquina, é possível determinar **univocamente** qual era o estado anterior. Não há ambiguidade: o caminho de volta é tão determinístico quanto o caminho de ida.

### Por que uma MT clássica NÃO é reversível?

Uma MT clássica opera com **quíntuplas**:

```
(estado_atual, símbolo_lido) → (próximo_estado, símbolo_escrito, direção)
```

O problema é que a operação combina **escrever** e **mover** em um único passo. O inverso de "ler-escrever-mover" seria "mover-ler-escrever", que é um tipo completamente diferente de transição. Além disso, múltiplas configurações diferentes podem levar à mesma configuração seguinte, tornando impossível identificar de onde viemos.

### O que torna uma MT reversível?

Para ser reversível, a MT precisa garantir que:

- **Cada configuração tenha exatamente um predecessor** (injetividade).
- **As transições sejam invertíveis** — para cada regra de transição, existe uma regra inversa com a mesma estrutura.

---

## 3. Solução de Bennett

### 3.1. Das Quíntuplas às Quádruplas

Bennett percebeu que, para garantir a reversibilidade, era necessário um formato de transição onde **a ação e seu inverso tivessem exatamente a mesma estrutura**. A solução foi decompor cada quíntupla em duas **quádruplas**:

| Tipo        | O que faz                         | Formato                                          |
|-------------|-----------------------------------|--------------------------------------------------|
| **ESCREVER** | Lê um símbolo e escreve outro    | `(estado, símbolo_lido) → (estado', símbolo_escrito)` |
| **MOVER**    | Lê um símbolo e move o cabeçote  | `(estado, símbolo_lido) → (estado', direção)`        |

A regra fundamental: **a máquina nunca lê/escreve e se move no mesmo passo**.

#### Exemplo concreto

A quíntupla original:

```
(1, 0) → (2, $, R)
```

É decomposta em duas quádruplas com um **estado intermediário** (ex: estado 7):

```
Quádrupla 1 [ESCREVER]: (1, 0) → (7, $)     — lê '0', escreve '$'
Quádrupla 2 [MOVER]:    (7, $) → (2, R)      — lê '$', move para a direita
```

### 3.2. Invertendo as Quádruplas

Com as quádruplas, a inversão é **matematicamente perfeita**:

- **Inversa de ESCREVER:** trocar `estado_atual ↔ próximo_estado` e `símbolo_lido ↔ símbolo_escrito`.
- **Inversa de MOVER:** trocar `estado_atual ↔ próximo_estado` e inverter a direção (`R ↔ L`).

Para o exemplo acima:

```
Inversa da Quádrupla 2 [MOVER]:    (2, $) → (7, L)     — move para a esquerda
Inversa da Quádrupla 1 [ESCREVER]: (7, $) → (1, 0)     — lê '$', escreve '0' (restaura)
```

Note que a inversão desfaz **exatamente** o que foi feito, na ordem reversa.

### 3.3. O Modelo de 3 Fitas

Bennett propôs uma máquina com **3 fitas** para garantir a reversibilidade completa:

```
┌─────────────────────────────────────────────────┐
│  Fita 1 (Trabalho)    → onde a computação ocorre │
│  Fita 2 (Histórico)   → registra cada passo dado │
│  Fita 3 (Saída)       → cópia limpa do resultado  │
└─────────────────────────────────────────────────┘
```

- **Fita 1** contém a entrada e é modificada durante a computação.
- **Fita 2** grava o índice de cada quíntupla executada, criando um "diário" completo.
- **Fita 3** recebe apenas o resultado final, sem nenhum lixo computacional.

---

## 4. Estágios de Execução

A execução da MT reversível segue **3 estágios** sequenciais:

### Estágio 1 — Computação (Ida)

A máquina emula o programa original na Fita 1. A cada transição executada, grava na Fita 2 o **índice da quíntupla** que foi aplicada. Isso cria um registro completo que permite desfazer tudo depois.

```
Fita 1: [0] 0  1  1     →    $  X  X  X [B]
Fita 2: (vazia)          →    0 3 5 9 12 ...
```

### Estágio 2 — Cópia

Após atingir o estado de aceitação, a máquina copia o resultado da Fita 1 para a Fita 3. Esse processo de cópia é **intrinsecamente reversível** (copiar bit-a-bit não destrói informação).

```
Fita 1:  $  X  X  X     (não muda)
Fita 3: (vazia)          →    $  X  X  X
```

### Estágio 3 — Retorno (Desfazer)

A máquina lê a Fita 2 (Histórico) **de trás para frente**, aplicando a **inversa** de cada quíntupla registrada. Isso:

- **Restaura** a Fita 1 ao seu conteúdo original (a entrada).
- **Limpa** completamente a Fita 2 (volta ao branco).
- **Restaura** o estado da máquina ao estado inicial.

```
Fita 1:  $  X  X  X     →    0  0  1  1   (restaurada!)
Fita 2:  0 3 5 9 12 ... →    (limpa!)
Fita 3:  $  X  X  X     (preservada)
```

### Resultado final

Ao término dos 3 estágios:

| Fita | Estado |
|------|--------|
| Fita 1 (Trabalho) | restaurada ao conteúdo original da entrada |
| Fita 2 (Histórico) | completamente limpa (apenas brancos) |
| Fita 3 (Saída) | contém o resultado da computação |

A máquina não deixou **nenhum rastro** — toda informação intermediária foi apagada reversivelmente.

### Complexidade

Se a MT original leva **V** passos, a MT reversível leva aproximadamente **4V** passos: V para a ida, um pouco para a cópia, e V para a volta.

---

## 5. Estrutura do Projeto

O código segue princípios de **Clean Code** com responsabilidades bem separadas:

```
.
├── simulador.py              ← ponto de entrada (main)
├── modelos.py                ← dataclasses: Quintupla, Quadrupla, MTDefinition
├── parser.py                 ← leitura e interpretação do arquivo de entrada
├── fita.py                   ← classe Fita (fita infinita com dicionário)
├── conversor.py              ← conversão quíntupla → quádruplas reversíveis
├── simulador_reversivel.py   ← classe SimuladorReversivel (3 estágios)
├── entrada-quintupla.txt     ← arquivo de teste fornecido
└── README.md                 ← este arquivo
```

### Descrição dos módulos

| Módulo | Responsabilidade |
|--------|-----------------|
| `modelos.py` | define as estruturas de dados do domínio (`Quintupla`, `Quadrupla`, `MTDefinition`) |
| `parser.py` | parseia o arquivo de entrada e constrói a `MTDefinition` |
| `fita.py` | implementa a fita infinita usando `dict[int, str]` para posições arbitrárias |
| `conversor.py` | converte quíntuplas clássicas em pares de quádruplas (diretas e inversas) |
| `simulador_reversivel.py` | orquestra os 3 estágios de Bennett e imprime os resultados |
| `simulador.py` | ponto de entrada que conecta parser → simulador |

---

## 6. Execução

### Pré-requisitos

- Python 3.10 ou superior

### Execução

```bash
python simulador.py < entrada-quintupla.txt
```

O programa lê a definição da MT pela **entrada padrão** (`stdin`), conforme especificado no enunciado. Mesmo assim se seu PowerShell não aceitar o redirecionamento utilizando o operador `<`. Execute o projeto com : 

```bash
Get-Content entrada-quintupla.txt | py simulador.py
```

---

## 7. Formato de Entrada

O arquivo de entrada segue o formato abaixo:

```
<nº_estados> <nº_símbolos_entrada> <nº_símbolos_fita> <nº_transições>
<estado_1> <estado_2> ... <estado_n>
<símbolo_entrada_1> <símbolo_entrada_2> ...
<símbolo_fita_1> <símbolo_fita_2> ...
(estado_atual,símbolo_lido)=(próximo_estado,símbolo_escrito,direção)
...
<cadeia_de_entrada>
```

### Convenções

- O **primeiro estado** da lista é o estado inicial.
- O **último estado** da lista é o estado de aceitação.
- A **direção** é `R` (direita) ou `L` (esquerda).
- O símbolo `B` representa a célula em branco (blank).

### Exemplo (`entrada-quintupla.txt`)

```
6 2 5 17
1 2 3 4 5 6
0 1
0 1 $ X B
(1,0)=(2,$,R)
(1,1)=(3,$,R)
(1,B)=(6,B,R)
(2,0)=(2,0,R)
(2,X)=(2,X,R)
(2,1)=(4,X,L)
(3,1)=(3,1,R)
(3,X)=(3,X,R)
(3,0)=(4,X,L)
(4,0)=(4,0,L)
(4,1)=(4,1,L)
(4,X)=(4,X,L)
(4,$)=(5,$,R)
(5,X)=(5,X,R)
(5,0)=(2,X,R)
(5,1)=(3,X,R)
(5,B)=(6,B,R)
0011
```

Esta MT reconhece a linguagem **{0ⁿ1ⁿ | n ≥ 0}** — cadeias com a mesma quantidade de 0s e 1s consecutivos.

---

## 8. Funcionamento

A seguir, a descrição detalhada do que o software faz em cada etapa:

### 8.1. Leitura e Parsing (`parser.py`)

O parser lê o arquivo de entrada linha a linha:

1. **Linha 1** → extrai os 4 inteiros (nº estados, símbolos de entrada, símbolos da fita, transições).
2. **Linha 2** → constrói a lista de estados; o primeiro é o inicial, o último é o de aceitação.
3. **Linha 3** → monta o alfabeto de entrada.
4. **Linha 4** → monta o alfabeto da fita.
5. **Linhas 5 a 5+N** → parseia cada transição com expressão regular, criando objetos `Quintupla`.
6. **Última linha** → armazena a cadeia de entrada.

O resultado é um objeto `MTDefinition` com todos os dados prontos para uso.

### 8.2. Conversão de Quíntuplas para Quádruplas (`conversor.py`)

Para cada quíntupla, o conversor:

1. **Cria um estado intermediário** único (começando após o maior estado existente).
2. **Gera a quádrupla de escrita** (primeira metade da quíntupla).
3. **Gera a quádrupla de movimento** (segunda metade da quíntupla).
4. **Gera as quádruplas inversas** correspondentes (trocando estados, símbolos e direção).

Exemplo visual da conversão:

```
Quíntupla original:     (1, 0) → (2, $, R)

Par direto (ida):
  Q1 [ESCREVER]:  (1, 0) → (7, $)     lê '0', escreve '$', não move
  Q2 [MOVER]:     (7, $) → (2, R)     lê '$', move R, não escreve

Par inverso (volta):
  Q2⁻¹ [MOVER]:   (2, $) → (7, L)     move L (oposto de R)
  Q1⁻¹ [ESCREVER]: (7, $) → (1, 0)    lê '$', escreve '0' (restaura)
```

### 8.3. Inicialização da Fita (`fita.py`)

A fita é implementada como um **dicionário** `{posição: símbolo}`:

- Posições sem entrada no dicionário são consideradas `B` (branco).
- Isso simula naturalmente uma fita infinita sem alocar memória desnecessária.
- O cabeçote é representado por um inteiro `posicao` que pode crescer em ambas as direções.

### 8.4. Estágio 1 — Computação (`simulador_reversivel.py`)

O simulador executa um **loop principal**:

```
enquanto estado_atual ≠ estado_de_aceitação:
    1. lê o símbolo sob o cabeçote da Fita 1
    2. busca a quíntupla correspondente na tabela de lookup
    3. se não encontrar → rejeita (MT parou sem transição)
    4. executa a quíntupla: escreve na Fita 1 e move o cabeçote
    5. grava o índice da quíntupla na próxima posição da Fita 2
    6. atualiza o estado
```

A cada passo, o software imprime: estado, símbolo lido, símbolo escrito, direção e o conteúdo atual da Fita 1 (com `[colchetes]` indicando a posição do cabeçote).

### 8.5. Estágio 2 — Cópia

Após a computação:

1. Percorre todas as posições da Fita 1 que contêm símbolos não-brancos.
2. Copia cada símbolo sequencialmente para a Fita 3.
3. Restaura a posição original do cabeçote da Fita 1.

### 8.6. Estágio 3 — Retorno

O simulador **percorre a Fita 2 de trás para frente**:

```
para cada posição do histórico (do último ao primeiro):
    1. lê o índice da quíntupla gravado
    2. recupera a quíntupla original correspondente
    3. move o cabeçote da Fita 1 na direção OPOSTA
    4. escreve o símbolo ORIGINAL (desfaz a escrita)
    5. restaura o estado anterior
    6. apaga a posição da Fita 2 (escreve branco)
```

### 8.7. Validações Finais

Após os 3 estágios, o software verifica e reporta:

| Validação | Critério |
|-----------|----------|
| Fita 2 limpa | todas as posições devem conter apenas `B` |
| Fita 1 restaurada | conteúdo deve ser idêntico à entrada original |
| Estado restaurado | deve ser igual ao estado inicial |

Se todas as validações passam (`✓`), a reversibilidade foi demonstrada com sucesso.

---

## 9. Exemplo Completo

Para a entrada `0011` (linguagem 0ⁿ1ⁿ, n=2):

```
╔══════════════════════════════════════════════════════════╗
║  SIMULADOR DE MÁQUINA DE TURING REVERSÍVEL (Bennett)     ║
╚══════════════════════════════════════════════════════════╝

── Definição da MT ──
  Estados:            [1, 2, 3, 4, 5, 6]
  Estado inicial:     1
  Estado de aceitação:6
  Entrada:            '0011'

============================================================
  ESTÁGIO 1 — COMPUTAÇÃO (IDA)
============================================================
  Passo    1: Estado=1, Lê='0' → Escreve='$', Move=R, Estado'=2
  Passo    2: Estado=2, Lê='0' → Escreve='0', Move=R, Estado'=2
  Passo    3: Estado=2, Lê='1' → Escreve='X', Move=L, Estado'=4
  ...
  Passo   15: Estado=5, Lê='B' → Escreve='B', Move=R, Estado'=6

  ✓ Estado de aceitação (6) atingido em 15 passos.

============================================================
  ESTÁGIO 2 — CÓPIA
============================================================
  Copiados 4 símbolos para a Fita 3.
  Fita 3 (saída): $XXX

============================================================
  ESTÁGIO 3 — RETORNO (DESFAZER)
============================================================
  Desfaz    1: Quíntupla[16] inversa — Restaura='B'
  ...
  Desfaz   15: Quíntupla[0] inversa — Restaura='0'

  ✓ Retorno completo em 15 passos.

╔══════════════════════════════════════════════════════════╗
║  RESULTADO FINAL                                         ║
╚══════════════════════════════════════════════════════════╝

  Entrada '0011': ✓ ACEITA

── Validações de Reversibilidade ──
  Fita 2 (Histórico) limpa:     ✓
  Fita 1 restaurada ao original: ✓  (atual='0011', esperado='0011')
  Estado restaurado ao inicial:  ✓  (atual=1, esperado=1)

── Estatísticas ──
  Passos Estágio 1 (Ida):     15
  Passos Estágio 2 (Cópia):   4
  Passos Estágio 3 (Volta):   15
  Total de passos:            34
  Razão total/ida:            2.27x (Bennett prevê ~4V)
```

A razão de **2.27x** (ao invés de ~4x) ocorre porque o estágio de cópia é simples para esta entrada. Para computações mais longas, a razão se aproxima de 4V conforme previsto por Bennett.

---

## 10. Interface Gráfica de Visualização

Além da execução pelo terminal, o projeto possui uma interface gráfica para **visualizar a execução da Máquina de Turing Reversível em tempo real**.

A interface gráfica funciona como um **visualizador**, não substituindo a entrada pelo terminal. A definição da Máquina de Turing continua sendo lida normalmente pela **entrada padrão (`stdin`)**, mantendo o formato de entrada já descrito neste documento.

### 10.1. Visualização das três fitas

Durante a execução, a interface apresenta as três fitas utilizadas pelo modelo de Bennett:

- **Fita 1 — Trabalho:** mostra as alterações realizadas durante a computação e, posteriormente, sua restauração durante o retorno.
- **Fita 2 — Histórico:** mostra os registros das quíntuplas executadas e sua limpeza durante o estágio de retorno.
- **Fita 3 — Saída:** mostra os símbolos copiados durante o estágio de cópia.

As fitas são atualizadas visualmente conforme as operações do simulador acontecem. A posição do cabeçote também é indicada na representação gráfica.

### 10.2. Controles da interface

A interface possui apenas dois controles de execução:

- **Executar:** inicia a execução automática do simulador, atualizando a representação das fitas a cada passo.
- **Passo a Passo:** executa a simulação de forma controlada, permitindo avançar uma operação por vez e observar as alterações nas fitas.

Não há alteração na lógica da Máquina de Turing nem no formato de entrada utilizado pelo projeto.

### 10.3. Execução em paralelo com o terminal

A interface gráfica funciona em paralelo com a saída do terminal. Os `print()` originais do simulador continuam sendo executados, mantendo as informações detalhadas da execução no console.

Ao mesmo tempo, o simulador envia o estado atual das fitas, do cabeçote, do estado da máquina, do estágio e da transição para o visualizador gráfico.

Dessa forma, a mesma execução pode ser acompanhada:

1. **No terminal**, pelos `print()` detalhados do simulador.
2. **Na interface gráfica**, pela representação visual das três fitas em tempo real.

---

## Referências

- Bennett, C. H. (1973). *Logical Reversibility of Computation*. IBM Journal of Research and Development, 17(6), 525–532.
- Landauer, R. (1961). *Irreversibility and Heat Generation in the Computing Process*. IBM Journal of Research and Development, 5(3), 183–191.
