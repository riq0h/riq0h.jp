---
title: "NeovimからClaude 3.7 Sonnetを使う方法"
date: 2025-02-25T22:47:46+09:00
draft: false
tags: ["tech"]
---

数あるLLMの中でも僕は一番Claudeが好きだ。話していて謙虚で紳士的な雰囲気がするし、他のLLMよりも独特な世界観を持っている感じがする。開発元の[Webページ](https://www.anthropic.com/claude)のデザインがセリフ体中心で構成されているところもレトロフューチャーっぽくて気に入っている。

Webデザインの実装がうまいところが特に好きだ。「Tailwind CSSでなんかクールにスタイリングしてくれ」みたいなざっくりした指示でも、それなりにちゃんと見栄えのするものを持ってきてくれる。ChatGPTが大抵どのバージョンでも素組みのHTMLと大差ない代物しか寄越してこない様子を見ると、この分野では明らかに突出していると言える。

さて、そんなミスターClaudeはつい先ほど持ち前の謙虚さを活かして自身のバージョンをコンマ2刻みで上げてきた。**Claude 3.7 Sonnet**のリリースだ。需要の少ない高度な計算機能と引き換えに、実用的なコーディングと推論能力にフォーカスして作られたという。さっそく彼をいじりたい。皆さんもどうせそれが目当てだろう。すぐにNeovimの設定をセットアップしよう。パッケージマネージャには[lazy.nvim](https://github.com/folke/lazy.nvim)を使用する。

```lua
{ "yetone/avante.nvim", event = "VeryLazy" },
{ "zbirenbaum/copilot.lua", event = "VeryLazy" },
{ "nvim-lua/plenary.nvim", event = "VeryLazy" },
{ "stevearc/dressing.nvim", event = "VeryLazy" },
{ "MunifTanjim/nui.nvim", event = "VeryLazy" },
```

僕の構成では今時のナウいAIエディタっぽい操作体系を提供する[avante.nvim](https://github.com/yetone/avante.nvim)を採用している。これは通常では任意のLLMのAPIキーを登録する形式のプラグインだが、今回はGitHub Copilotを使う。CopilotがClaude 3.7 Sonnetに即日対応してくれたおかげで、本家の従量制課金に怯えずともエディタの内側で彼と思う存分ランデヴーできるのだ。

とはいえ、これらのプラグインを初めて導入する人にとってはちょっと話がややこしいかもしれない。簡単に説明すると、plenary.nvimやらdressing.nvimやらnui.nvimやらはavante.nvimのUIを構築するための依存プラグインで、copilot.luaはGitHub Copilotとの連携に使われている。そして、avante.nvimが諸々の情報を受け取って洒落たUI上に表示する。一度理解したら簡単だ。では次にavante.nvimの設定をやっていく。

```lua
require("avante_lib").load()
require("avante").setup({
	provider = "copilot",
	copilot = {
		model = "claude-3.7-sonnet",
	},
	auto_suggestions_provider = "copilot", -- 一応設定しておく
	file_selector = {
		provider = "telescope",
	},
	behaviour = {
		auto_suggestions = false, -- 試験的機能につき無効化を推奨
		auto_set_highlight_group = true,
		auto_set_keymaps = true,
		auto_apply_diff_after_generation = false,
		support_paste_from_clipboard = true,
		minimize_diff = true,
	},
	windows = {
		position = "right",
		wrap = true,
		width = 30,
		sidebar_header = {
			enabled = true,
			align = "right",
			rounded = false,
		},
		input = {
			height = 5,
		},
		edit = {
			border = "single",
			start_insert = true,
		},
		ask = {
			floating = true,
			start_insert = true,
			border = "single",
		},
	},
})
```

公式のリファレンスではパッケージマネージャと一緒に設定を書いているが、僕は個別に分けて書く方が好きだ。本稿をあてにして来たからには皆さんもそうした方がいい。反映後、Neovimを起動して`:Copilot auth signin`を実行して認証を行う。この時点でGitHub Copilotのサブスクに登録しておくと話が早い。

次に、GitHubのWebページの右上の`Your Copilot`から設定に飛び、`Anthropic Claude 3.7 Sonnet in Copilot `の項目をEnabledにする。これを忘れるとavante.nvimを呼び出して会話を始めてもエラーを起こしてしまう。上記の設定では`model`に`claude-3.7-sonnet`を指定しているからだ。逆に`copilot = {}`の項目を消すと自動的にGPT-4oが使われる。

ここまで首尾よく設定できていたなら`:AvanteBuild`を実行後、ショートカットでavante.nvimを動かせるはずだ。デフォルトのキーマップでは`<leader>at`で右側に会話用のサイドバーが現れる。最初は慣れないがTabキーで各ウインドウのフォーカルを切り替えられる。また、会話ウインドウにフォーカスがあたっている時にEscキーを2回押すとサイドバーを閉じることができる。

さらに上から2つ目のウインドウはLLMに読み込んでほしいファイルを指定する機能を持っていて、dキーで削除、@キーで追加が行える。上記の設定では`telescope`が指定されているので、[telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)がインストールされていなければ機能しない。よく分からないなら`native`に設定を変えると内蔵のファイルセレクタが使用される。親の仇みたいに`border`が`single`だったり`rounded`が`false`なのも単に僕が角丸を好まないせいだ。

LLMを呼び出す方法としては一番下のウインドウに自然言語を入力して応答を待つほかに、エディタ上で範囲選択を伴って`<leader>aa`や`<leader>ae`を用いる手段もある。これらは選択した範囲とその後の入力内容に基づいて自動的にエディタ上に差分が挿入される。HEADの部分にカーソルを合わせて`ca`や`co`などで提案を受け入れるか決定できる。

![](/img/374.png)

サイドバー上で出力した場合でも、応答文が表示されるウインドウにフォーカスを合わせた状態でAキーを押すとコード差分がエディタ上に展開されて同様の判断を促される。複数のファイルが修正された際にはそれらのファイルがすべてバッファに展開される。下記が基本的なショートカットの一覧となる。

| キー         | 説明                               |
| ------------ | ---------------------------------- |
| `<Leader>aa` | 質問ウインドウを表示               |
| `<leader>at` | サイドバーを表示                   |
| `<leader>ar` | サイドバーを更新                   |
| `<leader>af` | サイドバーのフォーカスを切り替える |
| `<leader>ae` | 選択されたブロックを編集           |
| co           | 自身のコードを維持                 |
| ct           | LLMの提案を受け入れる              |
| ca           | LLMの提案をすべて受け入れる        |
| c0           | 変更箇所を選択しない               |
| cb           | どちらのコードも反映させる         |
| cc           | カーソル位置の変更箇所を反映させる |
| ]x           | 前の競合箇所に移動                 |
| [x           | 次の競合箇所に移動                 |
| [[           | 前のコードブロックに移動           |
| ]]           | 次のコードブロックに移動           |

実際に使ってみた感想としては、他のLLMがシンプルな解決策を示すのに対して様々なユースケースを踏まえた提案をいくつもしてくれる印象が強かった。反面、なにも言わないと冗長な生成もどしどしやってしまうため、用途次第ではプロンプトで適度に制御する必要があるだろう。言うまでもなく総合的にとても優秀なLLMなのは間違いない。

以上でNeovimからClaude 3.7 Sonnetを使う方法の説明は終了である。ところで、最近は生成AI関連の記事を生成AIに書かせて「実はこれも生成AIに書かせました！」とオチをつけるのが流行りらしい。事実、本稿を書く前に軽く情報収集をしたらそんな感じのnoteがいくつか引っかかった。はてさて、僕の文章はどう見えているのかな。
