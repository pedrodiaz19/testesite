# app.py (somente trecho alterado da função buscar_processo_por_entrada)

def buscar_processo_por_entrada(entrada):
    db_processos = os.path.join(BASE_DIR, "processos.db")
    db_calculos = os.path.join(BASE_DIR, "calculos.db")

    conn_proc = sqlite3.connect(db_processos)
    cursor_proc = conn_proc.cursor()

    resultados = []

    cursor_proc.execute("SELECT processo, vara, nome, status, cpf, matriculas, tipo FROM processos WHERE cpf = ?", (entrada,))
    resultados = cursor_proc.fetchall()

    if not resultados:
        cursor_proc.execute("SELECT processo, vara, nome, status, cpf, matriculas, tipo FROM processos")
        for row in cursor_proc.fetchall():
            processo, vara, nome, status, cpf, matriculas, tipo = row
            lista_matriculas = [m.strip() for m in re.split(r"[\/,]", matriculas)]
            if entrada in lista_matriculas:
                resultados.append(row)

    if not resultados:
        conn_proc.close()
        return []

    conn_proc.close()

    # Conectar ao banco de cálculos
    conn_calc = sqlite3.connect(db_calculos)
    cursor_calc = conn_calc.cursor()

    saida = []
    for processo, vara, nome, status, cpf, matriculas, tipo in resultados:
        todas_matriculas = [m.strip() for m in re.split(r"[\/,]", matriculas) if m.strip()]
        links = []

        cursor_calc.execute("SELECT nome, matriculas, link, link_extra FROM calculos")
        for nome_calc, matr_calc, link, link_extra in cursor_calc.fetchall():
            mats = [m.strip() for m in re.split(r"[\/,]", matr_calc)] if matr_calc else []

            if any(m in todas_matriculas for m in mats):
                if tipo in ("SEPE 1", "SFPMVR"):
                    if link and link not in links:
                        links.append(link)
                else:
                    if link_extra and link_extra not in links:
                        links.append(link_extra)

        if not links:
            nome_normalizado = re.sub(r"\s+", "", nome).lower()
            cursor_calc.execute("SELECT nome, link FROM calculos")
            for nome_calc, link in cursor_calc.fetchall():
                nome_calc_normalizado = re.sub(r"\s+", "", nome_calc).lower()
                if nome_normalizado == nome_calc_normalizado:
                    if link not in links:
                        links.append(link)

        saida.append({
            "processo": processo,
            "tipo": tipo,
            "vara": vara,
            "nome": nome,
            "status": status,
            "cpf": cpf,
            "matriculas": " / ".join(todas_matriculas),
            "calculos": links
        })

    conn_calc.close()
    return saida
