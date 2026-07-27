"""
Testes do filtro de sigilo fail-closed e do parser de dados principais.

O filtro de sigilo é o teste mais importante do repositório: se ele
quebrar ou for enfraquecido, o projeto pode expor dados protegidos por
lei. Qualquer PR que altere normalizer.py deve manter estes testes
passando.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from normalizer import ProcessoSigilosoError, normalizar_html_1grau


# ===================================================================
# Filtro de sigilo — FAIL-CLOSED
# ===================================================================

class TestFiltroSigilo:
    """Estes testes NÃO podem ser enfraquecidos. Nunca."""

    def test_bloqueia_processo_com_marcador_explicito_de_sigilo(self):
        html = "<html><body>Processo em SEGREDO DE JUSTIÇA " + "x" * 200 + "</body></html>"
        with pytest.raises(ProcessoSigilosoError):
            normalizar_html_1grau("0000000-00.0000.0.00.0000", html)

    def test_bloqueia_html_vazio(self):
        with pytest.raises(ProcessoSigilosoError):
            normalizar_html_1grau("0000000-00.0000.0.00.0000", "")

    def test_bloqueia_html_curto_suspeito(self):
        with pytest.raises(ProcessoSigilosoError):
            normalizar_html_1grau("0000000-00.0000.0.00.0000", "<html>negado</html>")

    def test_bloqueia_marcador_restrito(self):
        html = "<html><body>Acesso Restrito ao processo " + "x" * 200 + "</body></html>"
        with pytest.raises(ProcessoSigilosoError):
            normalizar_html_1grau("0000000-00.0000.0.00.0000", html)


# ===================================================================
# Parser de dados principais — calibrado contra HTML real do TJAC
# ===================================================================

# HTML baseado na estrutura real confirmada em 2026-07-27
# (processo 0800224-44.2013.8.01.0001, Ação Civil Pública)
HTML_PROCESSO_REAL = """
<html><body>
<div class="unj-entity-header__summary">
  <div id="containerDadosPrincipaisProcesso" class="container">
    <div class="row">
      <span id="numeroProcesso" class="unj-larger-1">
        0800224-44.2013.8.01.0001
      </span>
      <span id="labelSituacaoProcesso" class="unj-tag">Baixado</span>
    </div>
    <div class="row">
      <div class="col-lg-3">
        <span id="classeProcesso" title="Ação Civil Pública">Ação Civil Pública</span>
      </div>
      <div class="col-lg-2">
        <span id="assuntoProcesso" title="Defeito, nulidade ou anulação">Defeito, nulidade ou anulação</span>
      </div>
      <div class="col-lg-2">
        <span id="foroProcesso" title="Rio Branco">Rio Branco</span>
      </div>
      <div class="col-lg-3">
        <span id="varaProcesso" title="2ª Vara Cível">2ª Vara Cível</span>
      </div>
      <div class="col-lg-3">
        <span id="juizProcesso" title="Thaís Queiroz B. de Oliveira A. Khalil">Thaís Queiroz B. de Oliveira A. Khalil</span>
      </div>
    </div>
  </div>
</div>
<div id="maisDetalhes">
  <div class="row">
    <div class="col-lg-3">
      <div id="dataHoraDistribuicaoProcesso">28/06/2013 às 13:00 - Sorteio</div>
    </div>
    <div class="col-lg-3">
      <div id="numeroControleProcesso">2013/000461</div>
    </div>
    <div class="col-lg-2">
      <div id="areaProcesso"><span title="Cível">Cível</span></div>
    </div>
    <div class="col-lg-2">
      <div id="valorAcaoProcesso">R$         10.000.000,00</div>
    </div>
  </div>
</div>
</body></html>
"""


class TestParserDadosPrincipais:
    """Testa extração de campos contra estrutura HTML real do TJAC."""

    def test_extrai_classe(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.classe == "Ação Civil Pública"

    def test_extrai_assunto(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.assunto == "Defeito, nulidade ou anulação"

    def test_extrai_foro(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.foro == "Rio Branco"

    def test_extrai_vara(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.vara == "2ª Vara Cível"

    def test_extrai_juiz(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.juiz == "Thaís Queiroz B. de Oliveira A. Khalil"

    def test_extrai_situacao(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.situacao == "Baixado"

    def test_extrai_area(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.area == "Cível"

    def test_extrai_valor_acao(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert "10.000.000,00" in resultado.valor_acao

    def test_extrai_distribuicao(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.distribuicao == "28/06/2013 às 13:00 - Sorteio"

    def test_extrai_numero_controle(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.numero_controle == "2013/000461"

    def test_numero_processo_preservado(self):
        resultado = normalizar_html_1grau("0800224-44.2013.8.01.0001", HTML_PROCESSO_REAL)
        assert resultado.numero_processo == "0800224-44.2013.8.01.0001"
