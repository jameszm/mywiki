"""kloop — 内部“知识闭环”(knowledge loop) 参考实现。

模块一览:
    models      数据模型 (dataclasses)
    store       SQLite 存储 (版本化知识条目 + 对话/反馈/评分/策展/评测日志)
    connectors  接入器: markdown 文档 / python 代码 / 配置文件 / 日志
    chunking    切分、上下文头、稳定 id
    sync        增量同步 (按 sha256 对比, 仅重建受影响条目的索引)
    index       BM25 + 字符 3-gram TF-IDF 余弦 + RRF 融合
    search      DeepSearch 风格的多步检索循环
    answer      带引用的答案合成
    llm         可插拔的 LLM 客户端 (HeuristicLLM 默认 / AnthropicLLM 可选)
    feedback    对话与反馈日志, 纠错 -> 候选知识
    scoring     基于日志的知识条目评分 / 陈旧与冲突 / 缺口 / 策展任务
    evaluate    黄金集评测、新鲜度测试、回归对比、黄金集挖掘
    cli         命令行入口

仅依赖 Python 标准库。
"""

__version__ = "0.1.0"
