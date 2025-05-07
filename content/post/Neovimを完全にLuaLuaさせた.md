---
title: "Neovimを完全にLuaLuaさせた"
date: 2023-01-20T21:06:01+09:00
draft: false
tags: ["tech"]
---

[前回の記事](https://riq0h.jp/2022/10/21/150848/)の続編にして最終章の幕開けである。ついにinit.lua化は果たされ、主だったプラグインはどれもLua製に置き換わった。プラグイン総数が50前後しかないカジュアルユーザの僕でも丸一日かかったがやるだけの価値はあったと思いたい。

今や業務以外ではエディタをVim一本に絞りきれるところまで馴染んだ。主流のプラグインマネージャがNeoBundleの時代からVimに触れてきた割にはずいぶん手間を食ったものだ。「Vimはサブ武器です」と尻込みしていた頃とはうってかわり、Vimはもう僕のメイン武器となった。

## init.lua化の実践

**■シングルファイル**  
Web上の様々な設定例はたいていファイルが細かく分割されている。プラグインごとに独立したファイルを与えている事例もよく見るし、init.luaが数行しかないのも珍しくない。だいたいみんな5個くらいには分けているようだ。僕も以前はinit.vimとdein.vim、dein_lazy.vimの3つに分けていたが、編集を重ねていく過程で僕はこのメソッドにさほど嬉しみを感じていないことに気がついた。

もしかすると僕の知らない利点があるのかもしれないが、単に可読性の都合でしかないとしたら全部まとめても500行程度に収まる設定をあえてバラけさせる理由はなさそうだ。というわけでinit.lua化に合わせて全設定を一つのファイルに集約した。したがって、本エントリの記述例はすべてinit.luaに記されていると考えて構わない。

**■記述のパターン化**  
init.lua化に役立つ知見はありとあらゆる場所に記されているとはいえ、手早く移行を完了させたいユーザにとっては迂遠な説明が多かったり、特殊な設定に文面を割いていたりしていまいち要領を得ないのが実情だ。そこで僕はいくつかのパターンを重点的に捉えることにした。

とりわけ重要なパターン例はVim scriptにおける`set xxx`構文がinit.luaでは`vim.opt.xxx = boolean`に置き換わっているところである。前者では設定した値がそのまま有効化されるが、後者の場合はboolean型で変数を入力する。つまり、trueなら有効でfalseなら無効化される。設定の大部分はこれだけ知っておけば書き換えられなくもない。

```Lua
set hidden --Vim script
vim.opt.hidden = true --大半の設定はこのパターンで書ける。

set helplang='ja', 'en' --Vim script
vim.opt.helplang = 'ja', 'en' --設定部分によっては値も変わる。

set cmdheight=2 --Vim script
vim.opt.cmdheight = 2 --元の値が数値ならここも数値で指定する。

set signcolumn=yes --Vim script
vim.opt.signcolumn = 'yes' --数値でもboolean型でもない設定も稀にある。
```

他にショートハンドの`vim.o.xxx`や`vim.bo.xxx`などもあるが、基本的には`vim.opt.xxx`を使っておけば無用な誤りを減らせる。一方、数少ない例外への対処法としてはLuaっぽく直した構文をかたっぱしからGitHubの検索窓に叩き込む手法が非常に有効だった。ヒット件数が多ければ多いほど設定の確からしさを推測できる。

惜しむらくは資料の膨大さゆえ誰のどのコードを参考にしたのかまるで憶えておらず、技術文章にあるまじき不誠実な状態に陥ってしまったことだ。さしあたってはinit.luaを書いた全人類に感謝を捧げるという体裁でどうか容赦願いたい。

```Lua
set mapleader='/<Space>' --Vim scriptの場合はエスケープ処理と文字コードが必要。
vim.g.mapleader = ' ' --この設定は構文が異なりエスケープ処理も文字コードも不要。

set clipboard+=unnamedplus --Vim script
vim.opt.clipboard:append{'unnamedplus'} --特別な指定方法の一つ。

set list listchars=tab:»-,trail:-,eol:↲,extends:»,precedes:«,nbsp:% --Vim script
vim.opt.listchars = {tab='»-', trail='-', eol='↲', extends='»', precedes='«', nbsp='%'} --特別な指定方法の一つ。

set shortmess+=I --Vim script
vim.cmd('set shortmess+=I') --代替しうる構文が見つからない時はvim.cmdを利用してVim scriptで書く。

set noundofile --Vim script
vim.opt.undofile = false --init.luaに否定形の構文はないため、この場合は指定すべき真偽値が逆になることに注意されたし。
```

キーマッピングも同様のパターンで対応可能だ。たとえば`nmap a b`のようなマッピングをinit.luaは`vim.keymap.set('n', 'a', 'b')`の形で記す。`vim.api.nvim_set_keymap()`といった記述も有効だがこれは古い書き方である。このように既存の設定をパターン化して順次書き換えていき、必要に応じてGitHubの検索を活用すればいずれinit.lua化が完了するだろう。ただし、autocmdを多用している人はちょっと苦労しそうだ。

```Lua
nnoremap <silent> sv :<C-u>vsplit<CR> --Vim script
vim.keymap.set('n', 'sv', ':<C-u>vsplit<CR>', {silent = true}) --<silent>などもboolean型で指定する。

--やっている人が多そうなカーソル位置の保存設定をLua化したもの。
vim.api.nvim_create_autocmd({ 'BufReadPost' }, {
    pattern = { '*' },
    callback = function()
        vim.api.nvim_exec('silent! normal! g`"zv', false)
    end,
})
```

ベテランユーザにとって以上の実践例は本質を無視した邪悪な所業かもしれないが、とにかく有効なinit.luaを仕立てる上ではこんな大雑把な理解でも一応差し支えはない。そのうちちゃんと`:help lua-guide`を読むから許してほしい。

## [lazy.nvim](https://github.com/folke/lazy.nvim)

init.lua化の次に取り掛かるのはプラグインマネージャの移行だ。今まで使っていたdein.vimにはなんの不満もないどころか、むしろ離れがたいとさえ感じているがLua化の欲望には抗えない。どうせやるからには真のルアラーを目指していきたい。まあ、真のルアラーは設定をコピペで書いたりはしないんだろうけど。

かつてLua製のプラグインマネージャといえばpacker.nvimの存在感が大きかった。僕もinit.lua化を果たした暁には半ば自動的にそれに移行するものと考えていたが、昨年の晩秋に突如現れた[lazy.nvim](https://github.com/folke/lazy.nvim)の新進気鋭ぶりが凄まじく、せっかくならと新しい方を試すことにした。

使ってみると好評の理由はすぐに判った。俗な言い方をすればUIが強すぎる。プラグインの追加を検知すると再起動後にグラフィカルなインストール処理が自動で走り、アップデート時にはその概要までもが過不足のない洗練された画面で表示される。似たような機能は他のプラグインマネージャも持っているがポン付けでよしなにやってくれる点ではこちらが上回る。

![](/img/172.png)

極めつけは`:Lazy profile`のベンチマーク機能だ。`nvim --startup`抜きで即座に起動時間が把握できて、なおかつどのプラグインがどんな順序で読み込まれているのかも判る。伊達にlazyなどと銘打っていないだけはあり、遅延に関する機能はかなり豊富に見える。

![](/img/173.png)

遅延設定そのものも書きやすい。さすがにフルオートメーションとはいかず結局は手動で書かざるをえなかったがドキュメント類も賢くまとまっており、移行直前の億劫ささえ乗り越えればなんとかなった。これもいくつかのパターンを抑えれば簡単に遅延化を実現できる。以下に設定の一部を記す。

```Lua
{'windwp/nvim-autopairs', event = 'InsertEnter'}, --文字の挿入を伴うプラグインは'InsertEnter'を指定する。
{'j-hui/fidget.nvim', event = 'LspAttach'}, --LSPと連動するプラグインは'LspAttach'を指定する。
{'nvim-telescope/telescope.nvim', cmd = 'Telescope'}, --特定のコマンドを入力するまで不要なプラグインはcmd = 'cammand'で対応する。
{'vim-jp/vimdoc-ja', ft = 'help'}, --特定のファイルタイプでのみ必要なプラグインはft = 'filetype'で対応する。
{'lewis6991/gitsigns.nvim', event = 'BufNewFile, BufRead'}, --ファイルを読み込んだ後に装飾を加えるプラグインは'BufNewFile'と'BufRead'が有力。
{'echasnovski/mini.surround', event = 'ModeChanged'}, --モードの切り替え時に発動させたいプラグインは'ModeChanged'が適切。
{'nvim-lualine/lualine.nvim', event = 'VeryLazy'}, --他の設定でうまく動かなかったものは一律に'VeryLazy'で対処する。（VimEnter相当らしい）
{'vim-denops/denops.vim', lazy = false}, --即時読み込んでくれないと不都合なプラグインは逆に遅延を無効化する。（config.default.lazy = falseの場合）
```

lazy.nvimの作者曰く、遅延設定を最強に極めると90以上のプラグインを抱えていても10ms台で立ち上がるらしい。僕の周りでもベテランユーザたちが次々と30ms台を達成している。残念ながら上記の中途半端なやり方では50msを切るか切らないかが精一杯だが、それでもデフォルト設定の2倍近く高速化できたので当面はこれで納得しておく。

## [nvim-cmp](https://github.com/hrsh7th/nvim-cmp)

補完プラグインも例によってLua製に置き換えた。僕は補完プラグインについてはShougoware一筋（neocomplete.vim→deoplete.nvim→ddc.vim）だったが、当初の懸念とは裏腹にこのnvim-cmpは使っていてなんの不満も感じない。Neovim界隈で事実上のデファクトスタンダートと認められているのも納得の完成度と言える。大衆人気を得るプラグインにありがちなおせっかいさも見られず、自分でキーマップやソースを設定しなければならないところも好印象だ。

たとえばLSPと連携するための[cmp-nvim-lsp](https://github.com/hrsh7th/cmp-nvim-lsp)、バッファ内のワードを拾う[cmp-buffer](https://github.com/hrsh7th/cmp-buffer)、コマンドラインの入力を補完してくれる[cmp-cmdline](https://github.com/hrsh7th/cmp-cmdline)などが挙げられる。ソース群の種類はddc.vimに引けをとらず豊富で、なにがなくて困るというよりはトレンドを掴む方がかえって大変かもしれない。以下に僕の設定を示す。

```Lua
local cmp = require('cmp')
local lspkind = require('lspkind')

 cmp.setup({
   snippet = {
     expand = function(args)
       vim.fn['vsnip#anonymous'](args.body)
     end
   },

   window = {
      completion = cmp.config.window.bordered({
        border = 'single'
    }),
      documentation = cmp.config.window.bordered({
        border = 'single'
    }),
   },

   mapping = cmp.mapping.preset.insert({
     ['<Tab>'] = cmp.mapping.select_next_item(),
     ['<S-Tab>'] = cmp.mapping.select_prev_item(),
     ['<C-b>'] = cmp.mapping.scroll_docs(-4),
     ['<C-f>'] = cmp.mapping.scroll_docs(4),
     ['<C-Space>'] = cmp.mapping.complete(),
     ['<C-e>'] = cmp.mapping.abort(),
     ['<CR>'] = cmp.mapping.confirm({ select = true }),
   }),

 formatting = {
   format = lspkind.cmp_format({
     mode = 'symbol',
     maxwidth = 50,
     ellipsis_char = '...',
   })
  },

 sources = cmp.config.sources({
   { name = 'nvim_lsp' },
   { name = 'vsnip' },
   { name = 'nvim_lsp_signature_help' },
   { name = 'calc' },
  }, {
   { name = 'buffer', keyword_length = 2 },
  })
 })

 cmp.setup.cmdline({ '/', '?' }, {
   mapping = cmp.mapping.preset.cmdline(),
   sources = cmp.config.sources({
  { name = 'nvim_lsp_document_symbol' }
  }, {
   { name = 'buffer' }
  })
 })

 cmp.setup.cmdline(':', {
 mapping = cmp.mapping.preset.cmdline(),
 sources = cmp.config.sources({
   { name = 'path' }
  }, {
   { name = 'cmdline', keyword_length = 2 }
  })
 })

local capabilities = require('cmp_nvim_lsp').default_capabilities()
vim.cmd('let g:vsnip_filetypes = {}')
```

もちろん、これらを適用するには任意のプラグインマネージャに導入したいソース群を予め列挙しておく必要がある。lazy.nvimでの記述例は以下の通りになる。

```Lua
{'hrsh7th/nvim-cmp', event = 'InsertEnter, CmdlineEnter'},
{'hrsh7th/cmp-nvim-lsp', event = 'InsertEnter'},
{'hrsh7th/cmp-buffer', event = 'InsertEnter'},
{'hrsh7th/cmp-path', event = 'InsertEnter'},
{'hrsh7th/cmp-vsnip', event = 'InsertEnter'},
{'hrsh7th/cmp-cmdline', event = 'ModeChanged'}, --これだけは'ModeChanged'でなければまともに動かなかった。
{'hrsh7th/cmp-nvim-lsp-signature-help', event = 'InsertEnter'},
{'hrsh7th/cmp-nvim-lsp-document-symbol', event = 'InsertEnter'},
{'hrsh7th/cmp-calc', event = 'InsertEnter'},
{'onsails/lspkind.nvim', event = 'InsertEnter'},
{'hrsh7th/vim-vsnip', event = 'InsertEnter'},
{'hrsh7th/vim-vsnip-integ', event = 'InsertEnter'},
{'rafamadriz/friendly-snippets', event = 'InsertEnter'},
```

導入すると下記動画のような美しい補完ウインドウが姿を現す。すっかり手垢のついた言い回しになってしまうが、GUIのIDEに勝るとも劣らない上等な表現力だと思っている。

![](/img/174.gif)

## [telescope-file-browser.nvim](https://github.com/nvim-telescope/telescope-file-browser.nvim)

昨今のファイラと言えば[fern.vim](https://github.com/lambdalisue/fern.vim)がよく知られている。しかし今の僕には可能なかぎりNeovimをLuaLuaさせたいモチベが堆積しており、Telescopeをファイラに仕立てた本プラグインをチョイスした。当然ながら操作方法はTelescopeそのもので、あとはファイル管理に関わるショートカットキーさえ覚えればすでに手に馴染んだも同然である。

![](/img/175.gif)

他のファジーファインダーを使っている人もこれを目当てにTelescopeに移行すべきかと訊かれたら「そこまでではない」と答えるが、突出した特長がない代わりに一通りの機能は揃っているためTelescopeユーザには一度試してもらいたいファイラだ。デフォルトでAltキーを占有しているところは若干気に入らないものの、その気になれば容易に変更できるのでtmuxやi3wmユーザでも不都合はないだろう。

## おわりに

init.lua化、プラグインマネージャ、補完プラグイン、ファイラと立て続けに大がかりな移行を終えた現在、もはや完全にNeovimをLuaLuaさせたと言っても過言ではないはずだ。よって本シリーズはこれにて一旦の完結を見るが、今後もなにか面白い発見があれば随時紹介していきたい。もし読者の皆さんに「あまり知られていないが自分はこれがないと生きていけない」というようなプラグインがあったらぜひ教えていただきたい。

## あわせて読ませたい

・[NeovimをさらにLuaLuaさせた](https://riq0h.jp/2023/12/03/103850/)  
主にDAPとLSPの関連プラグインについて書いた待望の番外編。
