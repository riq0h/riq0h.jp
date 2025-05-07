---
title: "NeovimでCodyを使う"
date: 2024-12-30T10:00:20+09:00
draft: false
tags: ["tech"]
---

今日、コード生成AIは巷にあふれかえっているが、いち消費者の我々としては無料で補える範囲が広いのに越したことはない。最近いくつか触った中で[Cody](https://sourcegraph.com/cody)と呼ばれるツールが特にサービス精神に旺盛だと感じたので紹介したい。

# Cody Free vs GitHub Copilot Free

**■無制限のコード補完**  
任意のエディタ上でのコード補完は制限なく行える。対話形式でのレスポンスを求めていない人にはうってつけと思われる。対して、GitHub Copilot Freeは月2000回までに制限されている。

**■チャットも月200回まで無料**  
対話機能を求める場合でも月200回までは無料で使用できる。他方、GitHub Copilot Freeは月50回までに制限されている。

**■ローカルLLM対応**  
ローカルLLM（Ollamaなど）をインテグレートして使用することも可能。ある程度の性能のマシンを持っている人は用途に応じて使い分ければかなりのヘビーユースでも無料の範囲で済んでしまうかもしれない。GitHub CopilotはローカルLLMをサポートしていない。

以上の比較から、業界の雄たるGitHub Copilotと比べても極めて優良な無料プランを有していると考えられる。有料機能を含めた詳細な比較は[ここ](https://sourcegraph.com/compare/copilot-vs-cody)から確認できる。

# NeovimでCodyを使う

しかし、どんなに寛大なサービスであってもNeovimで使えなければ僕としては話にならない。Web上ではNeovimとの連携に関する情報が掲載されていなかったので危うく解散しかけたが、公式のリポジトリを探してみるとちゃんとプラグインが[提供されていた。](https://github.com/sourcegraph/sg.nvim)総員集合！ というわけで、さっそく設定を行っていく。

```lua
{ "sourcegraph/sg.nvim", event = "LspAttach" },
```

使用するパッケージマネージャはlazy.nvimとする。まずは上記の形でプラグインを導入する。`event`の発火タイミングは好みで構わない。インストール後、Neovimを再起動して`:SourcegraphLogin`を実行すると、ブラウザが開いてログイン認証（OAuth）が実行される。認証経路にはGitHubやGoogleアカウントなどが用意されている。

ログインに成功するとブラウザ上で再度、エディタの再起動を促される。ここからようやくCodyの諸機能を試せる。リポジトリのページには"This plugin is currently experimental"などと謙遜した一文が記されているものの、基本的な機能はすでに網羅されている印象だ。

```
:CodyAsk ~
    Ask a question about the current selection.

:CodyExplain ~
    Ask a question about the current selection.

:CodyChat{!} {title} ~
    State a new cody chat, with an optional {title}

:CodyToggle ~
    Toggles the current Cody Chat window.

:CodyTask {task_description} ~
    Instruct Cody to perform a task on selected text.

:CodyRestart ~
    Restarts Cody and Sourcegraph, clearing all state.
```

`CodyChat`はCodyと対話形式のチャットを行うコマンドで、実行すると専用のフローティングウインドウが展開される。しかし実際には`CodyToggle`を任意のキーにマップする方が出し入れが可能なぶん便利だ。また、`CodyAsk`と`CodyExplain`は前者が引数（任意の質問文）を必須とするのに対して、後者は選択範囲の内容を自動的に解説してくれる。

![](/img/354.png)

一方、`CodyTask`は指定された引数（命令文）の要求を満たすコードを会話文なしで出力する。フローティングウインドウ上でエンターを押すと、出力されたコードがそのままNeovimのバッファに展開される。選択範囲を指定して実行した場合は元のコードを置換する形で機能する。なにをしてほしいかが明確ならこっちの方が効率的かもしれない。

```lua
require("sg").setup()
vim.keymap.set("n", "<leader>9", ":<C-u>CodyToggle<CR>", { silent = true })
vim.keymap.set("v", "<leader>0", ":CodyTask ")
vim.keymap.set("v", "<leader>-", ":CodyAsk ")
```

最後に自動補完プラグインのnvim-cmpとの連携を行う。といっても連携機能自体がCodyのプラグインに含まれているので、nvim-cmpのソース設定にCodyを追加するだけで済む。[lspkind.nvim](https://github.com/onsails/lspkind.nvim)を用いた補完候補のピクトグラム表示については、GitHubのような専用の絵文字が見当たらなかったのでさしあたり雪の結晶で代用した。

```lua
	formatting = {
		format = lspkind.cmp_format({
			mode = "symbol",
			maxwidth = 50,
			ellipsis_char = "...",
			symbol_map = { Cody = "❄" },
		}),
	},

	sources = cmp.config.sources({
		{ name = "nvim_lsp", max_item_count = 15, keyword_length = 2 },
		{ name = "vsnip", max_item_count = 15, keyword_length = 2 },
		{ name = "nvim_lsp_signature_help" },
		{ name = "cody", keyword_length = 2 },
		{ name = "buffer", max_item_count = 15, keyword_length = 2 },
	}),
```

![](/img/355.png)

## 総評

後発なだけあってこなれ感があるのかCopilotよりも全体的に使用体験が良い。Experimentalなどと書かれている割には常用可能なクオリティに達していると評価できる。プログラミングに強いClaude 3.5 Sonnetを無料で潤沢に扱えるのもかなりのアドバンテージと言える。

以上の理由から僕はGitHub Copilot Proを解約してCodyに乗り換えることにした。万が一、無料の範囲で補えなくなるほど多用するとしても、その時にはCody Proを契約するだろう。中身はほぼ共通のLLMでも巨大資本に対して有力な競合他社が現れるのはとてもありがたい。

とはいえ、GitHubはGitHubで大したものだと思う。つい数日前に更新月を迎えていたのでひと月分を無駄にする前提で解約したのだが、驚くべきことに自動で全額返金してくれた。容赦なく過大な請求をして憚らない企業も少なくない中で、GitHubはまだ幾ばくかの高潔さを保っているようである。
