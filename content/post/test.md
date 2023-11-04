---
title: "とりあえずnone-ls.nvimでよくないか？ / null-ls.nvimの保守的代替"
date: 2023-11-05T08:27:28+09:00
draft: true
tags: ['tech']
---

夏真っ盛りのある日、Neovimの超有名プラグインが爆発四散した。[null-ls.nvim](https://github.com/jose-elias-alvarez/null-ls.nvim)はLSPの規格に合わないLinterやFormatterをLSのように機能させられる画期的なクライアントだった。ほぼコピペの設定で完結する簡便さは同プラグインを事実上のデファクトスタンダードの座に押し上げた。

しかし、そんな圧倒的権勢を誇るプラグインは驚くべきことにたった一人の開発者によって維持されていた。あまりの多忙さゆえ彼がギブアップを宣言した瞬間、null-ls.nvimのリポジトリはたちまちアーカイブせしめられ、我々は事態を否が応にでも悟らざるをえなくなった。貢献に相応しい報酬を受け取れないのは誠に遺憾ながらOSS開発の常である。

さて、こうして一つの歴史が終焉を迎えた。Neovim本体のアップデートや環境の変化次第でnull-ls.nvimは早晩動かなくなるだろう。かつてのユーザたちはさっそく動きはじめた。僕の周りでは競合プラグインの[efm-langserver](https://github.com/mattn/efm-langserver)に乗り換える者が多い。あるいは、まったく別の新しいプラグインを試す者もいた。

かくいう僕はならばいっそクライアント自体を捨ててマニュアルセットアップだ、と意気込んで個別導入を試みていた。たとえば[prettier.nvim](https://github.com/MunifTanjim/prettier.nvim)などをそれぞれインストールして、対応するキーバインドを設定していくのだ。こうすれば新しいクライアントの作法や設定ファイルの書き方を覚える必要なく、とりあえず任意のLinterやFormatterを動かせる。実際、動くは動く。だがそれらは一つや二つでは済まない。数が増えれば増えるほど面倒くさくなる。

考えるまでもなく当たり前だ。そもそもそれらすべてが単独のプラグインとして存在しているのかも定かではない。だからこそnull-ls.nvimやefm-langserverといったアプローチが生まれたのだった。然らば、やはり重い腰をあげて生き残っている方の作法を学ばなければならないか……？　そう思っていたところへ、吉報が降って湧いた。[none-ls.nvim](https://github.com/nvimtools/none-ls.nvim)だ。なんでもnull-ls.nvimをコミュニティベースで保守的に維持していくという。リポジトリには以下の説明が記されている。

>**none-ls.nvim**  
>null-ls.nvim Reloaded, maintained by the community.  
>Only the repo name is changed for compatibility concerns. All the API and future changes will keep in place as-is.  

本当だろうな？　やる気があったら100行だって設定を書き換えるが、そうでない時は一文字たりとも変えたくない僕のいい加減さをなめるなよ。残念だが今はだいぶ後者寄りだ。そう疑いつつも以前のnull-ls.nvimの設定をそのままに、説明通りにリポジトリの名前だけ変えて再導入したところ、**マジで完璧に動いた。** どうやら看板に偽りなく、ほとんど中身をいじっていないようだ。

とはいえアーカイブされて座して死を待つのみとなったプラグインと、コミュニティで維持していくと明言されているプラグインでは、中身が同じでも将来性には雲泥の差がある。そのうち`:%s/null-ls/none-ls/cg`とかで変数の書き換えぐらいはするのかもしれないが、やる気がない寄りでもその程度ならかろうじてできなくはない。

実際に数日使ってみて、なんら不具合が起きないことを確認した。下記の通り、既存の設定で完全に動作している。null-ls.nvimにLinterやFormatterのインストールオプションを付与する[mason-null-ls.nvim](https://github.com/jay-babu/mason-null-ls.nvim)も問題なく動く。null-ls.nvimの実質的な存続が決まったからにはこれらの連携プラグインも当面は廃止されないだろう。

```lua
--none-ls.nvim

require("mason-null-ls").setup({
    ensure_installed = { 'prettierd', 'rubocop', 'black', 'goimports' },
    handlers = {},
})

local status, null_ls = pcall(require, 'null-ls')
if (not status) then return end

null_ls.setup({
    sources = {
        null_ls.builtins.formatting.prettierd,
        null_ls.builtins.diagnostics.rubocop,
        null_ls.builtins.formatting.rubocop,
        null_ls.builtins.formatting.black,
        null_ls.builtins.formatting.goimports,
    },
    debug = false,
})

vim.keymap.set('n', '<leader>p', function() vim.lsp.buf.format { async = true } end)
vim.keymap.set('v', '<leader>p', function() vim.lsp.buf.format { async = true } end)
```

efm-langserverに無事移行できたモチベ神の方々はともかく、現状あまりテンションが上がりきっていない我々はとりあえずnone-ls.nvimでよくないか？　すでにあらかたの機能は揃っているゆえ目新しいものに飛びつく必要性も特にない。数年先の話は判らないけども、その時はその時で設定を100行ぐらい書き換えてやってもいい気分がどこからか生えてきているんじゃないか。


![](/img/221.gif)

ところで、忘れちゃいけないのが[fidget.nvim](https://github.com/j-hui/fidget.nvim)のアニメーションだ。やっぱりこいつがいないと画面が締まらない。
