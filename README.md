# DeepSeek RAG Demo

一个可直接启动的轻量 RAG 项目，特点如下：

- LLM 使用 `deepseek-v4-flash`
- 检索层使用本地 `BM25 + 向量索引` 混合检索，并结合上下文与中英术语扩展
- 支持上传 `.txt`、`.md`、`.pdf`、`.docx` 和常见代码文件
- 支持导入文档网页 URL
- 支持会话持久化与连续追问
- 提供美化后的 FastAPI 前端工作台
- 支持 `PDF OCR` 自动回退，改善扫描件或乱码页的提取质量
- 支持本地持久化 `vectors.json`，上传后自动写入向量索引

## 目录结构

```text
rag_deepseek_v4/
├── app/
├── data/
├── scripts/
├── .env.example
├── Dockerfile
├── README.md
└── requirements.txt
```

## 本地启动

1. 初始化环境

```bash
cd /home/meiluoluo/code/rag_deepseek_v4
chmod +x scripts/bootstrap.sh scripts/start.sh
./scripts/bootstrap.sh
```

如果系统缺少 `python3-venv`，脚本会自动退回到用户级安装，不需要额外手动处理。

2. 配置环境变量

```bash
cp .env.example .env
```

填写以下关键项：

```env
DEEPSEEK_API_KEY=你的_key
DEEPSEEK_MODEL=deepseek-v4-flash
```

3. 启动服务

```bash
./rag_deepseek_v4/scripts/start.sh
```

打开 `http://127.0.0.1:8000` 即可使用。

## 当前能力

- 左侧会话栏支持新建、切换、删除会话
- 会话历史持久化到本地，刷新页面不会丢上下文
- 检索会自动带入最近用户问题，适合“那这个呢”“它和前者差别是什么”这类追问
- 对常见技术术语做了中英扩展，例如 `蓝牙 / bluetooth / BT`、`低功耗蓝牙 / BLE`、`经典蓝牙 / BR/EDR`、`主机栈 / host stack`、`指南 / guide`
- 上传导入后会同时生成标准化 `chunk` 和本地持久化向量索引，默认保存到 `data/index/chunks.json` 和 `data/index/vectors.json`
- 导入时会尽量保留结构化定位信息：
  - `PDF`：页码、页标签、目录锚点、章节路径、`text / table / toc` 结构块；原生抽取质量差时自动回退到 OCR，并清洗常见页眉页脚噪音
  - `DOCX`：标题层级、段落范围
  - `Markdown / 代码 / 文本`：章节路径、文件名、行号范围
  - `Web`：来源 URL、章节路径、近似 anchor 位置
- `PDF` 表格会尽量拆出表头与表体，跨页表会继承上一页表标题
- 结构块会区分 `text / table / toc`，便于后续做更细粒度的引用与检索
- 文本类文件启用自动编码识别，尽量减少因编码不兼容导致的乱码

## 检索与向量索引

当前检索采用 `BM25 + embedding + reranker` 的两阶段混合方案：

- `BM25` 负责关键词、章节路径、页码位置等精确召回
- embedding 向量索引负责补充中英混合表达、术语变体和上下文近义表达
- reranker 对召回候选进行二次精排，提升私域开发问答的引用命中率
- 对“BLE-only / 纯 BLE / 主机栈 / NimBLE / Bluedroid”这类开发意图会做额外重排，减少数据手册压过编程指南的情况

相关环境变量：

- `RAG_VECTOR_DIM=1024`
- `RAG_HYBRID_BM25_WEIGHT=0.55`
- `RAG_HYBRID_VECTOR_WEIGHT=0.45`
- `RAG_RETRIEVAL_CANDIDATE_LIMIT=40`
- `RAG_EMBEDDING_PROVIDER=hash`：本地哈希向量，无需额外 key，适合离线兜底
- `RAG_EMBEDDING_PROVIDER=openai`：使用 OpenAI-compatible embedding API，例如百炼兼容接口
- `RAG_EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `RAG_EMBEDDING_MODEL=text-embedding-v4`
- `RAG_EMBEDDING_DIMENSIONS=1024`：通用 RAG 推荐维度，效果和成本较均衡
- `RAG_EMBEDDING_BATCH_SIZE=10`：百炼 embedding 单批 input 不应超过 10
- `RAG_RERANK_PROVIDER=none`：默认不启用外部重排
- `RAG_RERANK_PROVIDER=jina`：使用 Jina reranker API
- `RAG_RERANK_PROVIDER=dashscope`：使用百炼 `qwen3-rerank`
- `RAG_RERANK_BASE_URL=https://dashscope.aliyuncs.com/compatible-api/v1`
- `RAG_RERANK_MODEL=qwen3-rerank`

启用真实 embedding / reranker 后，建议先重建 chunks，确认 `data/index/chunks.json` 干净后再重建向量：

```bash
python3 scripts/reindex_documents.py --skip-vectors
python3 scripts/rebuild_vectors.py
```

## PDF OCR

当前 `PDF` 导入采用“结构化 Markdown 抽取 + 原生文本/OCR 兜底”的混合模式：

- 优先使用 `pymupdf4llm` 将 PDF 转为 Markdown，保留标题、段落与 Markdown 表格结构
- 自动清理常见页眉、页脚、`GoBack`、反馈链接等导航噪声
- 表格会作为独立 `table` block 入库，避免与普通段落混切
- `RAG_PDF_OCR_ENABLED=true`：开启 OCR
- `RAG_PDF_OCR_MODE=auto`：仅对抽取质量差的页面启用 OCR
- `RAG_PDF_OCR_MODE=always`：所有 PDF 页面都走 OCR
- `RAG_PDF_OCR_DPI=200`：OCR 渲染分辨率
- `RAG_PDF_OCR_QUALITY_THRESHOLD=0.72`：原生文本低于该可读性阈值时触发 OCR

OCR 依赖 `pdftoppm` 和 `rapidocr_onnxruntime`。当前这台机器已验证 `pdftoppm` 可用。

## API

- `GET /health`
- `GET /api/documents`
- `POST /api/documents/upload`
- `POST /api/documents/import-url`
- `DELETE /api/documents/{document_id}`
- `GET /api/sessions`
- `POST /api/sessions`
- `GET /api/sessions/{session_id}`
- `DELETE /api/sessions/{session_id}`
- `POST /api/chat`

### 网页导入示例

```bash
curl -X POST http://127.0.0.1:8000/api/documents/import-url \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://docs.espressif.com/projects/esp-idf/zh_CN/latest/esp32/api-guides/bt-architecture/overview.html"
  }'
```

### 一键导入 Espressif 官方蓝牙文档

```bash
python3 scripts/import_espressif_bt_docs.py
```

脚本会导入一组官方蓝牙核心页面，包括架构、BLE、经典蓝牙、蓝牙 API 和 NimBLE 说明。

### 一键导入 Espressif 官方 ESP 开发资料

```bash
python3 scripts/import_espressif_esp_docs.py
```

脚本会筛选并导入一批官方 ESP 开发常用资料，覆盖：

- `ESP-IDF` 编程指南入口、快速入门、`idf.py`、构建系统
- 分区表、`NVS`、`OTA`、安全概述、`Flash` 加密
- 蓝牙架构、`BLE`、蓝牙 API
- `GPIO`、`UART`、`FreeRTOS`
- `ESP32 / ESP32-S3 / ESP32-C3` 的产品文档页、硬件参考页
- `ESP32 / ESP32-S3 / ESP32-C3` 的 `Datasheet / TRM / Hardware Design Guidelines`

此外脚本还会生成一份中文“资料导入总览”文档，帮助 RAG 在回答时先命中导航信息，再跳转到具体官方原文。

### 批量导入本地项目目录

```bash
python3 scripts/import_project_directory.py /path/to/your/project
```

这个脚本适合把私有项目源码、`README`、配置文件、构建脚本批量导入知识库，便于朝“项目开发助理 / 私域 agent 数据库”的方向继续演进。

常用参数：

- `--replace`：如果同一路径已存在，则替换旧索引
- `--include-hidden`：包含隐藏文件
- `--max-files 200`：限制本次最多导入的文件数

### 重建现有知识库索引

当你升级了索引结构（例如新增 PDF 页码元数据）后，可运行：

```bash
python3 scripts/reindex_documents.py
```

这个脚本会重建当前 `data/index/` 下的文档与分块索引。对于 PDF，新的索引会按页保留 `page_number`，并尽量重建目录章节树、表格块和页内定位信息，问答引用里可以直接返回页码。

如果你升级了导入器，或者之前导入的文档存在乱码、缺失页码、缺失行号等问题，建议重新运行一次该脚本。

### 一键链路检查

```bash
python3 scripts/verify_pipeline.py
```

这个脚本会实际验证：

- 文件上传到导入器是否成功
- `chunk` 和 `vector` 是否同步入库
- 编码识别是否正确
- `PDF` 页码元数据是否保留
- `Markdown / 代码` 行号元数据是否保留
- 中文问题是否能可靠命中英文蓝牙文档
- LLM 是否能用中文完成带引用的问答

### 问答接口示例

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "请总结这份资料的核心内容"
  }'
```

### 会话式问答示例

```bash
curl -X POST http://127.0.0.1:8000/api/sessions
```

拿到 `session_id` 后继续提问：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "你的_session_id",
    "question": "那如果我后续还要兼容经典蓝牙呢？"
  }'
```

## Docker

本机当前没有安装 Docker，但项目已经附带 `Dockerfile`，后续有 Docker 环境时可直接构建：

```bash
docker build -t deepseek-rag .
docker run --rm -p 8000:8000 --env-file .env deepseek-rag
```

## 后续可升级点

- 把当前本地哈希向量索引升级为更强的多语言 embedding / reranker
- 增加知识库分组、来源过滤和会话内检索范围控制
- 增加文档批量导入、网页抓取和知识库分组
