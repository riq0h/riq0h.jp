---
title: "Neovimの見た目を削ぎ落とした"
date: 2023-01-30T13:43:07+09:00
draft: false
tags: ["tech"]
---

Lua化が一段落ついたら今度は細部の外見が気になってきた。どんなに些末な内容でも一旦そっちに気を取られると直すまでなにも手がつかないってよくありがちだ。僕はもう手遅れだが、せめて他の誰かの時間を節約せしむることによって名誉の回復を図りたい。

## Neovimの角ぜんぶ四角くする

近年のOSはどれもウインドウの角が丸くなっている。おそらく最初にやりはじめたmacOSはもちろん、Windowsもどさくさに紛れてちゃっかりまた丸まってる始末だ。きっとソフトウェア工学にもなんらかの安全基準が設けられたのだろう。角を丸くしておかないと怪我をするかもしれないからな。指とか。iOSやAndroidに至ってはそもそもスマートフォンのディスプレイ自体が角丸で作られているから、おのずと丸くならざるをえない。

だからなのか、Neovimのプラグインも角が丸いものが多い。いま言ったようにmacOSはもともと丸いし、Windowsは11からまた丸くなったし、Linuxでも主要なデスクトップ環境の角は大抵丸い。然るにウインドウの中に展開されるウインドウも予め丸くしておくのは実に理にかなった話で、誠に遺憾ながらこれらのデフォルト設定を咎める道理はない。

だが、僕はデスクトップ環境ではなくウインドウマネージャのi3wmを使っている。i3wmが作るウインドウは令和最新バージョンでもばっちりカクカクだ。僕はカクカクしている方が好きだからそれで全然いい。いいのだけれど、そうするとNeovimの内側と見た目が合わなくなってしまう。これまではなんとなく受け入れてきたがやはり全部四角くなるべきだ。さもなければ全体の一貫性が保てない。指を怪我するとかぶっちゃけ嘘だしな。

**■nvim-cmp**

```lua
local cmp = require('cmp')

 cmp.setup({
   window = {
      completion = cmp.config.window.bordered({
        border = 'single'
    }),
      documentation = cmp.config.window.bordered({
        border = 'single'
   }),
  },
})
```

nvim-cmpには便利なオプション（`window.{completion,documentation}.border`）が生えており、ここに`single`を指定することで角を四角くできる。なお、`double`だと二重の角に変えられる。

![](/img/176.png)

**■dressing**

```lua
require('dressing').setup({
  input = {
    border = 'single',
  },
  builtin = {
    border = 'single',
  },
})
```

Neovimの内蔵UIをリッチな様式に置き換えてくれるこの有名なプラグインにも同様の設定値が存在する。

**■Telescope**

```lua
 require('telescope').setup({
  defaults = {
    borderchars = { "─", "│", "─", "│", "┌", "┐", "┘", "└" },
  },
})
```

![](/img/177.png)

対して、Telescopeは少々厄介だ。プリセット的なオプションが用意されていないため、自分でウインドウのパーツを一つずつ指定しなければいけない。僕は上記の設定でちゃんと四角くなったがフォント環境によって崩れる可能性がある。実際、ググって簡単に見つけられる設定例ではズレまくりだったので、うまくいくまでにそこそこのトライアンドエラーを要した。なんか図工の時間みたいだな。

## モード表示いらない説

lualineやlightlineでstatuslineを装飾している人ほどモード表示への気配りも手厚いと思われる。お気に入りのカラースキームに適合するスキンが見つからない時は自作したりもしていたはずだ。僕も多分に漏れずそうだった。単にデザインとして見てもモード表示の地位は高い。

しかし、[modes.nvim](https://github.com/mvllow/modes.nvim)というプラグインを知ってからはすっかり事情が変わってしまった。モード表示が切り替わるとカーソルラインが任意の色に光るだけのプラグインだが、実のところめちゃくちゃ助けられている。現在のモードが即時に把握できるおかげでつまらない操作ミスもしなくなった。**……ということは、あんなに気を遣っていたstatuslineのモード表示なんて、もともとろくに見ていなかったのだ。** ならば、不要な情報は削られるべきである。

```lua
require('modes').setup({
    colors = {
		copy = '#FFEE55',
		delete = '#DC669B',
		insert = '#55AAEE',
		visual = '#DD5522',
 },
})
```

まずmodes.nvimの色を指定する。カラースキームとの色合いを意識するとカッコよくなるが別に何色でも構わない。僕は[こういうサイト](https://ironodata.info)をだらだらと眺めながら決めた。

![](/img/178.gif)

いい感じ。

```lua
require('lualine').setup {
options = {
 component_separators = { left = '', right = ''},
 section_separators = { left = '', right = ''},
 disabled_filetypes = {'TelescopePrompt'},
 always_divide_middle = true,
 colored = false,
 globalstatus = true,
 },
 sections = {
  lualine_a = {''},
  lualine_b = {'branch', 'diff'},
  lualine_c = {
   {
    'filename',
    path = 1,
    file_status = true,
    shorting_target = 40,
    symbols = {
    modified = '[+]',
    readonly = '[RO]',
    unnamed = 'Untitled',
    }
   }
  },
  lualine_x = {'filetype'},
  lualine_y = {
   {
    'diagnostics',
    source = {'nvim-lsp'},
     },
   {'progress'},
   {'location'}
    },
  lualine_z = {''}
 },
 inactive_sections = {
  lualine_a = {},
  lualine_b = {},
  lualine_c = {'filename'},
  lualine_x = {'location'},
  lualine_y = {},
  lualine_z = {}
 },
 tabline = {},
 extensions = {}
}
```

次にlualineの設定を行う。モード表示を削るべく`lualine_a = {}`の中身を空に指定する。`component_separators`や`section_separators`もグレーの濃淡だけで区分可能なため特に必要ない。通常はlocationが置かれる`lualine_z = {}`もすべて`lualine_y`の方に寄せることで不要となった。反映させた結果は下記画像の通りだ。

![](/img/179.png)

若干の寂しさは否めないが自分にとって無用な情報が鎮座しているよりはずっと望ましい。

## おわりに

こんな偏屈なこだわりに3時間も溶かした僕をどうか嗤わないでほしい。
