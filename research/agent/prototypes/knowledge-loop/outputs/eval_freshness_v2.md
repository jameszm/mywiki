# 评测报告 freshness_v2-38-2

- 名称: freshness_v2  语料版本: v2  条目数: 7  时间: 2026-10-16T10:20:15.830292+00:00

| 指标 | 值 |
|---|---|
| recall@5 | 0.952 |
| recall@10 | 1.000 |
| mrr | 1.000 |
| ndcg@5 | 0.945 |
| ndcg@10 | 0.966 |
| keyword_coverage | 1.000 |
| citation_precision | 0.691 |
| groundedness | 1.000 |
| abstain_ok_rate | 1.000 |
| freshness_pass_rate (n=7) | 1.000 |

## 逐条结果

| id | query | R@5 | R@10 | MRR | nDCG@10 | kw | cite_p | grounded | abstain_ok | fresh | 步数/停止 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| g27 | 学习率默认值是多少 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.67 | 1.00 | ✓ | ✓ | 3/no_more_queries |
| g28 | 7 天点击次数特征现在叫什么名字 | 0.67 | 1.00 | 1.00 | 0.91 | 1.00 | 0.67 | 1.00 | ✓ | ✓ | 3/no_more_queries |
| g29 | 灰度发布分几个阶段，什么时候自动回滚 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.75 | 1.00 | ✓ | ✓ | 4/max_steps |
| g30 | RedisConnectionReset 错误出现过多少次 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.50 | 1.00 | ✓ | ✓ | 3/no_more_queries |
| g31 | warmup_steps 是什么配置 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.25 | 1.00 | ✓ | ✓ | 1/coverage_reached |
| g32 | 模型发布流程现在应该看哪个文档 | 1.00 | 1.00 | 1.00 | 0.85 | 1.00 | 1.00 | 1.00 | ✓ | ✓ | 2/no_more_queries |
| g33 | _cnt_ 后缀还能用吗 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | ✓ | ✓ | 2/no_more_queries |
