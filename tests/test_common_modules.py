"""
Tests for common utility modules:
- config.py (centralized config loader)
- spatial_utils.py (GeoDataFrame helpers, chunked spatial join)
- aggregation_utils.py (calcular_indicadores)
- bulk_write.py (batched MongoDB writes)
- observability.py (pipeline metrics)
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Tests: src/common/config.py
# ---------------------------------------------------------------------------

class TestConfig:
    def test_get_config_loads_ibge(self):
        from src.common.config import get_config
        cfg = get_config("ibge_censo")
        assert "filtro_uf" in cfg
        assert isinstance(cfg["filtro_uf"], list)
        assert "25" in cfg["filtro_uf"]

    def test_get_config_loads_geocode(self):
        from src.common.config import get_config
        cfg = get_config("config_geocode")
        assert "geocode_pipeline" in cfg
        assert "paths" in cfg

    def test_get_config_invalid_name_raises(self):
        from src.common.config import get_config, ConfigError
        with pytest.raises(ConfigError, match="not found"):
            get_config("nonexistent_config_xyz")

    def test_validate_keys_passes(self):
        from src.common.config import validate_keys
        cfg = {"ftp": {"host": "example.com"}, "paths": {"silver": "/tmp"}}
        validate_keys(cfg, ["ftp.host", "paths.silver"])

    def test_validate_keys_fails(self):
        from src.common.config import validate_keys, ConfigError
        cfg = {"ftp": {"host": "example.com"}}
        with pytest.raises(ConfigError, match="Missing"):
            validate_keys(cfg, ["ftp.host", "paths.silver"])

    def test_get_nested(self):
        from src.common.config import get_nested
        cfg = {"a": {"b": {"c": 42}}}
        assert get_nested(cfg, "a.b.c") == 42
        assert get_nested(cfg, "a.b.x", default="nope") == "nope"


# ---------------------------------------------------------------------------
# Tests: src/common/spatial_utils.py
# ---------------------------------------------------------------------------

class TestSpatialUtils:
    def test_escolas_para_geodataframe(self):
        from src.common.spatial_utils import escolas_para_geodataframe
        df = pd.DataFrame({
            "CO_ENTIDADE": ["1", "2", "3"],
            "latitude": [-7.1, -8.0, None],
            "longitude": [-34.8, -35.0, None],
        })
        gdf = escolas_para_geodataframe(df)
        assert len(gdf) == 2  # one row dropped (None coords)
        assert gdf.crs.to_epsg() == 4326

    def test_escolas_para_geodataframe_all_valid(self):
        from src.common.spatial_utils import escolas_para_geodataframe
        df = pd.DataFrame({
            "CO_ENTIDADE": ["1", "2"],
            "latitude": [-7.1, -8.0],
            "longitude": [-34.8, -35.0],
        })
        gdf = escolas_para_geodataframe(df)
        assert len(gdf) == 2

    def test_poligono_para_geojson(self):
        from src.common.spatial_utils import poligono_para_geojson
        from shapely.geometry import Point
        geojson = poligono_para_geojson(Point(0, 0))
        assert geojson["type"] == "Point"
        assert geojson["coordinates"] == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Tests: src/common/aggregation_utils.py
# ---------------------------------------------------------------------------

class TestAggregationUtils:
    def test_calcular_indicadores_basic(self):
        from src.common.aggregation_utils import calcular_indicadores
        df = pd.DataFrame({
            "municipio_cep": ["A", "A", "B"],
            "QT_MAT_FUND": [100, 200, 50],
            "QT_MAT_MED": [50, 60, 30],
            "QT_MAT_INF": [20, 30, 10],
            "IN_INTERNET": [1, 0, 1],
            "IN_BIBLIOTECA": [1, 1, 0],
            "IN_LABORATORIO_INFORMATICA": [0, 0, 1],
            "IN_ACESSIBILIDADE_INEXISTENTE": [0, 1, 0],
        })
        config = {
            "matriculas": ["QT_MAT_FUND", "QT_MAT_MED", "QT_MAT_INF"],
            "internet": "IN_INTERNET",
            "biblioteca": "IN_BIBLIOTECA",
            "lab_informatica": "IN_LABORATORIO_INFORMATICA",
            "sem_acessibilidade": "IN_ACESSIBILIDADE_INEXISTENTE",
        }
        result = calcular_indicadores(df, "municipio_cep", config)
        assert len(result) == 2

        row_a = result[result["municipio_cep"] == "A"].iloc[0]
        assert row_a["total_escolas"] == 2
        assert row_a["total_matriculas"] == 460
        assert row_a["pct_com_internet"] == 50.0
        assert row_a["pct_com_biblioteca"] == 100.0

    def test_calcular_indicadores_empty_group(self):
        from src.common.aggregation_utils import calcular_indicadores
        df = pd.DataFrame({
            "grupo": ["A"],
            "QT_MAT_FUND": [10],
            "QT_MAT_MED": [5],
            "QT_MAT_INF": [2],
            "IN_INTERNET": [1],
            "IN_BIBLIOTECA": [0],
            "IN_LABORATORIO_INFORMATICA": [0],
            "IN_ACESSIBILIDADE_INEXISTENTE": [0],
        })
        config = {
            "matriculas": ["QT_MAT_FUND", "QT_MAT_MED", "QT_MAT_INF"],
            "internet": "IN_INTERNET",
            "biblioteca": "IN_BIBLIOTECA",
            "lab_informatica": "IN_LABORATORIO_INFORMATICA",
            "sem_acessibilidade": "IN_ACESSIBILIDADE_INEXISTENTE",
        }
        result = calcular_indicadores(df, "grupo", config)
        assert len(result) == 1
        assert result.iloc[0]["total_matriculas"] == 17


# ---------------------------------------------------------------------------
# Tests: src/common/bulk_write.py
# ---------------------------------------------------------------------------

class TestBulkWrite:
    def test_batched_bulk_write_splits_into_batches(self):
        from src.common.bulk_write import batched_bulk_write, BulkWriteResult

        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.upserted_count = 3
        mock_result.modified_count = 2
        mock_collection.bulk_write.return_value = mock_result

        # 10 operations with batch_size=4 → 3 batches
        operations = [MagicMock() for _ in range(10)]
        result = batched_bulk_write(mock_collection, operations, batch_size=4)

        assert mock_collection.bulk_write.call_count == 3
        assert result.upserted_count == 9   # 3 per batch × 3 batches
        assert result.modified_count == 6   # 2 per batch × 3 batches
        assert result.batches_completed == 3

    def test_batched_bulk_write_empty_operations(self):
        from src.common.bulk_write import batched_bulk_write
        mock_collection = MagicMock()
        result = batched_bulk_write(mock_collection, [])
        assert result.total == 0
        mock_collection.bulk_write.assert_not_called()

    def test_batched_bulk_write_continues_on_error(self):
        from src.common.bulk_write import batched_bulk_write

        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.upserted_count = 2
        mock_result.modified_count = 1

        # First batch fails, second succeeds
        mock_collection.bulk_write.side_effect = [
            Exception("connection lost"),
            mock_result,
        ]

        operations = [MagicMock() for _ in range(6)]
        result = batched_bulk_write(mock_collection, operations, batch_size=3)

        assert result.batches_completed == 1
        assert result.upserted_count == 2
        assert len(result.errors) == 1


# ---------------------------------------------------------------------------
# Tests: src/common/observability.py
# ---------------------------------------------------------------------------

class TestObservability:
    def test_pipeline_report_basic(self):
        from src.common.observability import PipelineReport

        report = PipelineReport("test_pipeline")

        with report.stage("step1") as metrics:
            metrics.records_processed = 100

        with report.stage("step2") as metrics:
            metrics.records_processed = 200

        summary = report.summary()
        assert summary["pipeline"] == "test_pipeline"
        assert summary["total_stages"] == 2
        assert summary["failed_stages"] == 0
        assert summary["stages"][0]["records_processed"] == 100
        assert summary["stages"][1]["records_processed"] == 200

    def test_pipeline_report_captures_error(self):
        from src.common.observability import PipelineReport

        report = PipelineReport("test_pipeline")

        with pytest.raises(ValueError):
            with report.stage("failing_step") as metrics:
                raise ValueError("boom")

        summary = report.summary()
        assert summary["failed_stages"] == 1
        assert "boom" in summary["stages"][0]["error"]

    def test_pipeline_report_save(self):
        from src.common.observability import PipelineReport

        with tempfile.TemporaryDirectory() as tmpdir:
            report = PipelineReport("test", output_dir=tmpdir)
            with report.stage("s1") as m:
                m.records_processed = 5

            path = report.save()
            assert path.exists()

            data = json.loads(path.read_text())
            assert data["pipeline"] == "test"
            assert data["stages"][0]["records_processed"] == 5

    def test_global_metrics(self):
        from src.common.observability import PipelineReport

        report = PipelineReport("test")
        report.record("total_escolas", 75000)
        report.record("ufs_processadas", 9)

        summary = report.summary()
        assert summary["metrics"]["total_escolas"] == 75000
        assert summary["metrics"]["ufs_processadas"] == 9
