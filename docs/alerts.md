# Runbooks - CP2 Alerts

## Alert 1

- **Tên:** high_tail_latency
- **Severity:** CRITICAL
- **Duration:** 5 minutes
- **Kênh thông báo:** Slack (#incidents)
- **SLI/SLO liên quan:** fast_successful_requests SLO (P95 latency ≤ 3000ms)
- **Điều kiện và thời gian duy trì:** P95 latency > 3000ms sustained for 5 minutes
- **Ảnh hưởng tới người dùng:** Users experience slow response times; SLA breach risk
- **Ba bước kiểm tra đầu tiên:**
  1. Check dashboard latency panel → identify if retriever or generation is slow
  2. Review logs for correlation IDs with high latency_ms; check for RAG_SLOW incident
  3. Check Langfuse traces waterfall → which span (retriever/generation) is the bottleneck
- **Mitigation tạm thời:**
  - Increase timeout for RAG calls or scale retriever service
  - Enable request queuing if overloaded
  - Temporarily disable complex query expansion
- **Owner:** platform-team

## Alert 2

- **Tên:** retrieval_failure_spike
- **Severity:** HIGH
- **Duration:** 10 minutes
- **Kênh thông báo:** Slack (#incidents)
- **SLI/SLO liên quan:** Retrieval success rate ≥ 90% (from SLO guardrails)
- **Điều kiện và thời gian duy trì:** retrieval_success_rate_pct < 90 for 10 minutes
- **Ảnh hưởng tới người dùng:** Degraded answer quality; fallback answers used
- **Ba bước kiểm tra đầu tiên:**
  1. Check dashboard errors panel → tool_success breakdown; see if tool_name=retrieval
  2. Filter logs for tool_success=false and tool_name=retrieval; check error_type
  3. Check Langfuse retriever span; look for exceptions or timeouts in waterfall
- **Mitigation tạm thời:**
  - Restart vector store service or check connection
  - Clear cache if index corrupted
  - Fall back to fallback retriever or disable filtering
- **Owner:** rag-team

## Alert 3

- **Tên:** error_rate_elevation
- **Severity:** HIGH
- **Duration:** 10 minutes
- **Kênh thông báo:** Slack (#incidents)
- **SLI/SLO liên quan:** Error rate ≤ 2% (from SLO guardrails)
- **Điều kiện và thời gian duy trì:** error_rate_pct > 2% for 10 minutes
- **Ảnh hưởng tới người dùng:** Increased 5xx responses; API reliability issues
- **Ba bước kiểm tra đầu tiên:**
  1. Check dashboard errors panel → count breakdown by error_type
  2. Filter logs for event=request_failed; identify most common error_type with correlation IDs
  3. Check Langfuse traces for failed spans; see which step (retriever/generation) threw exception
- **Mitigation tạm thời:**
  - Restart API service or LLM service
  - Check resource availability (memory, disk, connections)
  - Enable request shedding or circuit breaker for failing service
- **Owner:** platform-team
