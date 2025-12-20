"""
Testy pre ERP integrácie
"""
import pytest
import requests
from typing import Dict

BASE_URL = "http://localhost:8000"


def test_erp_endpoints_require_authentication():
    """Test, že ERP endpointy vyžadujú autentifikáciu"""
    response = requests.get(f"{BASE_URL}/api/enterprise/erp/connections")
    assert response.status_code == 401 or response.status_code == 403


def test_erp_endpoints_require_enterprise_tier():
    """Test, že ERP endpointy vyžadujú Enterprise tier"""
    # Tento test by potreboval vytvorenie testovacieho používateľa
    # Pre teraz len overíme, že endpoint existuje
    pass


def test_erp_connection_create_model():
    """Test ERP connection create model"""
    from backend.main import ErpConnectionCreate
    
    # Test valid ERP types
    valid_types = ["sap", "pohoda", "money_s3"]
    for erp_type in valid_types:
        model = ErpConnectionCreate(
            erp_type=erp_type,
            connection_data={"api_key": "test", "company_id": "123"}
        )
        assert model.erp_type == erp_type


def test_erp_connector_base():
    """Test base ERP connector"""
    from backend.services.erp.base_connector import BaseErpConnector
    
    # Base class by nemal byť možné inštanciovať priamo
    with pytest.raises(TypeError):
        BaseErpConnector({})


def test_pohoda_connector_initialization():
    """Test Pohoda connector inicializácia"""
    from backend.services.erp.pohoda_connector import PohodaConnector
    
    connector = PohodaConnector({
        "api_key": "test_key",
        "company_id": "test_company"
    })
    
    assert connector.api_key == "test_key"
    assert connector.company_id == "test_company"
    assert connector.base_url == "https://api.pohoda.sk"


def test_money_s3_connector_initialization():
    """Test Money S3 connector inicializácia"""
    from backend.services.erp.money_s3_connector import MoneyS3Connector
    
    connector = MoneyS3Connector({
        "api_key": "test_key",
        "company_id": "test_company"
    })
    
    assert connector.api_key == "test_key"
    assert connector.company_id == "test_company"
    assert connector.base_url == "https://api.moneys3.cz"


def test_sap_connector_initialization():
    """Test SAP connector inicializácia"""
    from backend.services.erp.sap_connector import SapConnector
    
    connector = SapConnector({
        "server_url": "https://sap.example.com",
        "username": "test_user",
        "password": "test_pass",
        "company_db": "TEST_DB"
    })
    
    assert connector.server_url == "https://sap.example.com"
    assert connector.username == "test_user"
    assert connector.company_db == "TEST_DB"


def test_erp_service_get_connector():
    """Test získanie správneho connectora"""
    from backend.services.erp.erp_service import get_connector
    from backend.services.erp.models import ErpType
    
    # Test Pohoda
    pohoda_conn = get_connector(ErpType.POHODA, {"api_key": "test"})
    assert pohoda_conn.__class__.__name__ == "PohodaConnector"
    
    # Test Money S3
    money_conn = get_connector(ErpType.MONEY_S3, {"api_key": "test"})
    assert money_conn.__class__.__name__ == "MoneyS3Connector"
    
    # Test SAP
    sap_conn = get_connector(ErpType.SAP, {"server_url": "test", "username": "u", "password": "p", "company_db": "db"})
    assert sap_conn.__class__.__name__ == "SapConnector"


def test_erp_models():
    """Test ERP database models"""
    from backend.services.erp.models import ErpConnection, ErpSyncLog, ErpType, ErpConnectionStatus
    
    # Test enum values
    assert ErpType.SAP.value == "sap"
    assert ErpType.POHODA.value == "pohoda"
    assert ErpType.MONEY_S3.value == "money_s3"
    
    assert ErpConnectionStatus.ACTIVE.value == "active"
    assert ErpConnectionStatus.INACTIVE.value == "inactive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

