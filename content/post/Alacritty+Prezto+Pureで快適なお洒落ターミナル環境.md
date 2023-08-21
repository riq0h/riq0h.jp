---
title: "Alacritty+Prezto+Pureで快適なお洒落ターミナル環境"
date: 2021-03-22T20:13:20+09:00
draft: false
tags: ["tech"]
---
![](/img/06.png)
## 経緯
ターミナル周りのことであれこれと試行錯誤していたのも今は昔。近頃はKDEを入れるついでに[Konsole](https://konsole.kde.org/)も追加しておく手癖が身についてしまい、気が付けば最近のターミナル事情にすっかり疎くなっていた。Linuxはもともとターミナル文化が根強かったせいか、今さら新顔が幅を利かせる余地などないとたかをくくっていたのかもしれない。

聞けば[Alacritty](https://github.com/alacritty/alacritty)というターミナルエミュレータがミニマルで快適だという。なにげにマルチプラットフォーム対応でWindows版もリリースされている。設定はテキストファイルのみで行うので煩雑なメニュー画面に惑わされることもない……なるほど、なかなか良さそうじゃないか。

むろん、欠点もなくはない。Pros/Consで表すと以下の通りになる。

**Pros**  
・Rust製かつGPU支援が実装されているため動作が軽快  
・マルチプラットフォーム対応  
・設定をテキストファイルに記述する形で行う

**Cons**  
・環境によってはフルインストールにビルドを要する  
・スクロールバーはない  
・タブもない  
~~・日本語のインライン入力は現状サポートされていない~~ 0.11.0で対応した。fcitxユーザは「アドオン」→「X Input Method フロントエンド」→「XIMでOn The Spotスタイルを使う」を有効化しておく必要がある。

書いておいてなんだが、こうして一覧にしてみるとけっこう人を選びそうな気もする。しかし動作が軽快なのは想像以上に本当の話で、僕程度のカジュアルな使い方でも十分に効能を実感できたほどだ。ビルドに関しては一度慣れてしまえばどうということはないし、タブ機能もtmuxを駆使すればおおよそ問題ない。インライン入力はそのうち何とかしてほしい。

## Alacrittyの導入方法（Linux）
ここにちょっと面倒なところがある。Arch Linuxなど特別な仕様のリポジトリを持っているディストリビューションはともかく、他の環境では自らビルドを行わなければならない。以下にその手順を示す。

```shell
#リポジトリをクローンしてから当該フォルダに移動する
$ git clone https://github.com/alacritty/alacritty.git
$ cd alacritty

#ビルドに必要なrustupとcargoを導入する。
$ curl https://sh.rustup.rs -sSf | sh

#コンパイラの設定を行う。rustupが働かない場合はOSを再起動する。
$ rustup override set stable
$ rustup update stable

#ビルド開始。コーヒーを淹れて飲み干すくらい時間がかかった。
$ cargo build --release

#Alacrittyの情報をシステムに登録する。
$ sudo cp target/release/alacritty /usr/local/bin
$ sudo cp extra/logo/alacritty-term.svg /usr/share/pixmaps/Alacritty.svg
$ sudo desktop-file-install extra/linux/Alacritty.desktop
$ sudo update-desktop-database

#Alacrittyのmanualを登録する。
$ sudo mkdir -p /usr/local/share/man/man1 gzip -c extra/alacritty.man | sudo tee /usr/local/share/man/man1/alacritty.1.gz > /dev/null
```

## Alacrittyの導入方法（Windows）
想定環境はWindows10。本項ではPowerShellと[Scoop](https://scoop.sh/)を使用する。

```shell
#PowerShellに実行許可を与える。
PS> set-executionpolicy remotesigned -scope currentuser

#Scoopの導入を行う。
PS> Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://get.scoop.sh')

#導入したScoopを用いてAlacrittyと推奨パッケージを入手する。
PS> scoop bucket add extras
PS> scoop install alacritty
PS> scoop install extras/vcredist2017
```

## Alacrittyの設定
Linuxは`~/.config/alacritty/alacritty.yml`、  
Windowsは`/%APPDATA%/Roaming/Alacritty/alacritty.yml` に設定ファイルを置く仕組みになっている。設定例の一つとして僕のファイルを下記に掲載する。

```yaml
# シェル
shell:
  program: /usr/bin/zsh
  args:
    - --login

# カーソル
cursor:
  style:
    shape: Underline 
    blinking: Always
  unfocused_hollow: false
  blink_interval: 470

# タブスペース
tabspaces: 4

# ウインドウ
window:
  opacity: 0.95
  padding:
   x: 0
   y: 0
  dynamic_padding: false

# フォント
font:
  size: 13
  normal:
    family: 'UDEV Gothic 35NFLG'
    style: Regular
  bold:
    family: 'UDEV Gothic 35NFLG'
    style: Bold
  italic:
    family: 'UDEV Gothic 35NFLG'
    style: Italic
  bold_italic:
    family: 'UDEV Gothic 35NFLG'
    style: Bold Italic

# 環境変数
env:
  TERM: alacritty

# Colors (Horizon Dark)
colors:
  # Primary colors
  primary:
    background: '0x1c1e26'
    foreground: '0xe0e0e0'

  # Cursor
  cursor:
    cursor: '0x00ff00'
  vi_mode_cursor:
    cursor: '0x00ff00'

  # Normal colors
  normal:
    black: '0x16161c'
    red: '0xe95678'
    green: '0x29d398'
    yellow: '0xfab795'
    blue: '0x26bbd9'
    magenta: '0xee64ac'
    cyan: '0x59e1e3'
    white: '0xd5d8da'

  # Bright colors
  bright:
    black: '0x5b5858'
    red: '0xec6a88'
    green: '0x3fdaa4'
    yellow: '0xfbc3a7'
    blue: '0x3fc4de'
    magenta: '0xf075b5'
    cyan: '0x6be4e6'
    white: '0xd5d8da'
```

すべてのマシンで同一の設定ファイルを使い回すのはさすがに厳しかったので、HiDPIのラップトップではフォントを大きめにして、~~Windowsではフォントを[白源](https://qiita.com/tawara_/items/374f3ca0a386fab8b305)に変え（Rictyとの相性が悪いため）、~~ （追記：現在はUDEV Gothicというマジで神のフォントがあるため使い分ける必要がなくなった） シェルのパスをWSLに指定している。

Windows Terminalや、もっと以前のminttyも決して強い不満を抱くような代物ではなかったが、僕にはAlacrittyの方が性に合っていたらしい。

なお、Alacrittyのテーマは[ここ](https://github.com/eendroroy/alacritty-theme)からテキストをコピーする形で利用できる。探せば他にもあると思う。

## あれこれ気になりはじめた
改めてターミナル周りについて事細かに探っていると、関連した他の情報もおのずと目に入ってくる。聞けばzshにはいくつものフレームワークが存在しており、導入するだけで手堅くよしなに設定してくれるようだ。これまではoh-my-zshしか知らなかったが、[Prezto](https://github.com/sorin-ionescu/prezto)というフレームワークが簡便で良さそうだった。遠い昔に見様見真似で`.zshrc`をえいやとこしらえ、今の今まで特段の不自由なく使ってきた僕にとっては順当なアプローチに思える。

プロンプト部分も手動でガチャガチャやるよりも、フレームワークに付属するテーマの方がより洗練されているように感じた。特に[Pure](https://github.com/sindresorhus/pure)というプロンプトは一切の無駄がなく本当にミニマルで美しい。どこかの男性が人間と恋に落ちた時、僕はターミナルエミュレータのプロンプトに一目惚れしたのだ。

従前の手動プロンプト設定に取り入れていた情報（カレントディレクトリやSSH接続先の表示など）はしっかり網羅されており、PowerlineでおなじみのGitのステージング関係も控えめながら組み込まれている。その上でPreztoの強力な補完機能も得られる。すごい。

![](/img/07.png)
うーん、いい感じだ。  
紹介が済んだところでPreztoとPureを導入する手順を記していく。

```shell
#まずはPreztoを引っ張ってくる。
$ git clone --recursive https://github.com/sorin-ionescu/prezto.git "${ZDOTDIR:-$HOME}/.zprezto"

#シェルオプションを有効にする。
$ setopt EXTENDED_GLOB

#設定済みファイルのシンボリックリンクを張る。
$ for rcfile in "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/^README.md(.N); do
ln -s "$rcfile" "${ZDOTDIR:-$HOME}/.${rcfile:t}"
done
```
ここで一つ注意がある。既に`.zshrc`や`.zshenv`がホームディレクトリに置かれていた場合、当該のシンボリックリンクは当たり前だが作成されない。これをうっかり忘れてそのままだとPreztoが機能しないので`~/.zprezto/runcoms/`直下にある実体ファイルを参照しながら適宜修正するか、一旦、自前の設定ファイルを引っ込ませて、後で新しくできたファイルの方に設定を付け加えるかしよう。

とはいえ定番の機能はPreztoの方で一通り有効化されているため、結局はほとんどの記述を削除することになると思われる。僕の`.zshrc`も逆に心配になるくらいスカスカになってしまった。

正しく設定が読み込まれていれば、Alacrrityの再起動後に大きく外観が変わっているはずだ。初期設定ではsorinというテーマが適用されている。Preztoの設定は`~/.zpreztorc`の内容を書き換える形で変更する。例によって僕の設定ファイルを下記に掲載しておく。

```zsh
# 色彩
zstyle ':prezto:*:*' color 'yes'

# プリロード
zstyle ':prezto:load' pmodule \
  'archive' \
  'environment' \
  'terminal' \
  'editor' \
  'history' \
  'directory' \
  'spectrum' \
  'utility' \
  'completion' \
  'syntax-highlighting' \
  'history-substring-search' \
  'prompt'

# キーマップ
zstyle ':prezto:module:editor' key-bindings 'emacs'

# テーマ
zstyle ':prezto:module:prompt' theme 'pure'

# ハイライト
zstyle ':prezto:module:syntax-highlighting' color 'yes'
zstyle ':prezto:module:syntax-highlighting' highlighters \
  'main' \
  'brackets' \
  'pattern'

# 途中まで打ったコマンドの履歴を検索
zstyle ':prezto:module:history-substring-search' case-sensitive 'yes'
zstyle ':prezto:module:history-substring-search' color 'yes'
zstyle ':prezto:module:history-substring-search:color' found ''
zstyle ':prezto:module:history-substring-search:color' not-found ''
zstyle ':prezto:module:history-substring-search' globbing-flags ''
```
Pureの導入は設定例に従って名称を記述するだけで完了する。これだけの作業で快適なお洒落ターミナル環境が手に入ってしまうのだからすばらしい。

## その他（順次追記）
・tmuxでNeovimを開いた際にTrue Colorが無効になるエラーを修正する

```yml
#.alacritty.ymlに以下を追記
env:
    TERM: alacritty

#.tmux.confに以下を追記
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",$TERM:Tc"
set-option -sa terminal-overrides ',alacritty:RGB'

#init.vimに以下を追加
set termguicolors
let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"

#init.luaの場合
opt.termguicolors = true
```

## 既知の問題点（たぶん何かを見落としている）
~~・tmuxからdetachするとカーソルが点滅しなくなる~~ → そもそもdetatchしなくなった。  
~~・カーソルの色設定が反映されない~~ → 解決した。前述の設定ファイルに反映済み。  
~~・ウインドウサイズの設定が反映されない~~ → i3wmに移行したのでどうでもよくなった。  
~~・コマンド以外だとなんでも下線が付くところがちょっと気に入らない~~ → 有効なPATHになっているか分かるのでむしろ気に入った。  

たまには実用的な記事を書くのも楽しいが、ポエム的な文章表現を自重することがとても難しい。
