---
title: "超ミニマルなZshプロンプト「typewritten」"
date: 2022-10-15T16:27:31+09:00
draft: false
tags: ["tech"]
---

![](https://raw.githubusercontent.com/reobin/typewritten/main/docs/_media/typewritten.gif)

以前、[この記事](https://riq0h.jp/2021/03/22/201320/)でPreztoに付属するPureというプロンプトを紹介したが、最近よりミニマルなものを発見したので共有しておきたい。[typewritten](https://github.com/reobin/typewritten)は特に機能性を求めず、極めて簡素な外観を好む人に最適な選択肢だ。

導入は`npm`またはマニュアルで行う。前者は動作に必要な記述を自動で行ってくれるので楽。ただし、後者の場合でもパッケージをクローンして数行の設定を`.zshrc`に足すだけですぐに使える。

```t
#このコマンドで導入した人は以下二つの工程は不要
$ sudo npm -g install typewritten
```

```t
#マニュアルダウンロード
$ mkdir -p "$HOME/.zsh"
$ git clone https://github.com/reobin/typewritten.git "$HOME/.zsh/typewritten"
```

```zsh
#.zshrc
fpath+=$HOME/.zsh/typewritten
autoload -U promptinit; promptinit
prompt typewritten
```

導入後、`source ~/.zshrc`で`.zshrc`を読み込み直すと本記事冒頭のgif画像のような外観に切り替わっているはずだ。

typewrittenはミニマル仕様のプロンプトではあるものの、デフォルト設定が気に入らない場合は部分的に変更することもできる。設定は`.zshrc`に追記する形で行う。例えば、`TYPEWRITTEN_PROMPT_LAYOUT="half_pure"`と書き加えるとGitのステータス表示をシンボルの上部に移せる。

![](https://typewritten.dev/_media/layouts/half_pure.png)

カレントディレクトリの表示も含めてすべて上部に移す設定は`TYPEWRITTEN_PROMPT_LAYOUT="pure"`で可能だ。

![](https://typewritten.dev/_media/layouts/pure.png)

表示位置以外にも、シンボルの形状や文字の色を変えることもできる。これはDracula風らしい。

```zsh
export TYPEWRITTEN_COLOR_MAPPINGS="primary:#9580FF;secondary:#8AFF80;accent:#FFFF80;info_negative:#FF80BF;info_positive:#8AFF80;info_neutral_1:#FF9580;info_neutral_2:#FFFF80;info_special:#80FFEA"
```

![](https://typewritten.dev/_media/configuration_examples/dracula.png)

他の細かい設定は[ここ](https://typewritten.dev/#/prompt_color_customization)に載っている。設計思想上、リッチさにあふれた外観は望めないが、逆にとことん情報量を削ぎ落としたい人にはまさにうってつけのプロンプトではないだろうか。

一方、見た目はもちろん機能性ももう少しどうにか……という人はぜひ本記事冒頭のリンクからPreztoの項目を読むか、[Starship](https://starship.rs/ja-JP/)を試してみてほしい。あるいは、別途探せば類似のプロダクトもいくつか見つかるだろう。どのフレームワークやプロンプトにもそれぞれの思想性が備わっていて、CLIの表現力にはまだまだ未踏の領域が存在することを感じさせてくれる。
