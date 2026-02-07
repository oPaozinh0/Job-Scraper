"""Testes unitários para o módulo scraper.py."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import MagicMock, call, patch

import pytest
import requests

import scraper


# ============================================================================
# TESTES UNITÁRIOS - is_valid_job_link()
# ============================================================================


def test_is_valid_job_link_greenhouse() -> None:
    """Testa validação de link Greenhouse."""
    assert scraper.is_valid_job_link("https://job-boards.greenhouse.io/company/jobs/123", "Green House")
    assert scraper.is_valid_job_link("https://greenhouse.io/careers/job", "Green House")
    assert scraper.is_valid_job_link("https://www.greenhouse.io/apply", "Green House")


def test_is_valid_job_link_lever() -> None:
    """Testa validação de link Lever."""
    assert scraper.is_valid_job_link("https://jobs.lever.co/company/abc", "Lever")
    assert scraper.is_valid_job_link("https://www.lever.co/test", "Lever")


def test_is_valid_job_link_ashby() -> None:
    """Testa validação de link AshBy."""
    assert scraper.is_valid_job_link("https://jobs.ashbyhq.com/company/xyz", "AshBy")
    assert scraper.is_valid_job_link("https://www.ashbyhq.com/job", "AshBy")


def test_is_valid_job_link_workable() -> None:
    """Testa validação de link Workable."""
    assert scraper.is_valid_job_link("https://apply.workable.com/company/job1", "Workable")
    assert scraper.is_valid_job_link("https://www.workable.com/test", "Workable")


def test_is_valid_job_link_breezy() -> None:
    """Testa validação de link Breezy."""
    assert scraper.is_valid_job_link("https://company.breezy.hr/job/123", "Breezy")
    assert scraper.is_valid_job_link("https://www.breezy.hr/test", "Breezy")


def test_is_valid_job_link_jazz() -> None:
    """Testa validação de link Jazz CO."""
    assert scraper.is_valid_job_link("https://company.jazz.co/apply", "Jazz CO")
    assert scraper.is_valid_job_link("https://www.jazz.co/job", "Jazz CO")


def test_is_valid_job_link_smart_recruiters() -> None:
    """Testa validação de link Smart Recruiters."""
    assert scraper.is_valid_job_link("https://careers.smartrecruiters.com/company", "Smart Recruiters")
    assert scraper.is_valid_job_link("https://www.smartrecruiters.com/job", "Smart Recruiters")


def test_is_valid_job_link_icims() -> None:
    """Testa validação de link ICIMS."""
    assert scraper.is_valid_job_link("https://careers.icims.com/jobs/123", "ICIMS")
    assert scraper.is_valid_job_link("https://www.icims.com/apply", "ICIMS")


def test_is_valid_job_link_pinpoint() -> None:
    """Testa validação de link PinpointHQ."""
    assert scraper.is_valid_job_link("https://jobs.pinpointhq.com/company", "PinpointHQ")
    assert scraper.is_valid_job_link("https://www.pinpointhq.com/job", "PinpointHQ")


def test_is_valid_job_link_app_dover() -> None:
    """Testa validação de link app.dover (padrão válido especial)."""
    # app.dover. é válido apenas se não contiver outros padrões excluídos
    assert scraper.is_valid_job_link("https://app.dover.io/careers/job", "Dover")
    assert scraper.is_valid_job_link("https://app.dover.tech/apply/company/job123", "Dover")
    # mas dover.com está na lista de exclusão, então app.dover.com é rejeitado
    assert not scraper.is_valid_job_link("https://app.dover.com/apply/job", "Dover")


def test_is_valid_job_link_excluded_facebook() -> None:
    """Testa rejeição de links do Facebook."""
    assert not scraper.is_valid_job_link("https://facebook.com/jobs/123", "Greenhouse")
    assert not scraper.is_valid_job_link("https://www.facebook.com/careers", "Lever")


def test_is_valid_job_link_excluded_linkedin() -> None:
    """Testa rejeição de links do LinkedIn."""
    assert not scraper.is_valid_job_link("https://linkedin.com/jobs/view/123", "Greenhouse")
    assert not scraper.is_valid_job_link("https://www.linkedin.com/jobs", "Lever")


def test_is_valid_job_link_excluded_glassdoor() -> None:
    """Testa rejeição de links do Glassdoor."""
    assert not scraper.is_valid_job_link("https://glassdoor.com/job/123", "Greenhouse")
    assert not scraper.is_valid_job_link("https://www.glassdoor.com/jobs", "Lever")


def test_is_valid_job_link_excluded_indeed() -> None:
    """Testa rejeição de links do Indeed."""
    assert not scraper.is_valid_job_link("https://indeed.com/viewjob?jk=123", "Greenhouse")
    assert not scraper.is_valid_job_link("https://www.indeed.com/jobs", "Lever")


def test_is_valid_job_link_excluded_upwork() -> None:
    """Testa rejeição de links do Upwork."""
    assert not scraper.is_valid_job_link("https://upwork.com/freelance-jobs/123", "Greenhouse")
    assert not scraper.is_valid_job_link("https://www.upwork.com/jobs", "Lever")


def test_is_valid_job_link_excluded_dover() -> None:
    """Testa rejeição de links do Dover (exceto app.dover)."""
    assert not scraper.is_valid_job_link("https://dover.com/jobs", "Greenhouse")
    assert not scraper.is_valid_job_link("https://dovercorporation.com/careers", "Lever")
    assert not scraper.is_valid_job_link("https://app.dover.com/dover/careers", "Lever")  # Padrão excluído


def test_is_valid_job_link_excluded_weworkremotely() -> None:
    """Testa rejeição de links do WeWorkRemotely."""
    assert not scraper.is_valid_job_link("https://weworkremotely.com/jobs/123", "Greenhouse")


def test_is_valid_job_link_excluded_careers_only() -> None:
    """Testa rejeição de URLs que terminam com /careers/."""
    assert not scraper.is_valid_job_link("https://company.com/careers/", "Greenhouse")


def test_is_valid_job_link_empty_string() -> None:
    """Testa validação com string vazia."""
    assert not scraper.is_valid_job_link("", "Greenhouse")


def test_is_valid_job_link_no_protocol() -> None:
    """Testa validação sem protocolo."""
    assert scraper.is_valid_job_link("greenhouse.io/job/123", "Greenhouse")
    assert scraper.is_valid_job_link("lever.co/company/job", "Lever")


def test_is_valid_job_link_mixed_case() -> None:
    """Testa validação com case misto (case-insensitive)."""
    assert scraper.is_valid_job_link("https://GREENHOUSE.IO/job", "Greenhouse")
    assert scraper.is_valid_job_link("https://Lever.Co/job", "Lever")
    assert not scraper.is_valid_job_link("https://FACEBOOK.COM/jobs", "Greenhouse")


def test_is_valid_job_link_no_valid_pattern() -> None:
    """Testa rejeição de link sem padrão válido."""
    assert not scraper.is_valid_job_link("https://randomsite.com/job", "Unknown")
    assert not scraper.is_valid_job_link("https://example.org/careers", "Unknown")


# ============================================================================
# TESTES UNITÁRIOS - fetch_page()
# ============================================================================


def test_fetch_page_success() -> None:
    """Testa fetch_page com sucesso."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"organic": [{"title": "Test Job"}]}
    
    with patch("requests.post", return_value=mock_response):
        result = scraper.fetch_page("test query", "Greenhouse", 1, "test-api-key")
        
        assert result == {"organic": [{"title": "Test Job"}]}


def test_fetch_page_empty_api_key() -> None:
    """Testa fetch_page com API key vazia retorna dict vazio."""
    result = scraper.fetch_page("test query", "Greenhouse", 1, "")
    assert result == {}


def test_fetch_page_request_exception() -> None:
    """Testa fetch_page com RequestException retorna dict vazio."""
    with patch("requests.post", side_effect=requests.RequestException("Network error")):
        result = scraper.fetch_page("test query", "Greenhouse", 1, "test-api-key")
        assert result == {}


def test_fetch_page_sends_correct_payload() -> None:
    """Testa se fetch_page envia payload correto."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        scraper.fetch_page("test query", "Greenhouse", 2, "test-api-key")
        
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        
        assert payload["q"] == "test query"
        assert payload["num"] == 10
        assert payload["page"] == 2
        assert payload["tbs"] == "qdr:w"


def test_fetch_page_sends_correct_headers() -> None:
    """Testa se fetch_page envia headers corretos."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        scraper.fetch_page("test query", "Greenhouse", 1, "my-api-key")
        
        call_args = mock_post.call_args
        headers = call_args.kwargs["headers"]
        
        assert headers["X-API-KEY"] == "my-api-key"
        assert headers["Content-Type"] == "application/json"


def test_fetch_page_timeout() -> None:
    """Testa se fetch_page usa timeout correto."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        scraper.fetch_page("test query", "Greenhouse", 1, "test-api-key")
        
        call_args = mock_post.call_args
        assert call_args.kwargs["timeout"] == 30


# ============================================================================
# TESTES UNITÁRIOS - query_jobs()
# ============================================================================


def test_query_jobs_pagination() -> None:
    """Testa paginação em query_jobs."""
    mock_responses = [
        {"organic": [{"title": f"Job {i}", "snippet": "desc", "link": f"https://greenhouse.io/job{i}"} for i in range(10)]},
        {"organic": [{"title": f"Job {i}", "snippet": "desc", "link": f"https://greenhouse.io/job{i}"} for i in range(10, 20)]},
        {"organic": [{"title": f"Job {i}", "snippet": "desc", "link": f"https://greenhouse.io/job{i}"} for i in range(20, 30)]},
    ]
    
    with patch("scraper.fetch_page", side_effect=mock_responses), \
         patch("time.sleep"):
        results = scraper.query_jobs("test query", "Greenhouse", "test-api-key", target_min=25)
        
        # Deve buscar 3 páginas para atingir target_min=25
        assert len(results) == 30


def test_query_jobs_stops_when_no_organic_results() -> None:
    """Testa que query_jobs para quando não há mais resultados."""
    mock_responses = [
        {"organic": [{"title": "Job 1", "snippet": "desc", "link": "https://greenhouse.io/job1"}]},
        {"organic": []},  # Página vazia
    ]
    
    with patch("scraper.fetch_page", side_effect=mock_responses), \
         patch("time.sleep"):
        results = scraper.query_jobs("test query", "Greenhouse", "test-api-key", target_min=50)
        
        # Deve parar após a segunda página vazia
        assert len(results) == 1


def test_query_jobs_deduplication() -> None:
    """Testa deduplicação de links iguais em múltiplas páginas."""
    mock_responses = [
        {"organic": [
            {"title": "Job 1", "snippet": "desc", "link": "https://greenhouse.io/job1"},
            {"title": "Job 2", "snippet": "desc", "link": "https://greenhouse.io/job2"},
        ]},
        {"organic": [
            {"title": "Job 2 (duplicate)", "snippet": "desc", "link": "https://greenhouse.io/job2"},  # Duplicado
            {"title": "Job 3", "snippet": "desc", "link": "https://greenhouse.io/job3"},
        ]},
    ]
    
    with patch("scraper.fetch_page", side_effect=mock_responses), \
         patch("time.sleep"):
        results = scraper.query_jobs("test query", "Greenhouse", "test-api-key", target_min=50)
        
        # Deve ter 3 jobs únicos (job2 duplicado é ignorado)
        assert len(results) == 3
        links = [r["Link"] for r in results]
        assert len(set(links)) == 3


def test_query_jobs_on_progress_callback() -> None:
    """Testa que on_progress é chamado com eventos corretos."""
    mock_responses = [
        {"organic": [{"title": "Job 1", "snippet": "desc", "link": "https://greenhouse.io/job1"}]},
        {"organic": [{"title": "Job 2", "snippet": "desc", "link": "https://greenhouse.io/job2"}]},
        {"organic": []},  # Página vazia para parar
    ]
    
    callback_calls: List[tuple[str, dict]] = []
    
    def on_progress(event: str, data: dict) -> None:
        callback_calls.append((event, data))
    
    with patch("scraper.fetch_page", side_effect=mock_responses), \
         patch("time.sleep"):
        scraper.query_jobs("test query", "Greenhouse", "test-api-key", target_min=50, on_progress=on_progress)
    
    # Deve ter 3 eventos page_fetched (incluindo a página vazia)
    page_fetched_events = [call for call in callback_calls if call[0] == "page_fetched"]
    assert len(page_fetched_events) == 3
    
    assert page_fetched_events[0][1]["origin"] == "Greenhouse"
    assert page_fetched_events[0][1]["page"] == 1
    assert page_fetched_events[0][1]["results"] == 1
    
    assert page_fetched_events[1][1]["page"] == 2
    assert page_fetched_events[1][1]["results"] == 1
    
    assert page_fetched_events[2][1]["page"] == 3
    assert page_fetched_events[2][1]["results"] == 0


def test_query_jobs_max_pages_limit() -> None:
    """Testa que query_jobs respeita limite de 5 páginas."""
    # Cada página retorna jobs com links únicos
    def mock_fetch_page(query, origin, page, api_key):
        start = (page - 1) * 10
        return {"organic": [
            {"title": f"Job {i}", "snippet": "desc", "link": f"https://greenhouse.io/job{i}"}
            for i in range(start, start + 10)
        ]}
    
    with patch("scraper.fetch_page", side_effect=mock_fetch_page), \
         patch("time.sleep"):
        results = scraper.query_jobs("test query", "Greenhouse", "test-api-key", target_min=1000)
        
        # Deve parar em 5 páginas (5 * 10 = 50 jobs)
        assert len(results) == 50


def test_query_jobs_filters_invalid_links() -> None:
    """Testa que query_jobs filtra links inválidos."""
    mock_response = {"organic": [
        {"title": "Valid Job", "snippet": "desc", "link": "https://greenhouse.io/job1"},
        {"title": "Invalid Job", "snippet": "desc", "link": "https://facebook.com/jobs/123"},  # Excluído
        {"title": "Another Valid", "snippet": "desc", "link": "https://lever.co/job2"},
        {"title": "Invalid 2", "snippet": "desc", "link": "https://linkedin.com/jobs/456"},  # Excluído
    ]}
    
    with patch("scraper.fetch_page", return_value=mock_response), \
         patch("time.sleep"):
        results = scraper.query_jobs("test query", "Greenhouse", "test-api-key", target_min=50)
        
        # Deve ter apenas 2 jobs válidos
        assert len(results) == 2
        assert "facebook" not in results[0]["Link"].lower()
        assert "linkedin" not in results[1]["Link"].lower()


def test_query_jobs_handles_fetch_exception() -> None:
    """Testa que query_jobs trata exceções no fetch_page."""
    callback_calls: List[tuple[str, dict]] = []
    
    def on_progress(event: str, data: dict) -> None:
        callback_calls.append((event, data))
    
    with patch("scraper.fetch_page", side_effect=Exception("Network error")), \
         patch("time.sleep"):
        results = scraper.query_jobs("test query", "Greenhouse", "test-api-key", on_progress=on_progress)
        
        # Deve retornar lista vazia
        assert results == []
        
        # Deve ter emitido evento de erro
        error_events = [call for call in callback_calls if call[0] == "error"]
        assert len(error_events) == 1
        assert error_events[0][1]["origin"] == "Greenhouse"


# ============================================================================
# TESTES UNITÁRIOS - run_full_scrape()
# ============================================================================


def test_run_full_scrape_calls_query_jobs_for_all_ats() -> None:
    """Testa que run_full_scrape chama query_jobs para todas as 9 plataformas ATS."""
    with patch("scraper.query_jobs", return_value=[]) as mock_query, \
         patch("time.sleep"):
        scraper.run_full_scrape("test-api-key")
        
        # Deve ter chamado query_jobs 9 vezes (uma para cada ATS)
        assert mock_query.call_count == 9


def test_run_full_scrape_returns_results_and_stats() -> None:
    """Testa que run_full_scrape retorna (results_list, stats_dict)."""
    mock_jobs = [
        {"Job Title": "Job 1", "Snippet": "desc", "Link": "https://greenhouse.io/job1"},
        {"Job Title": "Job 2", "Snippet": "desc", "Link": "https://greenhouse.io/job2"},
    ]
    
    with patch("scraper.query_jobs", return_value=mock_jobs), \
         patch("time.sleep"):
        results, stats = scraper.run_full_scrape("test-api-key")
        
        # Deve ter 9 * 2 = 18 jobs (2 por ATS)
        assert len(results) == 18
        
        # Stats deve ter 9 entradas (uma por ATS)
        assert len(stats) == 9
        
        # Cada ATS deve ter count = 2
        for origin, count in stats.items():
            assert count == 2


def test_run_full_scrape_on_progress_callback() -> None:
    """Testa que on_progress recebe eventos ats_start e ats_complete."""
    callback_calls: List[tuple[str, dict]] = []
    
    def on_progress(event: str, data: dict) -> None:
        callback_calls.append((event, data))
    
    with patch("scraper.query_jobs", return_value=[]), \
         patch("time.sleep"):
        scraper.run_full_scrape("test-api-key", on_progress=on_progress)
    
    # Deve ter 9 ats_start + 9 ats_complete = 18 eventos
    ats_start_events = [call for call in callback_calls if call[0] == "ats_start"]
    ats_complete_events = [call for call in callback_calls if call[0] == "ats_complete"]
    
    assert len(ats_start_events) == 9
    assert len(ats_complete_events) == 9
    
    # Verifica estrutura do primeiro evento ats_start
    assert ats_start_events[0][1]["index"] == 0
    assert ats_start_events[0][1]["total"] == 9
    assert "origin" in ats_start_events[0][1]
    
    # Verifica estrutura do primeiro evento ats_complete
    assert ats_complete_events[0][1]["index"] == 0
    assert ats_complete_events[0][1]["total"] == 9
    assert "origin" in ats_complete_events[0][1]
    assert "count" in ats_complete_events[0][1]


def test_run_full_scrape_accumulates_results() -> None:
    """Testa que run_full_scrape acumula resultados de todas as plataformas."""
    # Retorna jobs diferentes para cada chamada
    call_count = [0]
    
    def mock_query_jobs(*args, **kwargs):
        call_count[0] += 1
        return [{"Job Title": f"Job {call_count[0]}", "Snippet": "desc", "Link": f"https://greenhouse.io/job{call_count[0]}"}]
    
    with patch("scraper.query_jobs", side_effect=mock_query_jobs), \
         patch("time.sleep"):
        results, stats = scraper.run_full_scrape("test-api-key")
        
        # Deve ter 9 jobs únicos
        assert len(results) == 9
        
        # Cada job deve ter título diferente
        titles = [r["Job Title"] for r in results]
        assert len(set(titles)) == 9


def test_run_full_scrape_sleeps_between_ats() -> None:
    """Testa que run_full_scrape dorme 2s entre cada ATS."""
    with patch("scraper.query_jobs", return_value=[]), \
         patch("time.sleep") as mock_sleep:
        scraper.run_full_scrape("test-api-key")
        
        # Deve ter chamado sleep 9 vezes com 2 segundos
        sleep_calls = [call for call in mock_sleep.call_args_list if call[0][0] == 2]
        assert len(sleep_calls) == 9


# ============================================================================
# TESTES UNITÁRIOS - save_results_to_csv()
# ============================================================================


def test_save_results_to_csv_creates_file(tmp_path: Path) -> None:
    """Testa que save_results_to_csv cria arquivo com nome correto."""
    results = [
        {"Job Title": "Job 1", "Snippet": "desc 1", "Link": "https://greenhouse.io/job1"},
        {"Job Title": "Job 2", "Snippet": "desc 2", "Link": "https://lever.co/job2"},
    ]
    
    file_path = scraper.save_results_to_csv(results, tmp_path)
    
    # Verifica que arquivo foi criado
    assert file_path.exists()
    
    # Verifica formato do nome
    assert file_path.name.startswith("jobs_php_any_")
    assert file_path.name.endswith(".csv")


def test_save_results_to_csv_writes_correct_content(tmp_path: Path) -> None:
    """Testa que save_results_to_csv escreve conteúdo correto."""
    results = [
        {"Job Title": "Senior PHP Engineer", "Snippet": "Remote job", "Link": "https://greenhouse.io/job1"},
        {"Job Title": "Laravel Developer", "Snippet": "Backend work", "Link": "https://lever.co/job2"},
    ]
    
    file_path = scraper.save_results_to_csv(results, tmp_path)
    
    # Lê conteúdo
    content = file_path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    
    # Verifica header
    assert lines[0] == "Job Title,Snippet,Link"
    
    # Verifica que tem 3 linhas (header + 2 jobs)
    assert len(lines) == 3
    
    # Verifica conteúdo
    assert "Senior PHP Engineer" in lines[1]
    assert "Remote job" in lines[1]
    assert "greenhouse.io" in lines[1]
    
    assert "Laravel Developer" in lines[2]
    assert "Backend work" in lines[2]
    assert "lever.co" in lines[2]


def test_save_results_to_csv_creates_directory(tmp_path: Path) -> None:
    """Testa que save_results_to_csv cria diretório se não existir."""
    output_dir = tmp_path / "nested" / "output"
    results = [{"Job Title": "Job 1", "Snippet": "desc", "Link": "https://greenhouse.io/job1"}]
    
    file_path = scraper.save_results_to_csv(results, output_dir)
    
    # Verifica que diretório foi criado
    assert output_dir.exists()
    assert output_dir.is_dir()
    
    # Verifica que arquivo foi criado no diretório
    assert file_path.parent == output_dir


def test_save_results_to_csv_handles_empty_results(tmp_path: Path) -> None:
    """Testa que save_results_to_csv lida com lista vazia."""
    results: List[Dict[str, str]] = []
    
    file_path = scraper.save_results_to_csv(results, tmp_path)
    
    # Verifica que arquivo foi criado
    assert file_path.exists()
    
    # Verifica que contém apenas header
    content = file_path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 1
    assert lines[0] == "Job Title,Snippet,Link"


def test_save_results_to_csv_accepts_path_object(tmp_path: Path) -> None:
    """Testa que save_results_to_csv aceita Path object."""
    results = [{"Job Title": "Job 1", "Snippet": "desc", "Link": "https://greenhouse.io/job1"}]
    
    file_path = scraper.save_results_to_csv(results, tmp_path)
    
    assert file_path.exists()
    assert isinstance(file_path, Path)


def test_save_results_to_csv_accepts_string_path(tmp_path: Path) -> None:
    """Testa que save_results_to_csv aceita string path."""
    results = [{"Job Title": "Job 1", "Snippet": "desc", "Link": "https://greenhouse.io/job1"}]
    
    file_path = scraper.save_results_to_csv(results, str(tmp_path))
    
    assert file_path.exists()
    assert isinstance(file_path, Path)


# ============================================================================
# TESTES UNITÁRIOS - _emit_progress()
# ============================================================================


def test_emit_progress_calls_callback() -> None:
    """Testa que _emit_progress chama callback com args corretos."""
    callback_calls: List[tuple[str, dict]] = []
    
    def on_progress(event: str, data: dict) -> None:
        callback_calls.append((event, data))
    
    scraper._emit_progress(on_progress, "test_event", {"key": "value"})
    
    assert len(callback_calls) == 1
    assert callback_calls[0][0] == "test_event"
    assert callback_calls[0][1] == {"key": "value"}


def test_emit_progress_no_error_when_callback_is_none() -> None:
    """Testa que _emit_progress não falha quando callback é None."""
    # Não deve lançar exceção
    scraper._emit_progress(None, "test_event", {"key": "value"})


def test_emit_progress_handles_callback_exception() -> None:
    """Testa que _emit_progress trata exceção no callback graciosamente."""
    def failing_callback(event: str, data: dict) -> None:
        raise RuntimeError("Callback error")
    
    # Não deve propagar a exceção
    scraper._emit_progress(failing_callback, "test_event", {"key": "value"})


# ============================================================================
# TESTS - build_ats_queries()
# ============================================================================


def test_build_ats_queries_default_returns_9_queries() -> None:
    """Test that default args return 9 queries (one per ATS)."""
    queries = scraper.build_ats_queries()
    assert len(queries) == 9


def test_build_ats_queries_contains_site_prefix() -> None:
    """Test each query contains the correct site: prefix."""
    queries = scraper.build_ats_queries()
    for origin, query in queries.items():
        assert "site:" in query


def test_build_ats_queries_contains_tech_keywords() -> None:
    """Test queries contain technology keywords."""
    queries = scraper.build_ats_queries(technology="python")
    for origin, query in queries.items():
        assert '"Python"' in query or '"Django"' in query or '"FastAPI"' in query or '"Flask"' in query


def test_build_ats_queries_pinpointhq_no_level_no_location() -> None:
    """Test PinpointHQ query has no level and no location filters."""
    queries = scraper.build_ats_queries(technology="php", level="senior")
    pinpoint_query = queries["PinpointHQ"]
    assert '"Senior"' not in pinpoint_query
    assert '"LATAM"' not in pinpoint_query
    assert '"remote"' in pinpoint_query
    assert '"PHP"' in pinpoint_query


def test_build_ats_queries_icims_no_location_but_has_level() -> None:
    """Test ICIMS query has level but no location filter."""
    queries = scraper.build_ats_queries(technology="php", level="senior")
    icims_query = queries["ICIMS"]
    assert '"Senior"' in icims_query
    assert '"LATAM"' not in icims_query


def test_build_ats_queries_other_ats_has_level_and_location() -> None:
    """Test other ATS platforms have both level and location filters."""
    queries = scraper.build_ats_queries(technology="php", level="senior")
    greenhouse_query = queries["Green House"]
    assert '"Senior"' in greenhouse_query
    assert '"LATAM"' in greenhouse_query


def test_build_ats_queries_invalid_technology() -> None:
    """Test ValueError raised for invalid technology."""
    with pytest.raises(ValueError, match="Unknown technology"):
        scraper.build_ats_queries(technology="cobol")


def test_build_ats_queries_invalid_level() -> None:
    """Test ValueError raised for invalid level."""
    with pytest.raises(ValueError, match="Unknown level"):
        scraper.build_ats_queries(level="expert")


def test_build_ats_queries_level_any_no_seniority_terms() -> None:
    """Test level 'any' produces queries without seniority terms."""
    queries = scraper.build_ats_queries(technology="php", level="any")
    for origin, query in queries.items():
        assert '"Senior"' not in query
        assert '"Junior"' not in query
        assert '"Trainee"' not in query


def test_build_ats_queries_different_technologies_different_keywords() -> None:
    """Test different technologies produce different keyword strings."""
    php_queries = scraper.build_ats_queries(technology="php")
    python_queries = scraper.build_ats_queries(technology="python")
    # Compare the query for same ATS - should be different
    assert php_queries["Green House"] != python_queries["Green House"]


def test_build_ats_queries_all_technologies_valid() -> None:
    """Test that all technology presets produce valid queries."""
    for tech in scraper.TECHNOLOGY_PRESETS:
        queries = scraper.build_ats_queries(technology=tech)
        assert len(queries) == 9


def test_build_ats_queries_all_levels_valid() -> None:
    """Test that all seniority levels produce valid queries."""
    for level in scraper.SENIORITY_LEVELS:
        queries = scraper.build_ats_queries(level=level)
        assert len(queries) == 9
