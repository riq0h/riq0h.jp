---
title: "NeovimでFlutterの開発環境を構築する"
date: 2024-07-16T10:11:32+09:00
draft: true
tags: ['tech']
---

ようやくSwiftに馴染んできたと思ったら次の案件はFlutterだという。まだ具体的な時期は決まっていないが今年中の話には違いない。面接で「あらゆる技術領域にチャレンジしたい」などと大上段をかましたことがボディーブローのように効いてきている。

とはいえ、良い話もある。SwiftでのiOSアプリ開発はXcodeの使用が絶対条件だがFlutterはVimで書ける。Xcodeを使うのは最後のビルドの時だけだ。その上、よほど込み入った作りでなければ一つのコードでAndroidアプリもビルドできるため受託側としては工数が少なく非常に都合が良い。いちコーダーとしては、単純なモバイル案件は全部FlutterかReact Nativeで受ければいいじゃんと感じてしまうがそうもいかない事情があるのだろう。

なんにせよまずは環境構築である。例によって会社の財布から教本を召喚して早めに勉強に取り掛かる。Swiftの時は入社直後だったため徒手空拳での適応を余儀なくされたが、今回はまだいくらか猶予が残されている。毎日こつこつとキャッチアップしていれば正式なアサイン後には最低限動けるようになっているはずだ。


## Flutterの導入および設定
まずはFlutterのパッケージを導入する。以下に続く記述はLinux環境を想定しているが、WindowsのWSLやmacOSのターミナル環境でも大差はないと思われる。各々のディストリビューションの作法に従い`flutter`パッケージをインストールした後、`flutter doctor`コマンドの実行を行う。

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

上記のコマンドはFlutterの実行環境を精査するもので、たとえばAndroidアプリを作る場合には少なくとも`Android toolchain`と`Android Studio`にチェックマークが入っていなければならない。macOSで実行すると別途Xcodeなどの項目も現れる。目的がiOSアプリ開発ならそれらのチェックマークが要求される。

といっても特に難しい要素はなく、指定されているソフトウェアを導入するだけで基本的には条件をクリアしたものと認められる。たとえばAndroid関連の項目にチェックマークが入っていないのなら、`android-studio`パッケージを導入して起動し、ウィザードに沿って必要最低限の初期設定を済ませれば解決する。ついでに`SDK Manager`の`SDK Tools`から`Android SDK Command-line Tools`にチェックを入れておくと`Anroid toolchain`の項目も満たすことができる。

最後に`flutter doctor --android-licenses`でライセンス条項への同意を済ませればAndroidアプリ開発の条件は完全にクリアしたと言える。任意のディレクトリ下で`flutter create`を実行し、雛形のプロジェクトが作成されるか確認しよう。続けて`flutter run`でエミュレータ（デフォルトではWebアプリ開発用のエミュレータが立ち上がる）が立ち上がれば正常に動作している。


## flutter-tools.nvimの導入および設定
FlutterではDartというAltJSな言語を用いる。大抵の場合は[mason-lspconfig.nvim]()で簡単にLSPを導入するか、さもなければ[nvim-lspconfig]()の設定を書く形が通例だが、Flutterに関しては[flutter-tools.nvim]()を導入するだけでDartのLSPも含めた開発環境が完成する。導入には[lazy.nvim]()など任意のプラグインマネージャを用いる。

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

上記はとりあえずで決めた僕の設定。`flutter-tools.nvim`を入れるとLSPのみならずFlutterのCLI操作（`flutter run`など）もVimから行えるようになるが、そのたびにログがスプリットで表示されるのはあまり嬉しくないため`dev_log`を無効化している。また、頻繁に使いそうな`Flutter Reload`および`Flutter Restart`にはキーマップをあてがい、その他はTelescopeから呼び出せる形にした。


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


さらに以前に紹介した`nvim-dap`との連係も一応有効にしておく。`debugger`を`enabled = true`かつ`run_via_dap = true`とすることで機能が働くようになる。現状では起動確認のために最小限の実行オプションのみを作り、上記の要領で`nvim-dap`の設定に追記を行った。以上でFlutterの環境構築は完了である。


## 動作確認
![]()

`Flutter emulators`で任意の仮想デバイスを呼び出してから`:FlutterRun`を実行すると、プロジェクトの内容が読み込まれた状態でエミュレータが立ち上がる。後はひたすらコードを書いていくだけだ。Flutterはホットリロードに対応しているのであたかもWebサービスのごとくモバイルアプリを実装していくことができる。元来、畑違いの僕にもよく馴染んだ開発スタイルでたいへん体験が良い。やっぱり全部こうなってほしい。
