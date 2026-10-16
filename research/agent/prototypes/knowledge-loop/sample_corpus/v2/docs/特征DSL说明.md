# 特征 DSL 说明

特征 DSL 用一行声明式语法定义统计类特征, 由 `feature_dsl.py` 编译为 FeatureSpec 并注册到特征平台。

## 语法概览

语法: `feature <name> = <expr> window <window>`。
expr 支持 count、sum、avg、last、decay 等内置函数, window 支持 1h、1d、7d、30d。

## 内置函数

- count(event): 事件次数
- sum(event.field): 字段求和
- avg(event.field): 字段均值
- decay(event, half_life): 时间衰减计数
- bucketize(expr, [边界]): 分桶

## 示例

用户 7 天点击次数特征定义为: `feature user_click_count_7d = count(click) window 7d` (原名 user_click_cnt_7d 已重命名)。
物品 1 天 CTR: `feature item_ctr_1d = avg(impression.clicked) window 1d`。

## 编译与校验

`feature_dsl.compile_feature(line)` 先解析语法, 再调用 `validate_name` 校验命名规范 (`<实体>_<统计量>_<窗口>`), 输出 FeatureSpec。
命名不合规会抛出 `FeatureDSLError`。

## 命名规范

实体取值 user、item、author; 统计量使用 count、sum、avg、ctr 等完整单词; 窗口必须与 window 一致。
自 2026-10 起 `_cnt_` 缩写已废弃, 统一使用 `_count_`, 编译器会对 `_cnt_` 报 FeatureDSLError。
