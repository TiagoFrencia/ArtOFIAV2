"""
Report Generator - Vulnerability Report Aggregation & Generation
==================================================================
Módulo especializado en generar reportes ejecutivos y técnicos.

Correlaciona hallazgos de Neo4j en reportes formateados.
Tipos de reportes:
- Executive Summary (C-level)
- Technical Details (developers)
- CVSS Scores
- Remediation Steps
- Timeline
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VulnerabilityReport:
    """Reporte de vulnerabilidad individual"""
    id: str
    title: str
    description: str
    severity: str
    cvss_score: float
    affected_endpoints: List[str]
    attack_chain: List[str]
    remediation_steps: List[str]
    business_impact: str
    discovered_at: str


class ReportGenerator:
    """
    Generador de reportes de vulnerabilidades.
    
    Formato de salida:
    - Markdown para portabilidad
    - HTML para visualización
    - JSON para integración con SIEM
    """
    
    def __init__(self) -> None:
        self.report_id: str | None = None
        self.generated_at: datetime | None = None
    
    async def generate_executive_report(self, vulnerabilities: List[Dict[str, Any]],
                                       target_url: str) -> str:
        """
        Generar reporte ejecutivo (CEO/CISO friendly).
        """
        
        self.generated_at = datetime.now()
        
        # Actualizar ID del reporte
        self.report_id = f"REP-{hash(str(vulnerabilities))}"
        
        # Calcular estadísticas
        stats = self._calculate_statistics(vulnerabilities)
        
        # Construcción del reporte ejecutivo
        report = f"""
# EXECUTIVE VULNERABILITY REPORT
## {target_url}

**Report ID:** {self.report_id}  
**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Summary:** {len(vulnerabilities)} vulnerabilities identified

---

## KEY FINDINGS

### Risk Score: {stats['overall_risk']}/10

| Severity | Count | Impact |
|----------|-------|--------|
| Critical | {stats['critical']} | Immediate exploitation risk |
| High | {stats['high']} | Significant security breach potential |
| Medium | {stats['medium']} | Should be addressed in sprint |
| Low | {stats['low']} | Address during maintenance |

---

## BUSINESS IMPACT

**Estimated Financial Impact:** ${self._estimate_financial_impact(stats)}

**Recommended Actions:**
1. **Immediate (24 hours):** Patch all CRITICAL vulnerabilities
2. **Short-term (1 week):** Address HIGH severity issues
3. **Medium-term (30 days):** Remediate MEDIUM severity
4. **Long-term:** Monitor and update LOW severity

---

## TOP 3 VULNERABILITIES

"""
        
        top_vulns = sorted(vulnerabilities, 
                          key=lambda x: ['critical', 'high', 'medium', 'low'].index(x.get('severity', 'low')))[:3]
        
        for i, vuln in enumerate(top_vulns, 1):
            report += f"""
### {i}. {vuln.get('title', 'Unknown')}

**Severity:** {vuln.get('severity', 'Unknown')}  
**Impact:** {vuln.get('business_impact', 'Data breach, system compromise')}

{vuln.get('description', 'N/A')}

"""
        
        report += """
---

## REMEDIATION TIMELINE

- **Week 1:** Patch critical vulnerabilities
- **Week 2-3:** Deploy patches to production
- **Week 4:** Verify fixes, conduct retesting
- **Month 2:** Implement security improvements

---

## NEXT STEPS

1. Assign vulnerabilities to development team
2. Schedule remediation sprints
3. Establish security review process
4. Conduct penetration testing post-remediation
"""
        
        logger.info(f"Executive report generated: {self.report_id}")
        
        return report
    
    async def generate_technical_report(self, vulnerabilities: List[Dict[str, Any]],
                                       target_url: str) -> str:
        """
        Generar reporte técnico (developers).
        """
        
        report = f"""
# TECHNICAL VULNERABILITY REPORT
## {target_url}

**Report ID:** {self.report_id}  
**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S') if self.generated_at else 'N/A'}

---

## TABLE OF CONTENTS

"""
        
        for i, vuln in enumerate(vulnerabilities, 1):
            report += f"- {i}. {vuln.get('title', 'Unknown Vulnerability')}\n"
        
        report += "\n---\n"
        
        # Detalles técnicos para cada vulnerabilidad
        for i, vuln in enumerate(vulnerabilities, 1):
            report += f"""
## {i}. {vuln.get('title', 'Unknown Vulnerability')}

### Details
- **Severity:** {vuln.get('severity', 'Unknown')}
- **CVSS Score:** {vuln.get('cvss_score', 'N/A')}
- **CWE:** {vuln.get('cwe', 'N/A')}
- **Affected Endpoints:** {', '.join(vuln.get('affected_endpoints', []))}

### Vulnerability Description
{vuln.get('description', 'N/A')}

### Attack Chain
"""
            
            for step in vuln.get('attack_chain', []):
                report += f"1. {step}\n"
            
            report += """
### Proof of Concept
```
"""
            report += vuln.get('poc_code', '# PoC would go here\n')
            report += """
```

### Remediation Steps
"""
            
            for step in vuln.get('remediation_steps', []):
                report += f"- {step}\n"
            
            report += "\n"
        
        logger.info(f"Technical report generated: {self.report_id}")
        
        return report
    
    async def generate_json_report(self, vulnerabilities: List[Dict[str, Any]],
                                  target_url: str) -> Dict[str, Any]:
        """
        Generar reporte en formato JSON (para APIs/SIEM).
        """
        
        report = {
            "metadata": {
                "report_id": self.report_id,
                "generated_at": self.generated_at.isoformat() if self.generated_at else None,
                "target_url": target_url,
                "total_vulnerabilities": len(vulnerabilities),
            },
            "summary": {
                "critical": len([v for v in vulnerabilities if v.get('severity') == 'critical']),
                "high": len([v for v in vulnerabilities if v.get('severity') == 'high']),
                "medium": len([v for v in vulnerabilities if v.get('severity') == 'medium']),
                "low": len([v for v in vulnerabilities if v.get('severity') == 'low']),
            },
            "vulnerabilities": vulnerabilities,
            "remediation_priority": self._calculate_priority_order(vulnerabilities),
        }
        
        logger.info(f"JSON report generated with {len(vulnerabilities)} vulnerabilities")
        
        return report
    
    def _calculate_statistics(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular estadísticas de vulnerabilidades"""
        
        severity_map = {'critical': 10, 'high': 7, 'medium': 4, 'low': 1}
        
        stats = {
            'critical': len([v for v in vulnerabilities if v.get('severity') == 'critical']),
            'high': len([v for v in vulnerabilities if v.get('severity') == 'high']),
            'medium': len([v for v in vulnerabilities if v.get('severity') == 'medium']),
            'low': len([v for v in vulnerabilities if v.get('severity') == 'low']),
        }
        
        # Calcular overall risk score
        total_score = sum(
            severity_map.get(v.get('severity', 'low'), 1) 
            for v in vulnerabilities
        )
        overall_risk = min(10, total_score / max(len(vulnerabilities), 1))
        stats['overall_risk'] = int(round(overall_risk, 1))
        
        return stats
    
    def _estimate_financial_impact(self, stats: Dict[str, Any]) -> int:
        """Estimar impacto financiero de vulnerabilidades"""
        
        # Modelo simplista: critical=$100k, high=$20k, medium=$5k, low=$1k
        impact = (
            int(stats['critical']) * 100000 +
            int(stats['high']) * 20000 +
            int(stats['medium']) * 5000 +
            int(stats['low']) * 1000
        )
        
        return impact
    
    def _calculate_priority_order(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calcular orden de prioridad de remediación"""
        
        # Ordenar por severidad y complejidad de fix
        priority_order = []
        
        for i, vuln in enumerate(sorted(vulnerabilities, 
                                        key=lambda x: (
                                            ['critical', 'high', 'medium', 'low'].index(x.get('severity', 'low')),
                                            x.get('complexity', 'medium') == 'high'
                                        )), 1):
            
            priority_order.append({
                "order": i,
                "vulnerability": vuln.get('title'),
                "severity": vuln.get('severity'),
                "estimated_fix_time": self._estimate_fix_time(vuln),
            })
        
        return priority_order
    
    def _estimate_fix_time(self, vuln: Dict[str, Any]) -> str:
        """Estimar tiempo de remediación"""
        
        severity = vuln.get('severity', 'medium')
        complexity = vuln.get('complexity', 'medium')
        
        times = {
            ('critical', 'high'): "2-4 hours",
            ('critical', 'medium'): "1-2 hours",
            ('critical', 'low'): "30 minutes",
            ('high', 'high'): "4-8 hours",
            ('high', 'medium'): "2-4 hours",
            ('high', 'low'): "1-2 hours",
            ('medium', 'high'): "8-16 hours",
            ('medium', 'medium'): "4-8 hours",
            ('medium', 'low'): "2-4 hours",
            ('low', 'high'): "16-24 hours",
            ('low', 'medium'): "8-16 hours",
            ('low', 'low'): "4-8 hours",
        }
        
        return times.get((severity, complexity), "TBD")
