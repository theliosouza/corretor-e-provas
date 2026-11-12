"""Corrige uma pasta de ZIPs e gera dois CSVs para abrir no Excel."""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import uuid
from collections import Counter
from pathlib import Path

IMAGE = "corretor-python:local"
MAX_ZIP_BYTES = 8 * 1024 * 1024
TIMEOUT = 45
STATUS = {"Certa", "Incorreta", "Em branco", "Rever"}
BLOCKS = (("Listas", 0, 15, 8), ("Matrizes", 15, 30, 8), ("Bloco final", 30, 40, 5))


def docker_ready():
    try:
        check = subprocess.run(
            ["docker", "image", "inspect", IMAGE],
            capture_output=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("Abra o Docker Desktop com contêineres Linux e tente novamente.") from error
    if check.returncode:
        raise ValueError(f"Abra o Docker e prepare a imagem com docker build -t {IMAGE} .")


def evaluate_zip(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_ZIP_BYTES + 1)
    if len(raw) > MAX_ZIP_BYTES:
        raise ValueError("O ZIP ultrapassa o limite de 8 MiB.")
    container = f"corretor-{uuid.uuid4().hex}"
    command = [
        "docker", "run", "--rm", "--pull", "never", "--interactive", "--name", container,
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges=true", "--pids-limit", "32",
        "--memory", "384m", "--memory-swap", "384m", "--cpus", "1",
        IMAGE,
    ]
    try:
        process = subprocess.run(command, input=raw, capture_output=True, timeout=TIMEOUT, check=False)
    except subprocess.TimeoutExpired as error:
        try:
            subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
        raise ValueError("A correção desse ZIP excedeu o tempo limite.") from error
    if process.returncode:
        raise ValueError("O contêiner não concluiu a correção. Confira se o Docker está em execução.")
    try:
        response = json.loads(process.stdout)
        if "error" in response:
            raise ValueError(response["error"])
        results = response["results"]
        fingerprint = response["fingerprint"]
        if [row["question"] for row in results] != list(range(1, 41)) or len(fingerprint) != 64:
            raise ValueError("Resultado incompleto.")
        if any(row["status"] not in STATUS or not isinstance(row["note"], str) for row in results):
            raise ValueError("Resultado inválido.")
    except (TypeError, KeyError, json.JSONDecodeError) as error:
        raise ValueError("O motor devolveu uma resposta inválida.") from error
    return response


def read_names(path):
    if path is None:
        return {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        if not reader.fieldnames or not {"Arquivo", "Aluno"}.issubset(reader.fieldnames):
            raise ValueError("O CSV de nomes precisa das colunas Arquivo;Aluno.")
        names = {}
        for line, row in enumerate(reader, 2):
            name = (row["Aluno"] or "").strip()
            filename = (row["Arquivo"] or "").strip().replace(chr(92), "/")
            if not filename and not name:
                continue
            if not filename or not name or filename in names:
                raise ValueError(f"Nome ausente ou arquivo repetido na linha {line} do CSV de nomes.")
            names[filename] = name
    return names


def collect_paths(source):
    if source.is_file() and source.suffix.lower() == ".zip":
        return source.parent, [source]
    if not source.is_dir():
        raise ValueError("Informe a pasta das entregas ou o caminho de um ZIP.")
    paths = sorted(
        (item for item in source.rglob("*") if item.is_file() and item.suffix.lower() == ".zip"),
        key=lambda item: item.as_posix().casefold(),
    )
    if not paths:
        raise ValueError("Nenhum ZIP encontrado nessa pasta.")
    return source, paths


def run_batch(root, paths, names, evaluate=evaluate_zip):
    batch = []
    for path in paths:
        filename = path.relative_to(root).as_posix()
        name = names.get(filename) or names.get(path.name) or ""
        item = {"file": filename, "name": name}
        try:
            item.update(evaluate(path))
        except (OSError, ValueError) as error:
            item["error"] = str(error)
        batch.append(item)
    return batch


def decimal(value):
    return f"{value:.2f}".replace(".", ",")


def report_rows(batch):
    counts = Counter(item["fingerprint"] for item in batch if "fingerprint" in item)
    notes = [["Aluno", "Nota provisória", "Situação", "Arquivo", "Listas / 15",
              "Matrizes / 15", "Bloco final / 10", "Em branco", "Rever", "Observação"]]
    details = [["Aluno", "Arquivo", "Questão", "Assunto", "Resultado", "Observação"]]
    for item in batch:
        filename, name = item["file"], item["name"]
        if "error" in item:
            notes.append([name, "", "Erro de leitura", filename, "", "", "", "", "", item["error"]])
            continue
        results = item["results"]
        correct = [sum(row["status"] == "Certa" for row in results[start:end]) for _, start, end, _ in BLOCKS]
        blanks = sum(row["status"] == "Em branco" for row in results)
        review = sum(row["status"] == "Rever" for row in results)
        score = max(0, sum(min(1, count / block[3]) for count, block in zip(correct, BLOCKS)) * 10 / 3
                    - max(0, blanks - 20) * 0.10)
        duplicate = counts[item["fingerprint"]] > 1
        status = "Em conferência" if duplicate else "Corrigida provisoriamente"
        observation = []
        if duplicate:
            observation.append("Conjunto de respostas idêntico ao de outro ZIP do lote.")
        if not name:
            observation.append("Nome do aluno a confirmar. Consulte o arquivo ou preencha o CSV de nomes.")
        if review and not duplicate:
            observation.append("Confira as questões marcadas como Rever.")
        notes.append([name, "" if duplicate else decimal(score), status, filename,
                      *correct, blanks, review, " ".join(observation)])
        for subject, start, end, _ in BLOCKS:
            for row in results[start:end]:
                details.append([name, filename, row["question"], subject, row["status"], row["note"]])
    return notes, details


def safe_cell(value):
    if isinstance(value, str) and (value.lstrip().startswith(("=", "+", "-", "@"))
                                  or value.startswith(("\t", "\r", "\n"))):
        return "'" + value
    return value


def write_csv(path, rows):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="", dir=path.parent, delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            writer = csv.writer(stream, delimiter=";")
            writer.writerows([safe_cell(value) for value in row] for row in rows)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path, help="Pasta dos ZIPs ou um ZIP individual")
    parser.add_argument("--nomes", type=Path, help="CSV opcional com as colunas Arquivo;Aluno")
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="Pasta dos relatórios")
    args = parser.parse_args()
    try:
        root, paths = collect_paths(args.entrada)
        names = read_names(args.nomes)
        docker_ready()
        print(f"Corrigindo {len(paths)} ZIP(s)…", flush=True)
        batch = run_batch(root, paths, names)
        args.saida.mkdir(parents=True, exist_ok=True)
        notes, details = report_rows(batch)
        write_csv(args.saida / "notas.csv", notes)
        write_csv(args.saida / "questoes.csv", details)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Erro: {error}\n")
    pending = sum(row[2] != "Corrigida provisoriamente" for row in notes[1:])
    print(f"{len(batch)} ZIP(s) processado(s), {pending} em conferência ou com erro.")
    print(f"Relatórios em {args.saida.resolve()}")


if __name__ == "__main__":
    main()
