# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Mạnh Hải
- **MSSV:** 2A202602988
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/NguyenManhHai2004/K4-L3-DAY13-NguyenManhHai-2A202602988-Monitoring-LLMOps
- **Commit SHA cuối:** `782b080486562d10556d190b0d13566d6538bba9` (commit chứa toàn bộ code, report và evidence)
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602988`

## 2. Evidence index

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
| Prompt versions (sau rollback: `production` ở v1) | `evidence/09-prompt-versions.png` |
| Prompt promote `production` → v2 | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

Baseline được đo bằng cách chạy lại starter code (commit `13b6066`) trong một git worktree riêng, tắt tracing, chạy `load_test.py` và các validator.

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Baseline: `correlation_id=MISSING`, 22/23 record thiếu enrichment, 0 correlation ID hợp lệ |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | `config/dashboard.yaml` đã có sẵn đủ contract; validator chỉ kiểm tra YAML |
| `pytest` | 22 passed | 26 passed | Thêm 4 test PII: CCCD, thẻ (3 định dạng), hộ chiếu, và kiểm tra không scrub nhầm correlation ID/hash/số liệu |
| Số traces hợp lệ | 27 trace chỉ có root, không có child | 19 trace đủ root + `retriever` + `generation` | Tổng 66 trace trong project; 20 trace giữa chừng có retriever mang type SPAN (lỗi type đã sửa) |
| Số PII leak | 0 | 0 | Baseline đã scrub `message_preview` qua `summarize_text`; `scrub_event` bổ sung lớp bảo vệ ở tầng logger |
| Latency P95 / TTFT P95 | 152 ms / 51 ms | Bình thường: 1298 ms / 51 ms; khi incident: 2654 ms / 56 ms | P95 1298 ms là do request đầu tiên sau mỗi lần khởi động API (cold start lấy prompt từ Langfuse); các request còn lại khoảng 150 ms |
| Retrieval success rate | 100% | 100% | Incident `rag_slow` làm chậm retriever nhưng không làm retriever lỗi |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `CorrelationIdMiddleware` ([app/middleware.py](../app/middleware.py)) gọi `clear_contextvars()` ở đầu mỗi request để không rò context từ request trước. Middleware lấy `x-request-id` từ header; nếu không có thì sinh `req-<8-hex>` bằng `uuid.uuid4().hex[:8]`. ID được bind vào structlog contextvars, lưu vào `request.state` để truyền sang `LabAgent.run` và trace metadata, rồi trả lại qua header `x-request-id` cùng `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** `correlation_id` (middleware); `user_id_hash` (12 ký tự đầu SHA-256 của `user_id`), `session_id`, `feature`, `model` (`claude-sonnet-4-5`, lấy từ `agent.model` để khớp với trace), `env` được bind trong `/chat` trước `request_received`; processor thêm `level`, `ts`; mỗi event thêm `service`, `event`, và `response_sent` có thêm `latency_ms`, `ttft_ms`, `tokens_in/out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` được đăng ký trong processor chain ([app/logging_config.py](../app/logging_config.py)) ngay sau `TimeStamper` và trước `JsonlFileProcessor`/`JSONRenderer`, nên dữ liệu được redact trước khi serialize hoặc ghi file. Pattern trong [app/pii.py](../app/pii.py) thay email, số điện thoại Việt Nam (`+84`/`0` + 9 số, có hoặc không có dấu cách/chấm/gạch), CCCD 12 số, thẻ 16 số (liền, cách hoặc gạch) và hộ chiếu Việt Nam (1 chữ in hoa + 7 số, pattern tự bổ sung) bằng `[REDACTED_<TYPE>]`. Raw `user_id` không bao giờ được log, chỉ log hash.
- **Cách kiểm chứng kết quả:** Sau khi lưu baseline, xóa `data/logs.jsonl`, khởi động lại API và chạy lại load test. `validate_logs.py` đạt 100/100 trên 48 record, 21 correlation ID, 0 PII leak (`evidence/02-log-validator.png`); chạy lại trên toàn bộ log ở commit cuối vẫn đạt 100/100. Header `x-request-id: req-5aa0a281` được kiểm tra bằng `curl -i`. `evidence/05-pii-redaction.png` cho thấy email trong câu hỏi được thay bằng `[REDACTED_EMAIL]`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Key trong `.env` được tạo trong project `day13-k4-l3a-2A202602988`. Mỗi trace có `session_id`, `correlation_id` trùng với log local; ví dụ trace `f74a5780bc76d5d11dd316e70557eb27` có session `k4-l3a-challenge-s01`, khớp dòng log `req-7601dc00`. Trace ID cũng được lấy lại qua API `GET /api/public/v2/observations` bằng chính key của project.
- **Cấu trúc root/retrieval/generation observations:**
  - Root `lab-agent-run` (type `agent`): gắn `user_id` đã hash, `session_id`, `environment`, tags `lab`/feature/model, metadata `correlation_id`, `feature`, `model`, `prompt_name/label/version/source`.
  - Child `retriever` (type `retriever`, [app/mock_rag.py](../app/mock_rag.py)).
  - Child `generation` (type `generation`, [app/mock_llm.py](../app/mock_llm.py)): gọi `update_current_generation` với `model`, `usage_details` (input/output tokens), `cost_details` (3 USD/1M input, 15 USD/1M output), metadata `ttft_ms`; prompt được liên kết qua `propagate_attributes(prompt=...)`.
  - Cả ba observation đều dùng `capture_input=False, capture_output=False` để không đưa raw message (có thể chứa PII) lên Langfuse.
- **Danh sách trace hợp lệ** (19 trace đủ root `agent` + `retriever` + `generation` có model/usage/cost, lấy qua `GET /api/public/v2/observations` của project cá nhân; `correlation_id` đọc từ trace metadata và trùng với log):

  | # | Thời điểm (UTC) | Trace ID | Session | Correlation ID | Prompt |
  |---:|---|---|---|---|---|
  | 1 | 09:37:19 | `412ce0633f958dc30a21a0fab743cbfa` | s01 | `req-ee1eeec8` | v1 |
  | 2 | 09:37:20 | `a7284e4ae2dad95f76913b153c309640` | s02 | `req-967bf6f9` | v1 |
  | 3 | 09:37:20 | `bcd56406baf298a33b31d212f6268643` | s03 | `req-b413d175` | v1 |
  | 4 | 09:37:20 | `6cb26966306ed9ff19e3b8fe6a4de645` | s04 | `req-c66ca199` | v1 |
  | 5 | 09:37:20 | `c58410b33bc0d9a866920b2d4f28de75` | s05 | `req-13e58b15` | v1 |
  | 6 | 09:37:21 | `9403645af00cf6038f0e3b2de6c5491c` | s06 | `req-7371e9ad` | v1 |
  | 7 | 09:37:21 | `2311d8c2e30940d1dedd42cc84e8fef3` | s07 | `req-1594f225` | v1 |
  | 8 | 09:37:21 | `383efbf8b9d0ed90289eaeae80232e3e` | s08 | `req-51907527` | v1 |
  | 9 | 09:37:21 | `db4de2321c352f62ee88691ca2255ffb` | s09 | `req-70ce31c9` | v1 |
  | 10 | 09:37:21 | `e646270054f3cb5891609e82e779bfec` | s10 | `req-1877713f` | v1 |
  | 11 | 09:47:09 | `f74a5780bc76d5d11dd316e70557eb27` | k4-l3a-challenge-s01 | `req-7601dc00` | v1 |
  | 12 | 09:47:12 | `dec8abb0bc396c2655b1152963e04194` | k4-l3a-challenge-s05 | `req-c43fa48b` | v2 |
  | 13 | 09:47:15 | `a390f115dddef5305158a4a837bac537` | k4-l3a-challenge-s02 | `req-6579419c` | v2 |
  | 14 | 09:47:17 | `3fdedfb83802f981c66d9a29226b5ff9` | k4-l3a-challenge-s03 | `req-b0af753a` | v2 |
  | 15 | 09:47:20 | `c3002e2cff7685d525dcd3b761257db7` | k4-l3a-challenge-s04 | `req-a4ebc9e6` | v2 |
  | 16 | 10:00:47 | `f26318b4c96cbbfadb6e1aa2efe726d4` | prompt-ab-session | `req-5d0b3df0` | v1 |
  | 17 | 10:01:01 | `6a2409761e99c33f48f6414868217d78` | prompt-ab-session | `req-bae47160` | v2 |
  | 18 | 10:01:18 | `6614a75a9cee77b6092ee660b5a6250f` | prompt-ab-session | `req-2cddc486` | v2 |
  | 19 | 10:01:35 | `afd5eb391b0410d96d74b8075efc7d92` | prompt-ab-session | `req-8f4c75a3` | v1 |

- **Cách nối trace với log:** Cùng một `correlation_id` xuất hiện trong log (`data/logs.jsonl`) và trong trace metadata. Từ log, lấy `correlation_id` rồi lọc Langfuse theo metadata `correlation_id` (hoặc theo `session_id`) để mở đúng trace.
- **Prompt name:** `day13-chat` (tạo bằng [scripts/setup_prompts.py](../scripts/setup_prompts.py)).
- **Version/label baseline:** v1, labels `baseline` + `production`, template `Feature={{feature}} / Docs={{docs}} / Question={{message}}`.
- **Version/label candidate:** v2, label `candidate`; thay đổi nhỏ về format: `Please answer: {{message}}` và thêm `Keep response concise.`
- **Trace ID của mỗi version** (cùng input `Summarize the monitoring policy for production logging`, session `prompt-ab-session`; version được đọc từ field `version` của root observation):

  | Bước | Label khi chạy | Prompt version | Correlation ID | Trace ID |
  |---|---|---|---|---|
  | A | `baseline` | 1 | `req-5d0b3df0` | `f26318b4c96cbbfadb6e1aa2efe726d4` |
  | B | `candidate` | 2 | `req-bae47160` | `6a2409761e99c33f48f6414868217d78` |
  | C | `production` (đã promote v2) | 2 | `req-2cddc486` | `6614a75a9cee77b6092ee660b5a6250f` |
  | D | `production` (sau rollback) | 1 | `req-8f4c75a3` | `afd5eb391b0410d96d74b8075efc7d92` |

- **Cách promote và rollback `production`:** App đọc label từ `LANGFUSE_PROMPT_LABEL` (mặc định `production`), nên đổi version production không cần sửa code. Promote: gán label `production` cho v2 trong Langfuse (UI "Promote to production", `evidence/10-prompt-rollback.png`); Langfuse tự bỏ label này khỏi v1. Rollback: gán lại `production` cho v1; `evidence/09-prompt-versions.png` chụp sau rollback cho thấy #1 mang `production, baseline` và #2 mang `latest, candidate`. Vì client cache prompt 60 giây (`cache_ttl_seconds=60`), sau khi đổi label cần chờ hết TTL hoặc khởi động lại API; trace C và D xác nhận production lần lượt phục vụ v2 rồi v1.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Streamlit app [app/dashboard.py](../app/dashboard.py) đọc `data/logs.jsonl`, lọc 60 phút gần nhất theo `config/dashboard.yaml` (`streamlit run app/dashboard.py`):
  1. Latency P50/P95/P99 + TTFT P95 (ms), ngưỡng P95 ≤ 3000 ms.
  2. Request traffic: tổng request và req/phút, ngưỡng ≥ 1 req/phút.
  3. Error rate (%) và retrieval success (%), ngưỡng error ≤ 2%, retrieval ≥ 90%.
  4. Cost (USD): tổng trong cửa sổ và ước tính theo ngày, ngưỡng ≤ 2.50 USD.
  5. Input/output tokens, ngưỡng tổng ≤ 50k.
  6. Quality proxy: trung bình `quality_score` (0–1), ngưỡng ≥ 0.75.

  Lúc bình thường (`evidence/11-dashboard-overview.png`, 20 request): P50 152 ms, P95 1298 ms, TTFT P95 51 ms, error 0%, retrieval 100%, cost 0.041 USD, 3248 tokens, quality 0.88.
- **SLO và lý do chọn:** `fast_successful_requests` trong cửa sổ 28 ngày; SLI = số `response_sent` có `latency_ms ≤ 3000` / tổng `request_received`; target 99.5%. Baseline đo được P95 152 ms khi ổn định và khoảng 1.1–1.8 s ở request cold start, nên 3000 ms vẫn còn dư cho cold start mà không cảnh báo nhầm. Guardrails: error ≤ 2%, cost ≤ 2.50 USD/ngày, quality ≥ 0.75, retrieval success ≥ 90%. Challenge cho thấy ngưỡng này quá lỏng với feature `monitoring` (xem mục 7, preventive measure).
- **Cách tính error budget:** SLI tính theo request, nên error budget = 100% − 99.5% = 0.5% số request trong 28 ngày. Với lưu lượng tối thiểu 1 req/phút: 28 × 24 × 60 = 40 320 request, suy ra được phép tối đa khoảng 201 request chậm hoặc lỗi. Nếu 60 phút có tỷ lệ request xấu khoảng 20% (như lúc incident nếu áp ngưỡng 2000 ms của challenge: 10/49 request trong `evidence/12-incident-metric.png`), burn rate = 20% / 0.5% = 40 lần, tức ngân sách 28 ngày sẽ cạn trong khoảng 17 giờ.
- **Ba alert và runbook tương ứng** ([config/alert_rules.yaml](../config/alert_rules.yaml), runbook chi tiết ở [docs/alerts.md](../docs/alerts.md)):
  1. `high_tail_latency`: critical, P95 latency > 3000 ms trong 5 phút, owner `platform-team`, Slack `#incidents`. Runbook: xem panel latency, lấy correlation ID chậm trong log, mở waterfall để xác định retriever hay generation chậm.
  2. `retrieval_failure_spike`: high, retrieval success < 90% trong 10 phút, owner `rag-team`, Slack `#incidents`. Runbook: lọc log `tool_success=false`, xem `error_type`, kiểm tra span `retriever` có exception.
  3. `error_rate_elevation`: high, error rate > 2% trong 10 phút, owner `platform-team`, Slack `#incidents`. Runbook: phân rã `error_type` trên dashboard, lấy correlation ID của `request_failed`, tìm span lỗi trong trace.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` (cohort K4, incident `rag_slow`, seed 1311, feature bị ảnh hưởng `monitoring`, ngưỡng 2000 ms).
- **Khoảng thời gian điều tra:** 2026-09-29 10:26:47Z – 10:27:01Z (17:26:47 – 17:27:01 giờ Việt Nam), 5 request challenge chạy với `--concurrency 5`, ngay sau 10 request bình thường làm mốc. Lần chạy đầu lúc 09:47:08Z – 09:47:23Z cho kết quả giống hệt, xác nhận sự cố tái hiện ổn định.
- **Triệu chứng từ metrics:** Dashboard 60 phút (`evidence/12-incident-metric.png`, 49 request): P95 latency 2654 ms, P99 2680 ms, vượt ngưỡng challenge 2000 ms; lúc bình thường P95 là 1298 ms (`evidence/11-dashboard-overview.png`) và trong 10 request mốc ngay trước sự cố, 9 request chỉ 155–167 ms (request đầu tiên khoảng 1.5 s do cold start lấy prompt). P50 vẫn 154 ms và TTFT P95 56 ms, error rate 0%, retrieval success 100%, token/cost không đổi: sự cố chỉ nằm ở đuôi latency của một nhóm request, không phải lỗi hay chi phí.
- **Log line và correlation ID liên quan:** `req-ecd209a4`, session `k4-l3a-challenge-s05`, feature `monitoring` (`evidence/13-incident-log.png`): `response_sent` lúc 10:26:50.805Z với `latency_ms=2652`, `ttft_ms=50`, `tokens_in=35`, `tokens_out=123`, `cost_usd=0.00195`, `tool_success=true`. Bốn correlation ID còn lại (`req-4168133e`, `req-cf77f816`, `req-704a3481`, `req-b38f582d`) có `latency_ms` 2652–2680; toàn bộ đều thuộc feature `monitoring`.
- **Trace ID và span gây ảnh hưởng:** `78ca9a3975051104e28ccb80d66f7af6` (`evidence/14-incident-trace.png`): root `lab-agent-run` 2.656 s, trong đó `retriever` 2.504 s (94%) và `generation` 0.152 s. Bốn trace còn lại (`532d7f56ead9d9137dcdef06986b9b17`, `bdcc4580760f47ce84bfe878033029d3`, `5642d7f99a39b9e27ac6d296f5507ed5`, `41d79a00d4689e4b2e2ee47162b93f60`) cùng mẫu: retriever 2.503–2.505 s. 10 trace mốc ngay trước đó có retriever 0–0.007 s.
- **Root cause:** Bước retrieval (vector store) chậm thêm khoảng 2.5 s cho mỗi request do incident `rag_slow`; LLM generation và TTFT bình thường. Metric (P95 tăng nhưng P50/TTFT/error/cost không đổi), log (`latency_ms` cao, `ttft_ms=50`, `tool_success=true`) và trace (span `retriever` chiếm 94% thời gian) cùng chỉ về retriever.
- **Loại trừ prompt là nguyên nhân:** Ở lần chạy đầu (09:47Z), `production` vừa được promote sang v2: trace đầu dùng v1 (prompt cũ còn trong cache), bốn trace sau dùng v2. Ở lần chạy lại (10:26Z), sau rollback, cả năm trace dùng v1. Mọi trường hợp đều có latency khoảng 2.65 s và retriever khoảng 2.50 s, nên version prompt không ảnh hưởng tới sự cố.
- **Fix action:** Tắt incident (`python scripts/inject_incident.py --disable`). Kiểm chứng bằng cùng câu hỏi `monitoring` ngay sau đó: `req-024951c7`, trace `dcfa453aaeee063c713ed9294b484a03`, `x-response-time-ms=156`, `retriever` 0 s thay vì 2.5 s. Trong hệ thống thật: kiểm tra độ trễ vector store, thêm timeout cho `retrieve()` và fallback trả lời không có context khi quá hạn.
- **Preventive measure:**
  1. Alert `high_tail_latency` (P95 > 3000 ms) **không kích hoạt** trong incident này vì P95 chỉ khoảng 2650 ms. Đề xuất hạ ngưỡng SLI/alert xuống 2000 ms theo challenge, hoặc thêm alert theo burn rate.
  2. Thêm alert/panel riêng cho thời lượng span `retriever` (P95 theo feature), vì latency tổng bị pha loãng khi trộn với feature khác.
  3. Client đo được tới 13.3 s dù server chỉ mất 2.65 s mỗi request: `agent.run` là hàm đồng bộ chạy trong `async def chat`, chặn event loop nên 5 request bị xử lý tuần tự. Chuyển endpoint sang `def` (chạy trong threadpool) hoặc dùng `run_in_threadpool` để một request chậm không kéo chậm các request khác.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Tắt `capture_input/capture_output` trên cả ba observation và chỉ gửi metadata đã được kiểm soát (hash user, `query_preview` đã scrub, usage, cost) lên Langfuse. Log local được scrub bằng processor, nhưng Langfuse là hệ thống bên ngoài; nếu capture raw input thì PII sẽ rời khỏi hệ thống trước khi kịp scrub. Đánh đổi là trace không cho xem nguyên văn câu hỏi, nên phải dùng `correlation_id` để quay lại log đã scrub.
- **Một lỗi/blocker đã gặp:** Các trace đầu tiên báo `prompt_source=local-fallback` vì project chưa có prompt `day13-chat`. Sau khi tạo prompt bằng script, label `baseline` và `candidate` vẫn không xuất hiện trên Langfuse.
- **Cách tìm nguyên nhân và xử lý:** Đọc lại prompt qua API thì thấy v1 chỉ có label `production`, còn `candidate` nằm trong `tags`: script đã gửi label vào nhầm field `tags`. Sửa script dùng field `labels` và cập nhật label của các version hiện có qua `prompt_version.update`. Các blocker khác: `GET /api/public/traces` trả 410 cho organization mới nên chuyển sang `/api/public/v2/observations`; trace bị mất khi API bị kill ngay sau request nên phải chờ SDK flush; type `retrieval` không hợp lệ nên Langfuse hiển thị span retriever là SPAN, sửa thành `retriever`.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics trả lời "có vấn đề không và khi nào" (P95 tăng lên 2654 ms lúc 17:26). Logs trả lời "request nào bị ảnh hưởng" (lọc theo thời gian và feature, lấy `req-ecd209a4`). Traces trả lời "chậm ở bước nào" (waterfall cho thấy `retriever` 2.50 s). `correlation_id` là khóa nối log với trace.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version gắn vào mỗi trace giúp biết chính xác request nào dùng prompt nào; khi chất lượng hoặc latency thay đổi có thể so sánh v1/v2 trên cùng input, và rollback chỉ là chuyển label mà không cần deploy code. Token/cost gắn trên generation giúp phát hiện prompt dài ra hoặc output phình to. SLO và error budget cho biết khi nào cần dừng thay đổi và tập trung vào độ ổn định.
- **Điều quan trọng nhất đã học:** Một alert chỉ có ích nếu ngưỡng khớp với trải nghiệm người dùng: incident vượt ngưỡng 2000 ms của challenge nhưng alert đặt ở 3000 ms nên im lặng. Phải kiểm tra alert bằng một incident thật chứ không chỉ kiểm tra cú pháp YAML.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  - Dashboard hiển thị số tổng hợp trong 60 phút chứ không có biểu đồ theo thời gian; ngưỡng hiển thị dạng nhãn thay vì đường SLO, và phải bấm Rerun thay vì tự refresh mỗi 30 giây.
  - Chưa áp dụng các preventive measure ở mục 7 vào code/config (ngưỡng alert 2000 ms, alert theo span retriever, sửa blocking event loop).
  - `evidence/04` và `evidence/05` chụp từ log CP1, trước khi sửa `model` từ `gpt-4` sang `claude-sonnet-4-5` để khớp với trace.
  - Cold start: request đầu tiên sau khi khởi động API mất khoảng 1.1–1.8 s do lấy prompt từ Langfuse; có thể warm-up prompt cache khi app khởi động.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
