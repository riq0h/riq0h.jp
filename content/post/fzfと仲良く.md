---
title: "fzfと仲良く"
date: 2023-11-26T20:47:17+09:00
draft: false
tags: ['tech']
---

言わずと知れたあいまい検索ツールfzf。日々、Vimを通してよろしくやってきた。しかし、元を正せばそもそもfzfはターミナル上で使う代物ではなかったか？　そこへいくと僕の`.zshrc`に記されしかの設定群はいかにも心もとない。たぶん最初の出会い方が悪かったのだろう。今から言う昔話はちょっと気が早い人たちには心当たりがあるかもしれない。

初めてfzfをインストールした状態で、おもむろに`fzf`と打つ。すると、なにやら景気よくパァーッとファイルの一覧が表示される。ウオーッ、なんだかすごそうだ、選択したら一体どうなるんだ、などと期待に胸を膨らませつつ任意のファイルを選ぶと……普通に相対パスが標準出力される。

![](/img/223.gif)

……OK、他には？　もちろん、ある――むしろ使い道は無限大――到底語り尽くせぬほど――とはいえ、まったくの事前知識なしでそれらを把握するのは難しい。実際、なんか話題だしとりあえず触ってみるか程度のモチベでは、ネットに転がっているコード片をコピペして試すのが関の山だった。以来、僕にとってfzfとは「便利なVimプラグインの中身」という認識に留まっていた。

だが、そんな日々も今週で終わりである。かびの生えた`.zshrc`を棚卸しして、当たり前にfzfを使う時が来たのだ。いくらなんでも最初に触ってから5年以上も放置していたのは薄情が過ぎる気がしているが、5年後にはいっぱしのfzfプロフェッショナルになっていると考えれば遅きに逸したとは思わない。まずは原点に立ち返って、じわじわと仲良くなっていく。

```zsh
#本稿で使用するツール類を導入する（Arch Linux）
paru -S fzf ripgrep bat fd eza tmux-plugin-manager
```


## 組み込みショートカットキーを覚える
実はfzfには組み込みのショートカットが存在しており、初回セットアップ時に適用の可否を尋ねられるらしい。そうだったっけ？　僕の`.zshrc`にそれがないということは適用しなかったか、一度した後でよく判らずに消してしまったのだろう。なんにせよまずはそいつを使ってみないと始まらない。さっそく当該のスクリプトの場所を探り当てて設定に反映させる。

```zsh
[ -f /usr/share/fzf/key-bindings.zsh ] && source /usr/share/fzf/key-bindings.zsh
[ -f /usr/share/fzf/completion.zsh ] && source /usr/share/fzf/completion.zsh
```

なお、このディレクトリの位置は環境次第で異なる。Ubuntu環境では`/usr/share/doc/fzf/examples/`以下にそれぞれのファイルが置かれていた。無事に読み込みが終わると、3つのショートカットが発動可能になっている。1つ目のCTRL+Tは最初に見せたファイル名の標準出力なので、一見してすぐに便利とは感じられない。

![](/img/224.gif)

一方、他の2つは直感的にすごい。CTRL+Rは過去のコマンド履歴を検索してくれる。誰しも「このコマンドってどう使うんだっけ……」といった経験を一度ならず200回以上はしているはずだが、これがあればおぼろげに覚えているだけで即詠唱できる。上矢印で順々に履歴を戻っていったり、Tabキーの補完機能に望みを託すよりよっぽど確実なソリューションと言える。

![](/img/225.gif)

2つ目はALT+Cで呼び出せる。cdで飛びたい場所を検索して選べる機能だ。もう二度とTabキーを連打しまくって行きたいディレクトリのパスが完全に補完される日を待ちわびなくていい。大抵は行き先のディレクトリ名を一部入力すれば上位候補に昇ってくる。

![](/img/226.gif)

なにげにオートコンプリート機能も実装されている。これらをいい感じに表示せしめるには当然、`.zshrc`にて各々の設定が必要となる。たとえば、一連のfzfがなんだか浮いているように見えるのは目の錯覚ではなく、tmuxの表示形式を利用する`fzf-tmux`コマンドでポップアップ出力させているためだ。目線を中央に固定できるので地味に体験が良い。以下に設定例を記す。

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

個人的なこだわりとして、いくつかのショートカットでは`--preview`を有効にした上で表示・非表示を切り替えられるようにしてある。また、UIを簡素に保つべく外側は`--border=none`で、内側は`--preview-window=sharp`に設定している。他にも`--hidden`で隠しファイルの検索を有効化していると出るパーミッションエラーを`2> /dev/null`で握り潰している。色の設定はターミナルのカラースキームとだいたい合わせた。

通常は絞り込みにRipgrepを用いているものの、`FZF_ALT_C_OPTS`、つまりAlt+Cの時はfdに変えている。Ripgrepの方には検索対象をディレクトリに限る設定が見つからなかった。単純な見落としの可能性大だがfdは`-t d`で簡単に指定できたので現状はこっちを選んでいる。

最後に、ショートカットキーのバインドを置き換えている。僕の世界観ではウインドウマネージャの操作をMetaキー、ターミナルはAltキー、VimはCtrlキーと決まっているのでその理屈に沿わせた格好だ。大量のショートカットキーを覚えるのは確かに楽ではないが、操作の起点が明確に区別されているとだいぶ掴みやすい。


## .zshrcにスクリプトを埋め込んで使う
さて、CLI操作の中でもっとも基本的な二つがもはや効率化されてしまったわけだが、fzfは渡された条件に基づいてあいまい検索を実行するツールなので応用の幅は極めて広い。公式Wikiから拝借してきた実践例を自分なりにいじってみたので紹介したい。

![](/img/227.gif)
```zsh
fv() {
  IFS=$'\n' files=($(fzf --height 50% --preview 'bat  --color=always --style=plain {}' --preview-window=border-sharp,right:60% --query="$1" --multi --select-1 --exit-0))
  [[ -n "$files" ]] && ${EDITOR:-vim} "${files[@]}"
  zsh
}
```

元は違う名前の関数だったが打ちやすくした。普段、Vimで暮らしている人たちはファイルもVimの中から開くと思われるが（僕もそう）一応入れておけばなにか御利益がありそうだ。主な変更箇所としてはプレビューを表示させているほか、このコマンドを打つとなぜか組み込みのショートカットが機能しなくなる問題に対処すべく最後に`zsh`で再読み込みをかけている。

![](/img/228.gif)
```zsh
fman() {
    man -k . | fzf --height 50% -q "$1" --prompt='man> '  --preview $'echo {} | tr -d \'()\' | awk \'{printf "%s ", $2} {print $1}\' | xargs -r man | col -bx | bat -l man -p --color always' --preview-window=border-sharp,right:60% --bind '?:toggle-preview' | tr -d '()' | awk '{printf "%s ", $2} {print $1}' | xargs -r man
}
export MANPAGER="sh -c 'col -bx | bat -l man -p --paging always'"
```

manを検索して表示する。いちいちググるよりmanを読む方がなんだかんだで手っ取り早かったりする。ちなみに`fv`もそうだが、これらのスクリプトに`fzf-tmux -p`を用いていない理由はVim上でポップアップさせたtmuxを通して実行する場合が多いからだ。ポップアップ出力はネストできないゆえエラーが起きてしまう。組み込みショートカットの方は内蔵機能なだけあって勝手に切り替わってくれる。

本稿では2つの例の紹介に留めるが、[公式Wiki](https://github.com/junegunn/fzf/wiki/Examples)にはまだまだ数多くの設定例が掲載されている。ぜひ参照されたし。個人的にはGitやDockerの操作を簡便化させるものが特に良さそうだと感じた。


## fzfを応用したtmuxの運用改善
たいへんややこしい名前だが[tmux-fzf](https://github.com/sainnhe/tmux-fzf)というtmuxプラグインが存在する。上に書いた`fzf-tmux`コマンドとは別物だ。しかしtmuxとfzfの利用が前提のプラグインなのでまずもって無関係ではない。ますますややこしい。簡単に説明すると、tmuxのsessionやwindowの管理をfzfで行うプラグインである。

![](/img/229.gif)
```ini
## TPM
set -g @plugin "sainnhe/tmux-fzf"
run -b "/usr/share/tmux-plugin-manager/tpm"
## tmux-fzf
TMUX_FZF_LAUNCH_KEY="a"
TMUX_FZF_OPTIONS="-p 20% --preview 'echo {}' --preview-window=border-sharp,hidden --bind '?:toggle-preview' --multi --ansi --no-separator --no-scrollbar --reverse --border=none \
--color=bg+:#1c1e26,bg:#1c1e26,spinner:#ee64ac,hl:#e95678 \
--color=fg:#d5d8da,header:#e95678,info:#e95678,pointer:#ee64ac \
--color=marker:#ee64ac,fg+:#d5d8da,prompt:#e95678,hl+:#e95678"
TMUX_FZF_PREVIEW=0
```

さらにややこしさに拍車をかけるのは、fzfのオプションを読み込んでくれないので`.tmux.conf`にわざわざ同じ内容のオプションを書き足さないといけないところだ。プラグインの導入にはPrefix+Iを押す。とはいえしかし、一度やってしまえば任意のショートカットでtmuxを一元管理する機能が手に入る。悪い話ではない。

たとえtmuxにかなり習熟していてもsessionの削除やリネームまでバインドしている人はあまり多くないだろう。すでに構築したショートカットの操作体系から漏れた、使う頻度の少ない領域をこのプラグインが補ってくれる。少なくとも僕は[Prezto](https://github.com/sorin-ionescu/prezto)の:module:tmux:auto-startとこれでtmuxの管理には困らなくなった。

## おわりに
本稿で紹介したfzfの機能はその筋のプロフェッショナルにしてみれば序の口もいいところに違いない。事実、僕のFFにはfzfと褥を共にして自作ツールまで拵えた異常者が何人かいる。僕自身も早くなにかに困ってそういう異常開発に手を出すモチベを醸成したいものだ。
