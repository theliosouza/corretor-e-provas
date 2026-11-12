# corretor-e-provas

Corrige ZIPs da atividade de 40 questões de Lógica de Programação. Cada ZIP representa uma entrega. O programa aceita questões numeradas em arquivos separados ou em um arquivo Python único com comentários como `# Questão 1`.

## Rodar no Windows com VS Code

1. Instale e abra o [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/), usando contêineres Linux.
2. No VS Code, abra esta pasta e vá em **Terminal → Novo Terminal**.
3. Prepare a imagem uma vez. Repita este comando se alterar `motor.py` ou `casos.py`.

   ```powershell
   docker build -t corretor-python:local .
   ```

4. Coloque os ZIPs em uma pasta `entradas` ou use o caminho completo da pasta onde eles já estão.

   ```powershell
   py corretor.py entradas
   ```

   Também é possível corrigir um único ZIP com `py corretor.py "entradas\trabalho_01.zip"`.

5. Abra `saida/notas.csv` no Excel. O arquivo `saida/questoes.csv` contém a situação das 40 questões de cada ZIP.

O programa inicia um contêiner separado por entrega, sem rede, com sistema de arquivos somente leitura, limites de CPU e memória e sem acesso às pastas do computador. Os ZIPs são lidos localmente por entrada padrão e o código enviado é avaliado dentro do contêiner. Feche os CSVs no Excel antes de gerar uma nova versão.

## Colocar os nomes ao lado das notas

Faça uma cópia de `nomes.exemplo.csv` com o nome `nomes.csv`. Preencha as colunas `Arquivo` e `Aluno` com os nomes dos ZIPs e dos alunos. Se houver arquivos com o mesmo nome em subpastas, use o caminho relativo na coluna `Arquivo`, como `grupo-a/trabalho.zip`.

```powershell
py corretor.py entradas --nomes nomes.csv
```

As linhas sem correspondência ficam com o campo **Aluno** em branco e mostram o ZIP para conferência. Subpastas são incluídas na busca.

## Critérios

| Assunto | Questões | Mínimo para pontuação integral |
| --- | --- | --- |
| Listas | 1–15 | 8 acertos |
| Matrizes | 16–30 | 8 acertos |
| Bloco final | 31–40 | 5 acertos |

- A nota máxima é 10. Cada bloco vale um terço da nota. Abaixo do mínimo, a pontuação do bloco é proporcional aos acertos.
- Cada resposta em branco acima de 20 desconta 0,10 ponto. Questões não localizadas ficam como **Rever**.
- ZIPs com o mesmo conjunto de respostas no lote ficam **Em conferência**, com as notas em branco. Para comparar novas entregas com as anteriores, mantenha os ZIPs anteriores na pasta que será corrigida.
- Os casos em `casos.py` foram inferidos das entregas da turma e precisam ser conferidos com o enunciado oficial. A pontuação é provisória. O uso de função própria nas questões 31 a 39 continua sendo um critério provisório.
- O motor aceita os recursos de Python usados nesses exercícios. Código com construções fora do executor ou saídas divergentes vai para revisão. O limite por ZIP é de 8 MiB.

## Colocar no GitHub

Extraia o projeto em uma pasta local. Crie um repositório no [GitHub](https://github.com/new), por exemplo `corretor-python`. Use **Add file → Upload files** para enviar somente os arquivos do projeto. Inclua `.gitignore` e `.dockerignore` se a interface exibir esses arquivos.

Quem já usa Git e GitHub CLI pode publicar esta pasta pelo terminal.

```powershell
git init -b main
git add .
git commit -m "Adiciona corretor de atividades em Python"
gh auth login
gh repo create corretor-python --private --source . --remote origin --push
```

O repositório guarda o código. Execute o corretor no seu computador, com os ZIPs, nomes e relatórios em pastas locais.
