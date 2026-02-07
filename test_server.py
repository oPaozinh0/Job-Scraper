"""Testes para o backend Flask (server.py)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

import server


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_csv(tmp_path: Path) -> str:
    """Cria um CSV temporário com vagas de exemplo."""
    csv_path = tmp_path / "php_backend_jobs_2026-02-07.csv"
    csv_path.write_text(
        "Job Title,Snippet,Link\n"
        "Senior PHP Engineer,Remote job description,https://job-boards.greenhouse.io/company/jobs/123\n"
        "Laravel Developer,Another job,https://jobs.lever.co/company/abc\n"
        "Full Stack Dev,Building stuff,https://jobs.ashbyhq.com/company/xyz\n"
        "Python Developer,Backend work,https://www.workable.com/company/job1\n"
        "DevOps Engineer,Infrastructure,https://breezy.hr/company/job2\n"
        "Unknown Job,Something else,https://randomsite.com/job\n",
        encoding="utf-8"
    )
    return str(csv_path)


@pytest.fixture
def sample_csv_fallback(tmp_path: Path) -> str:
    """Cria um CSV fallback sem data no nome."""
    csv_path = tmp_path / "php_backend_jobs.csv"
    csv_path.write_text(
        "Job Title,Snippet,Link\n"
        "Fallback Job,This is fallback,https://job-boards.greenhouse.io/test/1\n",
        encoding="utf-8"
    )
    return str(csv_path)


@pytest.fixture
def sample_jobs() -> List[Dict[str, str]]:
    """Retorna lista de jobs de exemplo para testes de filtros."""
    return [
        {
            "title": "Senior PHP Engineer",
            "snippet": "Remote job description",
            "link": "https://job-boards.greenhouse.io/company/jobs/123",
            "origin": "Greenhouse"
        },
        {
            "title": "Laravel Developer",
            "snippet": "Another job",
            "link": "https://jobs.lever.co/company/abc",
            "origin": "Lever"
        },
        {
            "title": "Full Stack Dev",
            "snippet": "Building stuff",
            "link": "https://jobs.ashbyhq.com/company/xyz",
            "origin": "AshBy"
        },
        {
            "title": "PHP Backend Developer",
            "snippet": "Backend work",
            "link": "https://www.workable.com/company/job1",
            "origin": "Workable"
        },
        {
            "title": "DevOps Engineer",
            "snippet": "Infrastructure",
            "link": "https://breezy.hr/company/job2",
            "origin": "Breezy"
        },
        {
            "title": "Unknown Job",
            "snippet": "Something else",
            "link": "https://randomsite.com/job",
            "origin": "Unknown"
        }
    ]


@pytest.fixture
def client() -> FlaskClient:
    """Cria um test client do Flask."""
    server.app.config["TESTING"] = True
    with server.app.test_client() as client:
        yield client


# ============================================================================
# TESTES UNITÁRIOS - detect_origin()
# ============================================================================


def test_detect_origin_greenhouse() -> None:
    """Testa detecção de origem Greenhouse."""
    assert server.detect_origin("https://job-boards.greenhouse.io/company/jobs/123") == "Greenhouse"
    assert server.detect_origin("https://greenhouse.io/company") == "Greenhouse"
    assert server.detect_origin("https://www.greenhouse.io/job") == "Greenhouse"


def test_detect_origin_lever() -> None:
    """Testa detecção de origem Lever."""
    assert server.detect_origin("https://jobs.lever.co/company/abc") == "Lever"
    assert server.detect_origin("https://www.lever.co/test") == "Lever"


def test_detect_origin_ashby() -> None:
    """Testa detecção de origem AshBy."""
    assert server.detect_origin("https://jobs.ashbyhq.com/company/xyz") == "AshBy"
    assert server.detect_origin("https://www.ashbyhq.com/job") == "AshBy"


def test_detect_origin_workable() -> None:
    """Testa detecção de origem Workable."""
    assert server.detect_origin("https://www.workable.com/company/job1") == "Workable"
    assert server.detect_origin("https://workable.com/test") == "Workable"


def test_detect_origin_breezy() -> None:
    """Testa detecção de origem Breezy."""
    assert server.detect_origin("https://breezy.hr/company/job2") == "Breezy"
    assert server.detect_origin("https://www.breezy.hr/test") == "Breezy"


def test_detect_origin_jazz() -> None:
    """Testa detecção de origem Jazz CO."""
    assert server.detect_origin("https://jazz.co/company/job") == "Jazz CO"
    assert server.detect_origin("https://www.jazz.co/test") == "Jazz CO"


def test_detect_origin_smart_recruiters() -> None:
    """Testa detecção de origem Smart Recruiters."""
    assert server.detect_origin("https://careers.smartrecruiters.com/company") == "Smart Recruiters"
    assert server.detect_origin("https://www.smartrecruiters.com/job") == "Smart Recruiters"


def test_detect_origin_icims() -> None:
    """Testa detecção de origem ICIMS."""
    assert server.detect_origin("https://careers.icims.com/jobs") == "ICIMS"
    assert server.detect_origin("https://www.icims.com/test") == "ICIMS"


def test_detect_origin_pinpoint() -> None:
    """Testa detecção de origem PinpointHQ."""
    assert server.detect_origin("https://jobs.pinpointhq.com/company") == "PinpointHQ"
    assert server.detect_origin("https://www.pinpointhq.com/job") == "PinpointHQ"


def test_detect_origin_unknown() -> None:
    """Testa detecção de origem desconhecida."""
    assert server.detect_origin("https://randomsite.com/job") == "Unknown"
    assert server.detect_origin("https://example.org/career") == "Unknown"
    assert server.detect_origin("https://unknown-ats.io/job") == "Unknown"


def test_detect_origin_with_subdomain() -> None:
    """Testa detecção com subdomínios."""
    assert server.detect_origin("https://job-boards.greenhouse.io/test") == "Greenhouse"
    assert server.detect_origin("https://apply.workable.com/company") == "Workable"
    assert server.detect_origin("https://careers.breezy.hr/job") == "Breezy"


def test_detect_origin_with_www() -> None:
    """Testa detecção com www no domínio."""
    assert server.detect_origin("https://www.greenhouse.io/job") == "Greenhouse"
    assert server.detect_origin("https://www.lever.co/test") == "Lever"
    assert server.detect_origin("https://www.ashbyhq.com/job") == "AshBy"


def test_detect_origin_invalid_url() -> None:
    """Testa detecção com URL inválida."""
    assert server.detect_origin("not-a-url") == "Unknown"
    assert server.detect_origin("") == "Unknown"


# ============================================================================
# TESTES UNITÁRIOS - apply_filters()
# ============================================================================


def test_apply_filters_no_filters(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa sem filtros - deve retornar todos os jobs."""
    result = server.apply_filters(sample_jobs, None, None)
    assert len(result) == 6
    assert result == sample_jobs


def test_apply_filters_by_origin(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa filtro por origem."""
    result = server.apply_filters(sample_jobs, "Greenhouse", None)
    assert len(result) == 1
    assert result[0]["origin"] == "Greenhouse"
    assert result[0]["title"] == "Senior PHP Engineer"


def test_apply_filters_by_origin_case_insensitive(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa filtro por origem (case-insensitive)."""
    result = server.apply_filters(sample_jobs, "greenhouse", None)
    assert len(result) == 1
    assert result[0]["origin"] == "Greenhouse"


def test_apply_filters_by_search(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa filtro por busca no título."""
    result = server.apply_filters(sample_jobs, None, "PHP")
    assert len(result) == 2
    titles = [job["title"] for job in result]
    assert "Senior PHP Engineer" in titles
    assert "PHP Backend Developer" in titles


def test_apply_filters_by_search_case_insensitive(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa filtro por busca (case-insensitive)."""
    result = server.apply_filters(sample_jobs, None, "laravel")
    assert len(result) == 1
    assert result[0]["title"] == "Laravel Developer"


def test_apply_filters_combined(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa filtro combinado (origin + search)."""
    # Adiciona job que atende ambos critérios
    sample_jobs.append({
        "title": "Senior Laravel Developer",
        "snippet": "Work with Laravel",
        "link": "https://jobs.lever.co/company/test",
        "origin": "Lever"
    })
    
    result = server.apply_filters(sample_jobs, "Lever", "Laravel")
    assert len(result) == 2  # "Laravel Developer" e "Senior Laravel Developer"
    
    for job in result:
        assert job["origin"] == "Lever"
        assert "laravel" in job["title"].lower()


def test_apply_filters_no_results(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa filtro que não retorna resultados."""
    result = server.apply_filters(sample_jobs, "NonExistent", None)
    assert len(result) == 0
    
    result = server.apply_filters(sample_jobs, None, "Rust")
    assert len(result) == 0


# ============================================================================
# TESTES UNITÁRIOS - count_origins()
# ============================================================================


def test_count_origins(sample_jobs: List[Dict[str, str]]) -> None:
    """Testa contagem de origens."""
    result = server.count_origins(sample_jobs)
    
    assert len(result) == 6
    
    # Verifica estrutura
    for item in result:
        assert "name" in item
        assert "count" in item
        assert isinstance(item["count"], int)
    
    # Verifica contagens corretas
    origin_counts = {item["name"]: item["count"] for item in result}
    assert origin_counts["Greenhouse"] == 1
    assert origin_counts["Lever"] == 1
    assert origin_counts["AshBy"] == 1
    assert origin_counts["Workable"] == 1
    assert origin_counts["Breezy"] == 1
    assert origin_counts["Unknown"] == 1


def test_count_origins_sorted_by_count() -> None:
    """Testa ordenação por contagem decrescente."""
    jobs = [
        {"title": "Job 1", "snippet": "...", "link": "...", "origin": "Greenhouse"},
        {"title": "Job 2", "snippet": "...", "link": "...", "origin": "Greenhouse"},
        {"title": "Job 3", "snippet": "...", "link": "...", "origin": "Greenhouse"},
        {"title": "Job 4", "snippet": "...", "link": "...", "origin": "Lever"},
        {"title": "Job 5", "snippet": "...", "link": "...", "origin": "Lever"},
        {"title": "Job 6", "snippet": "...", "link": "...", "origin": "AshBy"},
    ]
    
    result = server.count_origins(jobs)
    
    # Deve estar ordenado: Greenhouse (3), Lever (2), AshBy (1)
    assert result[0]["name"] == "Greenhouse"
    assert result[0]["count"] == 3
    assert result[1]["name"] == "Lever"
    assert result[1]["count"] == 2
    assert result[2]["name"] == "AshBy"
    assert result[2]["count"] == 1


def test_count_origins_empty_list() -> None:
    """Testa contagem com lista vazia."""
    result = server.count_origins([])
    assert result == []


# ============================================================================
# TESTES UNITÁRIOS - get_latest_csv()
# ============================================================================


def test_get_latest_csv_with_dated_file(tmp_path: Path) -> None:
    """Testa busca de CSV com data no nome."""
    # Cria arquivo com data
    csv_path = tmp_path / "php_backend_jobs_2026-02-07.csv"
    csv_path.write_text("Job Title,Snippet,Link\n", encoding="utf-8")
    
    with patch.object(server, "BASE_DIR", tmp_path):
        result = server.get_latest_csv()
        assert result == str(csv_path)


def test_get_latest_csv_multiple_dated_files(tmp_path: Path) -> None:
    """Testa busca de CSV quando existem múltiplos arquivos datados."""
    # Cria múltiplos arquivos
    old_csv = tmp_path / "php_backend_jobs_2026-01-01.csv"
    old_csv.write_text("old\n", encoding="utf-8")
    
    import time
    time.sleep(0.01)  # Garante diferença no mtime
    
    new_csv = tmp_path / "php_backend_jobs_2026-02-07.csv"
    new_csv.write_text("new\n", encoding="utf-8")
    
    with patch.object(server, "BASE_DIR", tmp_path):
        result = server.get_latest_csv()
        # Deve retornar o mais recente (por mtime)
        assert result == str(new_csv)


def test_get_latest_csv_fallback(tmp_path: Path) -> None:
    """Testa fallback para php_backend_jobs.csv."""
    fallback_csv = tmp_path / "php_backend_jobs.csv"
    fallback_csv.write_text("Job Title,Snippet,Link\n", encoding="utf-8")
    
    with patch.object(server, "BASE_DIR", tmp_path):
        result = server.get_latest_csv()
        assert result == str(fallback_csv)


def test_get_latest_csv_no_files(tmp_path: Path) -> None:
    """Testa erro quando nenhum CSV existe."""
    with patch.object(server, "BASE_DIR", tmp_path):
        with pytest.raises(FileNotFoundError, match="No CSV file found"):
            server.get_latest_csv()


# ============================================================================
# TESTES DE INTEGRAÇÃO - Rotas Flask
# ============================================================================


def test_index_route(client: FlaskClient) -> None:
    """Testa rota GET / - deve retornar HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


def test_api_jobs_success(client: FlaskClient, sample_csv: str) -> None:
    """Testa GET /api/jobs - retorna jobs com estrutura correta."""
    with patch("server.get_latest_csv", return_value=sample_csv):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        
        data = response.get_json()
        assert "jobs" in data
        assert "total" in data
        assert "file" in data
        
        assert data["total"] == 6
        assert len(data["jobs"]) == 6
        
        # Verifica estrutura de cada job
        for job in data["jobs"]:
            assert "title" in job
            assert "snippet" in job
            assert "link" in job
            assert "origin" in job


def test_api_jobs_filter_by_origin(client: FlaskClient, sample_csv: str) -> None:
    """Testa GET /api/jobs?origin=Greenhouse - filtra por origem."""
    with patch("server.get_latest_csv", return_value=sample_csv):
        response = client.get("/api/jobs?origin=Greenhouse")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["total"] == 1
        assert data["jobs"][0]["origin"] == "Greenhouse"
        assert data["jobs"][0]["title"] == "Senior PHP Engineer"


def test_api_jobs_filter_by_search(client: FlaskClient, sample_csv: str) -> None:
    """Testa GET /api/jobs?search=Laravel - filtra por busca."""
    with patch("server.get_latest_csv", return_value=sample_csv):
        response = client.get("/api/jobs?search=Laravel")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["total"] == 1
        assert "Laravel" in data["jobs"][0]["title"]


def test_api_jobs_filter_combined(client: FlaskClient, sample_csv: str) -> None:
    """Testa GET /api/jobs?origin=Lever&search=Developer - filtros combinados."""
    with patch("server.get_latest_csv", return_value=sample_csv):
        response = client.get("/api/jobs?origin=Lever&search=Developer")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["total"] == 1
        assert data["jobs"][0]["origin"] == "Lever"
        assert "Developer" in data["jobs"][0]["title"]


def test_api_jobs_error_handling(client: FlaskClient) -> None:
    """Testa GET /api/jobs - tratamento de erro quando CSV não existe."""
    with patch("server.get_latest_csv", side_effect=FileNotFoundError("No CSV")):
        response = client.get("/api/jobs")
        assert response.status_code == 500
        
        data = response.get_json()
        assert "error" in data


def test_api_origins_success(client: FlaskClient, sample_csv: str) -> None:
    """Testa GET /api/origins - retorna origens com contagem."""
    with patch("server.get_latest_csv", return_value=sample_csv):
        response = client.get("/api/origins")
        assert response.status_code == 200
        
        data = response.get_json()
        assert "origins" in data
        
        origins = data["origins"]
        assert len(origins) == 6
        
        # Verifica estrutura
        for origin in origins:
            assert "name" in origin
            assert "count" in origin
            assert isinstance(origin["count"], int)
        
        # Verifica que cada origem tem count = 1
        origin_names = [o["name"] for o in origins]
        assert "Greenhouse" in origin_names
        assert "Lever" in origin_names
        assert "AshBy" in origin_names
        assert "Workable" in origin_names
        assert "Breezy" in origin_names
        assert "Unknown" in origin_names


def test_api_origins_error_handling(client: FlaskClient) -> None:
    """Testa GET /api/origins - tratamento de erro."""
    with patch("server.get_latest_csv", side_effect=Exception("Test error")):
        response = client.get("/api/origins")
        assert response.status_code == 500
        
        data = response.get_json()
        assert "error" in data


# ============================================================================
# TESTES DE INTEGRAÇÃO - POST /api/scrape
# ============================================================================


def test_api_scrape_success(client: FlaskClient) -> None:
    """Testa POST /api/scrape - sucesso."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "markdown": "# Job Title\n\nJob description here",
        "text": "Job Title Job description here"
    }
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        response = client.post(
            "/api/scrape",
            json={"url": "https://jobs.lever.co/company/job123"}
        )
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert "markdown" in data
        assert "text" in data
        assert data["markdown"] == "# Job Title\n\nJob description here"
        assert data["text"] == "Job Title Job description here"
        
        # Verifica que requests.post foi chamado corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.kwargs["timeout"] == 30
        assert call_args.kwargs["json"]["url"] == "https://jobs.lever.co/company/job123"


def test_api_scrape_empty_url(client: FlaskClient) -> None:
    """Testa POST /api/scrape - URL vazia retorna 400."""
    response = client.post("/api/scrape", json={"url": ""})
    assert response.status_code == 400
    
    data = response.get_json()
    assert "error" in data
    assert "required" in data["error"].lower()


def test_api_scrape_missing_url(client: FlaskClient) -> None:
    """Testa POST /api/scrape - URL ausente retorna 400."""
    response = client.post("/api/scrape", json={})
    assert response.status_code == 400
    
    data = response.get_json()
    assert "error" in data


def test_api_scrape_no_json_body(client: FlaskClient) -> None:
    """Testa POST /api/scrape - sem body JSON retorna 400."""
    response = client.post("/api/scrape")
    assert response.status_code == 400


def test_api_scrape_request_error(client: FlaskClient) -> None:
    """Testa POST /api/scrape - erro na API externa retorna 500."""
    with patch("requests.post", side_effect=Exception("API Error")):
        response = client.post(
            "/api/scrape",
            json={"url": "https://jobs.lever.co/company/job123"}
        )
        
        assert response.status_code == 500
        
        data = response.get_json()
        assert "error" in data
        assert "scrape" in data["error"].lower()


def test_api_scrape_http_error(client: FlaskClient) -> None:
    """Testa POST /api/scrape - erro HTTP (raise_for_status)."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 500")
    
    with patch("requests.post", return_value=mock_response):
        response = client.post(
            "/api/scrape",
            json={"url": "https://jobs.lever.co/company/job123"}
        )
        
        assert response.status_code == 500


def test_api_scrape_builds_correct_payload(client: FlaskClient) -> None:
    """Testa se POST /api/scrape constrói payload correto."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"markdown": "test", "text": "test"}
    
    test_url = "https://jobs.ashbyhq.com/company/xyz"
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        client.post("/api/scrape", json={"url": test_url})
        
        # Verifica payload
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        assert payload["url"] == test_url
        assert payload["includeMarkdown"] is True
        
        # Verifica headers
        headers = call_args.kwargs["headers"]
        assert "X-API-KEY" in headers
        assert headers["Content-Type"] == "application/json"


# ============================================================================
# TESTES UNITÁRIOS - build_serper_payload()
# ============================================================================


def test_build_serper_payload() -> None:
    """Testa construção do payload Serper."""
    url = "https://jobs.lever.co/company/job123"
    payload, headers = server.build_serper_payload(url)
    
    assert payload["url"] == url
    assert payload["includeMarkdown"] is True
    
    assert headers["Content-Type"] == "application/json"
    assert "X-API-KEY" in headers


# ============================================================================
# TESTES UNITÁRIOS - load_jobs()
# ============================================================================


def test_load_jobs_success(sample_csv: str) -> None:
    """Testa carregamento de jobs do CSV."""
    jobs = server.load_jobs(sample_csv)
    
    assert len(jobs) == 6
    
    # Verifica primeiro job
    assert jobs[0]["title"] == "Senior PHP Engineer"
    assert jobs[0]["snippet"] == "Remote job description"
    assert jobs[0]["link"] == "https://job-boards.greenhouse.io/company/jobs/123"
    assert jobs[0]["origin"] == "Greenhouse"
    
    # Verifica job desconhecido
    assert jobs[5]["title"] == "Unknown Job"
    assert jobs[5]["origin"] == "Unknown"


def test_load_jobs_file_not_found() -> None:
    """Testa erro ao carregar CSV inexistente."""
    with pytest.raises(Exception):
        server.load_jobs("/path/that/does/not/exist.csv")


def test_load_jobs_empty_csv(tmp_path: Path) -> None:
    """Testa carregamento de CSV vazio."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("Job Title,Snippet,Link\n", encoding="utf-8")
    
    jobs = server.load_jobs(str(csv_path))
    assert jobs == []


def test_load_jobs_missing_fields(tmp_path: Path) -> None:
    """Testa carregamento quando campos estão faltando."""
    csv_path = tmp_path / "incomplete.csv"
    csv_path.write_text(
        "Job Title,Snippet,Link\n"
        "Test Job,,https://greenhouse.io/job\n"  # snippet vazio
        ",Some snippet,https://lever.co/job\n"   # title vazio
        "Another Job,Description,\n",            # link vazio
        encoding="utf-8"
    )
    
    jobs = server.load_jobs(str(csv_path))
    assert len(jobs) == 3
    
    # Verifica que campos vazios são strings vazias
    assert jobs[0]["title"] == "Test Job"
    assert jobs[0]["snippet"] == ""
    
    assert jobs[1]["title"] == ""
    assert jobs[1]["snippet"] == "Some snippet"
    
    assert jobs[2]["link"] == ""
    assert jobs[2]["origin"] == "Unknown"


# ============================================================================
# FIXTURE - Reset scrape status
# ============================================================================


@pytest.fixture(autouse=True)
def reset_scrape_status():
    """Reset scrape status before and after each test."""
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = False
    server._scrape_status["events"] = []
    yield
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = False
    server._scrape_status["events"] = []


# ============================================================================
# TESTES DE INTEGRAÇÃO - POST /api/fetch-jobs
# ============================================================================


def test_api_fetch_jobs_starts_scrape(client: FlaskClient) -> None:
    """Testa POST /api/fetch-jobs - inicia scrape com sucesso."""
    with patch("server.threading.Thread") as mock_thread:
        response = client.post("/api/fetch-jobs")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["status"] == "started"
        assert data["stream_url"] == "/api/fetch-jobs/stream"
        
        # Verifica que thread foi criada e iniciada
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


def test_api_fetch_jobs_conflict_when_running(client: FlaskClient) -> None:
    """Testa POST /api/fetch-jobs - retorna 409 quando já está rodando."""
    # Simula scrape em execução
    server._scrape_status["running"] = True
    
    response = client.post("/api/fetch-jobs")
    
    assert response.status_code == 409
    
    data = response.get_json()
    assert "error" in data
    assert "running" in data["error"].lower()


def test_api_fetch_jobs_returns_stream_url(client: FlaskClient) -> None:
    """Testa POST /api/fetch-jobs - retorna URL de streaming."""
    with patch("server.threading.Thread"):
        response = client.post("/api/fetch-jobs")
        
        data = response.get_json()
        assert "stream_url" in data
        assert data["stream_url"] == "/api/fetch-jobs/stream"


def test_api_fetch_jobs_sets_running_flag(client: FlaskClient) -> None:
    """Testa POST /api/fetch-jobs - define flag running."""
    with patch("server.threading.Thread"):
        assert server._scrape_status["running"] is False
        
        client.post("/api/fetch-jobs")
        
        assert server._scrape_status["running"] is True


def test_api_fetch_jobs_clears_events(client: FlaskClient) -> None:
    """Testa POST /api/fetch-jobs - limpa eventos anteriores."""
    # Adiciona eventos antigos
    server._scrape_status["events"] = [{"event": "old_event"}]
    
    with patch("server.threading.Thread"):
        client.post("/api/fetch-jobs")
        
        assert server._scrape_status["events"] == []


# ============================================================================
# TESTES DE INTEGRAÇÃO - GET /api/fetch-jobs/status
# ============================================================================


def test_api_fetch_jobs_status_initial(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/status - estado inicial."""
    response = client.get("/api/fetch-jobs/status")
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["running"] is False
    assert data["completed"] is False
    assert data["events_count"] == 0


def test_api_fetch_jobs_status_while_running(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/status - durante execução."""
    server._scrape_status["running"] = True
    server._scrape_status["events"] = [
        {"event": "ats_start", "origin": "Greenhouse"},
        {"event": "page_fetched", "origin": "Greenhouse"},
    ]
    
    response = client.get("/api/fetch-jobs/status")
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["running"] is True
    assert data["completed"] is False
    assert data["events_count"] == 2


def test_api_fetch_jobs_status_after_completion(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/status - após conclusão."""
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = True
    server._scrape_status["events"] = [
        {"event": "ats_start"},
        {"event": "ats_complete"},
        {"event": "complete", "total_jobs": 10},
    ]
    
    response = client.get("/api/fetch-jobs/status")
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["running"] is False
    assert data["completed"] is True
    assert data["events_count"] == 3


# ============================================================================
# TESTES DE INTEGRAÇÃO - POST /api/fetch-jobs/reset
# ============================================================================


def test_api_fetch_jobs_reset(client: FlaskClient) -> None:
    """Testa POST /api/fetch-jobs/reset - reseta status."""
    # Define status como completo
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = True
    server._scrape_status["events"] = [{"event": "complete"}]
    
    response = client.post("/api/fetch-jobs/reset")
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "reset"
    
    # Verifica que status foi resetado
    assert server._scrape_status["running"] is False
    assert server._scrape_status["completed"] is False
    assert server._scrape_status["events"] == []


def test_api_fetch_jobs_reset_while_running(client: FlaskClient) -> None:
    """Testa POST /api/fetch-jobs/reset - reseta mesmo se estiver rodando."""
    server._scrape_status["running"] = True
    server._scrape_status["events"] = [{"event": "ats_start"}]
    
    response = client.post("/api/fetch-jobs/reset")
    
    assert response.status_code == 200
    
    # Verifica que status foi resetado
    assert server._scrape_status["running"] is False
    assert server._scrape_status["completed"] is False
    assert server._scrape_status["events"] == []


# ============================================================================
# TESTES DE INTEGRAÇÃO - GET /api/fetch-jobs/stream
# ============================================================================


def test_api_fetch_jobs_stream_returns_sse(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - retorna SSE content-type."""
    # Pre-popula eventos e marca como completo
    server._scrape_status["running"] = True
    server._scrape_status["completed"] = True
    server._scrape_status["events"] = [{"event": "complete", "total_jobs": 0}]
    
    response = client.get("/api/fetch-jobs/stream")
    
    assert response.status_code == 200
    assert response.content_type.startswith("text/event-stream")


def test_api_fetch_jobs_stream_events_format(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - eventos têm formato SSE correto."""
    # Pre-popula eventos
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = True
    server._scrape_status["events"] = [
        {"event": "ats_start", "origin": "Greenhouse", "index": 0, "total": 9},
        {"event": "page_fetched", "origin": "Greenhouse", "page": 1, "results": 10},
        {"event": "complete", "total_jobs": 10, "file": "test.csv"},
    ]
    
    response = client.get("/api/fetch-jobs/stream")
    
    # Parse SSE lines
    content = response.data.decode()
    lines = [line for line in content.split("\n") if line.strip()]
    
    # Verifica que tem linhas de dados
    data_lines = [line for line in lines if line.startswith("data:")]
    assert len(data_lines) == 3
    
    # Verifica formato de cada linha
    for line in data_lines:
        assert line.startswith("data: ")
        json_str = line[6:]  # Remove "data: "
        data = json.loads(json_str)
        assert "event" in data


def test_api_fetch_jobs_stream_complete_event(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - para no evento complete."""
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = True
    server._scrape_status["events"] = [
        {"event": "ats_start", "origin": "Greenhouse"},
        {"event": "ats_complete", "origin": "Greenhouse", "count": 10},
        {"event": "complete", "total_jobs": 10, "file": "test.csv"},
        {"event": "should_not_appear"},  # Este não deve aparecer no stream
    ]
    
    response = client.get("/api/fetch-jobs/stream")
    
    content = response.data.decode()
    data_lines = [line for line in content.split("\n") if line.startswith("data:")]
    
    # Deve ter apenas 3 eventos (para no complete)
    assert len(data_lines) == 3
    
    # Verifica que último evento é complete
    last_line = data_lines[-1]
    last_data = json.loads(last_line[6:])
    assert last_data["event"] == "complete"


def test_api_fetch_jobs_stream_read_only(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - não inicia scrape, apenas lê eventos."""
    # Estado inicial: não está rodando e não está completo
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = False
    # Pre-populate com complete para que o generator não fique em loop
    server._scrape_status["events"] = [{"event": "complete", "total_jobs": 0}]
    
    with patch("server.threading.Thread") as mock_thread:
        response = client.get("/api/fetch-jobs/stream")
        
        # GET /stream NÃO deve iniciar thread (side-effect removido)
        mock_thread.assert_not_called()
        
        # Mas deve retornar os eventos existentes
        assert response.status_code == 200
        assert response.content_type.startswith("text/event-stream")


def test_api_fetch_jobs_stream_error_event(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - para no evento error."""
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = True
    server._scrape_status["events"] = [
        {"event": "ats_start", "origin": "Greenhouse"},
        {"event": "error", "message": "Test error"},
        {"event": "should_not_appear"},
    ]
    
    response = client.get("/api/fetch-jobs/stream")
    
    content = response.data.decode()
    data_lines = [line for line in content.split("\n") if line.startswith("data:")]
    
    # Deve ter apenas 2 eventos (para no error)
    assert len(data_lines) == 2
    
    # Verifica que último evento é error
    last_line = data_lines[-1]
    last_data = json.loads(last_line[6:])
    assert last_data["event"] == "error"


def test_api_fetch_jobs_stream_returns_204_when_idle(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - retorna 409 quando nenhum scrape está ativo."""
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = False
    server._scrape_status["events"] = []

    response = client.get("/api/fetch-jobs/stream")

    assert response.status_code == 409
    data = response.get_json()
    assert "error" in data


def test_api_fetch_jobs_stream_timeout(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - emite timeout error após tempo limite."""
    server._scrape_status["running"] = True
    server._scrape_status["completed"] = False
    server._scrape_status["events"] = []

    # Simulate time.monotonic jumping past the timeout
    start = 0.0
    with patch("server.time.monotonic", side_effect=[start, start + 601]):
        with patch("server.time.sleep"):
            response = client.get("/api/fetch-jobs/stream")

    content = response.data.decode()
    data_lines = [line for line in content.split("\n") if line.startswith("data:")]

    assert len(data_lines) == 1
    last_data = json.loads(data_lines[0][6:])
    assert last_data["event"] == "error"
    assert "timed out" in last_data["message"]


def test_api_fetch_jobs_stream_no_terminal_event(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - emite error se scrape termina sem evento terminal."""
    server._scrape_status["running"] = False
    server._scrape_status["completed"] = True
    server._scrape_status["events"] = [
        {"event": "ats_start", "origin": "Greenhouse"},
        {"event": "page_fetched", "origin": "Greenhouse", "page": 1, "results": 5},
    ]  # Missing "complete" or "error" terminal event

    response = client.get("/api/fetch-jobs/stream")

    content = response.data.decode()
    data_lines = [line for line in content.split("\n") if line.startswith("data:")]

    # Should have 2 real events + 1 synthetic error
    assert len(data_lines) == 3
    last_data = json.loads(data_lines[-1][6:])
    assert last_data["event"] == "error"
    assert "terminal event" in last_data["message"]


def test_api_fetch_jobs_stream_handles_reset_desync(client: FlaskClient) -> None:
    """Testa GET /api/fetch-jobs/stream - reset last_index when events list shrinks."""
    # Simulate a completed scrape with many events
    server._scrape_status["running"] = True
    server._scrape_status["completed"] = False
    server._scrape_status["events"] = [
        {"event": "ats_start", "origin": "Greenhouse", "index": 0, "total": 9},
        {"event": "ats_complete", "origin": "Greenhouse", "count": 5, "index": 0, "total": 9},
        {"event": "complete", "total_jobs": 5, "file": "test.csv"},
    ]

    response = client.get("/api/fetch-jobs/stream")

    content = response.data.decode()
    data_lines = [line for line in content.split("\n") if line.startswith("data:")]

    # All 3 events should be emitted, stopping at complete
    assert len(data_lines) == 3
    last_data = json.loads(data_lines[-1][6:])
    assert last_data["event"] == "complete"


# ============================================================================
# TESTES UNITÁRIOS - _run_scrape_background()
# ============================================================================


def test_run_scrape_background_success() -> None:
    """Testa _run_scrape_background - executa scrape com sucesso."""
    mock_results = [
        {"Job Title": "Job 1", "Snippet": "desc", "Link": "https://greenhouse.io/job1"},
        {"Job Title": "Job 2", "Snippet": "desc", "Link": "https://lever.co/job2"},
    ]
    mock_stats = {"Greenhouse": 1, "Lever": 1}
    mock_csv_path = Path("/tmp/test.csv")
    
    with patch("server.run_full_scrape", return_value=(mock_results, mock_stats)), \
         patch("server.save_results_to_csv", return_value=mock_csv_path):
        server._run_scrape_background()
        
        # Verifica que status foi atualizado
        assert server._scrape_status["running"] is False
        assert server._scrape_status["completed"] is True
        
        # Verifica que evento complete foi adicionado
        complete_events = [e for e in server._scrape_status["events"] if e["event"] == "complete"]
        assert len(complete_events) == 1
        assert complete_events[0]["total_jobs"] == 2
        assert complete_events[0]["file"] == "test.csv"
        assert complete_events[0]["origins"] == mock_stats


def test_run_scrape_background_invalidates_cache() -> None:
    """Testa _run_scrape_background - invalida cache CSV."""
    server._csv_cache["path"] = "/old/path.csv"
    server._csv_cache["mtime"] = 123.456
    server._csv_cache["data"] = [{"title": "old"}]
    
    with patch("server.run_full_scrape", return_value=([], {})), \
         patch("server.save_results_to_csv", return_value=Path("/tmp/test.csv")):
        server._run_scrape_background()
        
        # Verifica que cache foi invalidado
        assert server._csv_cache["path"] is None
        assert server._csv_cache["mtime"] == 0.0
        assert server._csv_cache["data"] == []


def test_run_scrape_background_error() -> None:
    """Testa _run_scrape_background - trata erros graciosamente."""
    with patch("server.run_full_scrape", side_effect=Exception("Scrape error")):
        server._run_scrape_background()
        
        # Verifica que status foi atualizado
        assert server._scrape_status["running"] is False
        assert server._scrape_status["completed"] is True
        
        # Verifica que evento error foi adicionado
        error_events = [e for e in server._scrape_status["events"] if e["event"] == "error"]
        assert len(error_events) == 1
        assert error_events[0]["message"] == "Scrape error"


def test_run_scrape_background_sets_status() -> None:
    """Testa _run_scrape_background - define flags de status corretamente."""
    # Define running=True antes de executar
    server._scrape_status["running"] = True
    
    with patch("server.run_full_scrape", return_value=([], {})), \
         patch("server.save_results_to_csv", return_value=Path("/tmp/test.csv")):
        server._run_scrape_background()
        
        # Após execução, running deve ser False e completed deve ser True
        assert server._scrape_status["running"] is False
        assert server._scrape_status["completed"] is True


def test_run_scrape_background_calls_on_progress() -> None:
    """Test _run_scrape_background passes technology, level and on_progress."""
    with patch("server.run_full_scrape", return_value=([], {})) as mock_scrape, \
         patch("server.save_results_to_csv", return_value=Path("/tmp/test.csv")):
        server._run_scrape_background("python", "senior")
        
        # Verify run_full_scrape was called with technology, level and on_progress
        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        assert call_args.kwargs["technology"] == "python"
        assert call_args.kwargs["level"] == "senior"
        assert "on_progress" in call_args.kwargs
        assert callable(call_args.kwargs["on_progress"])


# ============================================================================
# TESTS - GET /api/technologies
# ============================================================================


def test_api_technologies_returns_all_presets(client: FlaskClient) -> None:
    """Test GET /api/technologies returns all 11 technology presets."""
    response = client.get("/api/technologies")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "technologies" in data
    assert len(data["technologies"]) == 11
    
    # Verify structure
    for tech in data["technologies"]:
        assert "key" in tech
        assert "label" in tech
        assert "keywords" in tech
        assert isinstance(tech["keywords"], list)


def test_api_technologies_contains_expected_keys(client: FlaskClient) -> None:
    """Test GET /api/technologies contains expected technology keys."""
    response = client.get("/api/technologies")
    data = response.get_json()
    
    keys = [t["key"] for t in data["technologies"]]
    expected = ["php", "javascript", "python", "java", "csharp", "ruby", "go", "rust", "devops", "data", "mobile"]
    for key in expected:
        assert key in keys


# ============================================================================
# TESTS - GET /api/levels
# ============================================================================


def test_api_levels_returns_all_presets(client: FlaskClient) -> None:
    """Test GET /api/levels returns all 7 seniority levels."""
    response = client.get("/api/levels")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "levels" in data
    assert len(data["levels"]) == 7
    
    # Verify structure
    for level in data["levels"]:
        assert "key" in level
        assert "label" in level
        assert "keywords" in level
        assert isinstance(level["keywords"], list)


def test_api_levels_contains_expected_keys(client: FlaskClient) -> None:
    """Test GET /api/levels contains expected level keys."""
    response = client.get("/api/levels")
    data = response.get_json()
    
    keys = [l["key"] for l in data["levels"]]
    expected = ["any", "trainee", "junior", "mid", "senior", "staff", "manager"]
    for key in expected:
        assert key in keys


def test_api_levels_any_has_empty_keywords(client: FlaskClient) -> None:
    """Test 'any' level has empty keywords list."""
    response = client.get("/api/levels")
    data = response.get_json()
    
    any_level = [l for l in data["levels"] if l["key"] == "any"][0]
    assert any_level["keywords"] == []
    assert any_level["label"] == "Any Level"


# ============================================================================
# TESTS - POST /api/fetch-jobs validation
# ============================================================================


def test_api_fetch_jobs_with_technology_and_level(client: FlaskClient) -> None:
    """Test POST /api/fetch-jobs accepts technology and level."""
    with patch("server.threading.Thread") as mock_thread:
        response = client.post(
            "/api/fetch-jobs",
            json={"technology": "python", "level": "senior"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "started"
        
        # Verify thread was created with correct args
        mock_thread.assert_called_once()
        call_kwargs = mock_thread.call_args
        assert call_kwargs.kwargs["args"] == ("python", "senior")


def test_api_fetch_jobs_invalid_technology(client: FlaskClient) -> None:
    """Test POST /api/fetch-jobs returns 400 for invalid technology."""
    response = client.post(
        "/api/fetch-jobs",
        json={"technology": "cobol", "level": "any"}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "technology" in data["error"].lower() or "cobol" in data["error"].lower()


def test_api_fetch_jobs_invalid_level(client: FlaskClient) -> None:
    """Test POST /api/fetch-jobs returns 400 for invalid level."""
    response = client.post(
        "/api/fetch-jobs",
        json={"technology": "php", "level": "expert"}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "level" in data["error"].lower() or "expert" in data["error"].lower()


def test_api_fetch_jobs_defaults_to_php_any(client: FlaskClient) -> None:
    """Test POST /api/fetch-jobs defaults to php/any when no body."""
    with patch("server.threading.Thread") as mock_thread:
        response = client.post("/api/fetch-jobs")
        
        assert response.status_code == 200
        
        # Verify defaults
        call_kwargs = mock_thread.call_args
        assert call_kwargs.kwargs["args"] == ("php", "any")


# ============================================================================
# TESTS - get_latest_csv() with new format
# ============================================================================


def test_get_latest_csv_new_format(tmp_path: Path) -> None:
    """Test get_latest_csv finds new format jobs_*_*_*.csv files."""
    csv_path = tmp_path / "jobs_python_senior_2026-02-07.csv"
    csv_path.write_text("Job Title,Snippet,Link\n", encoding="utf-8")
    
    with patch.object(server, "BASE_DIR", tmp_path):
        result = server.get_latest_csv()
        assert result == str(csv_path)


def test_get_latest_csv_new_format_preferred_over_legacy(tmp_path: Path) -> None:
    """Test new format is preferred over legacy format."""
    legacy = tmp_path / "php_backend_jobs_2026-02-07.csv"
    legacy.write_text("old\n", encoding="utf-8")
    
    import time
    time.sleep(0.01)
    
    new_format = tmp_path / "jobs_php_any_2026-02-07.csv"
    new_format.write_text("new\n", encoding="utf-8")
    
    with patch.object(server, "BASE_DIR", tmp_path):
        result = server.get_latest_csv()
        assert result == str(new_format)
