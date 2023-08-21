---
title: "NeovimをもっとLuaLuaさせた"
date: 2022-10-21T15:08:48+09:00
draft: false
tags: ["tech"]
---
この記事は[「NeovimをちょっとLuaLuaさせた」](https://riq0h.jp/2022/03/15/174239/)の続編である。あれからさらにいくつかのLua製プラグインを導入したので紹介していきたい。本シリーズはinit.luaとpacker.nvimへの移行体験を綴った「NeovimをむっちゃLuaLuaさせた」を以て最終回を迎える予定だ。（大嘘）

……まあたぶん、使用するプラグインがほぼすべてLua製になったとかでない限り、そこまで徹底して鞍替えする気にはならないと思う。なにしろ現在使用しているプラグインマネージャのdein.vimとはずいぶん長い付き合いだし、設定の書き方にもだいぶ慣れている。それに、他のマネージャを選ぶならpacker.nvimより[vim-jetpack](https://github.com/tani/vim-jetpack)の方がミニマルで良さそうだ。いずれにしても今のところ移行の意思はまったくない。

とりわけ既存のプラグインをLua製のものに置き換えていくにあたって、後発とて必ずしも上位互換にはなりえないことが分かったので現状はまだinit.vimとよろしくやっていく形になるだろう。なお、以下に続く設定はあくまで僕個人の例なので注意されたし。大半のプラグインを遅延起動させているため、当該の設定をコピペして用いる場合は`dein_lazy.toml`に書かないと機能しない。



## [indent-blankline.nvim](https://github.com/lukas-reineke/indent-blankline.nvim)

[vim-indent-guides](https://github.com/nathanaelkane/vim-indent-guides)を置き換えた。インデントの階層を可視化するプラグイン。追加の設定でスペース幅の表示をより詳細にしたりラインをカラフルにもできる。あまりゴチャつくと逆効果ゆえ僕は単純な設定に留めている。

![](/img/155.png)

```toml
#dein_lazy.toml
[[plugins]]
 repo = 'lukas-reineke/indent-blankline.nvim'
 on_event = 'BufEnter'
 hook_source = '''
 lua << EOF
 vim.opt.list = true
 vim.opt.listchars:append "eol:↴"
 
 require('indent_blankline').setup {
     show_end_of_line = true,
 }
EOF
'''
```

## [nvim-autopairs](https://github.com/windwp/nvim-autopairs)

[auto-pairs](https://github.com/jiangmiao/auto-pairs)を置き換えた。デフォルト設定での挙動が僕の性に合っていた。名前の通り、括弧やクォートの類を自動で閉じてくれる。Vimに限らずリッチな仕様のエディタやIDEでは当たり前の機能なので、今時は逆に使わない人の方が珍しいんじゃなかろうか。

```toml
#dein_lazy.toml
[[plugins]]
 repo = 'windwp/nvim-autopairs'
 on_event = 'BufEnter'
 hook_source = '''
 lua << EOF
 require('nvim-autopairs').setup()
EOF
'''
```

## [fidget.nvim](https://github.com/j-hui/fidget.nvim)

LSPの稼働状況をクールなアニメーションで通知してくれるプラグイン。言語にもよるが意外に助かる時がある。

![](https://raw.githubusercontent.com/j-hui/fidget.nvim/media/gifs/fidget-demo-rust-analyzer.gif)

```toml
#dein_lazy.toml
[[plugins]]
 repo = 'j-hui/fidget.nvim'
 on_event = 'BufEnter'
 hook_source = '''
 lua << EOF
 require('fidget').setup()
EOF
'''
```

## [lsp_lines.nvim](https://github.com/ErichDonGubler/lsp_lines.nvim)

LSPのdiagnosticsをいい感じに拵えるプラグイン。ビルトイン機能の方はたくさん表示させるとひどく見づらかったが、こういうふうにしてくれると俄然受け入れやすい。正直、このプラグインを知るまでは機能自体をオフにしていた。

![](/img/156.png)

```toml
#dein_lazy.toml
[[plugins]]
 repo = 'Maan2003/lsp_lines.nvim'
 on_event = 'BufEnter'
 hook_source = '''
 lua << EOF
 require('lsp_lines').setup()
EOF
'''
```

## [nvim-hlslens](https://github.com/kevinhwang91/nvim-hlslens)

`/`での検索後に出るカウンタを改良するプラグイン。該当ワードの真横に連番が現れるのでとても分かりやすい。何回分のnで目当てのワードに飛べるのかも教えてくれる。おかげでnnnnnとか連打しなくても5nで間に合うことが直感的に把握できる。

![](/img/157.png)

```toml
#dein_lazy.toml
[[plugins]]
 repo = 'kevinhwang91/nvim-hlslens'
 on_event = 'BufEnter'
 hook_source = '''
 lua << EOF
 require('hlslens').setup()
 local kopts = {noremap = true, silent = true}
 
 vim.api.nvim_set_keymap('n', 'n',
     [[<Cmd>execute('normal! ' . v:count1 . 'n')<CR><Cmd>lua require('hlslens').start()<CR>]],
     kopts)
 vim.api.nvim_set_keymap('n', 'N',
     [[<Cmd>execute('normal! ' . v:count1 . 'N')<CR><Cmd>lua require('hlslens').start()<CR>]],
     kopts)
 vim.api.nvim_set_keymap('n', '*', [[*<Cmd>lua require('hlslens').start()<CR>]], kopts)
 vim.api.nvim_set_keymap('n', '#', [[#<Cmd>lua require('hlslens').start()<CR>]], kopts)
 vim.api.nvim_set_keymap('n', 'g*', [[g*<Cmd>lua require('hlslens').start()<CR>]], kopts)
 vim.api.nvim_set_keymap('n', 'g#', [[g#<Cmd>lua require('hlslens').start()<CR>]], kopts)
 
 vim.api.nvim_set_keymap('n', '<Leader>x', ':noh<CR>', kopts)
EOF
'''
```

## [telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)

言わずと知れたファジーファインダー界の一大勢力。コピペ設定でもかなり賢く働いてくれるが自己流にカスタマイズするととんでもなく捗る。以前は素のfzf.vimでゴニョゴニョやっていたが、VSCodeよりもVimの使用頻度が高まるにつれて厳しさを感じはじめていた。結局、本プラグインと双璧をなす[fzf-preview.vim](https://github.com/yuki-yano/fzf-preview.vim)の作者である[Yuki Yano氏のアドバイス](https://twitter.com/yuki_ycino/status/1442056435253190665)が正しかったことになる……。まさに経験者は語るというやつだ。

![](/img/158.gif)

```toml
#dein.toml
[[plugins]]
 repo = 'nvim-telescope/telescope.nvim'
 hook_add = '''
 nnoremap <leader>. <cmd>lua require('telescope.builtin').find_files({hidden=true})<CR>
 nnoremap <leader>l <cmd>lua require('telescope.builtin').live_grep({grep_open_files=true})<CR>
 nnoremap <leader>k <cmd>lua require('telescope.builtin').live_grep()<CR>
 nnoremap <leader>b <cmd>lua require('telescope.builtin').buffers()<CR>
 nnoremap <leader>h <cmd>lua require('telescope.builtin').help_tags()<CR>
 nnoremap <leader>y <cmd>lua require('telescope.builtin').registers()<CR>
 nnoremap gd <cmd>lua require('telescope.builtin').lsp_definitions()<CR>
 nnoremap gr <cmd>lua require('telescope.builtin').lsp_references()<CR>
 nnoremap gi <cmd>lua require('telescope.builtin').lsp_implementations()<CR>
 nnoremap gx <cmd>lua require('telescope.builtin').diagnostics()<CR>

 lua << EOF
 local actions = require("telescope.actions")
 require("telescope").setup{
   defaults = {
     mappings = {
       i = {
     ["<esc>"] = actions.close
       },
     },
   },
 }

 local previewers = require("telescope.previewers")
 local Job = require("plenary.job")
 local new_maker = function(filepath, bufnr, opts)
   filepath = vim.fn.expand(filepath)
   Job:new({
     command = "file",
     args = { "--mime-type", "-b", filepath },
     on_exit = function(j)
       local mime_type = vim.split(j:result()[1], "/")[1]
       if mime_type == "text" then
         previewers.buffer_previewer_maker(filepath, bufnr, opts)
       else
         vim.schedule(function()
           vim.api.nvim_buf_set_lines(bufnr, 0, -1, false, { "BINARY" })
         end)
       end
     end
   }):sync()
 end

 require("telescope").setup {
   defaults = {
     buffer_previewer_maker = new_maker,
     extensions = {
     fzf = {
       fuzzy = true,
       override_generic_sorter = true,
       override_file_sorter = true,
       case_mode = "smart_case",
    },
   },
  },
 }

 vim.api.nvim_set_keymap('n', '<leader>,', "<cmd>lua require('telescope').extensions.frecency.frecency()<CR>", {noremap = true, silent = true})

EOF
'''

[[plugins]]
 repo = 'nvim-lua/plenary.nvim'
```

この設定例ではソースとしてファイル検索、絞り込み、バッファ一覧、ヘルプタグ、レジスタ履歴、LSPとの連携機能を利用している。要ripgrep。また、[telescope-frecency.nvim](https://github.com/nvim-telescope/telescope-frecency.nvim)を別途導入することで標準のoldfilesより高度なMRU（Most Recently Used）を使えるように仕上げている。現状はこれで十分だが習熟次第ではさらなる拡張の余地がありそうだ。

## [registers.nvim](https://github.com/tversteeg/registers.nvim)
コードをヤンクした後に他所でddしたらレジスタが上書きされてしまった！ ……なんて面倒を防ぐためのプラグイン。レジスタの中身をすべて一覧表示できる。僕みたいなコピペマンには絶対に欠かせない。Telescopeに乗り換えるまではよくお世話になっていた。デフォルト設定では`"`キーで展開される。

![](/img/159.png)

```toml
#dein.toml
[[plugins]]
 repo = 'tversteeg/registers.nvim'
 hook_add = '''
 lua << EOF
 require('registers').setup()
EOF
'''
```

新たに導入したLua製プラグインの紹介はこれで以上となる。おそらくパワーユーザにとっては目新しさに乏しいラインナップだったかと思われるが、半年以上も前に書いた前編が未だに一定のPVを呼び込んでいる様子を鑑みると、こうした基礎的な内容の記事もぼちぼち誰かの助けにはなっていそうだ。書く側としても導入に至った経緯を言語化できるのでまんざら無償の奉仕というわけでもない。今後も折りに触れて書いていくつもりである。

<iframe style="border-radius:12px" src="https://open.spotify.com/embed/track/1RIE9evNiaPTV7PrVSuqWG?utm_source=generator" width="100%" height="80" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>

## あわせて読ませたい
・[Neovimを完全にLuaLuaさせた](https://riq0h.jp/2023/01/20/210601/)  
シリーズ最終章。感動のフィナーレ。
