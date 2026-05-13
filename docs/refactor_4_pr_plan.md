# RAG 架构重构落地方案（4 个最小改造 PR）

## 目标

把当前“导入 -> chunk -> 向量 -> 检索 -> 问答”这一条强耦合、单通道链路，拆成可演进的分层架构，同时尽量控制每次改造的风险和回归范围。

这份方案遵循两个原则：

1. 不一次性推翻现有系统，优先通过兼容层平滑迁移。
2. 每个 PR 都应该能单独合并、单独验证、单独回滚。

## 当前问题映射

基于当前仓库代码，问题主要集中在下面几处：

- `app/importers.py`
  - 导入器直接输出接近最终 chunk 的结构，没有稳定的 `Document IR`。
  - PDF 规则和后处理逻辑过重，缺少统一结构层。
- `app/storage.py`
  - `add_document()` 把导入、切块、向量化、落盘绑在同一个事务里。
  - 无 draft/active 概念，无版本激活概念。
- `app/chunking.py`
  - 只有通用字符切块逻辑，没有策略注册和按文档类型选择策略的能力。
- `app/document_metadata.py`
  - 核心分类逻辑耦合 `ESP32 / ESP-IDF / datasheet / TRM` 等领域特征。
- `app/retrieval_core.py`、`app/retriever.py`
  - 术语扩展和 query intent 与当前测试领域强耦合。
  - 检索入口统一走 top-k，没有任务路由。
- `app/schemas.py`
  - 缺少 IR 层 schema、缺少 chunk/vector 版本与一致性字段。
- `scripts/reindex_documents.py`、`scripts/rebuild_vectors.py`
  - 可重建但缺乏强一致性校验。
- `scripts/run_rag_smoke_eval.py`
  - 评估只覆盖窄域问答，不覆盖 task routing 和跨领域普适性。

## 拆分原则

这次建议拆成 4 个最小 PR：

1. `PR-1`：Document IR
2. `PR-2`：ChunkStrategyRegistry
3. `PR-3`：VectorStore 抽象
4. `PR-4`：Task Router 骨架

顺序不能乱：

- 先有 IR，chunk 才能从“导入器输出格式”解耦。
- 先有 chunk strategy，向量构建才有明确的输入语义。
- 先有 vector store abstraction，才能把 draft/active、版本一致性、collection 接进来。
- 最后再加 task router，避免在脆弱数据面上做复杂任务分流。

---

## PR-1：Document IR

### 目标

在导入器和 chunker 之间建立统一的中间表示层，使 `PDF / DOCX / Markdown / Code / Web / Plain Text` 都先落到统一结构，再由后续流程消费。

### 核心结果

- 新增 IR schema，不再让 importer 直接产最终 chunk 形状。
- importer 输出 `DocumentIR`。
- storage 暂时通过兼容适配器把 `DocumentIR -> ChunkRecord`，保证外部 API 暂不破。

### 建议新增文件

- `app/document_ir.py`
- `app/ir_adapters.py`

### 建议修改文件

- `app/importers.py`
- `app/schemas.py`
- `app/storage.py`
- `scripts/reindex_documents.py`

### 建议结构

```python
# app/document_ir.py
from dataclasses import dataclass, field

@dataclass
class LayoutBox:
    x0: float | None = None
    y0: float | None = None
    x1: float | None = None
    y1: float | None = None
    page_width: float | None = None
    page_height: float | None = None

@dataclass
class IRPage:
    page_number: int
    page_label: str | None = None
    width: float | None = None
    height: float | None = None
    extraction_confidence: float | None = None
    used_ocr: bool = False

@dataclass
class IRBlock:
    block_id: str
    page_number: int | None
    role: str
    text: str
    section_path: list[str] = field(default_factory=list)
    bbox: LayoutBox | None = None
    parent_id: str | None = None
    order_on_page: int | None = None
    page_region: str | None = None
    role_confidence: float | None = None
    extraction_confidence: float | None = None
    source_uri: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    paragraph_start: int | None = None
    paragraph_end: int | None = None
    attributes: dict[str, str | int | float | bool | None] = field(default_factory=dict)

@dataclass
class DocumentIR:
    document_id: str | None
    source_type: str
    source_format: str
    title: str
    pages: list[IRPage] = field(default_factory=list)
    blocks: list[IRBlock] = field(default_factory=list)
    quality_signals: dict[str, str | int | float | bool | None] = field(default_factory=dict)
    metadata_hints: dict[str, str | int | float | bool | None] = field(default_factory=dict)
```

### 角色定义建议

- `role=text`
- `role=heading`
- `role=table`
- `role=formula`
- `role=toc`
- `role=code`
- `role=caption`
- `role=header_footer`
- `role=footnote`
- `role=noise`

### 关键实现策略

- 当前 `ExtractedBlock` 不直接删除，先作为 importer 内部结构保留。
- 在 `app/importers.py` 末端统一增加转换函数：
  - `ExtractedDocument -> DocumentIR`
- 对 PDF：
  - 先补 `block_id`
  - 先补 `order_on_page`
  - `page_region` 没有 bbox 时先按同页顺序粗估为 `top/middle/bottom`
- 对 Markdown / code / web：
  - 没有页概念时 `page_number=None`
  - `source_uri`、`line_start` 继续保留

### 对现有代码的兼容方式

- `storage.build_document_payload()` 不直接吃 `blocks=[block.__dict__]`
- 改成先接受 `document_ir`
- 在 `ir_adapters.py` 中提供：

```python
def document_ir_to_legacy_chunk_payloads(document_ir: DocumentIR) -> list[dict]:
    ...
```

这样 `ChunkRecord` 暂时不需要一起重做，先保证链路跑通。

### 验收标准

- 上传 PDF/DOCX/Markdown/code/web 后仍能成功导入。
- `reindex_documents.py` 可重建现有库。
- `DocumentIR` 至少覆盖：
  - `block_id`
  - `role`
  - `parent_id`
  - `order_on_page`
  - `page_region`
  - `extraction_confidence`
- 现有 API 不破。

### 风险

- importer 改动大，容易引入回归。

### 降风险措施

- 先保留 legacy chunk adapter。
- 先不让 IR 直接参与检索，只作为新的导入中间层。

---

## PR-2：ChunkStrategyRegistry

### 目标

把当前单一 `chunk_text()` 和 storage 后处理补丁，升级成基于文档 profile 与 block role 的 chunk 策略注册表。

### 核心结果

- chunking 从“按字符切”改成“按策略切”。
- 核心代码不再知道 `ESP-IDF` 或《汽车理论》。
- 领域规则开始从核心逻辑迁出，进入 profile/config。

### 建议新增文件

- `app/chunk_strategies.py`
- `app/chunk_profiles.py`
- `app/profiles/general.yaml`
- `app/profiles/espidf.yaml`
- `app/profiles/vehicle_textbook.yaml`

### 建议修改文件

- `app/chunking.py`
- `app/storage.py`
- `app/document_metadata.py`
- `app/importers.py`

### 建议结构

```python
class ChunkStrategy:
    name: str

    def supports(self, document_ir: DocumentIR, profile: dict) -> bool:
        ...

    def build_chunks(self, document_ir: DocumentIR, profile: dict) -> list[dict]:
        ...


class ChunkStrategyRegistry:
    def __init__(self, strategies: list[ChunkStrategy]):
        self.strategies = strategies

    def resolve(self, document_ir: DocumentIR, profile: dict) -> ChunkStrategy:
        ...
```

### 第一批策略建议

- `generic_text_strategy`
- `pdf_textbook_strategy`
- `pdf_paper_strategy`
- `docx_contract_strategy`
- `markdown_guide_strategy`
- `source_code_strategy`
- `web_article_strategy`

### profile 设计建议

```yaml
# app/profiles/general.yaml
profile_id: general
document_hints:
  title_keywords: []
  source_format_weights: {}
chunk_strategy: generic_text_strategy
retrieval_profile: general
metadata_profile: general
```

```yaml
# app/profiles/espidf.yaml
profile_id: espidf
document_hints:
  title_keywords: ["esp-idf", "esp32", "espressif"]
chunk_strategy: markdown_guide_strategy
retrieval_profile: espidf
metadata_profile: espidf
```

### 对现有分类逻辑的处理

`app/document_metadata.py` 里不要再硬编码 `ESP32 / NimBLE / api-guides` 作为核心逻辑。

改法建议：

- 核心保留通用 doc family：
  - `manual`
  - `guide`
  - `reference`
  - `textbook`
  - `paper`
  - `contract`
  - `report`
  - `code`
  - `catalog`
- 领域 profile 在配置里做 hint 和加权，不进入 core module。

### 迁移策略

- `chunk_text()` 暂时保留，作为 `generic_text_strategy` 的基础能力。
- `storage._attach_code_context_and_filter_connectors()` 和 `_merge_short_text_payloads()` 中的逻辑，逐步迁到 `source_code_strategy` / `markdown_guide_strategy`。

### 验收标准

- 同一个导入入口可以根据 profile 走不同 chunk 逻辑。
- `ChunkRecord` 输出仍兼容现有检索链路。
- 核心 chunk 逻辑不再直接包含特定领域词。

### 风险

- 策略分流如果判断错，会让 chunk 质量波动。

### 降风险措施

- 初期先允许 profile 显式指定。
- 只有 `general` 自动判定，其他 profile 可以先人工/脚本传入。

---

## PR-3：VectorStore 抽象

### 目标

把当前 `JSONStorage + vectors.json` 的耦合结构改成文档存储与向量存储分离，并引入版本、一致性、draft/active 的基础能力。

### 核心结果

- 新增 `VectorStore` 接口。
- 当前 JSON 向量文件变成 `JsonVectorStore` 实现，而不是默认架构。
- `import -> chunks -> quality -> vectors -> activate` 的生命周期开始可表达。

### 建议新增文件

- `app/vector_store.py`
- `app/vector_models.py`
- `app/vector_stores/json_store.py`
- `app/index_lifecycle.py`

### 建议修改文件

- `app/storage.py`
- `app/schemas.py`
- `app/retriever.py`
- `scripts/rebuild_vectors.py`
- `scripts/reindex_documents.py`

### 建议接口

```python
class VectorStore:
    def upsert(self, records: list["VectorEntry"], *, collection_id: str) -> None:
        ...

    def delete_by_document(self, document_id: str, *, collection_id: str) -> None:
        ...

    def search(self, query_vector: list[float], *, top_k: int, filters: dict | None = None, collection_id: str | None = None) -> list[tuple[str, float]]:
        ...

    def validate_consistency(self, chunks: list["ChunkRecord"], *, collection_id: str) -> dict:
        ...
```

### `VectorRecord` 升级建议

在 `app/schemas.py` 或新 `vector_models.py` 增加：

- `collection_id`
- `chunk_hash`
- `embedding_text_hash`
- `embedding_provider`
- `embedding_model`
- `embedding_dimension`
- `parser_version`
- `chunker_version`
- `chunk_schema_version`
- `created_at`
- `is_active`

### 生命周期建议

- `draft documents`
- `draft chunks`
- `quality report`
- `approved chunk set`
- `draft vectors`
- `active vectors`

初版不需要完整数据库事务，只要先把状态表达出来。

### 当前 JSON 方案的兼容实现

保留：

- `documents.json`
- `chunks.json`
- `vectors.json`

但增加：

- `collections.json`
- `chunk_sets.json`
- `vector_sets.json`

最小化做法也可以先不拆文件，只在记录里补：

- `collection_id`
- `status=draft|active`
- `version`

### `rebuild_vectors.py` 改造建议

当前脚本只会把所有 chunk 重新 embed 并整体覆盖 `vectors.json`。

建议改成：

```bash
python3 scripts/rebuild_vectors.py --collection default --only-active-chunks
```

并在脚本里加入：

- stale chunk 检测
- hash 不一致统计
- 构建前校验 embedding spec

### 检索侧改造建议

`VectorIndex` 不再自己持有整个 `vectors` 列表并遍历所有 chunk。

第一步先改成：

- 从 `VectorStore.search()` 返回 `chunk_id -> score`
- 再回表取 chunk

即使底层还是 JSON，也先抽象检索面。

### 验收标准

- `upload/import` 不再强制同步生成 active vectors。
- 可以只重建 chunks，不污染 active vectors。
- 可以检测 chunk/vector 是否 stale。
- 检索入口支持 `collection_id`。

### 风险

- 存储结构变化最大，容易影响现有导入和检索。

### 降风险措施

- 先做接口抽象，不立即切第三方向量库。
- `JsonVectorStore` 先保持原行为，再逐步增加一致性字段。

---

## PR-4：Task Router 骨架

### 目标

把当前统一 `HybridIndex.search()` 的问答入口，升级成“任务识别 -> 检索计划 -> 执行”的骨架，为后面支持全书索引、表格问答、代码定位做准备。

### 核心结果

- 新增 task type。
- 普通问答仍保持兼容。
- 特殊任务可以先只做骨架和最小实现。

### 建议新增文件

- `app/task_router.py`
- `app/task_plans.py`
- `app/task_types.py`

### 建议修改文件

- `app/main.py`
- `app/retriever.py`
- `app/retrieval_core.py`

### 第一版任务类型建议

- `qa_fact`
- `qa_explanation`
- `book_index`
- `table_lookup`
- `code_symbol_lookup`

### 骨架示例

```python
from dataclasses import dataclass

@dataclass
class TaskPlan:
    task_type: str
    candidate_limit: int
    require_locations: bool = False
    require_tables: bool = False
    require_code_symbols: bool = False


class TaskRouter:
    def route(self, question: str) -> TaskPlan:
        ...
```

### 第一版路由规则建议

- 命中“整理全书知识点/全书索引/按章总结”
  - `book_index`
- 命中“表格/参数/数值/对应值/同比/环比”
  - `table_lookup`
- 命中“函数/类/调用/定义/在哪个文件”
  - `code_symbol_lookup`
- 其他默认：
  - `qa_fact` 或 `qa_explanation`

### 第一版执行策略建议

#### `qa_fact`

- 沿用当前 `HybridIndex.search()`

#### `book_index`

- 先筛 `toc + heading-rich + page_number != None`
- 先召回目录相关 chunk
- 再按 `section_path` 聚合
- 输出结构化章节索引

注意：第一版不一定让 LLM 总结全书内容，只先输出“可扫描的章节骨架 + 页码”。

#### `table_lookup`

- 优先 `block_type=table`
- 若 `table_parse_confidence=low`，在最终回答中标记为“低置信表格证据”

#### `code_symbol_lookup`

- 优先 `symbol_name != None`
- 其次 `block_type=code`

### 和当前 `classify_query_intent()` 的关系

当前 `QueryIntent` 不要立刻删。

建议改成两层：

- `TaskRouter` 决定任务类型
- `QueryIntent` 只做任务内排序偏好

这样能避免“大任务路由”和“小排序偏置”混在一起。

### 验收标准

- 聊天入口先经过 task router。
- 普通问答结果不明显退化。
- `book_index`、`table_lookup`、`code_symbol_lookup` 至少有可观测骨架输出。

### 风险

- 路由误判会带来用户可见回归。

### 降风险措施

- 第一版只对高置信命中切任务。
- 其他请求全部回退到 `qa_fact`。

---

## 推荐实施顺序

### 第 1 周

- 合 PR-1
- 确保 IR 落地但旧接口不破

### 第 2 周

- 合 PR-2
- 跑一次全量 reindex
- 验证不同 source format 的 chunk 质量是否可接受

### 第 3 周

- 合 PR-3
- 把 active/draft 和 stale 检查接上
- 修复脚本链路

### 第 4 周

- 合 PR-4
- 先让 task router 可观测
- 再扩展 book/table/code 三类任务

---

## 每个 PR 的回归检查清单

### PR-1

- PDF 导入成功
- DOCX 导入成功
- Markdown/code/web 导入成功
- `reindex_documents.py` 可执行
- 旧 `ChatResponse` 引用字段不破

### PR-2

- `general` profile 可正常走默认切块
- code 文档行号仍保留
- PDF 页码仍保留
- 表格 block 不回退成普通 text

### PR-3

- chunks 与 vectors 可独立重建
- stale 检测生效
- `collection_id` 可传入检索
- 未激活 vectors 不参与检索

### PR-4

- 普通 QA 不退化
- `book_index` 请求不再走纯 top-k
- `table_lookup` 优先 table block
- `code_symbol_lookup` 优先符号级 chunk

---

## 我建议的文件改动顺序

为了减少冲突，实际编码时建议按下面顺序改：

1. `app/document_ir.py`
2. `app/importers.py`
3. `app/ir_adapters.py`
4. `app/storage.py`
5. `app/chunk_strategies.py`
6. `app/chunking.py`
7. `app/document_metadata.py`
8. `app/vector_store.py`
9. `app/retriever.py`
10. `app/main.py`
11. `scripts/reindex_documents.py`
12. `scripts/rebuild_vectors.py`
13. `scripts/run_rag_smoke_eval.py`

---

## 评估补充建议

这 4 个 PR 之后，评估也要同步升级，否则你还是会被“旧测试集看起来很好”误导。

建议把评估拆成三层：

- `import quality eval`
- `retrieval eval`
- `task eval`

每层至少增加这些指标：

- `expected_chunk_hit@k`
- `expected_page_hit@k`
- `section_accuracy`
- `citation_accuracy`
- `table_answer_accuracy`
- `task_completion_score`

并把数据集分成：

- PDF 教材
- 学术论文
- 合同
- 财报
- Markdown 技术文档
- 代码仓库
- Web 页面
- 扫描件

---

## 最后建议

这 4 个 PR 里，最重要的不是“把模块拆出来”，而是把下面三件事从架构上固定住：

1. importer 只负责提取，不负责决定最终 chunk 长什么样。
2. 向量索引只是可替换的检索实现，不是整个知识库的数据真相。
3. 普通 QA 不再代表全部任务，任务类型必须进入检索入口。

如果这三个原则落住了，你后面再接 Qdrant、加 bbox、做跨文档比对、做全书索引，都会顺很多。
