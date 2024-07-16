---
title: "NeovimでFlutterの開発環境を構築する"
date: 2024-07-16T20:34:32+09:00
draft: false
tags: ['tech']
---

ようやくSwiftに馴染んできたと思ったら次の案件はFlutterだと言う。まだ具体的な時期は決まっていないが今年中の話には違いない。面接で「あらゆる技術領域にチャレンジしたい」などと自信満々にアピールしたことがボディーブローのように効いてきている。

とはいえ、良い話もある。SwiftでのiOSアプリ開発はXcodeの使用が絶対条件だがFlutterはVimで書ける。Xcodeを使うとしたらビルド周りの設定をする時だけだ。その上、よほど込み入った作りでなければ共通のコードでAndroidアプリも開発できるため受託側としては工数が少なく非常に都合が良い。いちコーダーとしては、単純なモバイル案件は全部FlutterかReact Nativeで受ければいいじゃんと感じてしまうがそうもいかない事情があるのだろう。

なんにせよまずは環境構築である。例によって会社の財布から[教本](https://gihyo.jp/dp/ebook/2024/978-4-297-13994-0)を召喚して早めに勉強に取り掛かる。Swiftの時は入社直後だったため徒手空拳での対応を余儀なくされたが、今回は幾ばくかの猶予が残されている。毎日こつこつとキャッチアップしていれば正式なアサイン後には最低限動けるようになっているはずだ。


## Flutterの導入および設定
手始めにFlutterのパッケージを導入する。以下に続く記述はLinux環境を想定しているが、WindowsのWSL環境やmacOSのターミナル環境でも大差はないと思われる。各々のディストリビューションの作法に従い`flutter`パッケージをインストールした後、`flutter doctor`コマンドの実行を行う。

```bash
~
❯ flueter doctor
Doctor summary (to see all details, run flutter doctor -v):
[✓] Flutter (Channel , 3.22.2, on Arch Linux 6.9.9-arch1-1, locale ja_JP.UTF-8)
[✓] Android toolchain - develop for Android devices (Android SDK version 35.0.0)
[✓] Chrome - develop for the web
[✓] Linux toolchain - develop for Linux desktop
[✓] Android Studio (version 2024.1)
[✓] IntelliJ IDEA Ultimate Edition (version 2024.1)
[✓] Connected device (2 available)
[✓] Network resources

• No issues found!
```

上記のコマンドはFlutterの開発環境を精査するもので、たとえばAndroidアプリを作る場合には少なくとも`Android toolchain`と`Android Studio`にチェックマークが入っていなければならない。macOSで実行した場合には別途、Xcodeなどの項目も現れる。目的がiOSアプリ開発ならそれらの導入が要求される。

といっても特に難しい要素はなく、基本的には指定されているソフトウェアを順次取り入れると要件をクリアできる。たとえばAndroid関連の項目にチェックマークが入っていないのなら、`android-studio`パッケージを導入して起動し、ウィザードに沿って必要最低限の初期設定を済ませれば解決する。ついでに`SDK Manager`の`SDK Tools`から`Android SDK Command-line Tools`にチェックを入れておくと`Anroid toolchain`の項目も満たすことができる。

最後に`flutter doctor --android-licenses`でライセンス条項に同意すると、Androidアプリ開発の要件が完全に満たされる。任意のディレクトリ下で`flutter create`を実行し、雛形のプロジェクトが作成されるか確認しよう。続けて`flutter run`でエミュレータ（デフォルトではWebアプリ開発用のエミュレータが立ち上がる）が立ち上がれば正常に動作している。


## flutter-tools.nvimの導入および設定
FlutterではDartというaltJSな言語が用いられる。大抵の言語では[mason-lspconfig.nvim](https://github.com/williamboman/mason-lspconfig.nvim)経由でLSPを導入するか、さもなければ[nvim-lspconfig](https://github.com/neovim/nvim-lspconfig)の設定を書く形が通例だが、Flutterに関しては[flutter-tools.nvim](https://github.com/akinsho/flutter-tools.nvim)を導入するだけでDartのLSPも含めた実行環境が完成する。導入には[lazy.nvim](https://github.com/folke/lazy.nvim)など任意のプラグインマネージャを用いるものとする。

```lua
require("flutter-tools").setup({
    ui = {
        border = "none",
    },
    dev_log = {
        enabled = false,
    },
    debugger = {
        enabled = true,
        run_via_dap = true,
    },
})

vim.keymap.set("n", "<leader>0", require("telescope").extensions.flutter.commands, { desc = "Open command Flutter" })
vim.keymap.set("n", "<leader>r", ":FlutterReload<CR>", { silent = true, desc = "Flutter Reload" })
vim.keymap.set("n", "<leader>R", ":FlutterRestart<CR>", { silent = true, desc = "Flutter Restart" })
```

上記は暫定的に定めた僕の個人設定だ。`flutter-tools.nvim`を入れるとLSPのみならずFlutterのCLI操作（`flutter run`など）もVimから行えるようになるが、そのたびにログがスプリットで表示されるのはあまり嬉しくないため`dev_log`を無効化している。また、頻繁に使いそうな`Flutter Reload`および`Flutter Restart`にはキーマップをあてがい、その他はTelescopeから呼び出す形にした。

```lua
local dap = require("dap")

dap.adapters.flutter = {
    type = "executable",
    command = "flutter",
    args = { "debug_adapter" },
}

dap.configurations.dart = {
    {
        type = "flutter",
        request = "launch",
        name = "Launch Flutter Program",
        program = "${workspaceFolder}/lib/main.dart",
        cwd = "${workspaceFolder}",
    },
}
```

さらに、以前に[紹介](https://riq0h.jp/2023/12/03/103850/)した`nvim-dap`との連係も一応有効にしておく。`debugger`を`enabled = true`かつ`run_via_dap = true`とすることで機能が働くようになる。現状では起動確認のために最小限の実行オプションのみを作り、上記の要領で`nvim-dap`の設定に追記を行った。以上でFlutterの環境構築は完了である。


## 動作確認
![](/img/307.png)

`:FlutterEmulators`で任意の仮想デバイスを呼び出してから`:FlutterRun`を実行すると、プロジェクトが読み込まれた状態でエミュレータが立ち上がる。後はひたすらコードを書いていくだけだ。ホットリロードに対応しているおかげであたかもWebサービスのごとくモバイルアプリを実装できる。これは畑違いの僕にも元来よく馴染んだ開発スタイルでたいへん体験が良い。やっぱり全部こんな感じになってくれないかな。
