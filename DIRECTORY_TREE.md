# ArtOfIAV2 - Project Directory Tree

## Directory Structure

**Excluded folders:** .git, .github, .mypy_cache, .pytest_cache, .venv, __pycache__

├── 📁 clients/
│   └── 📁 cli/
│       ├── 📁 src/
│       │   ├── 📁 client/
│       │   │   ├── 📄 EventBus.ts
│       │   │   ├── 📄 index.ts
│       │   │   ├── 📄 OrchestratorClient.ts
│       │   │   └── 📄 StateManager.ts
│       │   ├── 📁 components/
│       │   │   ├── 📄 App.tsx
│       │   │   ├── 📄 ApprovalPanel.tsx
│       │   │   ├── 📄 AttackGraphVisualizer.tsx
│       │   │   ├── 📄 Base.tsx
│       │   │   ├── 📄 CommandOutputPanel.tsx
│       │   │   ├── 📄 EventStreamPanel.tsx
│       │   │   ├── 📄 index.ts
│       │   │   └── 📄 MetricsDashboard.tsx
│       │   ├── 📁 types/
│       │   │   ├── 📄 approval.ts
│       │   │   ├── 📄 events.ts
│       │   │   ├── 📄 index.ts
│       │   │   └── 📄 ui.ts
│       │   ├── 📁 utils/
│       │   │   ├── 📄 formatters.ts
│       │   │   ├── 📄 helpers.ts
│       │   │   ├── 📄 hooks.ts
│       │   │   ├── 📄 index.ts
│       │   │   └── 📄 validators.ts
│       │   └── 📄 index.tsx
│       ├── 📄 .eslintrc.json
│       ├── 📄 .gitignore
│       ├── 📄 .prettierrc
│       ├── 📄 ARCHITECTURE.md
│       ├── 📄 COMPLETION_SUMMARY.md
│       ├── 📄 FILES.md
│       ├── 📄 INTEGRATION.md
│       ├── 📄 package.json
│       ├── 📄 quickstart.sh
│       ├── 📄 README.md
│       └── 📄 tsconfig.json
├── 📁 config/
│   └── 📄 security_policy.py
├── 📁 docs/
│   ├── 📁 architecture/
│   │   └── 📄 overview.md
│   ├── 📁 deployment/
│   │   ├── 📄 DELIVERY_MANIFEST.md
│   │   ├── 📄 DELIVERY_SUMMARY.md
│   │   ├── 📄 DEPLOYMENT.md
│   │   ├── 📄 docker-compose.md
│   │   ├── 📄 INDEX.md
│   │   ├── 📄 OPERATIONS_GUIDE.md
│   │   ├── 📄 PRODUCTION_DEPLOYMENT_HUB.md
│   │   ├── 📄 SETUP_DEVOPS.md
│   │   ├── 📄 SETUP_SENIOR_BACKEND_1.md
│   │   └── 📄 SETUP_TECH_LEAD.md
│   ├── 📁 developers/
│   │   ├── 📄 BACKENDS_DOCUMENTATION.md
│   │   ├── 📄 CMAKE.md
│   │   ├── 📄 code-structure.md
│   │   ├── 📄 CODEBASE_STRUCTURAL_ANALYSIS.md
│   │   ├── 📄 CONCRETE_FIXES_GUIDE.md
│   │   ├── 📄 INDEX.md
│   │   ├── 📄 INTEGRATION_BACKENDS_GUIDE.md
│   │   ├── 📄 INTEGRATION_GUIDE.md
│   │   ├── 📄 INTEGRATION_SUMMARY.md
│   │   ├── 📄 SENIOR_CODE_REVIEW.md
│   │   ├── 📄 SENIOR_CODE_REVIEW_ANALYSIS.md
│   │   ├── 📄 testing-guide.md
│   │   └── 📄 TROUBLESHOOTING.md
│   ├── 📁 improvements/
│   │   ├── 📁 checkpoints/
│   │   │   ├── 📄 P1.2_AGGRESSIVE_FINAL_CHECKPOINT.md
│   │   │   ├── 📄 P1.2_AGGRESSIVE_SESSION_FINAL.md
│   │   │   ├── 📄 P1.2_CHECKPOINT_AGGRESSIVE_SESSION.md
│   │   │   ├── 📄 P1.2_MYPY_FIX_PROGRESS.md
│   │   │   ├── 📄 P1.2_MYPY_STRATEGY.md
│   │   │   └── 📄 P1.2_SESSION_STATUS.md
│   │   ├── 📄 COMPREHENSIVE_SESSION_REPORT.md
│   │   ├── 📄 FINAL_VALIDATION_SUMMARY.md
│   │   ├── 📄 IMPROVEMENT_REPORT_FINAL.md
│   │   ├── 📄 INDEX.md
│   │   ├── 📄 LOGIC_AGENT_v1.0.0_SUMMARY.md
│   │   ├── 📄 P1.1_DOCS_MIGRATION_COMPLETE.md
│   │   ├── 📄 PHASE1_COMPLETION.md
│   │   ├── 📄 PHASE1_SUMMARY.md
│   │   ├── 📄 PHASE2_SUMMARY.md
│   │   ├── 📄 PHASE3_SUMMARY.md
│   │   ├── 📄 PHASE4_SUMMARY.md
│   │   ├── 📄 session-v1.3.md
│   │   ├── 📄 SESSION_COMPLETION_SUMMARY.md
│   │   ├── 📄 SESSION_REPORT.md
│   │   ├── 📄 SESSION_V1.3_COMPLETE.md
│   │   └── 📄 VALIDATION_IMPROVEMENTS_REPORT.md
│   ├── 📁 operators/
│   │   ├── 📄 INDEX.md
│   │   └── 📄 quick_start.md
│   ├── 📄 GETTING_STARTED.md
│   ├── 📄 IMPLEMENTATION_SUMMARY_v1.2.0.md
│   ├── 📄 MEMORY_SYSTEM.md
│   └── 📄 README.md
├── 📁 prompts/
│   ├── 📄 auth_escalation.yaml
│   ├── 📄 guardrails.yaml
│   ├── 📄 jwt_reasoning.yaml
│   ├── 📄 post_exploitation.yaml
│   ├── 📄 prompts.json
│   ├── 📄 recon_strategy.yaml
│   ├── 📄 report_generation.yaml
│   └── 📄 workflow_analysis.yaml
├── 📁 results/
│   └── 📁 riocuarto_exploit/
│       ├── 📄 exploit_phase3.log
│       ├── 📄 EXPLOITATION_RESULTS.json
│       └── 📄 PHASE3_EXPLOITATION_REPORT.md
├── 📁 scripts/
│   ├── 📄 build_image.sh
│   ├── 📄 init_neo4j.py
│   └── 📄 lint_all.py
├── 📁 skills/
│   ├── 📁 api/
│   │   ├── 📁 references/
│   │   └── 📄 SKILL.md
│   ├── 📁 graphql/
│   │   ├── 📁 references/
│   │   ├── 📁 scripts/
│   │   │   └── 📄 graphql_helper.py
│   │   └── 📄 SKILL.md
│   ├── 📁 jwt_abuse/
│   │   ├── 📁 references/
│   │   │   └── 📄 standards.md
│   │   ├── 📁 scripts/
│   │   │   └── 📄 jwt_helper.py
│   │   └── 📄 SKILL.md
│   ├── 📄 api-auth-and-jwt-abuse.md
│   ├── 📄 api-authorization-and-bola.md
│   ├── 📄 api_discovery.md
│   ├── 📄 graphql-and-hidden-parameters.md
│   ├── 📄 graphql_attacks.md
│   └── 📄 jwt_abuse.md
├── 📁 src/
│   ├── 📁 agents/
│   │   ├── 📁 exploit_agent/
│   │   │   ├── 📁 lotl/
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 evasion_selector.py
│   │   │   │   ├── 📄 lolbas_database.py
│   │   │   │   └── 📄 lotl_executor.py
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 executor.py
│   │   │   ├── 📄 idor_agent.py
│   │   │   ├── 📄 jwt_server.py
│   │   │   ├── 📄 mitm_agent.py
│   │   │   ├── 📄 phishing_agent.py
│   │   │   ├── 📄 sqli_agent.py
│   │   │   ├── 📄 ssrf_agent.py
│   │   │   ├── 📄 ssti_agent.py
│   │   │   └── 📄 xss_agent.py
│   │   ├── 📁 logic_agent/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 agentic_identity.py
│   │   │   ├── 📄 auth_analyzer.py
│   │   │   ├── 📄 LOGIC_AGENT_INTEGRATION.md
│   │   │   ├── 📄 post_exploit.py
│   │   │   ├── 📄 remediation.py
│   │   │   ├── 📄 report_generator.py
│   │   │   ├── 📄 server.py
│   │   │   └── 📄 workflow_analyzer.py
│   │   ├── 📁 recon_agent/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 cache_layer.py
│   │   │   ├── 📄 graphql_mapper.py
│   │   │   ├── 📄 graphql_optimizer.py
│   │   │   ├── 📄 js_analyzer.py
│   │   │   ├── 📄 network_tools.py
│   │   │   ├── 📄 prompts.yaml
│   │   │   └── 📄 server.py
│   │   ├── 📄 __init__.py
│   │   └── 📄 base_agent.py
│   ├── 📁 backends/
│   │   ├── 📁 cloud_infrastructure/
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 aws_manager.py
│   │   ├── 📁 docker_sandbox/
│   │   │   ├── 📁 security_profiles/
│   │   │   │   └── 📄 seccomp_profile.json
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 Dockerfile.ephemeral
│   │   │   ├── 📄 ebpf_monitor.py
│   │   │   ├── 📄 sandbox_manager.py
│   │   │   └── 📄 websocket_bridge.py
│   │   ├── 📁 llm_providers/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 anthropic_client.py
│   │   │   ├── 📄 fallback_engine.py
│   │   │   ├── 📄 ollama_client.py
│   │   │   ├── 📄 openai_client.py
│   │   │   └── 📄 provider_manager.py
│   │   ├── 📄 __init__.py
│   │   └── 📄 base_backend.py
│   ├── 📁 core/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 exceptions.py
│   │   ├── 📄 input_validator.py
│   │   └── 📄 resilience.py
│   ├── 📁 evasion/
│   │   ├── 📁 browser/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 fingerprint_spoofing.py
│   │   │   └── 📄 stealth_controller.py
│   │   ├── 📁 captcha/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 challenge_detector.py
│   │   │   ├── 📄 solver_client.py
│   │   │   └── 📄 token_injector.py
│   │   ├── 📁 proxy/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 jitter_engine.py
│   │   │   ├── 📄 proxy_rotator.py
│   │   │   └── 📄 tls_spoofing.py
│   │   └── 📄 __init__.py
│   ├── 📁 intelligence/
│   │   ├── 📄 __init__.py
│   │   └── 📄 self_evolving_engine.py
│   ├── 📁 memory/
│   │   ├── 📁 cache/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 cache_decorator.py
│   │   │   ├── 📄 cache_manager.py
│   │   │   ├── 📄 redis_client.py
│   │   │   └── 📄 tiered_cache.py
│   │   ├── 📁 knowledge_graph/
│   │   │   ├── 📁 agents/
│   │   │   │   └── 📁 recon/
│   │   │   │       └── 📄 recon_agent_20260415_234225.log
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 audit_20260419.jsonl
│   │   │   ├── 📄 exploitation_context.py
│   │   │   ├── 📄 graph_manager.py
│   │   │   ├── 📄 orchestrator_20260415_234225.log
│   │   │   ├── 📄 orchestrator_20260419_145305.log
│   │   │   └── 📄 temporal_tracker.py
│   │   ├── 📁 vector_db/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 context_summarizer.py
│   │   │   ├── 📄 episodic_memory.py
│   │   │   └── 📄 pgvector_client.py
│   │   ├── 📄 __init__.py
│   │   ├── 📄 __init___temp.py
│   │   └── 📄 query_optimization.py
│   ├── 📁 orchestrator/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 backend_integration.py
│   │   ├── 📄 config_loader.py
│   │   ├── 📄 examples_quick_start.py
│   │   ├── 📄 INTEGRATION_GUIDE.md
│   │   ├── 📄 logging_context.py
│   │   ├── 📄 main_integration.py
│   │   ├── 📄 memory_manager.py
│   │   ├── 📄 planner.py
│   │   ├── 📄 README.md
│   │   ├── 📄 server.py
│   │   └── 📄 supervisor.py
│   └── 📄 __init__.py
├── 📁 tests/
│   ├── 📁 agentic_red_teaming/
│   │   └── 📄 test_adversarial.py
│   ├── 📁 evaluations/
│   ├── 📁 scenarios/
│   │   └── 📄 test_vulnerabilities.py
│   ├── 📄 test_agents_behavior.py
│   ├── 📄 test_backends_and_memory.py
│   ├── 📄 test_input_validation_integration.py
│   ├── 📄 test_orchestrator_core.py
│   ├── 📄 test_p0_fixes.py
│   ├── 📄 test_phase2_improvements.py
│   ├── 📄 test_phase3_performance.py
│   ├── 📄 test_recon_caching.py
│   ├── 📄 test_task_1_1_race_condition.py
│   └── 📄 test_task_1_5_exception_handling.py
├── 📄 .dockerignore
├── 📄 .gitattributes
├── 📄 .mcp.json
├── 📄 .pylintrc
├── 📄 AGENTS.md
├── 📄 ATTACK_STRATEGY_RIOCUARTO.md
├── 📄 DEPLOYMENT_VERIFICATION_GUIDE.md
├── 📄 DIRECTORY_TREE.md
├── 📄 docker-compose.yml
├── 📄 Dockerfile
├── 📄 DOCUMENTATION_INDEX.md
├── 📄 EXECUTIVE_SUMMARY_FINAL.md
├── 📄 EXECUTIVE_SUMMARY_RIOCUARTO.md
├── 📄 exploit_riocuarto_phase3.py
├── 📄 EXPLOIT_VECTORS_OPERATIONAL.md
├── 📄 FINAL_COMPLETE_CYCLE_REPORT.md
├── 📄 FINAL_CONSOLIDATED_REPORT.md
├── 📄 final_system_test.py
├── 📄 INDEX_RIOCUARTO.md
├── 📄 MASTER_ROADMAP_EXPLOIT_READY.md
├── 📄 PHASE_2_COMPLETE_INDEX.md
├── 📄 PROJECT_COMPLETION_SUMMARY.md
├── 📄 pyproject.toml
├── 📄 QUICK_REFERENCE.md
├── 📄 README.md
├── 📄 RECON_REPORT_RIOCUARTO.md
├── 📄 recon_riocuarto.py
├── 📄 recon_riocuarto_report.json
├── 📄 requirements.txt
├── 📄 SECURITY_FIXES_IMPLEMENTATION_GUIDE.md
├── 📄 START_HERE.md
├── 📄 SYSTEM_VERIFICATION_REPORT.md
├── 📄 test_complete_system.py
└── 📄 test_flow_complete.py