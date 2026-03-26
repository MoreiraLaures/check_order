import os
from datetime import datetime

from app.modules.order_checker import CheckResult


def _line(char: str = "-", width: int = 60) -> str:
    return char * width


def build_report(result: CheckResult) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lines: list[str] = []

    lines.append(_line("="))
    lines.append(f"  RELATÓRIO DE COMPARAÇÃO DE SEPARAÇÃO")
    lines.append(f"  Gerado em: {now}")
    lines.append(_line("="))
    lines.append("")

    # --- Identificação ---
    lines.append("[ IDENTIFICAÇÃO ]")
    lines.append(f"  Código no nome do arquivo : {result.filename_code}")
    lines.append(f"  Código na célula A1       : {result.cell_code}")
    if result.codes_match:
        lines.append("  Conferência de código     : OK")
    else:
        lines.append("  Conferência de código     : DIVERGENTE ← arquivo e célula não batem")
    lines.append("")

    # --- Quantidade de itens ---
    lines.append("[ ITENS ]")
    lines.append(f"  Qtd. SKUs no XLS  : {result.total_xls}")
    lines.append(f"  Qtd. SKUs na API  : {result.total_api}")
    if result.counts_match:
        lines.append("  Total de SKUs     : OK")
    else:
        lines.append(
            f"  Total de SKUs     : DIVERGENTE ← XLS tem {result.total_xls}, API tem {result.total_api}"
        )
    lines.append("")

    # --- Resultado final ---
    lines.append(_line("-"))
    if result.is_correct:
        lines.append("  RESULTADO: SEPARAÇÃO CORRETA ✓")
        lines.append("  Todos os SKUs e quantidades conferem com o pedido.")
    else:
        lines.append("  RESULTADO: SEPARAÇÃO INCORRETA ✗")
        lines.append("")
        lines.append("  Divergências encontradas:")
        lines.append("")

        if not result.codes_match:
            lines.append(
                f"  [CÓDIGO]  Arquivo={result.filename_code}  |  Célula A1={result.cell_code}"
            )
            lines.append("")

        for div in result.divergencias:
            if div.qty_api is None:
                lines.append(
                    f"  [SKU AUSENTE]  {div.sku:>6}  '{div.description_xls}'"
                    f"  — XLS: {div.qty_xls}  |  API: não encontrado"
                )
            else:
                lines.append(
                    f"  [QTD ERRADA]   {div.sku:>6}  '{div.description_xls}'"
                    f"  — XLS: {div.qty_xls}  |  API: {div.qty_api}"
                )

    lines.append(_line("="))
    return "\n".join(lines)


def save_report(result: CheckResult, output_dir: str = "response") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{result.order_code}_result.txt")
    content = build_report(result)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename
