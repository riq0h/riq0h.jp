---
title: "LinuxでNeovimでもSwiftを書きたい！"
date: 2024-06-02T19:11:27+09:00
draft: false
tags: ['tech']
---

転職して約一ヶ月。予想に反してiOSアプリ開発案件にアサインされたため業務時間中は常にMacを使っている。皆さんもよくご存知の通り、iOSアプリの開発にはMacが必須だからだ。リモートワークでは貸与されたMacを使うし、実機検証用のiPhoneも傍らに置いてある。半分Appleアンチで知られる僕も今やすっかり林檎林檎している。じきに取り囲まれて林檎シロップ漬けと化すことだろう。

さて、しかし業務時間が終わればもはやこっちのものである。退勤報告をぶち上げた直後に即ディスプレイの入力を切り替えればそこは僕の庭だ。Macの方でもなんとかタイル型WMの挙動を再現できないかと[yabai](https://github.com/koekeishiya/yabai)を入れてみたり、なるべくCommandキーを使わないショートカット体系を目指してみたりと試行錯誤しているものの、どうしたって自分の手に馴染んだ環境は他と代えがたい。

一方、個人的な課題もある。iOSアプリ開発案件ではSwiftのコーディングが不可欠だが、僕はその経験がろくすっぽない。かといって一から手取り足取りご指導願いますなんて言えるキャリアでもなし、自力でキャッチアップする前提でチームが組まれているのは明らかだ。定時内で不足ならプライベートでもSwiftの勉強にリソースを割かなければならない。幸い、残業は現状まったくない。

となると、やはり問題なのはMacだ。Swiftをやらなければどうせ他の言語を勉強するので勉強自体は構わないがせめて開発環境にはこだわりたい。ゲームプログラミングや業務用アプリケーション開発ならともかく、Swiftは意外にちゃんとしたオープンソースの言語でもある。構文を学ぶためにちょこちょこ動かすくらいならLinux環境でもやってやれないことはないのではないか。

もちろんエディタはNeovimでなければならない。Linux環境と同じくらいエディタがNeovimなのも重要だ。Xcodeにも割とこなれたVimキーバインドが存在しているが物足りない。IntelliJ IDEAほど高機能でもない。そんなわけで、僕はNeovimでSwiftを勉強する気持ちを固めたのだった。


## 言語環境の手動インストール
Neovimで言語サーバを扱う場合、通常は[mason-lspconfig.nvim](https://github.com/williamboman/mason-lspconfig.nvim)などで簡単に導入できるようにするのが一般的だが、悲しいかなSwiftの言語サーバ[SourceKit-LSP](https://github.com/apple/sourcekit-lsp)は対応リストに含まれていない。したがってマニュアル的な形式で言語サーバを認識させる必要がある。

Arch Linuxの場合はAURから`swift-bin`パッケージをインストールすると簡単に導入できる。Ubuntuなど他のディストリビューションは[公式サイト](https://www.swift.org/download/)から手動でファイルを取得する。これを下記の要領で展開して任意の場所に配置していく。

```zsh
$ tar xzf swiftの圧縮ファイル.tar.gz
$ sudo mv swiftの展開フォルダ /usr/local/bin/swift  #PATHが通っていれば場所はどこでも構わない
$ swift --version  #事前にシェルを再起動されたし
```

導入が済んだら試しにFizzBuzzを逐次実行してみよう。以下のコードをコピペして`fizzbuzz.swift`などのファイル名で保存した後、シェルから`swift fizzbuzz.swift`で実行できる。

```swift
for i in 1...100 {
if i % 3 == 0 && i % 5 == 0 {
    print("FizzBuzz")
} else if i % 3 == 0 {
    print("Fizz")
} else if i % 5 == 0 {
    print("Buzz")
} else {
    print(i)
 }
}
```

PATHが通っていれば言語サーバも`sourcekit-lsp`コマンドで起動可能になっているはずだ。ここまでうまくやれていれば話を次の段階に進められる。


## Neovimの設定および動作確認
あえて本記事を読んでどうにかしたいと思っている人はすでにある程度の設定を組んでいると思われる。そこで細かい部分は割愛してざっくりコード例を載せる。この例では[nvim-lspconfig](https://github.com/neovim/nvim-lspconfig)の導入を要する。他にvim-lspやcoc.nvimを用いた例もあり、[公式ドキュメント](https://github.com/apple/sourcekit-lsp/tree/main/Editors)で詳細を確認できる。

```lua
require("lspconfig").sourcekit.setup({
    cmd = { "/usr/bin/sourcekit-lsp" },
    filetypes = { "swift" },
    on_attach = on_attach,
    capabilities = capabilities,
})
```

2行目のファイルパスは環境ごとに各自変更する。Arch LinuxのAURから導入した人は上記のファイルパスになる。設定後、Neovimを再起動してswiftファイルを開いた際に補完が効いていれば成功である。なお、swiftの言語サーバはルートディレクトリに`.git`などがなければ自動起動しない。

![](/img/295.png)

## 総評
これでLinux、NeovimでもSwiftの学習に最低限文化的な環境が得られた。ちなみに教本は技術評論社の[Swift実践入門](https://gihyo.jp/dp/ebook/2020/978-4-297-11214-1)を読んでいる。正直よく分からなかったオプショナル型の理解が一層深まっ太郎になった。

別に勉強するだけならPlaygroundのVimキーバインドで我慢すればいいんじゃないかって？ まあそれは確かにそうだ。
