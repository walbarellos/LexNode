"""
Testes do base_crawler — formatação CNJ e helpers.

Testa apenas lógica interna (formatação de número, detecção de captcha),
sem fazer requests reais.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from base_crawler import BaseCrawler


class TestFormatarNumeroCNJ:
    """Testa a decomposição do número CNJ nos campos do formulário e-SAJ."""

    def test_formato_padrao(self):
        digito_ano, foro = BaseCrawler._formatar_numero_cnj(
            "0700616-57.2024.8.01.0001"
        )
        assert digito_ano == "0700616-57.2024"
        assert foro == "0001"

    def test_numero_sem_mascara(self):
        # 20 dígitos puros
        digito_ano, foro = BaseCrawler._formatar_numero_cnj(
            "07006165720248010001"
        )
        assert digito_ano == "0700616-57.2024"
        assert foro == "0001"

    def test_numero_curto_demais_levanta_erro(self):
        with pytest.raises(ValueError, match="inválido"):
            BaseCrawler._formatar_numero_cnj("12345")

    def test_outro_foro(self):
        digito_ano, foro = BaseCrawler._formatar_numero_cnj(
            "0800123-45.2023.8.01.0070"
        )
        assert digito_ano == "0800123-45.2023"
        assert foro == "0070"


class TestPareceCaptcha:
    def test_html_sem_captcha(self):
        assert BaseCrawler._parece_captcha("<html><body>Processo</body></html>") is False

    def test_html_com_recaptcha(self):
        assert BaseCrawler._parece_captcha('<div class="g-recaptcha">') is True

    def test_html_com_captcha_generico(self):
        assert BaseCrawler._parece_captcha("Por favor resolva o CAPTCHA") is True


class TestProcessoNaoEncontrado:
    """Confirmado contra HTML real do TJAC em 2026-07-27."""

    def test_detecta_mensagem_real_do_esaj(self):
        # Texto exato do td#mensagemRetorno do e-SAJ TJAC
        html = (
            '<td id="mensagemRetorno">Não existem informações disponíveis '
            "para os parâmetros informados</td>"
        )
        assert BaseCrawler._processo_nao_encontrado(html) is True

    def test_nao_dispara_em_pagina_de_processo_real(self):
        html = '<span id="classeProcesso">Procedimento Comum</span>' + "x" * 500
        assert BaseCrawler._processo_nao_encontrado(html) is False
