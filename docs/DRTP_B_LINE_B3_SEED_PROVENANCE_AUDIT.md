# DRTP B线 B3：候选训练 seed provenance 审计

状态：`PASS — UNUSED_FOR_SCIENTIFIC_RESULTS`

候选 paired training seeds：`2701`、`2702`、`2703`。

审计范围覆盖当前工作区的 source、configs、docs、diagnostics、results、archival、artifacts、manifest、checkpoint 路径与 Git 全分支历史。搜索限定为真正的训练 seed 语义：目录/文件名 `seed2701`--`seed2703`、JSON manifest 的 `"seed": 2701`--`2703` 与命令行 `--seed 2701`--`2703`。数值 CSV 中“第 2701 次 update”等同形字符串不计为 seed 使用。

结果：未发现三者曾作为训练、development、evaluation、debug/smoke 或历史 abandoned run 的科学结果 seed；也未发现对应目录、manifest、checkpoint 或 Git 历史语义记录。

因此这三个数值可冻结为 B3 的新 paired development seed。该结论不把它们称为 held-out 或 canonical；B3 仍仅是机制探索。
