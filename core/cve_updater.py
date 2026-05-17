import json
import requests
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

log = get_logger("cve_updater")

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CVE_CACHE_FILE = Path(__file__).parent.parent / "cve_cache.json"


class CVEUpdater:
    def __init__(self):
        self.cache = self._load_cache()

    def _load_cache(self):
        if CVE_CACHE_FILE.exists():
            try:
                with open(CVE_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"last_updated": None, "cves": []}

    def _save_cache(self):
        try:
            with open(CVE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning(f"Failed to save CVE cache: {e}")

    def fetch_recent(self, days=30, max_results=50):
        end_date = datetime.now()
        start_date = datetime.now()
        start_date = start_date.replace(day=start_date.day - days)

        params = {
            "lastModStartDate": start_date.strftime("%Y-%m-%dT00:00:00.000"),
            "lastModEndDate": end_date.strftime("%Y-%m-%dT23:59:59.999"),
            "resultsPerPage": max_results,
        }

        try:
            resp = requests.get(NVD_API, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            cves = []
            for item in data.get("vulnerabilities", []):
                cve = item.get("cve", {})
                cve_id = cve.get("id", "")
                description = ""
                for desc in cve.get("descriptions", []):
                    if desc.get("lang") == "en":
                        description = desc.get("value", "")[:200]
                        break

                cvss = 0
                for metric in cve.get("metrics", {}).values():
                    for m in metric:
                        cvss = m.get("cvssData", {}).get("baseScore", 0)
                        break

                vendors = []
                for node in cve.get("configurations", []):
                    for cpe in node.get("nodes", []):
                        for match in cpe.get("cpeMatch", []):
                            uri = match.get("criteria", "")
                            if uri:
                                parts = uri.split(":")
                                if len(parts) >= 5:
                                    vendors.append(parts[4])

                severity = "medium"
                if cvss >= 9.0:
                    severity = "critical"
                elif cvss >= 7.0:
                    severity = "high"
                elif cvss < 4.0:
                    severity = "low"

                cves.append({
                    "cve": cve_id,
                    "service": vendors[0].title() if vendors else "Unknown",
                    "port": 0,
                    "severity": severity,
                    "type": "unknown",
                    "metasploit": "",
                    "desc": description,
                    "cvss": cvss,
                    "source": "NVD",
                    "date": cve.get("lastModified", "")[:10],
                })

            self.cache["last_updated"] = datetime.now().isoformat()
            self.cache["cves"] = cves
            self._save_cache()
            log.info(f"Fetched {len(cves)} CVEs from NVD")
            return cves
        except Exception as e:
            log.error(f"NVD API error: {e}")
            return []

    def get_cached_cves(self):
        return self.cache.get("cves", [])

    def get_stats(self):
        cves = self.cache.get("cves", [])
        by_severity = {}
        for c in cves:
            sev = c.get("severity", "unknown")
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return {
            "total": len(cves),
            "last_updated": self.cache.get("last_updated", "never"),
            "by_severity": by_severity,
        }


_global_updater = None


def get_cve_updater():
    global _global_updater
    if _global_updater is None:
        _global_updater = CVEUpdater()
    return _global_updater
