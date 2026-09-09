import re

class Tape:
    """Representa uma fita infinita da Máquina de Turing."""
    def __init__(self, initial_content="", blank_symbol='B'):
        self.blank = blank_symbol
        self.tape = {i: char for i, char in enumerate(initial_content)} if initial_content else {}
        self.head = 0

    def read(self):
        return self.tape.get(self.head, self.blank)

    def write(self, symbol):
        if symbol != '/':
            self.tape[self.head] = symbol

    def shift(self, direction):
        if direction == '+': self.head += 1
        elif direction == '-': self.head -= 1

    def get_content(self):
        if not self.tape: return ""
        min_idx = min(self.tape.keys())
        max_idx = max(self.tape.keys())
        content = "".join(self.tape.get(i, self.blank) for i in range(min_idx, max_idx + 1))
        return content.strip(self.blank)


class ReversibleTuringMachine:
    def __init__(self, quadruples, initial_state, input_string, blank_symbol='B'):
        self.tapes = [
            Tape(input_string, blank_symbol), # Fita 1: Input/Work
            Tape("", blank_symbol),           # Fita 2: History
            Tape("", blank_symbol)            # Fita 3: Output
        ]
        self.quadruples = quadruples
        self.state = initial_state
        self.halted = False

    def step(self):
        if self.halted:
            return

        r1, r2, r3 = [t.read() for t in self.tapes]
        
        # Busca transição que dá match nos símbolos lidos (considerando '/' como coringa de leitura)
        transition = None
        for (st, t1, t2, t3), trans in self.quadruples.items():
            if st == self.state and (t1 == '/' or t1 == r1) and (t2 == '/' or t2 == r2) and (t3 == '/' or t3 == r3):
                transition = trans
                break

        if not transition:
            self.halted = True
            return

        op1, op2, op3, next_state = transition

        # Executa as operações (Escrita ou Shift)
        for i, op in enumerate([op1, op2, op3]):
            if op in ('+', '-', '0'):
                self.tapes[i].shift(op)
            else:
                self.tapes[i].write(op)

        self.state = next_state

    def run(self, max_steps=5000):
        steps = 0
        while not self.halted and steps < max_steps:
            self.step()
            steps += 1
        return [t.get_content() for t in self.tapes]


def parse_and_compile(input_text):
    """Lê a entrada padrão e compila para quádruplas reversíveis."""
    lines = [line.strip() for line in input_text.strip().split('\n') if line.strip()]
    
    # Linha 1 a 4: Metadados
    num_states, num_in, num_tape, num_trans = map(int, lines[0].split())
    states = lines[1].split()
    in_symbols = lines[2].split()
    tape_symbols = lines[3].split()
    blank = 'B' # Assumindo 'B' como branco baseado no alfabeto
    
    quintuples = []
    # Linha 5 até 5 + num_trans - 1: Transições
    for i in range(4, 4 + num_trans):
        # Ex: (1,0)=(2,$,R)
        match = re.match(r'\((\w+),([^)]+)\)=\((\w+),([^)]+),([RLS])\)', lines[i])
        if match:
            q_state, q_read, q_next, q_write, q_dir = match.groups()
            shift = '+' if q_dir == 'R' else '-' if q_dir == 'L' else '0'
            quintuples.append((q_state, q_read, q_next, q_write, shift))
            
    initial_input = lines[-1]
    
    quadruples = {}
    
    # ---------------------------------------------------------
    # ESTÁGIO 1: Computação (Geração de Histórico)
    # ---------------------------------------------------------
    final_states = set(states) - set(q[0] for q in quintuples)
    A_f = list(final_states)[0] if final_states else states[-1]

    for m, (A_j, T, A_k, T_prime, shift) in enumerate(quintuples, start=1):
        A_m_prime = f"A_{m}_prime"
        m_str = str(m)
        
        # A_j [T / B] -> [T' + B] A_m'
        quadruples[(A_j, T, '/', blank)] = (T_prime, '+', blank, A_m_prime)
        
        # A_m' [/ B /] -> [sigma m 0] A_k
        quadruples[(A_m_prime, '/', blank, '/')] = (shift, m_str, '0', A_k)

    # ---------------------------------------------------------
    # ESTÁGIO 2: Cópia
    # ---------------------------------------------------------
    # O controle passa para o estado B_rewind para voltar ao início da fita 1,
    # em seguida copia para a fita 3, mantendo a fita 2 parada.
    B_rew = "B_rewind"
    B_copy = "B_copy"
    
    # Inicia a cópia (transição do estado final do estágio 1 para B_rew)
    # Mantemos a fita 2 no histórico e apenas retrocedemos a fita 1 até o branco
    quadruples[(A_f, '/', '/', '/')] = ('-', '0', '0', B_rew)
    
    for sym in tape_symbols:
        if sym != blank:
            quadruples[(B_rew, sym, '/', '/')] = ('-', '0', '0', B_rew)
            
    # Chegou no branco à esquerda, avança 1 para começar a copiar
    quadruples[(B_rew, blank, '/', '/')] = ('+', '0', '0', B_copy)
    
    # Copia fita 1 para fita 3
    for sym in tape_symbols:
        if sym != blank:
            state_copy_prime = f"B_copy_prime_{sym}"
            quadruples[(B_copy, sym, '/', blank)] = (sym, '0', sym, state_copy_prime)
            quadruples[(state_copy_prime, '/', '/', '/')] = ('+', '0', '+', B_copy)
            
    # Ao encontrar branco na fita 1 durante a cópia, passa para C_f (início do Retrace)
    C_f = f"C_{A_f}"
    quadruples[(B_copy, blank, '/', blank)] = (blank, '0', blank, C_f)

    # ---------------------------------------------------------
    # ESTÁGIO 3: Retrace (Computação Inversa)
    # ---------------------------------------------------------
    for m, (A_j, T, A_k, T_prime, shift) in enumerate(quintuples, start=1):
        C_j = f"C_{A_j}"
        C_k = f"C_{A_k}"
        C_m_prime = f"C_{m}_prime"
        m_str = str(m)
        inv_shift = '-' if shift == '+' else '+' if shift == '-' else '0'
        
        # C_k [/ m /] -> [inv_sigma B 0] C_m'
        quadruples[(C_k, '/', m_str, '/')] = (inv_shift, blank, '0', C_m_prime)
        
        # C_m' [T' / B] -> [T - B] C_j
        quadruples[(C_m_prime, T_prime, '/', blank)] = (T, '-', blank, C_j)

    return quadruples, states[0], initial_input, blank

# Entrada fornecida no prompt
raw_input_data = """6 2 5 17
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
0011"""

# Execução
quadruples, start_state, initial_input, blank_sym = parse_and_compile(raw_input_data)
machine = ReversibleTuringMachine(quadruples, start_state, initial_input, blank_symbol=blank_sym)

print(f"-> Iniciando a MT Reversível com a entrada: {initial_input}")
final_tapes = machine.run(max_steps=5000)

print("\nResultados Finais após os 3 Estágios (Computação, Cópia, Retrace):")
print(f"Fita 1 (Input Restaurado): {final_tapes[0]}")
print(f"Fita 2 (History Limpo):    {final_tapes[1] if final_tapes[1] else '<Vazia>'}")
print(f"Fita 3 (Saída Gerada):     {final_tapes[2]}")
