# Network Rules 项目文档

## 项目概述

将 v2fly/domain-list-community 数据转换为 Surge/Clash 可用的域名规则文件。

## 核心目录

```text
src/                    # 解析与处理核心逻辑
tests/                  # 单元测试
config/tag_policies.json # 标签输出策略
config/customizations.json # 数据预处理策略
.github/workflows/build.yaml # CI 构建与发布
release/                # 输出目录
pages/                  # 前端页面目录（gh-pages）
```

## 输入数据格式

```text
# 注释
include:another-file
include:listname @attr1
domain:google.com
full:analytics.google.com
keyword:google
regexp:^odd[1-7]\.example\.org$
google.com @ads @cn
google.com @-cn
```

## 处理逻辑

- `filename.txt`：固定输出该文件的全量数据（有有效数据时）
- `filename@attr.txt`：输出命中该标签的数据
- 多标签条目会同时出现在多个标签文件中
- include 行的属性仅用于过滤子文件，不参与父文件标签归类
- include 导入后仅保留数据，不继承子文件标签
- 负向输入标签 `@-tag` / `@!tag` 统一归一化为 `@!tag`

## 标签策略（关键）

策略文件默认路径：`config/tag_policies.json`（可由 `TAG_POLICY_FILE` 覆盖）。
当 `TAG_POLICY_FILE` 为相对路径时，按项目根目录解析；绝对路径按原样使用。

```json
{
  "cn": { "pos": true, "neg": true },
  "ads": { "pos": true, "neg": false }
}
```

- 标签名作为主键
- `pos` 控制 `@tag` 是否输出
- `neg` 控制 `@!tag` 是否输出
- 未配置标签：`pos=false`、`neg=false`
- 缺失字段按 `false`
- 非布尔值会报错并停止执行
- 策略文件不存在时会降级为 `{}`，即忽略所有标签输出（仅保留 `filename.txt`）

## 环境变量

- `MIN_LINES`：最少行数（默认 `1`）
- `TAG_POLICY_FILE`：标签策略文件路径（默认 `config/tag_policies.json`）
- `CUSTOMIZATION_FILE`：数据预处理配置路径（默认 `config/customizations.json`）

## 本地命令

```bash
# 1) 应用预处理规则（与 CI 对齐）
python3 -m src.customizations domain-list-community/data

# 2) 生成 release 规则数据
python3 -m src.main domain-list-community/data release

# 3) 生成页面文件（fileList.js + index.html）
python3 -m src.generate_filelist release pages --repo-name owner/repo

# 4) 本地预览页面
python3 -m http.server 8000 -d pages

# 5) 运行测试
python3 -m pytest tests/

# 6) 抽样查看
wc -l release/google.txt release/google@ads.txt
```

## 前端模板维护规则

- 仅维护项目根目录 `index.html`（页面模板唯一真源）
- `pages/index.html` 为生成产物，由 `python3 -m src.generate_filelist` 自动覆盖
- 不直接编辑 `pages/index.html`

## 边界行为

- 空文件或仅注释文件：不会产生有效数据页
- 循环 include：检测后中断当前链路处理
- include 目标文件不存在：不崩溃，按空内容处理

## CI 说明

CI 会拉取上游数据，按顺序执行：
1. `python3 -m src.customizations domain-list-community/data`
2. `python3 -m src.main domain-list-community/data release`
3. `python3 -m src.generate_filelist release pages --repo-name ${{ github.repository }}`

随后发布：
- `release` 分支：`release/` 目录规则文件
- `gh-pages` 分支：`pages/` 目录前端页面
