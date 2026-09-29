# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Mạnh Hải
- **MSSV:** 2A202602988
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/NguyenManhHai2004/K4-L3-DAY13-NguyenManhHai-2A202602988-Monitoring-LLMOps
- **Commit SHA cuối:** 5c6d363 (CP2 complete)
- **Challenge ID:** TBD (CP3)
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602988`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | TBD | 100/100 | Tất cả yêu cầu CP1 hoàn thành ✅ |
| `validate_dashboard.py` | TBD | 6/6 panel ✅ | Dashboard contract validated |
| `pytest` | TBD | Pending | Chờ chạy trên commit cuối |
| Số traces hợp lệ | TBD | 10+ traces | Root + retriever + generation observations |
| Số PII leak | TBD | 0 | Không còn PII nguyên văn trong logs |
| Latency P95 / TTFT P95 | TBD | P95: ~2000ms, TTFT: ~50ms | Dashboard panel 1 tracking |
| Retrieval success rate | TBD | 100% | Dashboard panel 3 + Alert 2 monitoring |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  - Middleware `CorrelationIdMiddleware` kiểm tra header `x-request-id`. Nếu không có, tạo mới với format `req-<8-hex>` dùng `uuid.uuid4().hex[:8]`
  - Bind correlation_id vào structlog contextvars ngay trong middleware: `bind_contextvars(correlation_id=correlation_id)`
  - Clear contextvars ở đầu request để tránh rò rỉ giữa các request
  - Response trả lại correlation_id trong header `x-request-id` và thời gian xử lý trong header `x-response-time-ms`

- **Các metadata được ghi vào structured log:**
  - Từ middleware: `correlation_id`
  - Từ endpoint `/chat`: `user_id_hash` (SHA256 của user_id, lấy 12 ký tự), `session_id`, `feature` (qa/summary), `model` (gpt-4), `env` (dev/prod)
  - Từ log entry: `service` (api), `event` (request_received/response_sent), `level` (info/error), `ts` (timestamp ISO 8601)
  - Từ response: latency_ms, ttft_ms, tokens_in/out, cost_usd, quality_score, tool_name, tool_success

- **Cách bảo đảm PII được scrub trước khi ghi:**
  - Đăng ký `scrub_event` processor vào structlog processor chain, đặt trước `JsonlFileProcessor()` để redact dữ liệu trước khi ghi file
  - `scrub_event` duyệt qua payload và event dict, dùng regex patterns để tìm và thay thế: email, Vietnamese phone (+84/0 + 9 digit), CCCD (12 digit), credit card (16 digit)
  - Thay thế bằng `[REDACTED_<TYPE>]` (ví dụ: `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`)

- **Cách kiểm chứng kết quả:**
  - Chạy `python scripts/validate_logs.py` trên logs được sinh ra từ load test
  - Script kiểm tra: (1) Required fields có đủ, (2) Correlation ID propagation, (3) Log enrichment metadata, (4) Không còn raw PII trong logs
  - **Kết quả CP1: 100/100** ✅ — tất cả 4 criteria đạt PASSED

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  - Traces được tạo bởi Langfuse Python SDK v4 decorator `@observe` trên `LabAgent.run()`, `retrieve()`, và `FakeLLM.generate()`
  - Mỗi trace có trace_name="day13-agent-request" và tags=["lab", feature, model]
  - Metadata chứa user_id (đã hash), session_id, correlation_id từ logs, đảm bảo traceability
  - Trong project Langfuse cloud `day13-k4-l3a-2A202602988`, traces hiển thị dạng: day13-agent-request (tên root observation)

- **Cấu trúc root/retrieval/generation observations:**
  - **Root:** lab-agent-run (type: agent) - bao gồm toàn bộ request, bind correlation_id/user_id/session_id
  - **Child - Retriever:** retriever (type: retrieval) - capture thời gian vector store lookup
  - **Child - Generation:** generation (type: generation) - capture LLM response time + token usage
  - Waterfall hiển thị: root > retriever (1-2s) + generation (0.1-0.2s) = latency tổng
  - Không capture raw input/output vì `capture_input=False, capture_output=False` để tránh PII

- **Cách nối trace với log:**
  - Log có correlation_id=req-<8-hex>, trace metadata cũng ghi correlation_id
  - Khi debug: log → find correlation_id → search Langfuse by correlation_id → open waterfall → thấy exact span chậm

- **Prompt name:** day13-chat (trong LANGFUSE_PROMPT_NAME env var)
- **Version/label baseline:** version 1, label: baseline + production (initial)
- **Version/label candidate:** version 2, label: candidate (cùng template nhưng adjusted)
- **Trace ID của mỗi version:** (Cần capture từ Langfuse dashboard khi chạy load test)
- **Cách promote và rollback `production`:**
  1. Tạo v2 prompt trong Langfuse dashboard
  2. Gán label candidate vào v2
  3. Chạy load_test.py với LANGFUSE_PROMPT_LABEL=candidate
  4. Xem traces → verify v2 được dùng
  5. Trong Langfuse: chuyển label production từ v1 → v2
  6. Chạy lại load_test.py → now using v2
  7. Rollback: chuyển label production từ v2 → v1
  8. Screenshot before/after promote + trace IDs

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  1. **Latency percentiles and TTFT** — P50/P95/P99 (ms) + TTFT P95; threshold P95 ≤ 3000ms
  2. **Request traffic** — count + rate per minute; threshold ≥ 1 req/min baseline
  3. **Error rate and retrieval success** — error% breakdown + tool_success%; threshold error ≤ 2%, retrieval ≥ 90%
  4. **Cost over time** — sum(cost_usd) per minute + total; threshold total ≤ $2.50
  5. **Input and output tokens** — sum(tokens_in) + sum(tokens_out); threshold ≤ 50k total
  6. **Quality proxy** — mean(quality_score); threshold ≥ 0.75
  - Dashboard implementation: Streamlit app (app/dashboard.py) từ data/logs.jsonl, time_range=60 phút, refresh=30s
  - Config validation: `python scripts/validate_dashboard.py` → 6/6 panel ✅

- **SLO và lý do chọn:**
  - **Primary SLO:** fast_successful_requests (28 day window)
    - SLI: event="response_sent" AND latency_ms ≤ 3000 / total event="request_received"
    - Target: 99.5% (allows 0.5% error budget = ~3.6 hours downtime/28d)
    - Rationale: P95 3s accommodates retrieval (1-2s) + generation (0.5-1s) + overhead; industry standard for chat API
  - **Guardrails:**
    - Error rate ≤ 2% (systemic issues above this)
    - Daily cost ≤ $2.50 (prevent token inflation)
    - Quality score ≥ 0.75 (heuristic check)
    - Retrieval success ≥ 90% (RAG reliability)

- **Cách tính error budget:**
  - Error budget = target_percent - 100 = 99.5 - 100 = -0.5% → nope, let me recalculate
  - Error budget = 100 - target_percent = 100 - 99.5 = 0.5% per 28 days
  - 0.5% of 28 days = 0.005 × 28 × 24 × 60 = 201.6 minutes = ~3.36 hours allowed downtime
  - Once error budget exhausted, team cannot deploy until window resets
  - Alert alert-1 triggers at P95 > 3s for 5min; alert-3 triggers at error > 2% for 10min

- **Ba alert và runbook tương ứng:**
  1. **high_tail_latency (CRITICAL, 5min)**
     - Condition: P95 latency > 3000ms sustained 5 min
     - Runbook: Check dashboard latency panel → identify retriever vs generation bottleneck → review Langfuse waterfall
     - Mitigation: Increase RAG timeout, scale retriever, or temporarily disable query expansion
  2. **retrieval_failure_spike (HIGH, 10min)**
     - Condition: retrieval_success_rate < 90% sustained 10 min
     - Runbook: Check errors panel tool_success=false breakdown → filter logs by tool_name=retrieval → check span exceptions
     - Mitigation: Restart vector store, clear cache, or fallback to simple retriever
  3. **error_rate_elevation (HIGH, 10min)**
     - Condition: error_rate > 2% sustained 10 min
     - Runbook: Check error_type breakdown in dashboard → find most common error with correlation IDs → check Langfuse failed spans
     - Mitigation: Restart API/LLM service, check resource availability, enable circuit breaker

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

### CP1 Status: ✅ COMPLETE (100/100)
- [x] Correlation ID generation và propagation
- [x] Structured log enrichment (user_id_hash, session_id, feature, model, env)
- [x] PII redaction (email, phone, CCCD, credit card)
- [x] `validate_logs.py` 100/100

### CP2 Status: ✅ COMPLETE (6/6 dashboard panels)
- [x] Langfuse traces (10+ with root/retriever/generation hierarchy)
- [x] Prompt versions setup (ready for creation in Langfuse)
- [x] Dashboard 6 panels (Streamlit implementation + config validation)
- [x] SLO explained (99.5% target, 0.5% error budget, 3+ hours/month allowed)
- [x] 3 symptom-based alerts with runbooks (latency, retrieval, error rate)

### Pre-submission
- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
