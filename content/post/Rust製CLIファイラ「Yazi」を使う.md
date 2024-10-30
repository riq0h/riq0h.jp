---
title: "Rust製CLIファイラ「Yazi」を使う"
date: 2024-10-29T20:19:09+09:00
draft: false
tags: ["tech"]
---

ターミナル上からすべてを操作したいと願う者にとって、ファイラは是非とも備えておきたい代物の一つである。いかに我々が小洒落た種々のランチャやコマンドで日常の用を足せるとしても、ファイラの機能性に助けられる機会は少なくない。そのたびに任意のGUIファイラを起動してマウスをポチポチとやるのは少々惜しい。

CLIのファイラはすでに色々ある。古くには[ranger](https://github.com/ranger/ranger)があるし、Goで書かれたミニマルな[lf](https://github.com/gokcehan/lf)というのもある。実際、後者の方をたまに使っていた。とはいえ、まあ、せっかくなので新しいものを試したい。そこで、今回は[Yazi](https://github.com/sxyazi/yazi)を選んだ。それにしても自分がRustを書いているわけじゃないのにRust製って言われたら気になってしまうのはなんでだろうね。マイナー界のミーハーかな。


## 導入
Arch Linuxなら`pacman -S yazi`で簡単に手に入る。macOSもbrewが使えるなら`brew install yazi`で入手可能だ。[公式ドキュメント](https://yazi-rs.github.io/docs/installation)では同時に`fd`や`fzf`などもインストールするように指南されているが、どうせ皆さんはとっくに入れていることだろう。対して、Ubuntuなどだと若干面倒くさい。公式リポジトリにパッケージが用意されていないのでCargo経由で導入する必要がある。

```zsh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup update
cargo install --locked yazi-fm yazi-cli
```

インストールを済ませてシェルを読み込み直すと`yazi`でファイラが立ち上がる。CLIファイラらしいVim-likeな操作体系はもとより、カスタマイズされたVim風のstatuslineが特徴的と言える。デフォルト設定ではここに容量や権限などファイルに関するあらゆる情報が集約される。


## 設定
各機能の概要は[ここ](https://yazi-rs.github.io/features)を観た方が早い。対応するアプリケーションの起動やファイルのコピー、リネームはもちろんのこと、先に挙げた他のCLIツールと連携した応用的な操作も行える。複数のファイル名を一括で編集できるバルクリネームも地味に便利だ。以前は[mmv](https://github.com/itchyny/mmv)を使っていたが、こっちにまとめられる見込みが高い。

一方、僕の感覚ではチカチカ光るstatuslineやカラースキームがやや疎ましい。幸いにもYaziはカスタマイズ性に長けているので、適宜自分好みに設定を加えて改良を施していく。このツールの設定ファイルには基本設定を司る`yazi.toml`と、外観を司る`theme.toml`、そして外部プラグインの読み込みと設定を担当する`init.lua`が存在する。他にキーマップを変更する`keymap.toml`もあるが、本稿では扱わない。

まず`~/.config/`に`yazi`というディレクトリを設ける。残念ながら勝手には作ってくれない。次にカラースキームを選ぶ。Yaziではflavorsと呼ばれており、[ここ](https://github.com/yazi-rs/flavors)から種類を確認できる。最近、僕はVimのカラースキームをeverforestに変えたので、こっちもそれに合わせておく。

```zsh
ya pack -a Chromium-3-Oxide/everforest-medium
```
```toml
#theme.toml
[flavor]
use = "everforest-medium"
```

切り替えてみると、なるほど確かにeverforestだ。しかし僕的にはファイラはもっと素朴な色合いにしたい。さっそく、追加の設定を書いて色数を削ぎ落としていく。修正にあたっては[公式ドキュメントの関連ページ](https://yazi-rs.github.io/docs/configuration/theme)を参考にした。

```toml
#theme.toml
[manager]
cwd = { fg = "green" }

[filetype]

rules = [
  { name = "*", fg = "white" }
]
```

これでファイルパスの色はおとなしめの緑色になり、ファイルの色は一律で単色に変わった。が、これだと今度はディレクトリとファイルの区別が付きにくい。かといってアイコンを表示させるとそこに再び色が付いてしまう。どうやらアイコンをすべて単色にしてくれる設定はないようだ。やむをえず正規表現を用いて全アイコンの`fg_dark`の値を`white`に置換した。

```vim
:%s/\(fg_dark\s*=\s*\)"\([^"]*\)"/\1"white"/g
```

すると、設定は以下の形式となる。

```toml
[icon]

globs = []
dirs  = [
  { name = ".config", text = "" },
  { name = ".git", text = "" },
  { name = "Desktop", text = "" },
  { name = "Development", text = "" },
  { name = "Documents", text = "" },
  { name = "Downloads", text = "" },
  { name = "Library", text = "" },
  { name = "Movies", text = "" },
  { name = "Music", text = "" },
  { name = "Pictures", text = "" },
  { name = "Public", text = "" },
  { name = "Videos", text = "" },
]
files = [
  { name = ".babelrc", text = "", fg_dark = "white", fg_light = "#666620" },
  { name = ".bash_profile", text = "", fg_dark = "white", fg_light = "#447028" },
  { name = ".bashrc", text = "", fg_dark = "white", fg_light = "#447028" },
# 以下、アイコンごとに類似の記述が延々と500行くらい続く
```

最後に、statuslineを消すプラグインを導入する。僕はVimでもstatuslineを消しているし、モード表示がなくてもなんとかなる形にしている。ファイル関連の情報も特に求めていない。外部プラグインの一覧は[ここ](https://github.com/yazi-rs/plugins/tree/main)から得られる。

```zsh
ya pack -a yazi-rs/plugins:no-status
```
```lua
--init.lua
require("no-status"):setup()
```

注意点として、上記の`init.lua`は導入したプラグインのディレクトリ内にある方ではなく`yazi`フォルダ直下に自ら作成した方を指している。記述後にYaziを起動するとプラグインの名称通りstatuslineが消えている。結果、僕にとってはまことに好ましいミニマルな外見と相成った。

![](/img/346.png)


## 総評
既存のファイラと比べて他のCLIツールとの連携に長けている印象を受けた。たとえばデフォルト設定で起動中にZキーを押すとfzfが立ち上がり、ファジーファインダー経由で目的のディレクトリに移動できる。移動後はファイラ特有の操作を引き続き行えるのでfzf単体よりも利便性が高い。同様に、fdやzoxideとの連携にも対応している。

この手のCLIツール群とファイラはしばしば対立的に扱われがちだが、Yaziの世界観においては両者がうまく融和できているように感じる。なにより、痒いところに手をサイボーグ化してでも届かせると言わんばかりの豊富なカスタマイズ性はターミナル世界の住民にとても馴染み深い。

こうしてターミナルの内側の世界が改善されるたび、新たに手にした道具でさらなる改善を推し進めんとして際限なく時間が投入されていく。なんらかの作業効率を上げるという本来の目的は忘れ去られ、あたかも辺境の惑星に残置された自動機械のごとく我々はひたすら環境を改善し続けるのだ。
