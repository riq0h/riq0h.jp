---
title: "linux-zenの導入について"
date: 2020-12-07T21:00:53+09:00
draft: false
tags: ["tech"]
---
これまでカスタムカーネルにはほとんど縁がなかった。僕はオーディオ好きなのでリアルタイムカーネルには少しだけ関心を持っていたが、システムの安定性に影響を及ぼしそうなので試用には至っていない。

一方、linux-zen、俗にZENカーネルと呼ばれるカスタムカーネルにはもっと普遍的な付加価値がありそうに思われた。なんせArch LinuxのWikiでは下記のように説明されている。

> ZEN Kernel はカーネルハッカーたちの知恵の結晶です。日常的な利用にうってつけの最高の Linux カーネルになります。詳しい情報は https://liquorix.net を見てください (Debian 向けの ZEN ベースのカーネルバイナリ)。

なるほど、いかにもすごそうだ。しかしこれでは抽象的すぎて説明になっていない。文中のリンク先にもそのものズバリの情報はなかったので、自ら調べたところ下記の解説が得られた。

> Well I think the Zen Kernel (or the patches that are applied to it) increases your system's responsiveness and lowers your latency at the expense of some performance hit (I'd say about 1-3% at best).

簡単に言えば**わずかなパフォーマンスの犠牲（1~3%くらい）と引き換えにシステムの応答性を向上させてくれるカーネル**ということらしい。やはり試すだけの価値はありそうだ。なお、下記の一連のコマンドはArch Linux環境を前提にしている。

```shell
$ sudo pacman -S linux-zen linux-zen-headers
```

さっそくZENカーネルを導入する。インストールが完了したら以前のカーネルを削除しなければならないが、nVidiaのプロプライエタリなドライバーを使用している人はこちらの方もカスタムカーネルに適したものに変更しておく必要がある。

```shell
$ sudo pacman -S nvidia-dkms
```

続いて、以前のドライバーとlinuxカーネルを削除する。

```shell
$ sudo pacman -R nvidia linux
```

環境によっては先にnvidiaドライバーを削除してからでなければPacmanに怒られるかもしれない。また、LTSカーネルを使用している場合は`linux-lts`を指定すること。

これらの作業を終えたらinitramfsイメージを生成する。

```shell
$ sudo mkinitcpio -p linux-zen
```

最後にブートローダの再設定を行う。

```shell
$ sudo bootctl update #systemd-bootの例
$ sudo grub-mkconfig -o /boot/grub/grub.cfg #grubの例
$ sudo vim /boot/loader/entries/arch.conf #エントリの編集

#以下、編集画面
title   Arch Linux
linux   /vmlinuz-linux-zen #zenを付け足す
initrd  /intel-ucode.img
initrd  /initramfs-linux-zen.img #zenを付け足す
```

保存後、再起動して`uname -r`を実行した結果が下記の形になっていればZENカーネルの導入に成功している。

```shell
5.9.12-zen1-1-zen
```

ぶっちゃけ今のところ特に何かが改善された実感はないが、ZENカーネルに関して日本語の情報がほとんど見当たらなかったので共有しておこうと思った。Linuxコミュニティに栄光あれ。