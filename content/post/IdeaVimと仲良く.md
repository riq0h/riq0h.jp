---
title: "IdeaVimと仲良く"
date: 2024-05-05T20:46:56+09:00
draft: false
tags: ["tech"]
---

![](/img/269.png)

フレームワークを用いたJavaの開発案件をVimのみでこなすのは少々厳しい **（いや、こうすればうまくやれるとの案があれば教えてほしい！ 切実に！）** ので、IntelliJ IDEAにIdeaVimを入れてなんとかする。文脈から明らかな通り、IdeaVimとはVimっぽい操作体系を実現するためのプラグインである。

とはいえこれでVimの操作感を十分にエミュレートできるのか、と言われればやはり難しい。そもそも「Vimの操作感」とはVim単体のみならずプラグイン群と独自の設定を含めた個々人に固有の環境を指すため、他のソフトウェアがどんなに頑張ったところで**VimでなければVimではない**というのが正直な感想だ。しかし僕はプロのグラマーであり、過度の公私混同はプロフェッショナルに反する。

であればVimの完全なエミュレートは無理にせよ、わずかでも操作感が改善されるのなら取り入れない手はない。幸いにもIdeaVimの歴史は長く、メンテナンス体制は盤石に見える。多少の投資をしても決して無駄にはならないだろう。そんなわけで僕はIdeaVimの設定を模索する形と相成った。


## ショートカットをVimに優先させる
IdeaVimを導入すると設定欄に「Vim」という項目が生える。ここでショートカットの優先を設定する。たとえば`Ctrl+V`は標準の動作ではペーストになっているが、Vimを優先すると皆さんもご存知のV-BLOCKにキーマップが変わる。同様に、`Ctrl+A`や`Ctrl+X`は数値のインクリメントとデクリメントに置き換わる。

使いはじめでどのキーマップが競合しているか分からない場合でも、有効なショートカットを押下すると標準とVimのどちらを優先するかポップアップ形式で尋ねてくれる。無理にすべての項目を定める必要はない。普通にコーディングしていればいつか良い感じに仕上がるだろう。


## .ideavimrcを作る
ホームディレクトリ直下に`.ideavimrc`との名称でファイルを作り、そこにVimと同様の設定を書くと読み込んでくれる。ただし、Luaでの記述には対応しておらず、当然ながらVimプラグインの導入はほぼ不可能である。IdeaVimに元から埋め込まれているか、あるいは別途プラグインとして提供されているものに限り、特殊な記法を用いて有効化できる。

```vim
set surround
set commentary
set ideajoin
set highlightedyank
set easymotion
```

ある程度の訓練を積んだVimmerなら、これらのプラグインの名称にかなり見覚えがあるのではないかと思う。今となっては少々古い部類に属するものの、`surround`や`commentary`、`easymotion`はかつて大半のユーザが盛んに取り入れていたプラグインだ。本音を言えば[vim-sandwich](https://github.com/machakann/vim-sandwich)とかの方がありがたかったがないよりはずっと良い。

もちろん、通常のVimと同じくキーマップも行える。記述していないものに関してはデフォルトのキーマップが適用される。たとえばタブ間の移動は`gt`で行える。一例を以下に示した。

```vim
set clipboard+=unnamedplus
set incsearch
let mapleader=" "
nnoremap <leader><leader>r :<C-u>source ~/.ideavimrc<CR>
nnoremap ew :<C-u>w<CR>
nnoremap eq :<C-u>wq<CR>
nnoremap Q :<C-u>quit!<CR>
nnoremap <C-s> :<C-u>%s///cg<left><left><left><left>
nnoremap k gk
nnoremap j gj
nnoremap <UP> gk
nnoremap <DOWN> gj
nnoremap O :<C-u>call append(expand('.'), '')<CR>j
nnoremap p ]p
nnoremap P ]P
nnoremap ]p p
nnoremap ]P P
```

もしかすると中には受け付けないキーマップも存在するのかもしれないが、現状はさほど違和感なく操作できている。「とりあえずVimっぽく動ければ」というところまでハードルを下げられるのなら応分のクオリティには達していると感じた。


## IntelliJ特有の設定
`.ideavimrc`にIntelliJ IDEA本体のショートカットを書くこともできる。プラグインがほとんど使えない以上、ファインダーやタスクランナーなどの諸機能を本体に務めさせなければ物足りない。これらの設定群は**Action List**と呼ばれ、[このページ](https://gist.github.com/zchee/9c78f91cc5ad771c1f5d)で一覧を読み取れる。

見ての通り、設定項目は非常に多い。どれがどんなふうにあると嬉しいのか把握するのは先週からいじりはじめた人間には極めて困難だ。さしあたり確実に使うであろう箇所を抜き出して`.ideavimrc`に転写した。皆さんの参考になると嬉しい。

```vim
nnoremap [m :<C-u>action MethodUp<CR>
nnoremap ]m :<C-u>action MethodDown<CR>
nnoremap [e :<C-u>action GotoPreviousError<CR>
nnoremap ]e :<C-u>action GotoNextError<CR>
nnoremap <leader>k :<C-u>action QuickJavaDoc<CR>
nnoremap <leader>d :<C-u>action Debug<CR>
nnoremap <leader>a :<C-u>action GotoAction<CR>
nnoremap <leader>G :<C-u>action Generate<CR>
nnoremap <leader>gn :<C-u>action NewClass<CR>
nnoremap <leader>go :<C-u>action OverrideMethods<CR>
nnoremap <leader>gc :<C-u>action GenerateConstructor<CR>
nnoremap <leader>gg :<C-u>action GenerateGetter<CR>
nnoremap <leader>gs :<C-u>action GenerateSetter<CR>
nnoremap <leader>ga :<C-u>action GenerateGetterAndSetter<CR>
nnoremap <leader>ge :<C-u>action GenerateEquals<CR>
nnoremap <leader>gt :<C-u>action GenerateTestMethod<CR>
nnoremap <leader>p :<C-u>action ReformatCode<CR>
nnoremap <leader>o :<C-u>action FileStructurePopup<CR>
nnoremap <leader>q :<C-u>action CloseContent<CR>
nnoremap <leader>Q :<C-u>action ReopenClosedTab<CR>
nnoremap <leader>e :<C-u>action SearchEverywhere<CR>
nnoremap <leader>f :<C-u>action GotoFile<CR>
nnoremap <leader>F :<C-u>action FindInPath<CR>
nnoremap <leader>s :<C-u>action GotoClass<CR>
nnoremap <leader>S :<C-u>action GotoSymbol<CR>
nnoremap <leader>t :<C-u>action ActivateTerminalToolWindow<CR>
nnoremap <leader>. :<C-u>action ActivateProjectToolWindow<CR>
nnoremap <leader>P :<C-u>action ManageRecentProjects<CR>
nnoremap <leader>; :<C-u>action ToggleLineBreakpoint<CR>
nnoremap <leader>j :<C-u>action Run<CR>
nnoremap <leader>w :<C-u>action HideAllWindows<CR>
```

特に末尾に注目してほしい。これはメインエディタ以外のすべてのウインドウ（ファイラやデバッグ画面など）を閉じるActionである。通常、VimはEscキーかToggleでそれらのウインドウを閉じられるが、IntelliJ IDEAはそういう作りにはなっていない。そこでやや強引ながらこのActionを代わりに利用させてもらっている。


## 総評
案外悪くはない。むしろ思った以上に良い。IDEというとなにかにつけて煩雑な印象を抱いていたが少なくともIntelliJ IDEAの新しいUIはVSCode程度には落ち着いている。自分なりに仕上げたVimに及ばないのは仕方がないとしても、デフォルトの操作体系に甘んじるよりははるかに生産性が向上した。これで起動速度が100msを切ってくれたらマジで完璧なんだけどな。
