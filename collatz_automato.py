import tkinter as tk
from tkinter import messagebox
import random

class CollatzAutomatonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autômato Celular de Collatz Binário")
        self.root.geometry("900x650")
        self.root.configure(bg="#1e1e2e")

        self.current_number = 27  # Número clássico com trajetória longa (111 passos)
        self.setup_ui()
        self.generate_and_draw()

    def setup_ui(self):
        # Painel Superior de Controles
        control_frame = tk.Frame(self.root, bg="#282a36", pady=10, padx=10)
        control_frame.pack(fill=tk.X)

        tk.Label(
            control_frame, text="Número Inicial (n):", 
            fg="#f8f8f2", bg="#282a36", font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT, padx=5)

        self.entry_num = tk.Entry(control_frame, font=("Consolas", 12), width=15)
        self.entry_num.insert(0, str(self.current_number))
        self.entry_num.pack(side=tk.LEFT, padx=5)
        self.entry_num.bind("<Return>", lambda event: self.on_calculate())

        # Botões de Ação
        btn_style = {"font": ("Arial", 10, "bold"), "bd": 0, "padx": 10, "pady": 5, "cursor": "hand2"}
        
        tk.Button(
            control_frame, text="Calcular", bg="#50fa7b", fg="#282a36", 
            command=self.on_calculate, **btn_style
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            control_frame, text="- 1", bg="#6272a4", fg="#f8f8f2", 
            command=lambda: self.adjust_number(-1), **btn_style
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            control_frame, text="+ 1", bg="#6272a4", fg="#f8f8f2", 
            command=lambda: self.adjust_number(1), **btn_style
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            control_frame, text="Aleatório (Ímpar)", bg="#bd93f9", fg="#282a36", 
            command=self.random_odd, **btn_style
        ).pack(side=tk.LEFT, padx=5)

        # Opção de Alinhamento dos Bits
        self.align_var = tk.StringVar(value="right")
        tk.Label(
            control_frame, text="Alinhamento:", fg="#f8f8f2", bg="#282a36", font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(15, 5))
        
        tk.Radiobutton(
            control_frame, text="Direita (LSB)", variable=self.align_var, value="right",
            bg="#282a36", fg="#f8f8f2", selectcolor="#44475a", command=self.generate_and_draw
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            control_frame, text="Esquerda (MSB)", variable=self.align_var, value="left",
            bg="#282a36", fg="#f8f8f2", selectcolor="#44475a", command=self.generate_and_draw
        ).pack(side=tk.LEFT)

        # Painel de Estatísticas
        self.stats_label = tk.Label(
            self.root, text="", fg="#8be9fd", bg="#1e1e2e", font=("Consolas", 10), pady=5
        )
        self.stats_label.pack(fill=tk.X)

        # Área de Visualização (Canvas com Scrollbars)
        canvas_frame = tk.Frame(self.root, bg="#1e1e2e")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(
            canvas_frame, bg="#181825", highlightthickness=0,
            yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set
        )

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def get_collatz_binary_steps(self, n):
        steps = []
        max_val = n
        while n > 1:
            steps.append((n, bin(n)[2:]))
            if n % 2 == 0:
                n = n // 2
            else:
                n = 3 * n + 1
            if n > max_val:
                max_val = n
        steps.append((1, "1"))
        return steps, max_val

    def generate_and_draw(self):
        self.canvas.delete("all")
        steps, max_val = self.get_collatz_binary_steps(self.current_number)
        
        total_steps = len(steps) - 1
        max_bits = len(bin(max_val)[2:])
        
        self.stats_label.config(
            text=f"Início: {self.current_number} ({bin(self.current_number)[2:]}) | "
                 f"Passos até 1: {total_steps} | Pico Máximo: {max_val} ({max_bits} bits)"
        )

        # Ajuste dinâmico do tamanho da célula (pixel) do autômato
        cell_size = max(4, min(16, 750 // max(max_bits, 1)))
        offset_x = 120  # Espaço para mostrar o valor decimal ao lado
        offset_y = 20

        for row_idx, (dec_val, bin_str) in enumerate(steps):
            y1 = offset_y + row_idx * cell_size
            y2 = y1 + cell_size

            # Exibe o número decimal à esquerda se as células forem grandes o suficiente
            if cell_size >= 8:
                self.canvas.create_text(
                    offset_x - 10, (y1 + y2) / 2, text=str(dec_val),
                    anchor="e", fill="#6272a4", font=("Consolas", 8)
                )

            # Define o deslocamento horizontal com base no alinhamento escolhido
            if self.align_var.get() == "right":
                start_col = max_bits - len(bin_str)
            else:
                start_col = 0

            # Desenha cada bit como uma célula do autômato
            for bit_idx, bit in enumerate(bin_str):
                col_idx = start_col + bit_idx
                x1 = offset_x + col_idx * cell_size
                x2 = x1 + cell_size

                # Cor: Verde/Ciano para bit '1', Cinza escuro para bit '0'
                if bit == "1":
                    color = "#ff79c6" if dec_val % 2 != 0 else "#50fa7b"
                else:
                    color = "#282a36"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#181825" if cell_size > 5 else ""
                )

        # Atualiza a área de rolagem do Canvas
        total_width = offset_x + (max_bits * cell_size) + 40
        total_height = offset_y + (len(steps) * cell_size) + 40
        self.canvas.config(scrollregion=(0, 0, total_width, total_height))

    def on_calculate(self):
        try:
            val = int(self.entry_num.get())
            if val < 1:
                raise ValueError
            self.current_number = val
            self.generate_and_draw()
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número inteiro positivo (maior que 0).")

    def adjust_number(self, delta):
        new_val = max(1, self.current_number + delta)
        self.current_number = new_val
        self.entry_num.delete(0, tk.END)
        self.entry_num.insert(0, str(new_val))
        self.generate_and_draw()

    def random_odd(self):
        new_val = random.randrange(3, 100000, 2)
        self.current_number = new_val
        self.entry_num.delete(0, tk.END)
        self.entry_num.insert(0, str(new_val))
        self.generate_and_draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = CollatzAutomatonApp(root)
    root.mainloop()
