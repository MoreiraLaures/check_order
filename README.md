# Check Order

Ferramenta interna para verificação de separação de pedidos.

Recebe um arquivo `.xls` de apontamento de PA, consulta o pedido correspondente na API do PiedAdmin e informa se os SKUs e quantidades separados estão corretos.

---

## Como usar

### 1. Pré-requisitos

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) instalado

### 2. Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
TOKEN=seu_token_piedadmin
```

### 3. Instalar dependências

```bash
uv sync
```

### 4. Rodar

```bash
python main.py
```

O servidor sobe em `http://localhost:8000` e abre o browser automaticamente.

---

## Gerar o executável (.exe)

```bash
pyinstaller check_order.spec --noconfirm
```

O arquivo gerado fica em `dist/check_order.exe`.

Para distribuir, basta entregar:
- `check_order.exe`
- `.env` (com o TOKEN) — colocar na mesma pasta do .exe

Os relatórios são salvos em `response/` automaticamente criada ao lado do .exe.

---

## Uso

1. Acesse a interface no browser
2. Selecione o arquivo `.xls` de separação
   - O nome do arquivo deve ser o código do pedido: `260005913.xls`
3. Clique em **Verificar separação**
4. O resultado aparece na tela indicando se está correto ou listando as divergências

O relatório também é salvo automaticamente em `response/<codigo>_result.txt`.

---

## Estrutura do arquivo XLS esperado

| Célula | Conteúdo |
|--------|----------|
| A1 | `Apontamento de PA:260005913 - NOME DO CLIENTE` |
| A3:C3 | Cabeçalhos |
| A4:Cn | SKU \| Descrição \| Quantidade |

---

## Estrutura do projeto

```
check_order/
├── main.py                    # entrypoint — sobe servidor e abre browser
├── check_order.spec           # configuração do PyInstaller
├── app/
│   ├── server.py              # FastAPI: rotas GET / e POST /verificar
│   ├── paths.py               # resolução de caminhos (dev vs .exe)
│   ├── templates/
│   │   ├── index.html         # página principal com upload
│   │   └── result.html        # fragmento HTMX com resultado
│   ├── clients/
│   │   └── piedadmin.py       # cliente HTTP da API PiedAdmin
│   └── modules/
│       ├── xlsx_parser.py     # leitura e extração de dados do XLS
│       ├── order_checker.py   # lógica de comparação XLS vs API
│       └── report_writer.py   # geração do relatório .txt
├── dist/check_order.exe       # executável gerado (gitignored)
├── response/                  # relatórios gerados (gitignored)
├── .env                       # credenciais (gitignored)
└── pyproject.toml
```

---

## O que é verificado

| Verificação | Descrição |
|-------------|-----------|
| Código do arquivo | Nome do arquivo (`260005913.xls`) deve bater com o código em A1 |
| SKUs presentes | Todos os SKUs do XLS devem existir no pedido da API |
| Quantidades | Quantidade de cada SKU deve ser igual ao pedido |
