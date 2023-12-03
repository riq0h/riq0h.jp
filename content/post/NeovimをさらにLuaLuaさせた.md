---
title: "NeovimをさらにLuaLuaさせた"
date: 2023-12-03T10:38:50+09:00
draft: false
tags: ['tech']
---

[あれから](https://riq0h.jp/2023/01/20/210601/)一年近い年月が経った。ひとたび完結を見た僕のinit.luaはその後も拡張し続け、ずいぶんIDE的な出で立ちに成長した。当初のサブ武器としての位置付けはどこへやら、今ではすっかり長剣の顔をして鞘に収まっている。電脳空間を切り開くデジタルロードアウトはえてして可変長であり、所有者の意向次第で自在に特性を変えられるのだ。本稿では新たに増えたプラグイン群を紹介する。


## [jaq-nvim](https://github.com/is0n/jaq-nvim)
![](/img/230.png)
いわゆるタスクランナー。書いたコードを即時に実行してくれる。国内では応用の幅広さから[vim-quickrun](https://github.com/thinca/vim-quickrun)がとりわけ有名だが、元がVim用のプラグインなのでNeovim特有のUIに対応していない惜しさがあった。jaq-nvimは逆にNeovimでしか動かない代わりにfloat windowで表示できる。

設定では実行したい言語のコマンドを指定するほか、ウインドウの枠や位置を自分の好みに決められる。どうせターミナル上にいるのだからタブを開くなり、tmuxのpopupやpaneで別途実行するなりすればいいという意見もあるが（僕も前はそう思っていた）、多少なりともワンクッションの手間を減らせる効能は意外にあなどれない。以下に設定例を示す。

```lua
require("jaq-nvim").setup({
	cmds = {
		internal = {
			lua = "luafile %",
			vim = "source %",
		},
		external = {
			python = "python3 %",
			go = "go run %",
			sh = "sh %",
			ruby = "ruby %",
			java = "java %",
			javascript = "node %",
		},
	},

	behavior = {
		default = "float",
		startinsert = false,
		wincmd = false,
		autosave = false,
	},

	ui = {
		float = {
			border = "none",
			winhl = "Normal",
			borderhl = "FloatBorder",
			winblend = 0,
			height = 0.8,
			width = 0.8,
			x = 0.5,
			y = 0.5,
		},

		terminal = {
			position = "bot",
			size = 10,
			line_no = false,
		},
		quickfix = {
			position = "bot",
			size = 10,
		},
	},
})

vim.keymap.set("n", "<leader>j", ":<C-u>Jaq<CR>", { silent = true })
```

なにげにコンパイル言語もすぐに走らせられるので言語学習のお供にも役立つ。

## [colorful-winsep.nvim](https://github.com/nvim-zh/colorful-winsep.nvim)
![](/img/231.png)
splitしたwindowの枠に色をつける……たったそれだけのことが予想以上の視認性向上をもたらしめるのはまさに目からうろこだった。特に`laststatus = 3`にして単一のstatusしか表示させていない人はとても助かるだろう。以下に設定例を示す。

```lua
--colorful-winsep
require("colorful-winsep").setup({
	highlight = {
		bg = "",
		fg = "#E8AEAA",
	},
})
```

実際にはstatusをよく確認すればファイルパスの違いで見分けはつかなくもないが、編集位置を高速で移動している最中に直感的な気づきを得るのはなかなか難しい。自分の好みの色でハイライトされていると一瞬の躊躇なく迷わずに済む。

## [nvim-dap](https://github.com/mfussenegger/nvim-dap)
Neovimを含む現代のエディタがLSP（Language Server Protocol）の恩恵を受けているのはよく知られた話だ。いつになく気前のよいMicrosoftがオープンソースで公開してくれているので、我々は種々のプラグインを通してそれらを利用できる。同様に、実はデバッガもDAP（Debug Adapter Protocol）なる仕様が公開されており、今やNeovim上でIDE並みのデバッグ環境が手に入る。

恥ずかしながら僕はVimでデバッグをしようと考えたことがなかったので、初めて知った時はかなり感動した。名実ともにすべての作業がVimで行えるとなれば、大規模開発におけるエディタの立ち位置はますます見直されていくだろう。例によって設定を示す。

```lua
local function map(mode, lhs, rhs, opts)
	local options = { noremap = true }
	if opts then
		options = vim.tbl_extend("force", options, opts)
	end
	vim.api.nvim_set_keymap(mode, lhs, rhs, options)
end

map("n", "<leader>6", ":lua require'dap'.continue()<CR>", { silent = true })
map("n", "<leader>7", ":lua require'dap'.step_over()<CR>", { silent = true })
map("n", "<leader>8", ":lua require'dap'.step_into()<CR>", { silent = true })
map("n", "<leader>9", ":lua require'dap'.step_out()<CR>", { silent = true })
map("n", "<leader>;", ":lua require'dap'.toggle_breakpoint()<CR>", { silent = true })
map("n", "<leader>'", ":lua require'dap'.set_breakpoint(vim.fn.input('Breakpoint condition: '))<CR>", { silent = true })
map(
	"n",
	"<leader>i",
	":lua require'dap'.set_breakpoint(nil, nil, vim.fn.input('Log point message: '))<CR>",
	{ silent = true }
)
map("n", "<leader>d", ":lua require'dapui'.toggle()<CR>", { silent = true })
map("n", "<leader><leader>d", ":lua require'dapui'.eval()<CR>", { silent = true })
```

この例では`<leader>;`でブレークポイントを指定する。しかし当然、これのみでは肝心のデバッガ本体が存在しないため動かない。LSPクライアントで任意の言語サーバを導入するように、デバッガも各自導入して設定しなければならない。ほぼ入れただけでよしなにやってくれるものもあれば、ひと手間が必要な場合もある。

たとえばデバッガをMasonで管理していて、そっちの方を使いたい時は下記の要領でファイルパスを記さないといけない。nvim-dap-goは書かなくてもPATHが通っている外部のコマンドを勝手に実行してくれるが、nvim-dap-pythonはどちらにしても明記しないと怒られる仕様だった。

```lua
{ "suketa/nvim-dap-ruby", config = true, ft = "ruby" },
{ "leoluz/nvim-dap-go", ft = "go" },
{ "mfussenegger/nvim-dap-python", ft = "python" },

--nvim-dap-go
require("dap-go").setup({
	delve = {
		path = ".local/share/nvim/mason/packages/delve/dlv",
	},
})

--nvim-dap-python
require("dap-python").setup(vim.fn.stdpath("data") .. "/mason/packages/debugpy/venv/bin/python")
```

なお、Javaに至ってはあまりにも設定が面倒臭すぎて動作検証を放棄してしまった。Masonのjdtlsを使ってうまくやれた人がいたら逆に教えてほしい。

## [nvim-dap-ui]()
![](/img/232.gif)
ここまでで一応デバッグは行える形になったが、それにしても画面がおざなりすぎるのは否めない。そこでこのプラグインを導入すると、keymapに応じてデバッグ専用に設えられたwindowがジャキーンと展開される。さながら変形によって破壊力が上がる武器のようだ。ただし、敏捷性＜アジリティ＞は落ちる。ここぞという時に展開して一撃で獲物を仕留める……そんな印象を受ける。

```lua
require("dapui").setup({
	icons = { expanded = "▾", collapsed = "▸", current_frame = "▸" },
	mappings = {
		expand = { "<CR>", "<2-LeftMouse>" },
		open = "o",
		remove = "d",
		edit = "e",
		repl = "r",
		toggle = "t",
	},
	expand_lines = vim.fn.has("nvim-0.7") == 1,
	layouts = {
		{
			elements = {
				{ id = "scopes", size = 0.25 },
				"breakpoints",
				"stacks",
				"watches",
			},
			size = 40,
			position = "left",
		},
		{
			elements = {
				"repl",
			},
			size = 0.25,
			position = "bottom",
		},
	},
	controls = {
		enabled = true,
		element = "repl",
		icons = {
			pause = "",
			play = "",
			step_into = "",
			step_over = "",
			step_out = "",
			step_back = "",
			run_last = "↻",
			terminate = "□",
		},
	},
	floating = {
		max_height = nil,
		max_width = nil,
		border = "single",
		mappings = {
			close = { "q", "<Esc>" },
		},
	},
	windows = { indent = 1 },
	render = {
		max_type_length = nil,
		max_value_lines = 100,
	},
})
```

設定項目は非常に多い。そのうち細かく変えるつもりであえてデフォルト設定を書き連ねていたが、なんだかんだで大していじっていない。見ての通り、各windowの位置関係やアイコン類を変更できる。僕はREPLの表示領域を広めにした。いずれにしてもこれでIDEと同等の作業環境が手に入る。


## [Lspsaga](https://nvimdev.github.io/lspsaga/)
![](/img/233.png)
本稿のトリを務めるのはLSP関連の機能をリッチにせしめるプラグインだ。UIのみならずNeovim本体では提供していない部分もカバーしてくれる。このプラグインの存在は以前から知っていたものの、使いこなせる自信がいまいち持てず今まで放置していた。だが、一度入れてしまえば案外なんとかなるもので、[lsp_lines](https://github.com/ErichDonGubler/lsp_lines.nvim)などの一部プラグインを統廃合することに成功した。設定例は以下の通り。

```lua
require("lspsaga").setup({
	symbol_in_winbar = {
		enable = false,
	},
	ui = {
		border = "single",
		title = false,
	},
	lightbulb = {
		enable = false,
	},
})

local on_attach = function(client, bufnr)
	client.server_capabilities.documentFormattingProvider = false
	local set = vim.keymap.set
	set("n", "K", "<cmd>Lspsaga hover_doc<CR>")
	set("n", "<leader>1", "<cmd>Lspsaga finder<CR>")
	set("n", "<leader>2", "<cmd>Lspsaga rename<CR>")
	set("n", "<leader>3", "<cmd>Lspsaga code_action<CR>")
	set("n", "<leader>4", "<cmd>Lspsaga show_line_diagnostics<CR>")
	set("n", "<leader>5", "<cmd>Lspsaga peek_definition<CR>")
	set("n", "<leader>[", "<cmd>Lspsaga diagnostic_jump_prev<CR>")
	set("n", "<leaaer>]", "<cmd>Lspsaga diagnostic_jump_next<CR>")
end
vim.lsp.handlers["textDocument/publishDiagnostics"] =
	vim.lsp.with(vim.lsp.diagnostic.on_publish_diagnostics, { virtual_text = false })
```

もっとも、すべての制御をこれに任せるのもかえって冗長なので一部はTelescopeに割り振って機能の分散化を図っている。装飾もなるべく抑えて`lightbulb`や`winbar`は無効化している。総合的にはあまりうるさい画面にならず賢くまとまったと思う。


## おわりに
やはりLSPやDAP関連の機能は重たいのか、当初は50msを切っていたNeovimの起動速度がついに100msを超えてしまった。遅延処理をぼちぼち施してもせいぜい80ms程度なので、よほど設定を煮詰めないかぎりRyzen 5 5600G程度のCPUパワーではこの辺りが限界なのだろう。とはいえ、それでも本物のIDEと比べれば依然として高速な開発環境には違いない。いつの日か真にすべての開発作業がターミナルの内側で完結することを願う。
