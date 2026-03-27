import re
import os
from dataclasses import dataclass

import xlrd


@dataclass
class XlsParseResult:
    filename_code: str
    cell_code: str
    codes_match: bool
    items: list[dict]  # [{"sku": str, "description": str, "quantity": int}]


# Variantes de cabeçalho conhecidas para cada campo lógico (em minúsculas)
_SKU_HEADERS: set[str] = {
    # Com acento
    "cód.produto",
    "cód. produto",
    "cód. produto (mp)",
    # Sem acento
    "cod.produto",
    "cod. produto",
    "cod. produto (mp)",
    # Genérico
    "produto",
    "código",
    "codigo",
    "cód",
    "cod",
    "sku",
    "item",
    "ref",
    "referência",
    "referencia",
}
_DESC_HEADERS: set[str] = {
    # Com acento
    "descrição (produto)",
    "descrição (matéria prima)",
    "descrição",
    "descrição produto",
    # Sem acento
    "descricao (produto)",
    "descricao (materia prima)",
    "descricao",
    "descricao produto",
    # Abreviações
    "descr. produto",
    "descr.",
    "desc.",
    "desc",
    "nome",
    "nome produto",
    "denominação",
    "denominacao",
}
_QTY_HEADERS: set[str] = {
    "quantidade",
    "qtd. apontada",
    "qtd apontada",
    "qtd.",
    "qtd",
    "qtde.",
    "qtde",
    "quant.",
    "quant",
}


def _detect_columns(ws, header_row_idx: int) -> tuple[int, int, int]:
    """
    Lê a linha de cabeçalho e retorna os índices (sku_col, desc_col, qty_col).
    Lança ValueError se algum campo não for encontrado.
    """
    headers = [
        str(ws.cell_value(header_row_idx, j)).strip().lower()
        for j in range(ws.ncols)
    ]

    sku_col = desc_col = qty_col = None
    for idx, h in enumerate(headers):
        if sku_col is None and h in _SKU_HEADERS:
            sku_col = idx
        elif desc_col is None and h in _DESC_HEADERS:
            desc_col = idx
        elif qty_col is None and h in _QTY_HEADERS:
            qty_col = idx

    missing = [
        name
        for name, val in [("SKU", sku_col), ("Descrição", desc_col), ("Quantidade", qty_col)]
        if val is None
    ]
    if missing:
        raise ValueError(
            f"Colunas não encontradas no cabeçalho (linha {header_row_idx + 1}): "
            f"{', '.join(missing)}. Cabeçalhos lidos: {headers}"
        )

    return sku_col, desc_col, qty_col  # type: ignore[return-value]


def _extract_code_from_cell(text: str) -> str | None:
    """
    Extrai o código numérico do pedido da célula A1.
    Aceita formatos como:
      'Apontamento de PA:260005913 - ...'
      'PA: 260005913'
      '260005913 - ...'
    Busca sequências de 6+ dígitos consecutivos para evitar pegar
    anos, telefones curtos etc. Usa 'PA:' como âncora quando disponível.
    """
    # Tentativa 1: número imediatamente após 'PA:' (com ou sem espaço)
    match = re.search(r"PA:\s*(\d+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Tentativa 2: primeiro número com 6+ dígitos na string
    match = re.search(r"\b(\d{6,})\b", text)
    if match:
        return match.group(1)

    return None


def _extract_code_from_filename(filename: str) -> str:
    """
    Extrai o código do nome do arquivo.
    Espera o padrão padronizado '260005913.xls' (só o código).
    Retorna apenas os dígitos do nome (sem extensão).
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    # Pega apenas dígitos — robusto a espaços ou caracteres residuais
    digits = re.sub(r"\D", "", stem)
    return digits if digits else stem


def parse_xls(filepath: str) -> XlsParseResult:
    """
    Lê o arquivo .xls e retorna os dados parseados.
    - A1: célula com código do pedido (ex: 'Apontamento de PA:260005913...')
    - A3:C3: cabeçalhos (ignorados)
    - A4:C<n>: dados (SKU, Descrição, Quantidade)
    - Última linha com SKU vazio = linha de total, ignorada
    """
    wb = xlrd.open_workbook(filepath)
    ws = wb.sheet_by_index(0)

    # Extrai código da célula A1
    a1_value = str(ws.cell_value(0, 0)).strip()
    cell_code = _extract_code_from_cell(a1_value)
    if cell_code is None:
        raise ValueError(
            f"Não foi possível extrair o código do pedido de A1: '{a1_value}'"
        )

    # Extrai código do nome do arquivo
    filename_code = _extract_code_from_filename(filepath)

    # Dados começam na linha 4 (índice 3), header em linha 3 (índice 2)
    items: list[dict] = []
    HEADER_ROW = 2  # índice 0-based da linha de cabeçalho
    DATA_START = HEADER_ROW + 1

    sku_col, desc_col, qty_col = _detect_columns(ws, HEADER_ROW)

    for row_idx in range(DATA_START, ws.nrows):
        sku_raw = ws.cell_value(row_idx, sku_col)
        desc_raw = ws.cell_value(row_idx, desc_col)
        qty_raw = ws.cell_value(row_idx, qty_col)

        # Ignora linhas sem SKU (ex: linha de total)
        if not str(sku_raw).strip():
            continue

        try:
            sku = str(int(float(sku_raw)))
        except (ValueError, TypeError):
            continue

        try:
            quantity = int(float(qty_raw))
        except (ValueError, TypeError):
            quantity = 0

        items.append(
            {
                "sku": sku,
                "description": str(desc_raw).strip(),
                "quantity": quantity,
            }
        )

    return XlsParseResult(
        filename_code=filename_code,
        cell_code=cell_code,
        codes_match=(filename_code == cell_code),
        items=items,
    )
