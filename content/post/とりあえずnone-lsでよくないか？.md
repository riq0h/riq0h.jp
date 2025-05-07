---
title: "とりあえずnone-ls.nvimでよくないか？ / null-ls.nvimの保守的代替"
date: 2023-11-05T08:56:28+09:00
draft: false
tags: ["tech"]
---

夏真っ盛りのある日、Neovimの超有名プラグインが爆発四散した。[null-ls.nvim](https://github.com/jose-elias-alvarez/null-ls.nvim)はLSPの規格に合わないLinterやFormatterを言語サーバのように動作させられる画期的なクライアントだった。ほぼコピペの設定で完結する簡便さは同プラグインを事実上のデファクトスタンダードの座に押し上げた。

しかし、そんな圧倒的権勢を誇るプラグインは驚くべきことにたった一人の開発者によって維持されていた。極度の多忙さゆえ彼がギブアップを宣言した瞬間、null-ls.nvimのリポジトリはたちまちアーカイブせしめられ、我々は否が応にでも事態を悟らざるをえなくなった。貢献に相応しい報酬を受け取れないのは誠に遺憾ながらOSS開発の宿痾である。

さて、こうして一つの偉大な仕事が終焉を迎えた。Neovim本体のアップデートや環境の変化次第でnull-ls.nvimは早晩動かなくなるだろう。ユーザたちは移行作業に取り掛かりはじめた。僕の周りでは競合プラグインの[efm-langserver](https://github.com/mattn/efm-langserver)に乗り換える者が多い。あるいは、まったく別の新しいプラグインを試す者もいた。

かくいう僕もならばいっそマニュアルセットアップだ、と柄にもなく個別導入を試みていた。たとえば[prettier.nvim](https://github.com/MunifTanjim/prettier.nvim)などをそれぞれインストールして、対応するキーマップを設定していくのだ。こうすれば新しいクライアントの作法を覚える必要なく任意のLinterやFormatterを動かせる。だが、もちろんそれらは一つや二つでは済まない。数が増えれば増えるほど面倒くさくなる。

考えるまでもなく当たり前だ。そもそもそれらすべてが単独のプラグインとして存在しているのかも定かではない。だからこそnull-ls.nvimやefm-langserverといったアプローチが生まれたのだった。然らば、やはり重い腰をあげて設定ファイルを増やさなければならないか……？　そう思っていたところへ、吉報が降って湧いた。[none-ls.nvim](https://github.com/nvimtools/none-ls.nvim)の登場だ。なんでもnull-ls.nvimをコミュニティベースで保守的に維持していくという。リポジトリには以下の説明が記されている。

> **none-ls.nvim**  
> null-ls.nvim Reloaded, maintained by the community.  
> Only the repo name is changed for compatibility concerns. All the API and future changes will keep in place as-is.

本当だろうな？　やる気があったら100行だって設定を書き換えるが、そうでない時は一文字たりとも変えたくない僕のいい加減さをなめるなよ。残念だが無駄な試行錯誤を経た今はだいぶ後者寄りだ。そう疑いつつ以前のnull-ls.nvimの設定はそのままに、リポジトリの名前だけ変えて再導入したところ、**マジで完璧に動いた。** どうやら看板に偽りはないようだ。

アーカイブされて座して死を待つのみとなったプラグインと、コミュニティで維持していくと明言されているプラグインとでは、中身が同じでも将来性には雲泥の差がある。そのうち`:%s/null_ls/none_ls/g`とかで定義の書き換えぐらいはするのかもしれないが、やる気がない寄りでもその程度ならギリできなくはない。

実際に数日使ってみて、なんら不具合が起きないことを確認した。下記の通り、既存の設定で完全に動作している。null-ls.nvimに[mason.nvim](https://github.com/williamboman/mason.nvim)由来の管理機能を付与する[mason-null-ls.nvim](https://github.com/jay-babu/mason-null-ls.nvim)も問題なく動く。本体の実質的な存続が決まったからにはこれらの連携プラグインも当面は廃止されないだろう。

```lua
--none-ls.nvim

require('mason-null-ls').setup({
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
```

efm-langserverに無事移行できたモチベPro Maxな方々はともかく、現状あまりテンションがアガっていない我々はとりあえずnone-ls.nvimでよくないか？　すでに大方の機能は揃っているゆえ他の目新しいプラグインに飛びつく必要性も特にない。数年先の話は判らないけども、その時はその時で設定を100行ぐらい書き換えてやってもいい気分がどこからか生えてきているんじゃないか。

![](/img/221.gif)

ところで、忘れちゃいけないのが[fidget.nvim](https://github.com/j-hui/fidget.nvim)のアニメーションだ。やっぱりこいつがいないと画面が締まらない。
