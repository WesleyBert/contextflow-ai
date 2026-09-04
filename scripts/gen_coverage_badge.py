"""Gera um badge SVG (estilo shields.io) a partir da cobertura de testes atual.

Lê o resultado de `coverage report --format=total` (banco `.coverage` já
gerado por um `pytest --cov=src` anterior) e escreve um SVG simples em
`.github/badges/coverage.svg`. Sem dependências externas — só a lib
`coverage`, que já é instalada via `pytest-cov`.
"""

import subprocess
import sys
from pathlib import Path

OUTPUT_PATH = Path(".github/badges/coverage.svg")

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="114" height="20" role="img"
     aria-label="coverage: {pct}%">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="114" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="61" height="20" fill="#555"/>
    <rect x="61" width="53" height="20" fill="{color}"/>
    <rect width="114" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-size="11"
     font-family="Verdana,Geneva,DejaVu Sans,sans-serif">
    <text x="31" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="31" y="14">coverage</text>
    <text x="87" y="15" fill="#010101" fill-opacity=".3">{pct}%</text>
    <text x="87" y="14">{pct}%</text>
  </g>
</svg>
"""


def badge_color(pct: float) -> str:
    if pct >= 90:
        return "#4c1"
    if pct >= 80:
        return "#97ca00"
    if pct >= 60:
        return "#dfb317"
    return "#e05d44"


def main() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "coverage", "report", "--format=total"],
        capture_output=True,
        text=True,
        check=True,
    )
    pct = float(result.stdout.strip())
    svg = TEMPLATE.format(pct=int(pct), color=badge_color(pct))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Badge gerado em {OUTPUT_PATH} ({int(pct)}%)")


if __name__ == "__main__":
    main()
