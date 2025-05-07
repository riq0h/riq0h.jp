---
title: "NeovimをちょっとLuaLuaさせた"
date: 2022-03-15T17:42:39+09:00
draft: false
tags: ["tech"]
---

せっかくNeovim専をやっているのにLua製プラグインに手を出さないのはアレかと思い、とりあえず3つほど移行させてみることにした。真のルアラーはおそらくinit.vimもLuaで書いているのだろうし、プラグインマネージャもpackerとかを使っているのだろう。だが、僕としてはそこまで一気やるのは正直面倒くさい。こういうのはやるにしてもじわじわと段階を経て触っていきたいものだ。

## [lualine.nvim](https://github.com/nvim-lualine/lualine.nvim)

![](/img/94.png)

[lualine.nvim](https://github.com/nvim-lualine/lualine.nvim)はlightlineやairlineのLua実装とでも言うべきstatusline系プラグインである。Vimの扱いに習熟していたり、モダンなIDEの仕様に慣れたユーザはデフォルトのstatuslineではとても満足できない。そこで十年近く前からstatuslineの情報量や視認性を手軽に改善する手段としてこの手のプラグインが出回るようになった。先に述べたlightlineやairlineはその中でもとりわけ知名度が高く、ほとんどのVimmerに一度は使われていると言っても過言ではない。

lualineは豊富な機能を持ちながらもLua実装ゆえの高速さを兼ね備えた、いわば期待のニューホープだ。上のリポジトリページに掲載されている起動速度の検証では、もともと重いことで知られるairlineはもちろん、ミニマルを意識して設計されたlightlineをも僅かに上回る結果を叩き出している。もっとも約2msの差が知覚できるとは思えないが、見たところLuaの知識がなくても簡単に導入できそうなので試しにやってみることにした。なお、下記の設定例はすべて[dein.vim](https://github.com/Shougo/dein.vim)の利用を前提にしている。

```toml
#dein.toml
[[plugins]]
 repo = 'nvim-lualine/lualine.nvim'
 hook_add = '''
 lua << EOF
 require('lualine').setup {
 options = {
  icons_enabled = true,
  theme = 'auto',
  component_separators = { left = '|', right = '|'},
  section_separators = { left = '', right = ''},
  disabled_filetypes = {},
  always_divide_middle = true,
  colored = false,
  },
  sections = {
   lualine_a = {'mode'},
   lualine_b = {'branch', 'diff'},
   lualine_c = {
    {
     'filename',
     path = 1,
     file_status = true,
     shorting_target = 40,
     symbols = {
     modified = ' [+]',
     readonly = ' [RO]',
     unnamed = 'Untitled',
     }
    }
   },
   lualine_x = {'filetype', 'encoding'},
   lualine_y = {
    {
     'diagnostics',
     source = {'nvim-lsp'},
      }
     },
   lualine_z = {'location'}
 },
  inactive_sections = {
   lualine_a = {},
   lualine_b = {},
   lualine_c = {'filename'},
   lualine_x = {'location'},
   lualine_y = {},
   lualine_z = {}
 },
  tabline = {},
  extensions = {}
 }
EOF
'''
```

以上が僕の設定となる。lualineの仕様はlightlineよりはairlineの方式に近く、下記にあるstatuslineの模式図に示されたアルファベットが個別の設定項目とそれぞれ対応する形を採っている。

```
+-------------------------------------------------+
| A | B | C                             X | Y | Z |
+-------------------------------------------------+
```

つまり「B」の内容を変更したければ`lualine_b = {}`の中身を編集すればよいということになる。僕の設定ではGitのbranchとdiffを表示させている。lightlineでは設計思想上、これらを表示するのに外部プラグインとの連携が必要だったが、lualineならオプション名を指定するだけで行える。diagnosticsの表示も大抵は使っているLSPの名称を`source = {}`に書き込めば利用できる。

`tabline`をいじると文字通りタブの外観を変更することも可能だが、僕はタブではなくfzf.vimのバッファラインで管理しているので今回は空欄のままにした。なお、statuslineにカッチョいいファイルアイコンを生やすには`nvim-web-devicons`が必須である。

```toml
#dein.toml
[[plugins]]
 repo = 'kyazdani42/nvim-web-devicons'
```

ファイルアイコンをフルカラー表示させたい場合は本項冒頭の設定の`colored`を`true`にすること。

## [gitsigns.nvim](https://github.com/lewis6991/gitsigns.nvim)

![](/img/95.png)

Gitの差分をリアルタイムに表示させるために[vim-gitgutter](https://github.com/airblade/vim-gitgutter)などを入れている人はかなり多いと思う。実際、hunk（変更箇所へのジャンプ）のkeymapも用意されているし、これで困ることはまったくなかった。僕にとってLua製プラグインへの移行は趣味と挑戦を兼ねている。本項で紹介する[gitsigns.nvim](https://github.com/lewis6991/gitsigns.nvim)はそんなvim-gitgutterの上位互換を目指す意欲的なプラグインだ。

```toml
#dein.toml

[[plugins]]
 repo = 'nvim-lua/plenary.nvim'

[[plugins]]
 repo = 'lewis6991/gitsigns.nvim'
 hook_add = '''
 lua << EOF
 require('gitsigns').setup {
 signs = {
   add          = {hl = 'GitSignsAdd'   , text = '│', numhl='GitSignsAddNr'   , linehl='GitSignsAddLn'},
   change       = {hl = 'GitSignsChange', text = '│', numhl='GitSignsChangeNr', linehl='GitSignsChangeLn'},
   delete       = {hl = 'GitSignsDelete', text = '_', numhl='GitSignsDeleteNr', linehl='GitSignsDeleteLn'},
   topdelete    = {hl = 'GitSignsDelete', text = '‾', numhl='GitSignsDeleteNr', linehl='GitSignsDeleteLn'},
   changedelete = {hl = 'GitSignsChange', text = '~', numhl='GitSignsChangeNr', linehl='GitSignsChangeLn'},
 },
 signcolumn = true,
 numhl      = false,
 linehl     = false,
 word_diff  = false,
 watch_gitdir = {
   interval = 1000,
   follow_files = true
 },
 attach_to_untracked = true,
 current_line_blame = false,
 current_line_blame_opts = {
   virt_text = true,
   virt_text_pos = 'eol',
   delay = 1000,
   ignore_whitespace = false,
 },
 current_line_blame_formatter = '<author>, <author_time:%Y-%m-%d> - <summary>',
 sign_priority = 6,
 update_debounce = 100,
 status_formatter = nil,
 max_file_length = 40000,
 preview_config = {
   border = 'single',
   style = 'minimal',
   relative = 'cursor',
   row = 0,
   col = 1
 },
 yadm = {
   enable = false
  },
  on_attach = function(bufnr)
    local gs = package.loaded.gitsigns
    local function map(mode, l, r, opts)
      opts = opts or {}
      opts.buffer = bufnr
      vim.keymap.set(mode, l, r, opts)
    end
    map('n', ']c', function()
      if vim.wo.diff then return ']c' end
      vim.schedule(function() gs.next_hunk() end)
      return '<Ignore>'
    end, {expr=true})

    map('n', '[c', function()
      if vim.wo.diff then return '[c' end
      vim.schedule(function() gs.prev_hunk() end)
      return '<Ignore>'
    end, {expr=true})
    map({'n', 'v'}, '<leader>hs', ':Gitsigns stage_hunk<CR>')
    map({'n', 'v'}, '<leader>hr', ':Gitsigns reset_hunk<CR>')
    map('n', '<leader>hS', gs.stage_buffer)
    map('n', '<leader>hu', gs.undo_stage_hunk)
    map('n', '<leader>hR', gs.reset_buffer)
    map('n', '<leader>hp', gs.preview_hunk)
    map('n', '<leader>hb', function() gs.blame_line{full=true} end)
    map('n', '<leader>tb', gs.toggle_current_line_blame)
    map('n', '<leader>hd', gs.diffthis)
    map('n', '<leader>hD', function() gs.diffthis('~') end)
    map('n', '<leader>td', gs.toggle_deleted)
    map({'o', 'x'}, 'ih', ':<C-U>Gitsigns select_hunk<CR>')
  end
  }
EOF
'''
```

そのわりにはやたら設定の文字数が多く見えるかもしれないが、これらは大半がデフォルト設定のコピペなので使用感を確かめる目的ならおそらくもっと少ない行数で事足りる。ただ、基本設定から個人的なベストを探る上では予め全部書き写しておいた方が後々いじりやすい。`vim.keymap.set`はNeovim v0.7以降にのみ実装されている機能なので注意。

Lua製と高々に宣伝するだけのことはあって差分の反映は相当に速いと感じる。vim-gitgutterはハイライトされるまでにだいぶ時間を要したが、本プラグインではほぼ即時に行われる。競合より圧倒的に豊富らしい機能の半分も使わないと僕は確信しているが、これだけでも移行して良かったと思える。

![](/img/96.gif)

ちなみに`set signcolumn=yes`をinit.vimに書いておかないと、初めて差分がハイライトされるタイミングでVimがガクンと揺れてしまうので設定しておくことをおすすめする。

## [nvim-colorizer.lua](https://github.com/norcalli/nvim-colorizer.lua)

![](/img/97.png)

カラーコードに対応した背景色をつける定番のプラグイン。下記のおまじないを書き加えれば簡単に機能する。ついでに僕は遅延起動させているがどっちでも構わない。

```toml
#dein_lazy.toml
[[plugins]]
 repo = 'norcalli/nvim-colorizer.lua'
 on_event = 'BufEnter'
 hook_source = '''
 lua << EOF
 require('colorizer').setup()
EOF
'''
```

## LuaLuaしていないがすばらしいプラグイン

本来ここではかの有名な[vim-easymotion](https://github.com/easymotion/vim-easymotion)の事実上のLua実装である[hop.nvim](https://github.com/phaazon/hop.nvim)を紹介する予定だったが、それらよりずっと体験に優れたプラグインを見つけたので紹介したい。

[fuzzy-motion](https://github.com/yuki-yano/fuzzy-motion.vim)は横移動と縦移動に別個のkeymapを提供する前述の二つと異なり、絞り込んだ候補に向かってアルファベット大文字一文字で飛ぶ単純明快な仕様である。奇妙な話だが、これを使ったことで僕はようやくeasymotion系のプラグインに感じていた不満に気づかされた。

従来のeasymotion系の作法では必ずしも単一のキーアサインで目的の位置に飛べるとは限らないのだ。ゆえに行頭に飛ぶキーや二文字で絞り込むキーなどがあれこれと用意されている。どれか一つでは用が足りず、かといってすべて使おうとすると僕には煩雑すぎる。これこそが内心抱いていた不満の正体だったようだ。

![](/img/98.gif)

そこへいくと本プラグインの作法はすっきりしている。絞り込みに用いる文字数を上限なく受け付けることでキーアサインをたった一つに減らしている。ジャンプキーはデフォルトで大文字アルファベット一文字なので迷う余地もまずない。コロンブスの卵とはまさにことのことではないか。

## おわりに

そのうち気が変わって冒頭で述べたinit.vimのLua化やpackerにも手を出すのかもしれないが、さしあたりはこんな程度で僕のLua欲は満たされた。たとえ実際の生産性にそこまで寄与していないとしても、とりあえずトレンドを追っていけばなにかしら役に立つこともあるだろう。

## あわせて読ませたい

・[NeovimをもっとLuaLuaさせた](https://riq0h.jp/2022/10/21/150848/)  
続編。Lua製プラグインをもっと増やした。
