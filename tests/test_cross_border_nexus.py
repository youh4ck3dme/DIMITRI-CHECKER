"""
DIMITRI-CHECKER - Cross-Border Nexus Test
Test 3 IČO s live API calls a cezhraničným vyhľadávaním
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import requests
import json
from datetime import datetime

# Test IČO
TEST_ICOS = [
    {"ico": "52500888", "expected_country": "SK", "name": "Test SK 1"},
    {"ico": "53059417", "expected_country": "SK", "name": "Test SK 2"},
    {"ico": "10663037", "expected_country": "CZ", "name": "Test CZ/SK"},
]

API_URL = "https://localhost:8000"

class CrossBorderNexusTest:
    """Test Cross-Border Nexus funkcionality"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
    
    def test_health_check(self):
        """Test či API server beží"""
        print("\n" + "="*80)
        print("🏥 HEALTH CHECK")
        print("="*80)
        
        try:
            response = requests.get(f"{API_URL}/api/health", verify=False, timeout=5)
            if response.status_code == 200:
                print("✅ Backend API je dostupné")
                data = response.json()
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Database: {data.get('database', 'unknown')}")
                print(f"   Cache: {data.get('cache', 'unknown')}")
                return True
            else:
                print(f"❌ Backend vrátil status {response.status_code}")
                return False
        except requests.exceptions.SSLError:
            print("⚠️  SSL certifikát je self-signed, pokračujem s verify=False")
            return self.test_health_check()
        except Exception as e:
            print(f"❌ Backend nedostupný: {e}")
            print(f"   URL: {API_URL}")
            print(f"   Skontroluj, či backend beží na porte 8000")
            return False
    
    def test_ico_lookup(self, ico_data):
        """Test vyhľadania IČO"""
        ico = ico_data["ico"]
        expected_country = ico_data["expected_country"]
        name = ico_data["name"]
        
        print(f"\n{'='*80}")
        print(f"🔍 TEST IČO: {ico} ({name})")
        print(f"   Očakávaná krajina: {expected_country}")
        print(f"{'='*80}")
        
        test_result = {
            "ico": ico,
            "name": name,
            "expected_country": expected_country,
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # Step 1: Country Detection
            print(f"\n📍 Krok 1: Detekcia krajiny pre IČO {ico}")
            country = self.detect_country(ico)
            test_result["detected_country"] = country
            test_result["steps"].append({
                "step": "country_detection",
                "result": country,
                "status": "✅" if country == expected_country else "⚠️"
            })
            print(f"   Detekovaná krajina: {country}")
            if country != expected_country:
                print(f"   ⚠️  Očakávané: {expected_country}, Detekované: {country}")
            
            # Step 2: API Call
            print(f"\n🌐 Krok 2: Volanie API pre krajinu {country}")
            response = requests.get(
                f"{API_URL}/api/search",
                params={"q": ico, "force_refresh": False},
                headers={"X-Test-Request": "true"},
                verify=False,
                timeout=30
            )
            
            print(f"   HTTP Status: {response.status_code}")
            test_result["steps"].append({
                "step": "api_call",
                "status_code": response.status_code,
                "status": "✅" if response.status_code == 200 else "❌"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Step 3: Data Validation
                print(f"\n✅ Krok 3: Validácia dát")
                self.validate_company_data(data, test_result)
                
                # Step 4: Graph Analysis
                if "graph" in data:
                    print(f"\n🕸️  Krok 4: Analýza grafu")
                    self.analyze_graph(data["graph"], test_result)
                
                # Step 5: Risk Score
                if "risk_score" in data:
                    print(f"\n⚠️  Krok 5: Risk skóre")
                    self.analyze_risk(data, test_result)
                
                # Step 6: Cross-Border Links
                print(f"\n🌍 Krok 6: Cezhraničné prepojenia")
                self.check_cross_border_links(data, test_result)
                
                test_result["status"] = "PASSED"
                self.results["summary"]["passed"] += 1
                
            else:
                print(f"   ❌ API vrátilo chybu")
                error_data = response.json() if response.content else {}
                test_result["error"] = error_data.get("detail", "Unknown error")
                test_result["status"] = "FAILED"
                self.results["summary"]["failed"] += 1
                
        except Exception as e:
            print(f"\n💥 CHYBA: {e}")
            test_result["error"] = str(e)
            test_result["status"] = "FAILED"
            self.results["summary"]["failed"] += 1
        
        self.results["tests"].append(test_result)
        return test_result
    
    def detect_country(self, ico):
        """Detekcia krajiny podľa IČO"""
        ico_clean = ico.replace(" ", "").replace("-", "")
        length = len(ico_clean)
        
        if length == 8:
            return "SK"
        elif length == 9:
            return "CZ"
        elif length == 10:
            # Môže byť PL (NIP) alebo CZ
            return "PL"
        elif length in [11, 12]:
            return "HU"
        else:
            return "UNKNOWN"
    
    def validate_company_data(self, data, test_result):
        """Validácia firemných dát"""
        required_fields = ["name", "ico", "country"]
        optional_fields = ["address", "status", "legal_form", "registration_date"]
        
        validation = {
            "required": {},
            "optional": {}
        }
        
        for field in required_fields:
            present = field in data and data[field] is not None
            validation["required"][field] = present
            status = "✅" if present else "❌"
            print(f"   {status} {field}: {data.get(field, 'MISSING')}")
        
        for field in optional_fields:
            present = field in data and data[field] is not None
            validation["optional"][field] = present
            if present:
                print(f"   ℹ️  {field}: {data.get(field)}")
        
        test_result["steps"].append({
            "step": "data_validation",
            "validation": validation,
            "status": "✅" if all(validation["required"].values()) else "❌"
        })
    
    def analyze_graph(self, graph, test_result):
        """Analýza grafovej štruktúry"""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        print(f"   Uzly (nodes): {len(nodes)}")
        print(f"   Hrany (edges): {len(edges)}")
        
        # Typy uzlov
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print(f"\n   Typy uzlov:")
        for ntype, count in node_types.items():
            print(f"      - {ntype}: {count}")
        
        # Typy hrán
        edge_types = {}
        for edge in edges:
            edge_type = edge.get("type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        if edge_types:
            print(f"\n   Typy vzťahov:")
            for etype, count in edge_types.items():
                print(f"      - {etype}: {count}")
        
        test_result["steps"].append({
            "step": "graph_analysis",
            "nodes": len(nodes),
            "edges": len(edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "status": "✅"
        })
    
    def analyze_risk(self, data, test_result):
        """Analýza risk skóre"""
        risk_score = data.get("risk_score", 0)
        risk_factors = data.get("risk_factors", [])
        
        print(f"   Risk Skóre: {risk_score}/10")
        
        if risk_score >= 7:
            print(f"   🔴 VYSOKÉ RIZIKO")
        elif risk_score >= 4:
            print(f"   🟡 STREDNÉ RIZIKO")
        else:
            print(f"   🟢 NÍZKE RIZIKO")
        
        if risk_factors:
            print(f"\n   Rizikové faktory:")
            for factor in risk_factors:
                print(f"      - {factor}")
        
        test_result["steps"].append({
            "step": "risk_analysis",
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "status": "✅"
        })
    
    def check_cross_border_links(self, data, test_result):
        """Kontrola cezhraničných prepojení"""
        graph = data.get("graph", {})
        nodes = graph.get("nodes", [])
        
        countries = set()
        for node in nodes:
            if node.get("type") == "company":
                country = node.get("country")
                if country:
                    countries.add(country)
        
        is_cross_border = len(countries) > 1
        
        print(f"   Krajiny v grafe: {', '.join(sorted(countries))}")
        print(f"   Cezhraničné prepojenia: {'✅ ÁNO' if is_cross_border else '⚠️  NIE'}")
        
        if is_cross_border:
            print(f"\n   🌍 CROSS-BORDER NEXUS DETEKOVANÝ!")
            print(f"      Tento subjekt má prepojenia v {len(countries)} krajinách:")
            for country in sorted(countries):
                company_count = sum(1 for n in nodes if n.get("country") == country and n.get("type") == "company")
                print(f"         - {country}: {company_count} firiem")
        
        test_result["steps"].append({
            "step": "cross_border_check",
            "countries": list(countries),
            "is_cross_border": is_cross_border,
            "status": "✅"
        })
    
    def generate_report(self):
        """Generovanie finálneho reportu"""
        print("\n" + "="*80)
        print("📊 FINÁLNY REPORT - CROSS-BORDER NEXUS TEST")
        print("="*80)
        
        summary = self.results["summary"]
        print(f"\nCelkovo testov: {summary['total']}")
        print(f"✅ Úspešných: {summary['passed']}")
        print(f"❌ Neúspešných: {summary['failed']}")
        print(f"⚠️  Varovaní: {summary['warnings']}")
        
        success_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0
        print(f"\n🎯 Úspešnosť: {success_rate:.1f}%")
        
        # Detail každého testu
        print(f"\n{'='*80}")
        print("DETAILNÉ VÝSLEDKY")
        print("="*80)
        
        for i, test in enumerate(self.results["tests"], 1):
            print(f"\n{i}. IČO {test['ico']} - {test['name']}")
            print(f"   Status: {test.get('status', 'UNKNOWN')}")
            print(f"   Detekovaná krajina: {test.get('detected_country', 'N/A')}")
            
            if "error" in test:
                print(f"   ❌ Chyba: {test['error']}")
            
            # Kroky
            for step in test.get("steps", []):
                step_name = step.get("step", "unknown")
                step_status = step.get("status", "❓")
                print(f"   {step_status} {step_name}")
        
        # Uloženie do JSON
        report_file = "cross_border_nexus_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Report uložený do: {report_file}")
        
        return self.results


def main():
    """Hlavná testovacia funkcia"""
    print("\n" + "="*80)
    print("🌍 DIMITRI-CHECKER - CROSS-BORDER NEXUS TEST")
    print("="*80)
    print(f"Dátum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}")
    print(f"Test IČO: {len(TEST_ICOS)}")
    
    tester = CrossBorderNexusTest()
    
    # Health check
    if not tester.test_health_check():
        print("\n❌ Backend nie je dostupný. Ukončujem testy.")
        print("   Spusti backend: cd backend && source venv/bin/activate && python main.py")
        return
    
    # Testy pre každé IČO
    tester.results["summary"]["total"] = len(TEST_ICOS)
    
    for ico_data in TEST_ICOS:
        tester.test_ico_lookup(ico_data)
    
    # Finálny report
    tester.generate_report()


if __name__ == "__main__":
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()
