import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import sqlite3
import os
import webbrowser
from pathlib import Path
import shutil
from typing import Optional
import docx

# Estilos personalizados
ESTILO_BG = "#cbe3d8"
ESTILO_ALT_BG = "#cbbce5"
ESTILO_FONTE = ("Segoe UI", 11)
ESTILO_TITULO = ("Segoe UI", 13, "bold")
ESTILO_ENTRY = {
    "bg": "white",  # <- fundo branco para os campos de entrada
    "fg": "black",
    "bd": 0,
    "highlightthickness": 1,
    "highlightbackground": "#a9a9a9",
    "font": ESTILO_FONTE
}

def criar_banco():
    conn = sqlite3.connect("veterinario.db")
    cursor = conn.cursor()

    # Tabela de tutores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tutores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            endereco TEXT,
            telefone TEXT,
            rg TEXT,
            cpf TEXT UNIQUE
        )
    ''')

    # Tabela de pacientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            idade INTEGER,
            peso REAL,
            especie TEXT,
            raca TEXT,
            foto TEXT,
            tutor_id INTEGER,
            FOREIGN KEY (tutor_id) REFERENCES tutores(id) ON DELETE CASCADE
        )
    ''')

    # Tabela de exames
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            caminho_pdf TEXT NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados criado com sucesso!")

def abrir_tela_cadastro(root):
    root.destroy()
    cadastro = tk.Tk()
    cadastro.title("Cadastro de Paciente")
    cadastro.geometry("1920x1032+0+0")
    cadastro.state("zoomed")
    cadastro.configure(bg=ESTILO_BG)
    caminho_foto: Optional[str] = None
    caminhos_exames = []

    # Define o ícone da janela
    cadastro.iconbitmap("iconapplication.ico")

    frame_principal = tk.Frame(cadastro, bg=ESTILO_BG)
    frame_principal.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

    frame_esquerda = tk.Frame(frame_principal, bg=ESTILO_BG)
    frame_esquerda.grid(row=0, column=0, padx=20, pady=20)

    tk.Label(frame_esquerda, text="Dados do Paciente", font=ESTILO_TITULO, bg=ESTILO_BG).pack(anchor="w", pady=(0, 10))
    campos_paciente = ["Nome", "Idade", "Peso", "Espécie", "Raça"]
    entries_paciente = {}

    for campo in campos_paciente:
        tk.Label(frame_esquerda, text=campo + ":", font=ESTILO_FONTE, bg=ESTILO_BG).pack(anchor="w")
        entry = tk.Entry(frame_esquerda, **ESTILO_ENTRY, width=30)
        entry.pack()
        entries_paciente[campo] = entry

    frame_direita = tk.Frame(frame_principal, bg=ESTILO_BG)
    frame_direita.grid(row=0, column=1, padx=20, pady=20)

    tk.Label(frame_direita, text="Dados do Tutor", font=ESTILO_TITULO, bg=ESTILO_BG).pack(anchor="w", pady=(0, 10))
    campos_tutor = ["Nome", "Endereço", "Telefone", "RG", "CPF"]
    entries_tutor = {}

    for campo in campos_tutor:
        tk.Label(frame_direita, text=campo + ":", font=ESTILO_FONTE, bg=ESTILO_BG).pack(anchor="w")
        entry = tk.Entry(frame_direita, **ESTILO_ENTRY, width=30)
        entry.pack()
        entries_tutor[campo] = entry

    frame_botoes = tk.Frame(frame_principal, bg=ESTILO_BG)
    frame_botoes.grid(row=1, column=0, columnspan=2, pady=20)

    def anexar_foto():
        nonlocal caminho_foto
        arquivo = filedialog.askopenfilename()
        if arquivo:
            caminho_foto = arquivo
            messagebox.showinfo("Sucesso", "Foto anexada com sucesso!")

    def anexar_exames():
        nonlocal caminhos_exames
        arquivos = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if arquivos:
            caminhos_exames = arquivos
            messagebox.showinfo("Sucesso", "Exames anexados com sucesso!")

    tk.Button(frame_botoes, text="Anexar Foto", font=ESTILO_FONTE, command=anexar_foto).pack(pady=5)
    tk.Button(frame_botoes, text="Anexar Exames (PDF)", font=ESTILO_FONTE, command=anexar_exames).pack(pady=5)

    def salvar_dados():
        # Captura dos dados
        nonlocal caminho_foto
        nome_tutor = entries_tutor["Nome"].get()
        endereco = entries_tutor["Endereço"].get()
        telefone = entries_tutor["Telefone"].get()
        rg = entries_tutor["RG"].get()
        cpf = entries_tutor["CPF"].get()

        nome_paciente = entries_paciente["Nome"].get()
        idade = entries_paciente["Idade"].get()
        peso = entries_paciente["Peso"].get()
        especie = entries_paciente["Espécie"].get()
        raca = entries_paciente["Raça"].get()

        try:
            idade = int(idade)
            peso = float(peso)
            rg = int(rg)
            cpf = int(cpf)
            telefone = int(telefone)
        except ValueError:
            messagebox.showerror("Erro", "Idade, Peso, Telefone, RG e CPF devem ser algarismos")
            return

        if not nome_tutor or not cpf or not nome_paciente:
            messagebox.showerror("Erro", "Nome do tutor, CPF e nome do paciente são obrigatórios.")
            return

        try:
            conn = sqlite3.connect("veterinario.db")
            cursor = conn.cursor()

            # Inserir tutor
            cursor.execute('''
                INSERT INTO tutores (nome, endereco, telefone, rg, cpf)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome_tutor, endereco, telefone, rg, cpf))
            tutor_id = cursor.lastrowid

            # Inserir paciente (foto temporariamentee como None)
            cursor.execute('''
                INSERT INTO pacientes (nome, idade, peso, especie, raca, foto, tutor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome_paciente, idade, peso, especie, raca, None, tutor_id))
            paciente_id = cursor.lastrowid

            # Criar pasta do paciente
            pasta_paciente = Path("pacientes") / f"{nome_paciente}_{paciente_id}"
            pasta_paciente.mkdir(parents=True, exist_ok=True)

            # Copiar foto
            if caminho_foto is not None:
                caminho_foto_path = Path(caminho_foto)
                destino_foto = pasta_paciente / Path(caminho_foto).name
                shutil.copy2(str(caminho_foto_path), str(destino_foto))
                caminho_foto = str(destino_foto)
                cursor.execute("UPDATE pacientes SET foto = ? WHERE id = ?", (str(destino_foto), paciente_id))

            # Copiar exames
            for caminho_pdf in caminhos_exames:
                destino_pdf = pasta_paciente / Path(caminho_pdf).name
                shutil.copy2(caminho_pdf, destino_pdf)
                cursor.execute("INSERT INTO exames (paciente_id, caminho_pdf) VALUES (?, ?)", (paciente_id, str(destino_pdf)))

            # Copiar receituário padrão
            modelo_receituario = Path("modelos/receituario_padrao.docx")
            destino_receituario = pasta_paciente / "receituario_padrao.docx"

            if modelo_receituario.exists():
                shutil.copy2(modelo_receituario, destino_receituario)

            # Copiar anamnese padrão
            modelo_anamnese = Path("modelos/anamnese_padrao.docx")
            destino_anamnese = pasta_paciente / "anamnese_padrao.docx"
            if modelo_anamnese.exists():
                shutil.copy2(modelo_anamnese, destino_anamnese)

            try:
                conn.commit()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")
            finally:
                conn.close()

            messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")

            cadastro.destroy()
            iniciar_interface()

        except sqlite3.IntegrityError as e:

            if "UNIQUE constraint failed: tutores.cpf" in str(e):
                messagebox.showerror("Erro", "CPF já cadastrado para outro tutor.")
            else:
                messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")

    tk.Button(frame_botoes, text="Salvar", font=ESTILO_TITULO, command=salvar_dados).pack(pady=10)
    frame_voltar = tk.Frame(cadastro, bg=ESTILO_BG)
    frame_voltar.pack(side=tk.BOTTOM, anchor="w", padx=20, pady=20)

    tk.Button(frame_voltar, text="Voltar", font=ESTILO_FONTE,
              command=lambda: [cadastro.destroy(), iniciar_interface()]).pack(anchor="w")


def abrir_tela_historico():
    historico = tk.Tk()
    historico.title("Histórico de Pacientes")
    historico.geometry("1920x1032+0+0")
    historico.state("zoomed")
    historico.configure(bg=ESTILO_BG)

    # Define o ícone da janela
    historico.iconbitmap("iconapplication.ico")

    frame_principal = tk.Frame(historico, bg=ESTILO_BG)
    frame_principal.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    tk.Label(frame_principal, text="Histórico de Pacientes", font=ESTILO_TITULO, bg=ESTILO_BG).pack(pady=10)

    # Frame da lista de pacientes
    frame_lista = tk.Frame(frame_principal, bg=ESTILO_BG)
    frame_lista.pack(fill=tk.BOTH, expand=True)

    # Criar uma Treeview para listar os pacientes
    tree = ttk.Treeview(frame_lista, columns=("Nome",), show="headings")
    tree.heading("Nome", text="Nome do Paciente")
    tree.column("Nome", width=300)
    tree.pack(fill=tk.BOTH, expand=True, pady=10)

    def carregar_pacientes():
        # Conectar ao banco de dados e buscar pacientes
        conn = sqlite3.connect("veterinario.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM pacientes ORDER BY nome ASC")
        pacientes = cursor.fetchall()
        conn.close()

        # Limpar lista
        for item in tree.get_children():
            tree.delete(item)

        # Adicionar os pacientes na Treeview
        for paciente_id, nome in pacientes:
            tree.insert("", tk.END, values=(nome,), iid=paciente_id)

    def ver_paciente():
        item = tree.focus()

        if item:
            paciente_id = item
            historico.destroy()
            abrir_tela_visualizacao_edicao(paciente_id)
        else:
            messagebox.showwarning("Aviso", "Selecione um paciente para visualizar.")

    def excluir_paciente():
        item = tree.focus()
        if item:
            paciente_id = item
            resposta = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este paciente?")

            if resposta:
                conn = sqlite3.connect("veterinario.db")
                cursor = conn.cursor()

                # Buscar nome do paciente para montar o nome da pasta
                cursor.execute("SELECT nome FROM pacientes WHERE id = ?", (paciente_id,))
                resultado = cursor.fetchone()

                if resultado:
                    nome = resultado[0]
                    nome_pasta = f"{nome}_{paciente_id}"
                    pasta = Path("pacientes") / nome_pasta

                    # Apagar paciente do banco
                    cursor.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
                    conn.commit()
                    conn.close()

                    # Apagar pasta física
                    if pasta.exists():
                        try:
                            shutil.rmtree(pasta)
                        except Exception as e:
                            messagebox.showwarning("Aviso", f"Erro ao excluir pasta: {e}")
                            return

                    carregar_pacientes()
                    messagebox.showinfo("Sucesso", "Paciente excluído com sucesso.")
                else:
                    messagebox.showerror("Erro", "Paciente não encontrado no banco de dados.")
        else:
            messagebox.showwarning("Aviso", "Selecione um paciente para excluir.")

    frame_botoes = tk.Frame(frame_principal, bg=ESTILO_BG)
    frame_botoes.pack(pady=10)
    tk.Button(frame_botoes, text="Ver", font=ESTILO_FONTE, command=ver_paciente).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_botoes, text="Excluir", font=ESTILO_FONTE, command=excluir_paciente).pack(side=tk.LEFT, padx=10)
    tk.Button(historico, text="Voltar", font=ESTILO_FONTE, command=lambda: [historico.destroy(), iniciar_interface()]).pack(side=tk.BOTTOM, anchor=tk.W, padx=20, pady=20)

    carregar_pacientes()
    historico.mainloop()


def abrir_tela_visualizacao_edicao(paciente_id):
    visualizacao = tk.Tk()
    visualizacao.title("Visualização e Edição de Paciente")
    visualizacao.geometry("1920x1032+0+0")
    visualizacao.state("zoomed")
    visualizacao.configure(bg=ESTILO_BG)

    # Define o ícone da janela
    visualizacao.iconbitmap("iconapplication.ico")

    conn = sqlite3.connect("veterinario.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.nome, p.idade, p.peso, p.especie, p.raca, p.foto,
               t.nome, t.endereco, t.telefone, t.rg, t.cpf,
               p.id, t.id
        FROM pacientes p
        JOIN tutores t ON p.tutor_id = t.id
        WHERE p.id = ?
    """, (paciente_id,))
    dados = cursor.fetchone()

    if not dados:
        messagebox.showerror("Erro", "Paciente não encontrado.")
        visualizacao.destroy()
        return

    (nome_paciente, idade, peso, especie, raca, foto,
     nome_tutor, endereco, telefone, rg, cpf,
     id_paciente, id_tutor) = dados
    rg_original = str(rg)
    cpf_original = str(cpf)

    caminhos_novos_exames = []
    nova_foto_path = foto

    frame = tk.Frame(visualizacao, bg=ESTILO_BG)
    frame.place(relx=0.5, rely= 0.3, anchor="center")

    def criar_entry(parent, texto, valor):
        tk.Label(parent, text=texto + ":", font=ESTILO_FONTE, bg=ESTILO_BG).pack(anchor="w")
        entry = tk.Entry(parent, font=ESTILO_FONTE, width=30, bg="white", bd=0, highlightthickness=1,
                         highlightbackground="#a9a9a9")
        entry.insert(0, valor)
        entry.pack()
        return entry

    frame_paciente = tk.Frame(frame, bg=ESTILO_BG)
    frame_paciente.grid(row=0, column=0, padx=10, pady=10, sticky="n")
    tk.Label(frame_paciente, text="Dados do Paciente", font=ESTILO_TITULO, bg=ESTILO_BG).pack(pady=(0, 10))

    entry_nome = criar_entry(frame_paciente, "Nome", nome_paciente)
    entry_idade = criar_entry(frame_paciente, "Idade", idade)
    entry_peso = criar_entry(frame_paciente, "Peso", peso)
    entry_especie = criar_entry(frame_paciente, "Espécie", especie)
    entry_raca = criar_entry(frame_paciente, "Raça", raca)

    frame_foto = tk.Frame(visualizacao, bg=ESTILO_BG)
    frame_foto.place(relx=0.15, rely=0.35, anchor="center")

    label_foto = tk.Label(frame_foto, bg=ESTILO_BG)
    label_foto.pack()

    def exibir_foto(caminho):
        if caminho and os.path.exists(caminho):
            img = Image.open(caminho)
            img.thumbnail((150, 150))
            foto_tk = ImageTk.PhotoImage(img)
            label_foto.image = foto_tk
            label_foto.configure(image=foto_tk)

    def trocar_foto():
        nonlocal nova_foto_path
        arquivo = filedialog.askopenfilename()
        if arquivo:
            nova_foto_path = arquivo
            exibir_foto(nova_foto_path)

    exibir_foto(foto)

    btn_trocar_foto = tk.Button(frame_foto, text="Trocar Foto", font=ESTILO_FONTE, command=trocar_foto)
    btn_trocar_foto.pack(pady=5)

    frame_tutor = tk.Frame(frame, bg=ESTILO_BG)
    frame_tutor.grid(row=0, column=1, padx=10, pady=10, sticky="n")
    tk.Label(frame_tutor, text="Dados do Tutor", font=ESTILO_TITULO, bg=ESTILO_BG).pack(pady=(0, 10))

    entry_tutor = {
        "nome": criar_entry(frame_tutor, "Nome", nome_tutor),
        "endereço": criar_entry(frame_tutor, "Endereço", endereco),
        "telefone": criar_entry(frame_tutor, "Telefone", telefone),
        "rg": criar_entry(frame_tutor, "RG", rg),
        "cpf": criar_entry(frame_tutor, "CPF", cpf)
    }

    def abrir_exames():
        cursor.execute("SELECT caminho_pdf FROM exames WHERE paciente_id = ?", (paciente_id,))
        exames = cursor.fetchall()

        for (caminho,) in exames:
            if os.path.exists(caminho):
                webbrowser.open(caminho)
            else:
                messagebox.showwarning("Aviso", f"Arquivo {caminho} não encontrado.")

    def anexar_novos_exames():
        arquivos = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])

        if arquivos:
            caminhos_novos_exames.extend(arquivos)
            messagebox.showinfo("Sucesso", "Novos exames anexados!")

    def abrir_receituario():
        pasta = Path(f"pacientes/{nome_paciente}_{id_paciente}")
        receituario = pasta / "receituario_padrao.docx"
        if receituario.exists():
            webbrowser.open(str(receituario))
        else:
            messagebox.showerror("Erro", "Receituário não encontrado.")

    def abrir_anamnese():
        pasta = Path(f"pacientes/{nome_paciente}_{id_paciente}")
        anamnese = pasta / "anamnese_padrao.docx"
        if anamnese.exists():
            webbrowser.open(str(anamnese))
        else:
            messagebox.showerror("Erro", "Anamnese não encontrada.")


    def salvar_alteracoes():
        # Validação de CPF e RG
        rg_input = entry_tutor["rg"].get().strip()
        cpf_input = entry_tutor["cpf"].get().strip()

        if cpf_input != cpf_original or rg_input != rg_original:
            messagebox.showerror("Erro", "Não é permitido alterar o CPF ou RG do tutor.")
            return

        # Validação de idade e peso
        try:
            idade= int(entry_idade.get().strip())
            peso = float(entry_peso.get().strip())
        except ValueError:
            messagebox.showerror("Erro", "Idade deve ser número inteiro e peso deve ser número decimal (com ponto).")
            return

        # Se chegou aqui, pode atualizar no banco
        try:
            cursor.execute("""
                UPDATE pacientes SET nome=?, idade=?, peso=?, especie=?, raca=?, foto=? WHERE id=?
            """, (entry_nome.get(), idade, peso,
                  entry_especie.get(), entry_raca.get(), nova_foto_path, paciente_id))

            cursor.execute("""
                UPDATE tutores SET nome=?, endereco=?, telefone=?, rg=?, cpf=? WHERE id=?
            """, (entry_tutor["nome"].get(), entry_tutor["endereço"].get(), entry_tutor["telefone"].get(),
                  rg_input, cpf_input, id_tutor))

            # Salva exames novos com cópia para pasta do paciente
            pasta_paciente = Path("pacientes") / f"{nome_paciente}_{id_paciente}"
            pasta_paciente.mkdir(parents=True, exist_ok=True)

            for exame in caminhos_novos_exames:
                nome_arquivo = Path(exame).name
                destino_pdf = pasta_paciente / nome_arquivo

                if not destino_pdf.exists():
                    shutil.copy2(exame, destino_pdf)

                cursor.execute("INSERT INTO exames (paciente_id, caminho_pdf) VALUES (?, ?)",
                               (paciente_id, str(destino_pdf)))

            conn.commit()
            messagebox.showinfo("Sucesso", "Alterações salvas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar alterações: {e}")

    frame_botoes = tk.Frame(visualizacao, bg=ESTILO_BG)
    frame_botoes.place(relx=0.5, rely=0.7, anchor="center")

    tk.Button(frame_botoes, text="Abrir Exames", font=ESTILO_FONTE, width=25, command=abrir_exames).pack(pady=5)
    tk.Button(frame_botoes, text="Anexar Novos Exames (PDF)", font=ESTILO_FONTE, width=25, command=anexar_novos_exames).pack(pady=5)
    tk.Button(frame_botoes, text="Abrir Receituário Padrão", font=ESTILO_FONTE, width=25, command=abrir_receituario).pack(pady=5)
    tk.Button(frame_botoes, text="Abrir Anamnese", font=ESTILO_FONTE, width=25, command=abrir_anamnese).pack(pady=5)
    tk.Button(frame_botoes, text="Salvar Alterações", font=ESTILO_TITULO, width=25, command=salvar_alteracoes).pack(pady=10)

    frame_voltar = tk.Frame(visualizacao, bg=ESTILO_BG)
    frame_voltar.pack(side=tk.BOTTOM, anchor="w", padx=20, pady=20)

    tk.Button(frame_voltar, text="Voltar", font=ESTILO_FONTE,
              command=lambda: [visualizacao.destroy(), abrir_tela_historico()]).pack(anchor="w")

    visualizacao.mainloop()

def iniciar_interface():
    root = tk.Tk()
    root.title("Sistema Veterinário")
    root.geometry("1920x1032+0+0")
    root.state("zoomed")
    root.configure(bg=ESTILO_BG)

    # Define o ícone da janela
    root.iconbitmap("iconapplication.ico")

    frame = tk.Frame(root, bg=ESTILO_BG)
    frame.pack(expand=True)

    btn_cadastrar = tk.Button(frame, text="CADASTRAR", width=20, pady=10, font=ESTILO_TITULO, command=lambda: abrir_tela_cadastro(root))
    btn_cadastrar.pack(pady=20)

    btn_historico = tk.Button(frame, text="HISTÓRICO", width=20, pady=10, font=ESTILO_TITULO, command=lambda: [root.destroy(), abrir_tela_historico()])
    btn_historico.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    criar_banco()
    iniciar_interface()