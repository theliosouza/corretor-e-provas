"""Lê e avalia um único ZIP dentro do contêiner de correção."""

import hashlib
import io
import json
import re
import resource
import sys
from collections import defaultdict
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from casos import clean, grade

MIB = 1024 * 1024
MAX_ZIP_BYTES = 8 * MIB
MAX_SOURCE_BYTES = 256 * 1024
MAX_EXPANDED_BYTES = 16 * MIB
NUMBERS = set(range(1, 41))
QUESTION_FILE = re.compile(r"[ _#.-]*(?:q(?:ues?t(?:ao|oes)?)?|n|exercicio)?[ _#.-]*(\d{1,2})(?:[ _.-]*quest(?:ao|oes))?")
QUESTION_HEADER = re.compile(
    r"(?im)^#[ \t]*(?:quest[aã]o|q)[ \t]*(\d{1,2})\b[^\r\n]*$"
)
PATTERN_START = re.compile(r'''(?im)^print\(["']--- Gerador de Padrão em Matriz ---["']\)[ \t]*$''')


def question_number(path):
    match = QUESTION_FILE.fullmatch(clean(path.stem).strip())
    return int(match[1]) if match and int(match[1]) in NUMBERS else None


def decode(raw):
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def consolidated(source):
    source = source.replace("\r\n", "\n")
    marks = list(QUESTION_HEADER.finditer(source))
    result = {}
    for index, mark in enumerate(marks):
        number = int(mark[1])
        if number in result or number not in NUMBERS:
            return {}
        end = marks[index + 1].start() if index + 1 < len(marks) else len(source)
        result[number] = source[mark.end():end].strip("\r\n")
    if set(result) == NUMBERS - {40}:
        boundary = PATTERN_START.search(result[39])
        if boundary:
            result[39], result[40] = result[39][:boundary.start()], result[39][boundary.start():]
    return result if len(result) >= 2 else {}


def load_submission(raw):
    groups = defaultdict(list)
    combined = []
    with ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > 500 or sum(item.file_size for item in entries) > MAX_EXPANDED_BYTES:
            raise ValueError("O ZIP excede o limite de arquivos ou de tamanho após descompressão.")
        for item in entries:
            path = PurePosixPath(item.filename.replace(chr(92), "/"))
            if item.is_dir() or any(part.startswith(".") or part == "__MACOSX" for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ""}:
                continue
            number = question_number(path)
            if number is None and path.suffix.lower() != ".py":
                continue
            if item.file_size > MAX_SOURCE_BYTES:
                raise ValueError("Há um programa Python com mais de 256 KiB no ZIP.")
            source = decode(archive.read(item))
            if number is not None:
                groups[path.parent].append((number, source))
            else:
                block = consolidated(source)
                if block:
                    combined.append(block)

    sets = [dict(entries) for entries in groups.values() if len(entries) == len(dict(entries))]
    complete = [entry for entry in sets + combined if entry.keys() == NUMBERS]
    if len(complete) == 1:
        return complete[0]
    if len(complete) > 1:
        raise ValueError("O ZIP contém mais de um conjunto completo. Envie um trabalho por ZIP.")
    if len(sets) == 1 and len(groups) == 1 and not combined:
        return sets[0]
    if len(combined) == 1 and not groups:
        return combined[0]
    raise ValueError("Não foi possível identificar um único conjunto de questões numeradas.")


def evaluate(raw):
    sources = load_submission(raw)
    canonical = {
        number: source.replace("\r\n", "\n").strip("\n")
        for number, source in sources.items()
    }
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
    results = []
    for number in sorted(NUMBERS):
        status, note = grade(number, sources.get(number, ""))
        if number not in sources:
            status, note = "Rever", "Arquivo da questão não localizado. Confira o ZIP."
        elif status == "Erro":
            status = "Incorreta"
        results.append({"question": number, "status": status, "note": note})
    return {"fingerprint": fingerprint, "results": results}


def main():
    resource.setrlimit(resource.RLIMIT_AS, (256 * MIB, 256 * MIB))
    raw = sys.stdin.buffer.read(MAX_ZIP_BYTES + 1)
    if len(raw) > MAX_ZIP_BYTES:
        response = {"error": "O ZIP ultrapassa o limite de 8 MiB."}
    else:
        try:
            response = evaluate(raw)
        except (BadZipFile, ValueError, RuntimeError, NotImplementedError) as error:
            response = {"error": str(error) or "Não foi possível abrir o ZIP."}
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main()
