---
title: "ddc.vimとBuiltin LSPでサブ武器を錬成した"
date: 2021-09-15T08:40:23+09:00
draft: false
tags: ["tech"]
---

![](/img/52.png)

以前は[coc.nvim](https://github.com/neoclide/coc.nvim)を用いて開発環境を構築していたが、オールインワン系プラグインならではの過剰性能に思うところがあったのでリプレイスを図ることにした。というのも、CoCが提供する機能のうち僕が絶対に必要としているのはせいぜい下記の3つ程度だったからだ。

・自動補完  
・LSP  
・セレクタ  

したがって、上記の機能を満たす単機能のプラグインをそれぞれ見繕えば当座の目的は達成できたことになる。僕にとってのVimは小回りの利く**サブ武器**なので、さしあたり一通りの編集作業がこなせる形に持っていければよいものとした。

## ddc.vim
[ddc.vim](https://github.com/Shougo/ddc.vim)は自動補完を行うためのプラグインで、広く人気を集めたdeoplete.vimの後継にあたる。わずか数ヶ月前に公開されたニューフェイスながら既に実用可能なクオリティに達している。ただし仕様上、補完ソースやスニペットの類はすべて分離されているので、各要素の導入と併せてユーザ自らの手で設定しなければらない。

これは作者の言葉通り確かに初心者向けの作りではないものの、かえってそのミニマル志向が僕の使い方には合っていると感じた。さっそく以下から導入および設定例を示していくが、プラグイン管理に[dein.vim](https://github.com/Shougo/dein.vim)を用いている都合上、記述内容はそれに則る形をとる。

```toml
#dein_lazy.toml これらのプラグインはもっぱら遅延読み込みで運用する。
[[plugins]]
 repo = 'Shougo/ddc.vim'
 on_event = 'InsertEnter'
 depends = ['denops.vim']
 hook_source = '''
 call ddc#custom#patch_global('ui', 'native')
 call ddc#custom#patch_global('sources', ['nvim-lsp', 'around', 'vsnip'])
 call ddc#custom#patch_global('sourceOptions', {
      \ '_': {
      \ 'matchers': ['matcher_head'],
      \ 'sorters': ['sorter_rank'],
      \ 'converters': ['converter_remove_overlap'],
      \ },
      \ 'around': {'mark': 'A'},
      \ 'nvim-lsp': {
      \ 'mark': 'L',
      \ 'forceCompletionPattern': '\.\w*|:\w*|->\w*',
      \ },
      \ })

 call ddc#custom#patch_global('sourceParams', {
      \ 'around': {'maxSize': 500},
      \ })

 inoremap <silent><expr> <TAB>
      \ ddc#map#pum_visible() ? '<C-n>' :
      \ (col('.') <= 1 <Bar><Bar> getline('.')[col('.') - 2] =~# '\s') ?
      \ '<TAB>' : ddc#map#manual_complete()
 inoremap <expr><S-TAB>  ddc#map#pum_visible() ? '<C-p>' : '<C-h>'

 call ddc#enable()
'''
```
以上はddc.vimの設定として記述しているが、自動補完を働かせるには下記の補完ソースプラグインを別途要する。

```toml
#dein_lazy.toml

[[plugins]]
 repo = 'Shougo/ddc-ui-native'
 on_source = 'ddc.vim'

[[plugins]]
 repo = 'Shougo/ddc-around'
 on_source = 'ddc.vim'

[[plugins]]
 repo = 'Shougo/ddc-matcher_head'
 on_source = 'ddc.vim'

[[plugins]]
 repo = 'Shougo/ddc-sorter_rank'
 on_source = 'ddc.vim'

[[plugins]]
 repo = 'Shougo/ddc-converter_remove_overlap'
 on_source = 'ddc.vim'

[[plugins]]
 repo = 'Shougo/ddc-nvim-lsp'
 on_source = 'ddc.vim'

[[plugins]]
 repo = 'hrsh7th/vim-vsnip'
 on_event = 'InsertEnter'
 depends = ['vim-vsnip-integ', 'friendly-snippets']
 hook_add = '''
 imap <expr> <C-j> vsnip#expandable() ? '<Plug>(vsnip-expand)' : '<C-j>'
 smap <expr> <C-j> vsnip#expandable() ? '<Plug>(vsnip-expand)' : '<C-j>'
 imap <expr> <C-f> vsnip#jumpable(1)  ? '<Plug>(vsnip-jump-next)' : '<C-f>'
 smap <expr> <C-f> vsnip#jumpable(1)  ? '<Plug>(vsnip-jump-next)' : '<C-f>'
 imap <expr> <C-b> vsnip#jumpable(-1) ? '<Plug>(vsnip-jump-prev)' : '<C-b>'
 smap <expr> <C-b> vsnip#jumpable(-1) ? '<Plug>(vsnip-jump-prev)' : '<C-b>'
 let g:vsnip_filetypes = {}
 '''

[[plugins]]
 repo = 'hrsh7th/vim-vsnip-integ'

[[plugins]]
 repo = 'rafamadriz/friendly-snippets'

[[plugins]]
 repo = 'vim-denops/denops.vim'
```
LSPを利用しないのであれば、この段階でとりあえずddc.vimを動作させることができる。実際に使ってみて、明示的に設定していない動作は一切行わない無骨さにかなりの好感を持った。後述のLSPに関しては入れ替えの余地もまだ残されているが、少なくとも自動補完プラグインはこのまま定住するつもりでいる。

**■2022年10月27日追記**  
ddc.vimの再設計によりインターフェイス部分が分離されたので、すべてのユーザはnative UIか任意のUIプラグインを導入しなければいけなくなった。上記の設定例ではさしあたり前者を導入する形で記述している。

ざっくばらんに各ソースの機能を説明すると、[ddc-around](https://github.com/Shougo/ddc-around)はカーソル周辺の単語を検出するもので[ddc-matcher_head](https://github.com/Shougo/ddc-matcher_head)と[ddc-sorter_rank](https://github.com/Shougo/ddc-sorter_rank)が入力内容に応じて補完候補を決めるフィルタとして働いている。しかし、このままでは同じ単語を重複して補完してしまう恐れがあるため[ddc-converter_remove_overlap](https://github.com/Shougo/ddc-converter_remove_overlap)でそれを抑制している。

[ddc-nvim-lsp](https://github.com/Shougo/ddc-nvim-lsp)は言わずもがな、後述のNeovim Builtin LSPが提供する構文を引っ張ってくるソースだ。[vim-vsnip](https://github.com/hrsh7th/vim-vsnip)と以降の関連プラグイン群は補完を通じて多種多様なスニペットを提供してくれる。最後の[denops.vim](https://github.com/vim-denops/denops.vim)はddc.vimの動作に必須。

他にも多くのVimmerの手によって様々なソースが日々生み出されているが、誰にとっても入れておいて邪魔にならないソースは概ねこんなところだろう。

## Neovim Builtin LSP
Builtin LSPとは名前の通り、Neovimの本体に組み込まれたLSPである。しかし動作させるには結局あれこれプラグインを導入したり設定しなければならないので、coc.nvimや[vim-lsp](https://github.com/vim-lsp/vim-lsp)と比べると導入手順はむしろ面倒な部類に入る。Builtin LSPにもvim-lspにおける[vim-lsp-settings](https://github.com/mattn/vim-lsp-settings)のようなプラグイン（[nvim-lspinstall](https://github.com/kabouzeid/nvim-lspinstall)）が存在するが、これもポン付けで全部よしなにやってくれるほど良心的ではない。肝心のLSPとしての品質もいささか荒削りな印象を受けた。

つまり現状、Neovimをメインでバリバリ使う人にとってわざわざ乗り換えるメリットは特にないと思われる。一応内蔵されている（Luaで書かれている）ということで実行速度に優れる利点はあるが、体感的にそこまで明瞭な差は感じられなかった。いずれは公式の強みを活かして競合を追い越す可能性も無きしもあらずとはいえ、今時分は個人の趣味性の範疇に留まると言わざるを得ない。僕がBuiltin LSPに乗り換えたのも将来性に期待して贔屓している部分が大きい。

~~**■12月15日追記**~~  
~~前述のnvim-lspinstallはいつの間にか開発が終了していたので[nvim-lsp-installer](https://github.com/williamboman/nvim-lsp-installer)に乗り換えた。コマンドに目立った差異はほとんど見られないが、Language Serverのインストール画面が多少グラフィカルになっていたり、バージョンを指定する機能(例：`:LspInstall rust_analyzer@nightly`)が追加されている。また、かつては対応が疎かだったWindows環境もフルサポートしているなど、およそ上位互換品と見て間違いないと考えられる。~~

**■2022年10月13日追記**  
なんとnvim-lsp-installerの開発も終了してしまった。現在は[mason.nvim](https://github.com/williamboman/mason.nvim)が後継として開発されている。このプラグインの使用には[mason-lspconfig.nvim](https://github.com/williamboman/mason-lspconfig.nvim)も実質的に必要なので注意されたし。本プラグインは公式で遅延読み込みが非推奨となっているゆえ、関連設定はすべてinit.vimに直接書き込んでいる。


![](/img/78.png)

```vim
#init.vim
 " nvim-lspconfig+mason.nvim+mason-lspconfig
 lua << EOF
 local on_attach = function(client, bufnr)
  client.server_capabilities.documentFormattingProvider = false
  local set = vim.keymap.set
   set('n', 'gd', '<cmd>lua vim.lsp.buf.definition()<CR>')
   set('n', 'K', '<cmd>lua vim.lsp.buf.hover()<CR>')
   set('n', 'gi', '<cmd>lua vim.lsp.buf.implementation()<CR>')
   set('n', 'gs', '<cmd>lua vim.lsp.buf.signature_help()<CR>')
   set('n', 'gn', '<cmd>lua vim.lsp.buf.rename()<CR>')
   set('n', 'ga', '<cmd>lua vim.lsp.buf.code_action()<CR>')
   set('n', 'gr', '<cmd>lua vim.lsp.buf.references()<CR>')
   set('n', 'gx', '<cmd>lua vim.lsp.diagnostic.show_line_diagnostics()<CR>')
   set('n', 'g[', '<cmd>lua vim.lsp.diagnostic.goto_prev()<CR>')
   set('n', 'g]', '<cmd>lua vim.lsp.diagnostic.goto_next()<CR>')
   set('n', 'gf', '<cmd>lua vim.lsp.buf.formatting()<CR>')
   end
 vim.lsp.handlers["textDocument/publishDiagnostics"] = vim.lsp.with(
 vim.lsp.diagnostic.on_publish_diagnostics, { virtual_text = false })

 require("mason").setup()
 require("mason-lspconfig").setup()
 require("mason-lspconfig").setup_handlers {
   function(server_name) -- default handler (optional)
     require("lspconfig")[server_name].setup {
       on_attach = on_attach,
     }
   end
 }
EOF
```

```toml
#dein.toml
[[plugins]]
 repo = 'neovim/nvim-lspconfig'

[[plugins]]
 repo = 'williamboman/mason.nvim'

[[plugins]]
 repo = 'williamboman/mason-lspconfig.nvim'
```

~~導入後、対応ファイルを開くとLSPも連動して立ち上がる。プレビュープラグインの[ddc-nvim-lsp-doc](https://github.com/matsui54/ddc-nvim-lsp-doc)がIDEよろしく補完候補の詳細情報を提供してくれるのでかなり心強い。Language Serverごとの細かい設定はまだ定まっていないので本エントリでは割愛させていただく。LSPのインストール情報は`:LspInfo`で確認できる。~~

**■2022年1月3日追記**  
前述のddc-nvim-lsp-docは更新が停止され、新規プラグインの[denops-signature_help](https://github.com/matsui54/denops-signature_help)と[denops-popup-preview](https://github.com/matsui54/denops-popup-preview.vim)に置き換えられた。この変更に倣って下記の設定例も既に書き換えている。実装手法は異なるが機能面にほとんど差はないためさっさと乗り換えた方がよい。

![](/img/53.gif)

```toml
#dein_lazy.toml
[[plugins]]
 repo = 'matsui54/denops-signature_help'
 on_source = 'ddc.vim'
 hook_source = '''
 call signature_help#enable()
'''

[[plugins]]
 repo = 'matsui54/denops-popup-preview.vim'
 on_source = 'ddc.vim'
 hook_source = '''
 call popup_preview#enable()
'''
```

## セレクタ
セレクタとはファイルや文字列の絞り込みを行うためのインターフェイスを提供するプラグインだ。中でも[fzf.vim](https://github.com/junegunn/fzf.vim)は特に高速かつ多機能なことで知られている。Yuki Yano氏が開発した[fzf-preview.vim](https://github.com/yuki-yano/fzf-preview.vim)というさらに機能面に秀でたオールインワン版もあるが、あくまで僕はサブ武器的文脈に従ってfzf.vimの調整に留めている。

```toml
#dein.toml
[[plugins]]
 repo = 'junegunn/fzf'
 merged = 0
 build = '''
 ./install --all
'''

[[plugins]]
 repo = 'junegunn/fzf.vim'
 hook_add = '''
 nnoremap <silent> <Leader>. :<C-u>FZFFileList<CR>
 nnoremap <silent> <Leader>, :<C-u>FZFMru<CR>
 nnoremap <silent> <Leader>l :<C-u>Lines<CR>
 nnoremap <silent> <Leader>b :<C-u>Buffers<CR>
 nnoremap <silent> <Leader>k :<C-u>Rg<CR>
 command! FZFFileList call fzf#run({
            \ 'source': 'rg --files --hidden',
            \ 'sink': 'e',
            \ 'options': '-m --border=none',
            \ 'down': '20%'})
 command! FZFMru call fzf#run({
            \ 'source': v:oldfiles,
            \ 'sink': 'e',
            \ 'options': '-m +s --border=none',
            \ 'down':  '20%'})

 let g:fzf_layout = {'up':'~90%', 'window': { 'width': 0.8, 'height': 0.8,'yoffset':0.5,'xoffset': 0.5, 'border': 'none' } }

 augroup vimrc_fzf
 autocmd!
 autocmd FileType fzf tnoremap <silent> <buffer> <Esc> <C-g>
 autocmd FileType fzf set laststatus=0 noshowmode noruler
      \| autocmd BufLeave <buffer> set laststatus=2 noshowmode ruler
 augroup END

 function! RipgrepFzf(query, fullscreen)
    let command_fmt = 'rg --column --hiddden --line-number --no-heading --color=always --smart-case %s || true'
    let initial_command = printf(command_fmt, shellescape(a:query))
    let reload_command = printf(command_fmt, '{q}')
    let spec = {'options': ['--phony', '--query', a:query, '--bind', 'change:reload:'.reload_command]}
    call fzf#vim#grep(initial_command, 1, fzf#vim#with_preview(spec), a:fullscreen)
 endfunction

 command! -nargs=* -bang RG call RipgrepFzf(<q-args>, <bang>0)
'''
```

![](/img/54.png)

そうすると、こんな感じのセレクタを下から生やせる。たとえ候補が30万件あっても重さを一切知覚させないのは頼もしい。当初はTab補完が欲しいと考えもしたがそこはやはり天下のfzf。期待以上に雑なタイプで目当てのファイルを引っかけられるため特に必要なかった。よって、このケースでのTabキーは複数選択にあてがわれている。なお、LinesとRgコマンドはプレビューの必要性からfloating windowで表示させている。

極めつけはBuffersソースの存在だ。以前の僕はタブで管理をやりくりしようと考えていたが、バッファを明瞭に一覧化できるのならあえて依存せずともよい。表示したい箇所のテキストが予め分かっていればLinesソースを駆使して瞬時にジャンプすることもできる。

![](/img/79.gif)

## トラブルシューティング（順次追記）
**Q1.** 遅延読み込みさせているプラグインが動かない。  
**A1.** init.vimや.vimrcに遅延読み込みの記述をしていない可能性がある。

```vim
 #init.vim
 " .tomlファイルの場所
  let s:rc_dir = expand('~/.config/nvim/')
  if !isdirectory(s:rc_dir)
    call mkdir(s:rc_dir, 'p')
  endif
  let s:toml = s:rc_dir . '/dein.toml'
  let s:lazy_toml = s:rc_dir . '/dein_lazy.toml'

 " .tomlファイルを読み込む
 call dein#load_toml(s:toml, {'lazy': 0})
 call dein#load_toml(s:lazy_toml, {'lazy': 1})
```
上記の例の通り`lazy`が1に設定されていないtomlファイルは遅延読み込みを行わない。また、遅延読み込みが無効のtomlファイルで`hook_source`のようなオプションを記述しても、プラグインは起動しない。

**Q2.** Language Serverの導入・削除方法が分からない。  
**A2.** 基本的には`:MasonInstall LSの名称`でインストールされる。たとえば`:MasonInstall gopls`でGoのLanguage Serverが入る。逆に削除したい時は`MasonUninstall LSの名称`で行える。`MasonUninstallAll`ですべてのLSを一括して削除することもできる。

**Q3.** tomlファイルにLuaの記述を加えたらむっちゃ怒られた。  
**A3.** ほとんどの場合はEOFのインデントをミスっている。余計なスペースを削って行頭に置くと直る。

## おわりに
本件に伴ってプラグインの整理や管理方法の改善を実施した結果、時には300ms近くかかっていたNeovimの起動速度が100ms程度まで減少した。人間の単純反応速度に近い値なのでなかなか悪くないと思う。あえてオールインワン系の仕組みから一旦距離をとってみると、自分が真に必要としている機能が判ってくる。この考え方はVimのみならず、VSCodeやその他ツールを設定する上でもなにかと役に立つ。

ひとまずサブ武器としてのVimを錬成したところで、以降はより実戦に適した形状に刃先を尖らせていくことになる。だが、サブ武器だからといって戦闘能力が低いとは限らない。世界観によってはむしろ短剣類の方がハマれば高威力だったりする。僕にとってのVimもそのようなものだと信じている。

## 参考文献
[ddc.vimのlsp機能を強くする with nvim-lsp](https://zenn.dev/matsui54/articles/2021-09-03-ddc-lsp)  
[Neovim builtin LSP設定入門](https://zenn.dev/nazo6/articles/c2f16b07798bab)
