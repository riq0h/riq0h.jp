---
title: "i3wmクイックスタートアップガイド"
date: 2023-02-25T21:17:17+09:00
draft: false
tags: ['tech']
---

![](/img/184.png)

本エントリはタイル型ウインドウマネージャのi3wmを可及的速やかに動作させるためのテキストである。以下の条件に当てはまるユーザを想定読者層とする。

・Linuxの基本的な操作方法を理解している。  
・`i3-wm`パッケージの導入が完了している。  
・Arch Linuxかそれに類するディストリビューションを使用している。

Arch Linuxの導入については[この記事](https://riq0h.jp/2022/05/18/094517/)を、i3wm設定後のトラブルシューティングについては[この記事](https://riq0h.jp/2021/04/10/091649/)をそれぞれ参考にされたし。なお、本エントリではSwayとWaylandに関する説明は行わない。


## 初期設定
通常、i3wmを導入した状態で初回起動を行うとウェルカムメッセージと共にmodキーの設定を促される。modキーを決めると`~/.config/i3/`に`config`ファイルが生成され、原則的にはこれを基に設定ファイルを構築する形となる。**しかし、本エントリではこの手順は踏まず、i3wm移行前にあらかじめ設定ファイルを作っておく。** すなわち、`~/.config/i3`フォルダと`config`ファイル（ドットや拡張子は付かない）を手動で作成する。

というのも、ろくに整備されていない環境に放り込まれた状態では情報収集や編集作業に翳りが生じる恐れが否めないからだ。実際、本当になにも設定していないとブラウザの起動さえおぼつかない。したがって、繰り返すが前もって設定ファイルを構築することを強く勧めたい。


## アプリケーションの起動と終了
さっそく`config`ファイルに設定を列挙していく。まず記すべきは前述したmodキーである。modキーとはi3wmにおいてショートカットの始動を司るキーで、`$mod+e`のような形式でキーバインドを定義する際に用いる。デフォルトでは`Mod1`（Altキー）が採用されているが、Altキーは他のアプリケーションと衝突しやすいので、`Mod4`（Windowsキー、Commandキー）の方が好ましい。

```bash
set $mod Mod4
```

続いてアプリケーションやコマンドの起動ショートカットを決める。おそらくもっとも書く機会が多い構文だと思われる。一例としてターミナルアプリケーションの例を挙げる。

```bash
bindsym $mod+Return exec --no-startup-id alacritty
```

このショートカットの構文は`bindsym`から始まり、次に任意のキーバインド、アプリケーションやコマンドの起動では`exec --no-startup-id`が加わり、末尾でアプリケーションを指定する。さしあたりターミナル、ブラウザ、ファイラを設定して残りは移行後でも構わない。指定に必要なクラス名は`xprop | grep WM_CLASS`で求められる。実行後、アプリケーションにマウスカーソルを重ねるとターミナル上にクラス名が表示される。

反対に、アプリケーションを終了するショートカットは以下の通りに定める。これでひとまずアプリケーションの起動と終了が行えるようになった。

```bash
bindsym $mod+q kill
```


## 自動起動
システムの起動時にアプリケーションを自動で起動させたい場合は、キーバインドなしで`exec`オプションを書いて直に指定する。コマンドやスクリプトを実行させることもできる。たとえば`feh`は本来は画像ビューアだが、ここでは壁紙を表示させる役割を与えている。

```bash
exec --no-startup-id vivaldi-stable
exec --no-startup-id "feh --no-fehbg --bg-scale ~/Wallpaper.png"
exec --no-startup-id "xset r rate 200 30"
exec --no-startup-id fcitx5
```


## ショートカットの拡張
ショートカットを設定していくと次第に候補となるキーバインドが足りなくなってくる。そこで、ショートカットを二段構えにして実質的にキーバインドを増やす手法が役に立つ。

```bash
bindsym $mod+c mode "CMD"
mode "CMD"{
    bindsym v exec vivaldi-stable; mode "default"
    bindsym f exec "flameshot gui" mode "default"
    bindsym Return mode "default"
    bindsym Escape mode "default"
    bindsym $mod+c mode "default"
}
```

上記の例では`$mod+c`で一旦"CMD"モードに入り（この名称は自由に決められる）そこから追加のキーを押してアプリケーションが起動する構成になっている。`$mod+c`だけでは一つのショートカットしか設定できないが、このように工夫すると`$mod+c`の配下に複数のショートカットを定義できる。

注意点はショートカットをモード化した際に、そのモードを解除する挙動を定義しておかないといつまでもモード化が維持されてしまうところだ。そうすると他のショートカットを受けつけなくなるため、上記の例にしたがってアプリケーションの起動直後か、任意のキーバインドで通常モードに戻る設定`mode "default"`を書き加えておかなければならない。


## ウインドウの操作
i3wmはタイル型ウインドウマネージャであるからにして、ウインドウの操作もショートカットで完結させることが前提となる。手始めにウインドウフォーカスの設定例を記す。本項ではVimライクなキーバインドと矢印キーを使うものの二通りを紹介する。

```bash
# ウインドウフォーカス
bindsym $mod+h focus left
bindsym $mod+j focus down
bindsym $mod+k focus up
bindsym $mod+l focus right

# 代替ウインドウフォーカス
bindsym $mod+Left focus left
bindsym $mod+Down focus down
bindsym $mod+Up focus up
bindsym $mod+Right focus right
```

次にウインドウの交換ショートカットを設定する。並んでいるウインドウの位置を入れ替えたい時に用いる。

```bash
# ウインドウ交換
bindsym $mod+Shift+h move left
bindsym $mod+Shift+j move down
bindsym $mod+Shift+k move up
bindsym $mod+Shift+l move right

# 代替ウインドウ交換
bindsym $mod+Shift+Left move left
bindsym $mod+Shift+Down move down
bindsym $mod+Shift+Up move up
bindsym $mod+Shift+Right move right
```

続いて、ウインドウの分割ショートカットを設定する。ウインドウはもっぱら垂直に展開されるが、下記に倣って`$mod+s`を発動してからアプリケーションを起動すると水平に展開されるようになる。垂直での起動に戻すには`$mod+v`を押す。すでに展開済みのウインドウを水平または垂直に変更したい場合は`layout`オプションで`toggle split`を定義する。

```bash
# 水平ウインドウ分割
bindsym $mod+s split v

# 垂直ウインドウ分割
bindsym $mod+v split h

# ウインドウの分割切り替え
bindsym $mod+e layout toggle split
```

フルスクリーン表示も可能。`toggle`オプションを用いると同一のキーバインドで有効と無効を切り替えられる。

```bash
bindsym $mod+f fullscreen toggle
```

タイル型ウインドウマネージャはその名の通り、あたかもタイルのごとくウインドウを敷き詰める使い方が基本ではあるものの、一般のデスクトップ環境と同じくフローティングさせることもできる。ただし、前述のウインドウフォーカスはフロートウインドウに対しては効かないため、専用の設定を定義しておかなければならない。

```bash
# ウインドウフロート
bindsym $mod+w floating toggle

# フロートウインドウフォーカス
bindsym $mod+space focus mode_toggle
```

同様に、フロートウインドウを動かすキーバインドも個別に設定する。i3wmの仕様上、たとえフロートウインドウであってもマウスのドラッグ単体で動いてくれるとは限らない。

```bash
floating_modifier $mod
```

フロートウインドウの応用例として、特定のアプリケーションを必ずフロート起動させる設定が挙げられる。とりわけファイラや動画プレイヤーはフローティングのモチベが高い。`resize`オプションを定義しないと最大表示で展開してしまうので、こだわりがなくとも適当なウインドウサイズを指定した方がよい。

```bash
for_window [class="Thunar"] floating enable, resize set 1024 780
```

最後にウインドウのリサイズを行うショートカットを記す。僕はモード化して仕立てている。

```bash
bindsym $mod+r mode "RESIZE"
mode "RESIZE" {
        bindsym h resize shrink width 10 px or 5 ppt
        bindsym j resize grow height 10 px or 5 ppt
        bindsym k resize shrink height 10 px or 5 ppt
        bindsym l resize grow width 10 px or 5 ppt

        # 代替
        bindsym Left resize shrink width 10 px or 5 ppt
        bindsym Down resize grow height 10 px or 5 ppt
        bindsym Up resize shrink height 10 px or 5 ppt
        bindsym Right resize grow width 10 px or 5 ppt

        # 通常モード遷移
        bindsym Return mode "default"
        bindsym Escape mode "default"
        bindsym $mod+r mode "default"
}
```


## ワークスペースの設定
デスクトップ環境では「仮想デスクトップ」と呼称される機能をi3wmでは「ワークスペース」と呼ぶ。ウインドウを一面に敷き詰める文化は極めて効率に優れる一方で、なにかとすぐに余白が不足する。かつては無縁だったユーザもi3wmではワークスペースの助けなくしては生きられないだろう。

まずはワークスペースの変数を定義する。僕は1から始める数字派だが0から始める人もいる。数字ではなく記号派の人もけっこう多い。

```bash
set $ws1 "1"
set $ws2 "2"
set $ws3 "3"
set $ws4 "4"
set $ws5 "5"
set $ws6 "6"
set $ws7 "7"
set $ws8 "8"
set $ws9 "9"
set $ws10 "10"
```

次にワークスペース間を移動するショートカットを設定する。数字と対応させるのが無難オブ無難だが、ワークスペースが増えるほどmodキーから離れた位置にならざるをえない欠点もある。

```bash
bindsym $mod+1 workspace $ws1
bindsym $mod+2 workspace $ws2
bindsym $mod+3 workspace $ws3
bindsym $mod+4 workspace $ws4
bindsym $mod+5 workspace $ws5
bindsym $mod+6 workspace $ws6
bindsym $mod+7 workspace $ws7
bindsym $mod+8 workspace $ws8
bindsym $mod+9 workspace $ws9
bindsym $mod+0 workspace $ws10
```

使用頻度は人によるが、ウインドウを別のワークスペースに移動させるショートカットも設定しておく。一連のキーバインドには数字キーをすべて割り振っているが、もし他に使うあてがあれば適宜削っても差し支えはない。僕も本当に使用しているワークスペースの数はせいぜい5個くらいしかない。

```bash
bindsym $mod+Shift+1 move container to workspace $ws1
bindsym $mod+Shift+2 move container to workspace $ws2
bindsym $mod+Shift+3 move container to workspace $ws3
bindsym $mod+Shift+4 move container to workspace $ws4
bindsym $mod+Shift+5 move container to workspace $ws5
bindsym $mod+Shift+6 move container to workspace $ws6
bindsym $mod+Shift+7 move container to workspace $ws7
bindsym $mod+Shift+8 move container to workspace $ws8
bindsym $mod+Shift+9 move container to workspace $ws9
bindsym $mod+Shift+0 move container to workspace $ws10
```

特定のアプリケーションを指定したワークスペースでのみ起動させる設定も存在する。ワークスペース単位で用途を決めている人には欠かせない。前述の自動起動と併せて列挙すれば「システム起動時にSlackをワークスペース3に展開」といった挙動も実現できる。

```bash
assign [class="discord"] workspace 3
assign [class="Slack"] workspace 3
```


## システムの再起動と終了
その気になればシステムの再起動などもショートカットで行える。下記の設定では`$mod+Shift+e`を押して、そこからさらに追加のキーを加えないと発動しない仕組みだが、これにはあえて迂遠なキーバインドを採用することで誤爆を避ける意図がある。

```bash
bindsym $mod+Shift+e mode "SHUTDOWN SEQUENCE"
mode "SHUTDOWN SEQUENCE"{
    bindsym p exec "systemctl poweroff"
    bindsym r exec "systemctl reboot"
    bindsym Return mode "default"
    bindsym Escape mode "default"
    bindsym $mod+Shift+e mode "default"
}
```

対して、設定しておくと便利なのがi3wmの設定再読込みと再起動だ。特に構築中はこのショートカットがあると非常に捗る。

```bash
# 設定再読込み
bindsym $mod+Shift+c reload

# 再起動
bindsym $mod+Shift+r restart
```


## カラー定義
i3wmは外観の色合いも定義できる。当然ながら下記の設定例も僕のものだが、モロ被りすると照れくさいので一度試したら別のにしてほしい。

```bash
# i3wm全体の色
set $bg           #1C1E27
set $fg           #CACACC
set $darkred      #D95882
set $red          #E4436F
set $darkgreen    #68DDC4
set $green        #24E39D
set $darkyellow   #E8AEAA
set $yellow       #EDA685
set $darkblue     #64A4BF
set $blue         #2095B4
set $darkmagenta  #B382CF
set $darkcyan     #54AEB8
set $cyan         #00A5AF
set $darkwhite    #CACACC
set $white        #CACACA
set $darkgrey     #6C6F93

# フォーカスカラー
# class                     border      background      text        indicator       child_border
client.focused              $bg         $darkgrey       $fg         $yellow         $darkyellow
client.unfocused            $bg         $bg             $fg         $yellow         $bg
```


## その他の設定
マウスカーソルの移動でウインドウがフォーカスされるとたいへん鬱陶しいので無効にする。

```bash
focus_follows_mouse no
```

ウインドウの枠の太さや隙間の広さも自由に決められる。どうでもいい設定と見せかけて意外に奥が深い。

```bash
# ウインドウの枠の太さ
for_window [class="^.*"] border pixel 2

# ウインドウ間の隙間の広さ
gaps top 6
gaps bottom 6
gaps right 6
gaps left 6
gaps inner 6
```


## Rofiの導入
すべてのアプリケーションをショートカットで呼ぶのは逆に非効率なのでランチャを併用する。Rofiはタイル型ウインドウマネージャの界隈ではデファクトスタンダード的なランチャとされている。`rofi`パッケージを導入した後、i3wmの設定ファイルに起動ショートカットを書き加える。

```bash
bindsym $mod+z exec --no-startup-id "rofi -show drun"
bindsym $mod+x exec --no-startup-id "rofi -show run"
```

`drun`はアプリケーションの起動に適したモードで、`run`はLinuxコマンド全体に対応している。この二つと全モードが融合合体した`combi`モードも備わっている。細かい調整を好まないのであれば[Ulauncher](https://ulauncher.io)を使う手もある。


## Dunstの導入
Dunstはi3wmにおいて通知を取り仕切る軽量なデーモンとして機能する。KDEやGnomeと異なり自前の通知システムを持たないタイル型ウインドウマネージャでは必要不可欠と言える。`dunst`パッケージを導入した後、自動起動を設定する。

```bash
exec --no-startup-id dunst
```

より平易な選択肢として`xfce4-notifyd`も挙げられる。i3wmの環境に慣れるまではこちらを使っても問題はない。

## Picomの導入
Picomは様々なグラフィック描写をi3wm環境下で適切に処理してくれる。ウインドウの透過や影の投影に用いられるとの説明が一般的だが、実は動画再生にも影響するため導入は必須である。`picom`パッケージを導入した後、例によって自動起動を設定する。

```bash
exec --no-startup-id "picom -b"
```

動画再生やアニメーションに不審なちらつきが認められる場合は`~/.config/picom.conf`の`backend = "xrender";`を`backend = "glx";`に書き換えると解消される。


## bumblebee-statusの導入
最後にステータスバーを導入する。タイル型ウインドウマネージャの文化ではここに通知領域やワークスペースボタン、現在時刻、ネットワーク情報などを設けることが模範とされる。ステータスバーには`i3blocks`や新進気鋭の`i3status-rust`をはじめとする多種多様なパッケージが存在するが、本エントリでは僕が愛用している`bumblebee-status`を例にとる。

```bash
# ステータスバーの色
set $background #2B303B
set $foreground #C0C5CE
set $lightred #BF616A
set $lightgreen #A3BE8C
set $lightyellow #EBCB8B
set $lightblue #8FA1B3
set $lightmagenta #B48EAD
set $lightcyan #96B5B4
set $lightwhite #C0C5CE
set $pink #FFB6C1
set $orange #F08080

# ステータスバー関連
bar {
    font pango:UDEV Gothic 35 11
    mode dock
    position top
    workspace_buttons yes
    strip_workspace_numbers yes
    binding_mode_indicator yes
    tray_padding 2
    colors {
        background $background
        focused_background $background
        statusline $lightred
        focused_statusline $lightred
        # 左からborder, bg, fg
        focused_workspace  $orange $orange $background
        active_workspace $background $background $foreground
        inactive_workspace $background $background $foreground
        urgent_workspace   $green $green $background
        binding_mode       $green $green $background
    }
    status_command /usr/bin/bumblebee-status -m playerctl pasink pasource datetime battery \
    -p playerctl.hide="true" playerctl.format="{{artist}} - {{title}}" playerctl.layout="playerctl.song" datetime.format="%m/%d %H:%M" -t monotone
}
```

ステータスバーの外観はタイル型ウインドウマネージャの顔と言っても過言ではない。もし読者諸君らがi3wmのunixpornに惹かれて導入を決意したのであれば、いよいよついにセンスの見せどころかもしれない。bumblebee-statusの詳細設定は[公式ドキュメント](https://bumblebee-status.readthedocs.io/en/main/index.html)がとても参考になる。

なお、設定末尾のテーマ`monotone`は僕の自作ゆえ、[このページ](https://bumblebee-status.readthedocs.io/en/main/themes.html)を読んで他の種類に変更されたし。そのままコピペするとエラーを吐く。


## おわりに
以上でクイックスタートアップガイドは終了となる。以降は実際にi3wmを試して構築を楽しんでもらいたい。本エントリの趣旨上、個別の設定項目については[ArchWiki](https://wiki.archlinux.jp/index.php/I3)に後を譲る。なにはともあれ、これで諸君らもあらゆる操作をキーボードで完結させたがる異常者集団の仲間入りだ。
