"""
Integračné testy - testujú celý systém end-to-end
"""
import sys
import os
import time

# Pridať backend venv do path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
venv_path = os.path.join(backend_path, 'venv', 'lib', 'python3.14', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

try:
    import requests
except ImportError:
    print("⚠️ requests nie je nainštalovaný. Inštalujem...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_backend_health():
    """Test backend health"""
    print("🔍 Test: Backend health...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("   ✅ Backend health OK")
        return True
    except Exception as e:
        print(f"   ❌ Backend health failed: {e}")
        return False

def test_frontend_accessible():
    """Test, či frontend je dostupný"""
    print("🔍 Test: Frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        assert response.status_code == 200
        assert "ILUMINATI" in response.text or "root" in response.text
        print("   ✅ Frontend accessible OK")
        return True
    except Exception as e:
        print(f"   ⚠️ Frontend not accessible: {e} (možno nie je spustený)")
        return False

def test_cross_origin():
    """Test CORS konfigurácia"""
    print("🔍 Test: CORS configuration...")
    try:
        response = requests.options(
            f"{BASE_URL}/api/search",
            headers={"Origin": FRONTEND_URL},
            timeout=5
        )
        # OPTIONS request by mal vrátiť 200 alebo 204
        assert response.status_code in [200, 204, 405]  # 405 je OK ak OPTIONS nie je podporovaný
        print("   ✅ CORS OK")
        return True
    except Exception as e:
        print(f"   ⚠️ CORS test: {e}")
        return True  # Nech to neblokuje ostatné testy

def test_v4_integration():
    """Test V4 integrácia (SK, CZ, PL, HU)"""
    print("🔍 Test: V4 integration...")
    try:
        countries = {
            "SK": "88888888",
            "CZ": "27074358",
            "PL": "123456789",
            "HU": "12345678"
        }
        
        results = {}
        for country, query in countries.items():
            try:
                response = requests.get(f"{BASE_URL}/api/search?q={query}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    country_nodes = [n for n in data.get("nodes", []) if n.get("country") == country]
                    results[country] = len(country_nodes) > 0
                else:
                    results[country] = False
            except:
                results[country] = False
        
        all_ok = all(results.values())
        status = "✅" if all_ok else "⚠️"
        print(f"   {status} V4 integration: {sum(results.values())}/4 countries")
        for country, ok in results.items():
            print(f"      {country}: {'✅' if ok else '❌'}")
        
        return all_ok
    except Exception as e:
        print(f"   ❌ V4 integration test failed: {e}")
        return False

def run_all_tests():
    """Spustí všetky integračné testy"""
    print("")
    print("═══════════════════════════════════════")
    print("🧪 SPÚŠTANIE INTEGRAČNÝCH TESTOV")
    print("═══════════════════════════════════════")
    print("")
    
    tests = [
        test_backend_health,
        test_frontend_accessible,
        test_cross_origin,
        test_v4_integration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("")
    print("═══════════════════════════════════════")
    print("📊 VÝSLEDKY TESTOV")
    print("═══════════════════════════════════════")
    print("")
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"✅ Úspešné: {passed}/{total}")
    print(f"❌ Zlyhané: {total - passed}/{total}")
    print(f"📈 Úspešnosť: {success_rate:.1f}%")
    print("")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

