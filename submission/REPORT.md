# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Mạnh Hải
- **MSSV:** 2A202602988
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/NguyenManhHai2004/K4-L3-DAY13-NguyenManhHai-2A202602988-Monitoring-LLMOps
- **Commit SHA cuối:** 474fe5b (CP1 complete)
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
| `validate_dashboard.py` | TBD | Pending CP2 | Chưa triển khai traces/dashboard |
| `pytest` | TBD | Pending | Chờ chạy trên commit cuối |
| Số traces hợp lệ | TBD | Pending CP2 | Cần tối thiểu 10 traces |
| Số PII leak | TBD | 0 | Không còn PII nguyên văn trong logs |
| Latency P95 / TTFT P95 | TBD | Pending CP2 | Sẽ triển khai trong metrics panel |
| Retrieval success rate | TBD | Pending CP2 | Sẽ triển khai trong alerts |

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
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
- **SLO và lý do chọn:**
- **Cách tính error budget:**
- **Ba alert và runbook tương ứng:**

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

### CP2 Status: ⏳ IN PROGRESS
- [ ] Langfuse traces (tối thiểu 10)
- [ ] Prompt versions (v1/v2)
- [ ] Dashboard 6 panels
- [ ] SLO và alerts

### Pre-submission
- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
