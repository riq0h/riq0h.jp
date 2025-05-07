---
title: "i3wmの紹介およびトラブルシューティング"
date: 2021-04-10T09:16:49+09:00
draft: false
tags: ["tech"]
---

本エントリでは僕がi3wmに移行してハマった箇所を簡潔なQ&A形式で記していく。必要に応じて随時追記が行われる。このトラブルシューティング集は備忘録を兼ねているため、いつもの冗長な文章表現は極限まで省略される。

i3wmに移行した理由はもともと周囲でよく話を聞いていたというのもあるが、コロナ禍により使い道を失っていたラップトップマシンを久しぶりに開き、予想以上にトラックパッドの操作性が悪いと気づかされたことに端緒を発する。僕のラップトップはX1 Carbonなのでトラックパッドのハードウェア的な分解能が特別に悪いわけではない。思えば、Macbookを使っていた時もトラックパッド操作はそんなに好きではなかった。

つまり、僕がラップトップを快適に使用するためには、キーボードで大半の操作を完結させられる特別な仕組みが求められた。言わずもがな、すぐにi3wmのことが頭をよぎった。i3wmはKDEやGnomeのようなデスクトップ環境を要せず動作するウインドウマネージャで、主な設定をテキストファイルで行う敷居の高さと引き換えにキーボードでの操作性が極限まで高められている。

通常、アプリケーションの起動にはデスクトップかドックに配置されたアイコンまでマウスを持っていき、ダブルクリックする形をとることが一般的だが、i3wm単体の環境では任意のショートカットキーか、もしくはコマンドラインランチャが用いられる。たとえば僕はmodキーとMキーを同時押しするとファイラが開くように設定している。

同様に、ウインドウのリサイズや位置の変更、他のワークスペースへの遷移などもすべてキーボード操作で行う。ウインドウは基本的に重ならず、自動的に並んで配置されることから[タイル型ウインドウマネージャ](https://ja.wikipedia.org/wiki/%E3%82%BF%E3%82%A4%E3%83%AB%E5%9E%8B%E3%82%A6%E3%82%A3%E3%83%B3%E3%83%89%E3%82%A6%E3%83%9E%E3%83%8D%E3%83%BC%E3%82%B8%E3%83%A3)と呼称されている。ディスプレイ領域が無駄にならないので一定の閲覧性を維持できる。以下は僕のデスクトップ画面。

![](/img/18.gif)

キーボード操作は慣れるまでは多少の苦痛を伴うが、一度ものにした際にもたらされる作業効率性は通常の環境の比ではない。移行してから日が浅い僕も既に実家のような安心感を得ている。

前置きはこの辺にして、さっそくトラブルシューティング集に移る。なお、[ArchWiki](https://wiki.archlinux.jp/index.php/I3)で既出の内容は割愛する場合がある。

## トラブルシューティング集

**Q1.i3wmをインストールしても起動しない、画面が正常に映らない。**

A1.Arch Linuxの初期状態から`xorg-server`、`xorg-init`、`i3-wm`、`lightdm`およびlightdmのログインスクリーンを表示させるgreeter、各々のマシンに適したビデオドライバをすべて導入していても画面が映らない場合は、最終手段として`plasma-meta`などのデスクトップ環境を導入して、一旦ログインしてからi3wmに切り替え、後でデスクトップ環境を削除する形をとるとうまくいくことがある。恐らくなんらかのパッケージが不足していたせいだと思われるが、特定が困難だったり面倒くさい時はこういう荒業もなしではない。

**Q2.ステータスバーに色々な情報を表示させたいが面倒ごとは避けたい。**

A2.bumblebee-statusを導入する。i3blocksやPolybarと異なりi3wmのconfig内で設定を完結させられ、簡単にPowerlineライクな表示が行える。下記の例では左から順にSpotifyの楽曲情報、接続しているWi-FiのSSID、音量、デスクトップ通知のトグルボタンおよび日付が、nord-powerlineというテーマに基づいて表示される。ただしこれでカッコよくなるのはstatusだけなのでワークスペース領域を含む左半分も仕上げたいなら別途作り込もう。

```bash
status_command /usr/bin/bumblebee-status -m spotify nic pasink pasource dunst datetime \
    -p spotify.layout="spotify.song" nic.format="{ssid}" datetime.format="%m/%d %H:%M" -t nord-powerline
```

**Q3.壁紙を設定したい。**

A3.fehを導入する。fehそのものは単純な画像ビューワだが、i3wmのconfigファイルに`exec --no-startup-id "feh --bg-scale ~/Wallpaper.png"`と記述すると、fehを用いた壁紙の設定が行える。この例ではホームディレクトリ直下のWallpaper.pngを参照している。

**Q4.アプリケーションを自動起動させたい。**

A4.i3wmのconfigに`exec --no-startup-id hoge`の形でアプリケーションを指定する。以下に続く質問に登場するアプリケーション群は基本的にこれで自動起動させておく必要がある。

**Q5.タイル型ではなく自由に動かせるようにアプリケーションを起動させたい。**

A5.i3wmのconfigに`for_window [class="hoge"] floating enable`の形でアプリケーションを記述する。起動する際に大きさも指定したい場合は`floating enable, resize set 600 400`などと書く。指定するアプリケーションのclass名はターミナルエミュレータで`xprop | grep WM_CLASS`を実行して対象のアプリケーションをマウスでクリックすると取得できる。

**Q6.ウインドウを透過させたり、影をつけたり、フェードさせたい。**

A6.Picomを導入する。インストール後、`picom --config .config/picom.conf`でconfigファイルの雛形を召喚し、`picom -b`で起動すると自動的に初期設定が適用される。単なる装飾以外にも画面描写の整合性を保つための機能が含まれているので、基本的には導入しておくことが望ましい。

**Q7.デスクトップ通知を表示させたい。**

A7.Dunstを導入する。例によって`cp /usr/share/dunst/dunstrc ~/.config/dunst/dunstrc`で雛形を持ってくることができる。Picomやbumblebee-statusとは異なり、初期設定の表示はだいぶ具合が悪いので自身の理想に合わせてconfigファイルを再構築すべし。僕はここでかなり時間を吸いとられた。より平易な選択肢として`xfce4-notifyd`も挙げられる。

**Q8.ファイラがほしい。**

A8.Vimに習熟していて同様の操作体系を希望するならRangerはとても有力な選択肢になる。コンソールベースでVimライクな操作が行えるファイラなのでウインドウマネージャとの相性に優れている。しかしあくまでGUIのファイラを、ということであれば個人的にはThunarを勧める。GnomeのNautilusやKDEのDolphinほど依存パッケージを要求せず、必要十分の機能を提供してくれる。ゴミ箱やメディアのマウント機能が欲しい人は`gvfs`パッケージを導入すること。また、NTFSファイルシステムの認識には`ntfs-3g`パッケージ、コンテキストメニューで圧縮・解凍を行うには`thunar-archive-plugin`パッケージがそれぞれ要求される。

**Q9.GUIアプリケーションのUIやアイコン、カーソルをカッコよくしたい。**

A9.これをテキストで行うのは苦行なのでGUIアプリケーションの導入を推奨する。`lxappearance`ではGTK、`qt5ct`ではQt5のテーマを変更できる。Qt4の場合は`qt4config-qt4`を使う。すべてのツールキットでリリースされているテーマを用いれば統一感を保った画面作りが可能となる。Qt5は適用前にホームディレクトリ直下に.profile（.xprofileではない）ファイルを作成し、下記のコードを記述する必要がある。

```bash
[ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$XDG_CURRENT_DESKTOP" = "GNOME" ] || export QT_QPA_PLATFORMTHEME="qt5ct"
```

テーマファイルは[ここ](https://www.gnome-look.org/browse/cat/135/order/latest/)で手に入れられる。僕はQogir、Breezeあたりが好み。

**Q10.電源管理（ディスプレイの消灯やサスペンドまでの時間設定など）がしたい。**

A10.これもGUIアプリケーションの導入が手っ取り早い。`xfce4-power-manager`が推奨される。設定方法は見れば解ると思う。

**Q11.キーリピートの速度が遅すぎる。**

A11.i3wmのconfigに`exec --no-startup-id "xset r rate 200 30"`と記述する。数字の部分は好みに応じて変更されたし。これは自動起動オプションを用いてコンソールコマンドを実行させている。

**Q12.解像度やリフレッシュレートを指定したい。**

A12.上記と同様に`exec --no-startup-id "xrandr --output DVI-D-0 --mode 1920x1080 --rate 144.00"`といった具合に記述する。事前に手持ちのディスプレイに適した値を確認しておくこと。このやり方は他の手法と比べて確実性に優るが、i3wmの読み込みとともにxrandrコマンドが走るため画面が一瞬ブラックアウトする。

**Q13.ロックスクリーンがほしい。**

A13.lightdmを導入しているならlight-lockerが推奨される。lightdmで設定したgreeterを自動的に利用できる。おなじみのi3wmのconfigに`exec --no-startup-id light-locker --lock-on-suspend`と記述する。後半部分を忘れると起動直後に画面ロックが発動するので注意。

**Q14.シャットダウンメニューがほしい。**

A14.i3wmのconfig内で作る。僕はコマンド形式に仕立てた。

```bash
# シャットダウンシークエンス
bindsym $mod+Shift+e mode "SHUTDOWN SEQUENCE"
mode "SHUTDOWN SEQUENCE"{
    bindsym p exec "systemctl poweroff"
    bindsym r exec "systemctl reboot"
    bindsym Return mode "default"
    bindsym Escape mode "default"
    bindsym $mod+Shift+e mode "default"
}
```

色々なブログを読んだ限りではi3-negbarを使ったやり方が一般的のようだが、あれは見た目のよろしくないナビゲーションバーが出現するので僕はあまり好きではない。

**Q15.ラップトップマシンの特殊キーで音量や輝度を調節したい。**

A15.下記のコードのように記述する。デバイス名は環境によって異なる。コンソールで途中まで打ったらシェルがよしなに補完してくれるかもしれない。

```bash
# 音量調整
bindsym XF86AudioRaiseVolume exec pactl set-sink-volume @DEFAULT_SINK@ +5%
bindsym XF86AudioLowerVolume exec pactl set-sink-volume @DEFAULT_SINK@ -5%
bindsym XF86AudioMute exec pactl set-sink-mute alsa_output.pci-0000_00_1f.3.analog-stereo toggle
bindsym XF86AudioMicMute exec pactl set-source-mute alsa_input.pci-0000_00_1f.3.analog-stereo toggle

# 輝度調整
bindsym XF86MonBrightnessUp exec xbacklight -inc 10
bindsym XF86MonBrightnessDown exec xbacklight -dec 10
```

xbacklightの代替プログラムとして[light](https://wiki.archlinux.jp/index.php/%E3%83%90%E3%83%83%E3%82%AF%E3%83%A9%E3%82%A4%E3%83%88#light)というパッケージもある。これを使う場合は以下の要領でユーザをvideoグループに追加する。

```bash
$ sudo gpasswd -a $USER video
```

この時のconfigの記述は次の通りとなる。

```bash
bindsym XF86MonBrightnessUp exec light -A 10
bindsym XF86MonBrightnessDown exec light -U 10
```

**Q16.ウインドウがぎっちり敷き詰められていると圧迫感がきつい。**

A16.下記の形式でウインドウやディスプレイの端との間に隙間を作ることができる。

```bash
gaps top 2
gaps bottom 2
gaps right 2
gaps left 2
gaps inner 2
```

**Q17.アプリケーションを起動させると固まることがある。**

A17.[スワップファイル](https://wiki.archlinux.jp/index.php/%E3%82%B9%E3%83%AF%E3%83%83%E3%83%97)を作る。またはIntel Graphicsを使用しているユーザで`xf86-video-intel`をインストールしている人は削除する。このビデオドライバは現在では非推奨となっている。**ただし、前述のxbacklightを利用した輝度調整が行えなくなるので注意。**

**Q18.アプリケーションを特定のワークスペースで起動するようにしたい。**

A18.assignオプションを使う。以下の例ではDiscordを3番目、Slackを4番目のワークスペースで起動するように指定している。自動起動と組み合わせればスタートアップと同時に理想の作業環境を構築することができる。

```bash
# ワークスペース指定一覧
assign [class="discord"] workspace 3
assign [class="Slack"] workspace 4
```

**Q19.トラックパッドがまともに機能しない。**

A19.`libinput-gestures`がインストールされていなければまず導入し、次にユーザをinputグループに加える。

```bash
$ sudo gpasswd -a $USER input
```

スタンダードな設定でよければ`/etc/libinput-gestures.conf`にある雛形を`~/.config/libinput-gestures.conf`に持ってくるだけでキーバインドが完成する。当然だが、i3のconfigでlibinput-gesturesを自動起動するように設定しておくことを忘れないように。

最後に`90-touchpad.conf`を下記の形で作成して`/etc/X11/xorg.conf.d/90-touchpad.conf`に保存すればだいたい想定通りの挙動が得られるはずだ。

```bash
Section "InputClass"
        Identifier "touchpad"
        MatchIsTouchpad "on"
        Driver "libinput"
        Option "Tapping" "on"
        Option "ScrollMethod" "twofinger"
        Option "AccelProfile" "adaptive"
EndSection
```

この設定ではタップによるクリックと複数の指でのジェスチャ操作が有効化されている。

**Q20.画面のスクロールや動画再生でティアリング（ちらつき）が発生する。**

A20.Picomを導入し、バックエンドをOpenGLに変更する。具体的には`~/.config/picom.conf`の`backend = "xrender";`を`backend = "glx";`に書き換える。僕の手持ちのマシンではnVidia、Intel Graphicsのいずれにおいても本設定でティアリングの症状が解消された。

**Q21.デュアルディスプレイの位置関係を設定したい。**

A21.ARandRを導入する。GUIアプリケーションなので直感的にデュアルディスプレイの設定が行える。

**Q22.フォントやカーソルが小さすぎる。**

A22.HiDPIディスプレイを使用している場合、`.Xresources`ファイルを作成して以下のようにDPIを指定する。適切なDPIの値は解像度やディスプレイサイズ、個人の好みに応じて変化する。

```bash
!! Set DPI
Xft.dpi: 140
Xft.auohint: 0
Xft.lcdfilter: lcddefault
Xft.hintstyle: hintfull
Xft.antialias: 1
Xft.rgba: rgb
Xcursor.size: 32
```

ただし、これで正しくスケールされるのはQTアプリケーションのみでGTKは対象外となる。この問題に対する完全な解決方法は現状存在しないため、HiDPIディスプレイのユーザは極力QT製を使うことが望ましい。

他にも思いつき次第、随時追記していく予定だが細かい部分については[僕のdotfiles](https://code.mystech.ink/riq0h/dotfiles)を参考にしてくれても構わない。手が空いていたら[Twitter](https://twitter.com/riq0h)での質問にも答える。
