---
title: "fzfと仲良く"
date: 2023-11-25T18:20:17+09:00
draft: true
tags: ['tech']
---

日々、Telescopeを通してfzfとよろしくやっているが、そういえばそもそもこれはターミナル上で使う代物だったはずだ。そこへいくと僕の.zshrcに記されたfzfのオプションはいかにも心もとない。たぶん最初にfzfを導入した時の試し方が悪かったのだろう。今から言うことはちょっと気が早い人たちの一部には心当たりがあるかもしれない。

fzfをインストールした状態で、おもむろに`fzf`と打つ。すると、なにやら軽快なアニメーションが働いてパァーッとファイルの一覧が表示される。ウオーッ、なんだかすごそうだ、選択したら一体どうなるんだ、と期待に胸を膨らませて任意のファイルを選ぶと……そのファイル名がターミナル上に標準出力される。

![]

OK、他には？　もちろんあるにはあるが、まったくの事前知識なしでそれを知るのは難しい。実際、なんか話題だしとりあえず触ってみるか程度のモチベではパイプで繋げて処理をどうこうする、なんていうのもネットに転がっている例をコピペして試して終わりが関の山だった。以来、僕にとってfzfとは「便利なVimプラグインを使うために必要なもの」という認識で止まっていた。

しかしそんな日も今週で終わりである。かびの生えた`.zshrc`を棚卸しして当たり前にfzfを使う時が来たのだ。いくらなんでも最初に触ってから5年以上も無視していたのは薄情が過ぎる気がしているが、今から5年後にはいっぱしのfzfプロフェッショナルになっていると考えれば遅きに逸したとは思わない。まずは基本的なところから学んでいく。


## 組み込みショートカットキーを覚える
実はfzfには組み込みのショートカットが存在しており、初回セットアップ時に適用の可否を尋ねられるらしい。そうだったっけ？　僕の`.zshrc`にそれがないということは適用しなかったか、一度した後でよく判らずに消してしまったのだろう。なんにせよまずはそいつを使ってみないと始まらない。さっそく当該のスクリプトの場所を探り当てて設定に反映させる。

```zsh
[ -f /usr/share/fzf/key-bindings.zsh ] && source /usr/share/fzf/key-bindings.zsh
[ -f /usr/share/fzf/completion.zsh ] && source /usr/share/fzf/completion.zsh
```

なお、このディレクトリの位置は環境次第で異なる場合がある。Ubuntu環境では`/usr/share/doc/fzf/examples/`にそれぞれのファイルが置かれていた。無事に読み込みが終わると、3つのショートカットが発動可能になっている。1つ目のCTRL+Tは最初に見せたファイルの標準出力なので、まあ一見してすぐに便利とは感じられない。

一方、他の2つはなかなかすごい。CTRL+Rは今までに打ったコマンドの履歴を検索してくれる。誰しも「このコマンドってどう使うんだっけ……」といった経験を一度ならず200回以上はしていると思われるが、こいつがあれば一部を覚えているだけで即詠唱できる。上矢印で順々に履歴を戻っていったり、タブの補完機能に期待を託すよりよっぽど確実なソリューションに違いない。

![]()

もう一つはALT+Cで呼び出せる。cdで飛びたい場所を検索して選べる機能だ。もう二度とタブを連打しまくって行きたいディレクトリのパスが完全に補完される日を待ちわびなくていい。大抵は行き先のディレクトリ名を一部入力すれば上位候補に昇ってくる。検索できると嬉しいことって意外に身近にあったんだなと気付かされた。

![]()

これらをいい感じに表示せしめるには当然、`.zshrc`にてそれぞれの設定が必要である。たとえば上の2つがなんだか浮いているように見えるのは決して目の錯覚ではなく、`tmux-fzf`というtmuxの表示形式を利用するコマンドでポップアップ表示させているためだ。視線を中央に固定できるので思った以上に体験が良い。以下に設定例を記す。

```zsh
export FZF_TMUX="1"
export FZF_TMUX_OPTS="-p 50%"
export FZF_CTRL_R_OPTS="--reverse --preview 'echo {}' --preview-window=border-sharp,down:3:hidden:wrap --bind '?:toggle-preview'"
export FZF_DEFAULT_COMMAND="rg --files --hidden 2> /dev/null --follow --glob '!.git/*'"
export FZF_DEFAULT_OPTS="--ansi --no-separator --no-scrollbar --reverse --border=none \
--color=bg+:#1c1e26,bg:#1c1e26,spinner:#ee64ac,hl:#e95678 \
--color=fg:#d5d8da,header:#e95678,info:#e95678,pointer:#ee64ac \
--color=marker:#ee64ac,fg+:#d5d8da,prompt:#e95678,hl+:#e95678"
export FZF_CTRL_T_COMMAND="rg --files --hidden 2> /dev/null --follow --glob '!.git/*'"
export FZF_CTRL_T_OPTS="--preview 'bat  --color=always --style=plain --line-range :100 {}' --preview-window=border-sharp,right:60%"
export FZF_ALT_C_COMMAND="fd -t d --hidden"
export FZF_ALT_C_OPTS="--preview 'eza {} -h -T -F --no-user --no-time --no-filesize --no-permissions --long | head -200' --preview-window=border-sharp,hidden:right:60% --bind '?:toggle-preview'"
export RUNEWIDTH_EASTASIAN=0
bindkey "^[t" fzf-file-widget
bindkey "^[r" fzf-history-widget
bindkey -r "^T"
bindkey -r "^R"
```

個人的なこだわりとして、いくつかのコマンドでは`--preview`を有効にした上でtoggleで表示・非表示を切り替えられるようにしてある。また、なるべくUIを簡素に保つべく外側は`--border=none`で、内側は`--preview-window=sharp`に設定している。他にも`--hidden`で隠しファイルの検索を有効化していると出るパーミッションエラーを`2> /dev/null`で握り潰している。色の設定はターミナルのカラースキームとだいたい合わせた。

最後に、ショートカットキーのバインドを変えている。僕の中ではウインドウマネージャの操作がMetaキー、ターミナルはAltキー、VimはCtrlキーと決まっているのでその理屈に沿わせた格好だ。大量のショートカットキーを覚えるのは確かに楽ではないが、操作の起点が明確に区別されているとだいぶ掴みやすい。

## 関数を.zshrcに埋め込んで使う
さて、ターミナルで行う作業の中でも極めて重要な二つがもはや効率化されてしまったわけだが、fzfは渡された条件に基づいてあいまい検索を実行するソフトウェアなので応用の幅はかなり広い。公式のWikiから拝借してきたものをいくつか紹介したい。

![]()
```zsh
fv() {
  IFS=$'\n' files=($(fzf-tmux -p 50% --preview 'bat  --color=always --style=plain {}' --preview-window=border-sharp,right:60% --query="$1" --multi --select-1 --exit-0))
  [[ -n "$files" ]] && ${EDITOR:-vim} "${files[@]}"
  zsh
}
```

元は`fe`という名前の関数だったが打ちやすい名前に変えた。検索したディレクトリを



