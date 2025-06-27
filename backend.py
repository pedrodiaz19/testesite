# app.py
import os 
import re
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 5000))

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)

@app.route("/index.html")
def index_html():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/consulta", methods=["GET"])
def consulta():
    entrada = request.args.get("processo", "").strip()
    if not entrada:
        return jsonify({"erro": "Número do processo, CPF ou matrícula é obrigatório"}), 400

    entrada = re.sub(r"[^\d]", "", entrada)  # remove caracteres não numéricos

    resultados = buscar_processo_por_entrada(entrada)
    if resultados:
        return jsonify(resultados)
    else:
        return jsonify({"erro": "Nenhum resultado encontrado"}), 404

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
            lista_matriculas = [m.strip() for m in re.split(r"[\/,"]", matriculas)]
            if entrada in lista_matriculas:
                resultados.append(row)

    if not resultados:
        conn_proc.close()
        return []

    todas_matriculas = []
    tipos = set()
    processo_ref, vara_ref, nome_ref, status_ref, cpf_ref, _ = resultados[0][:6]

    for row in resultados:
        _, _, _, _, _, matriculas, tipo = row
        tipos.add(tipo)
        todas_matriculas.extend([m.strip() for m in re.split(r"[\/,"]", matriculas)])

    todas_matriculas = list(set(m for m in todas_matriculas if m))

    conn_proc.close()

    conn_calc = sqlite3.connect(db_calculos)
    cursor_calc = conn_calc.cursor()

    links = []
    cursor_calc.execute("SELECT nome, matriculas, link, link_extra FROM calculos")
    for nome_calc, matr_calc, link, link_extra in cursor_calc.fetchall():
        mats = [m.strip() for m in re.split(r"[\/,"]", matr_calc)] if matr_calc else []

        if any(m in todas_matriculas for m in mats):
            if any(t in ("SEPE 1", "SFPMVR") for t in tipos):
                if link and link not in links:
                    links.append(link)
            else:
                if link_extra and link_extra not in links:
                    links.append(link_extra)

    if not links:
        nome_normalizado = re.sub(r"\s+", "", nome_ref).lower()
        cursor_calc.execute("SELECT nome, link FROM calculos")
        for nome_calc, link in cursor_calc.fetchall():
            nome_calc_normalizado = re.sub(r"\s+", "", nome_calc).lower()
            if nome_normalizado == nome_calc_normalizado:
                if link not in links:
                    links.append(link)

    conn_calc.close()

    return [{
        "processo": processo_ref,
        "vara": vara_ref,
        "nome": nome_ref,
        "status": status_ref,
        "cpf": cpf_ref,
        "matriculas": " / ".join(todas_matriculas),
        "calculos": links
    }]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

