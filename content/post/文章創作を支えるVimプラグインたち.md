---
title: "文章創作を支えるVimプラグインたち"
date: 2023-02-18T14:24:47+09:00
draft: false
tags: ["tech"]
---

主に日本語しか書かないならVimより適したエディタは他にたくさんある。誠に遺憾ながらその点は認めざるをえない。それが文章創作ともなればなおさらそうだ。今時分は[novel-writer](https://marketplace.visualstudio.com/items?itemName=TaiyoFujii.novel-writer)という大変優れた小説執筆用のVSCodeエクステンションも存在していて、もう全部VSCodeでいいだろみたいな風潮になりつつある。マルチプラットフォーム対応で設定も同期可能なので環境も選ばない。

だから僕とて、もし「小説を書くのにおすすめのエディタはありますか？」と訊かれたら、相手がコードも書く人かLinuxユーザなら「VSCodeにnovel-writerを入れるといいよ」と答えるし、違うならMery（Windows）とかCotEditor（Mac）とか、そういうのを勧める。別にWordでもPagesでも秀丸でも全然いい。村上春樹はegwordを使っているらしい。とにかく、間違ってもVimを勧めたりはしない。縦書き表示もできないし。

だが、世の中にはVimに取り憑かれた連中がいる。Vimから離れられないやつらがいる。そういう輩の中にも当然物書きはいて、そんな荒くれ者たちはできれば日本語の長文もVimで書きたいと思っているか、あるいはすでに書いている。多分に漏れず、僕もその一人だ。あえて無難な選択肢を葬り去り、Vimならではの流儀で戦っていこうというわけだ。

本エントリでは文章創作などの日本語の長文執筆・校正を支えるVimプラグイン群を紹介する。

## [kensaku.vim](https://github.com/lambdalisue/kensaku.vim)

実は単純に日本語入力をするだけならVimといえども他のエディタと大した差異はない。Insertモードを維持した状態でただ書いていけばよい。しかし、それではVimの機能性がほとんどスポイルされてしまう。せっかくVimで日本語の長文を執筆・校正するからには、やはりVimの操作体系、Vimのプラグインを活かしていきたい。

その中心的な役割を担うのがkensaku.vimと、インテグレーションプラグインのkensaku-search.vimである。これらはjsmigemoを利用してローマ字で日本語の文字列検索を行うプラグインだが、デフォルトのVimが抱える日本語検索の問題点を見事に克服している。というのも、Ctrl+Fキーなどを押して検索窓に任意のワードを入力する一般的なエディタと異なり、Normalモードに一旦遷移して`/`キーで検索を行うVimでは、間に入力メソッドの切り替えが挟まっているとかなり手間が増えるからだ。

なぜならVimは英数字入力でなければコマンドを受けつけない。従来のやり方で日本語検索を行うとなると「Normalモードに遷移→`/`→**日本語入力に切り替え**→検索→**英数字入力に切り替え**→移動→Insertモードに遷移」といった手順になり、非常に面倒くさい。一度か二度くらいなら我慢できても日本語の長文執筆・校正ではこれを何十回、下手をすれば何百回と繰り返す羽目になる。

そこでkensaku.vimが役に立つ。英数字入力で日本語のワードを引っ掛けられるおかげで入力メソッドの切り替えが不要になるのだ。校正作業に限って言えば一般的なエディタよりも効率的かもしれない。実際、順に書き下していく執筆作業よりもあっちへ行ったりこっちへ行ったりとバッファ内の移動が多い校正作業の方が、なにかとエディタの機能に助けられる局面が多いように思う。そして、そういった移動系の動作はもちろんVimが得意とするところである。

このような機能はMigemoそのものと関連プラグインを導入すれば以前でも導入できたが、簡便性と開発の活発さを考慮すると今後はこれらを導入することが望ましい。下記の導入例はパッケージマネージャにLazy.nvimを用いたもの。

```lua
--Lazy.nvim
{'vim-denops/denops.vim', lazy = false}, --kensaku.vimの依存プラグイン。
{'lambdalisue/kensaku-search.vim', lazy = false}, --/キーでの検索でkensaku.vimを使うためのプラグイン。
{'lambdalisue/kensaku.vim', lazy = false},

--kensaku-search
vim.keymap.set('c', '<CR>', '<Plug>(kensaku-search-replace)<CR>')
```

プラグインが動作している様子は以下の通りとなる。

![](/img/180.gif)

## [fuzzy-motion.vim](https://github.com/yuki-yano/fuzzy-motion.vim)

なるほど全文検索が手早いのは分かった。では、目視範囲への移動はどうなる？　日本語の長文でだってカーソル位置から少し離れた場所に飛びたいモチベはある。不意に誤字脱字を見つけてしまったり、書き直したくなった表現を放置して先に進むのは業腹だ。かといって前述の`/`キーでの検索はバッファ内のすべての文字列が対象ゆえ、目当てのワードによっては逆にまだるっこしい。諦めてhjklキー連打でちまちまと向かうか？――いいや、僕たちにはもっと優れたソリューションがある。

fuzzy-motion.vimは言わずと知れた移動系プラグインだが、kensaku.vimのリリースから間もなく連携を可能にするアップデートが実施された。`/`キーでの全文検索だと冗長なケースは本プラグインが補ってくれる。僕の以前のエントリでもvim-easymotionやhop.nvimと比べて操作方法が平易で使いやすいとの切り口で紹介したが、今回のアップデートでますます手放せない存在となった。設定と実演は以下の通り。

```lua
vim.keymap.set('n', 'S', '<cmd>FuzzyMotion<CR>')
vim.cmd("let g:fuzzy_motion_matchers = ['kensaku', 'fzf']")
```

![](/img/181.gif)

## [clever-f.vim](https://github.com/rhysd/clever-f.vim)

同じ行内の日本語にローマ字で飛ぶ方法もある。割り切った挙動を許容できるのであればclever-f.vimのMigmoオプションを有効化にする手が使える。仕様上、検索に用いるアルファベット一文字と同じ母音の文字が丸ごと引っかかってしまうが、ひとまずこれでバッファ範囲、目視範囲、行範囲の三つの射程をカバーできる。

```lua
vim.cmd('let g:clever_f_across_no_line = 1')
vim.cmd('let g:clever_f_ignore_case = 1')
vim.cmd('let g:clever_f_smart_case = 1')
vim.cmd("let g:clever_f_chars_match_any_signs = ';'")
vim.cmd('let g:clever_f_use_migemo = 1')
```

![](/img/182.gif)

## [mini.surround/mini.ai](https://github.com/echasnovski/mini.nvim)

やたらと括弧で文字列を囲むのはなにもコーディングに限った話ではない。日本語の長文にもそういうやつがある。小説だ。小説の会話文だ。括弧（かぎ括弧）で文字列を囲っている。情景描写に富んだハードSFとかでは少ないかもしれないが、カジュアル寄りの作品になればなるほど括弧で囲われる文字列は増える。括弧をいじったり中身を手直ししたりしたいモチベはコーディングに引けをとらず極めて高い。

ところがこの手の括弧をいじくる系のプラグインは当然ながらコーディングのそれを想定しており、全角の括弧だのかぎ括弧だのに気を遣ってくれる初期設定にはなっていない。だから僕もそういうものかと思って半ば諦めていたのだが、折りよくvim-jpコミュニティで[@atusy](https://twitter.com/Atsushi776)さんが全角括弧をはじめとする文字種にプラグインを対応させるユーザ定義を公開してくれた。この場を借りて感謝申し上げる。

通常、mini.surroundで**aaa**という単語を **"aaa"** にしたい時は`saiw"`と入力する。`sa`がプラグインのbindで`iw`が対象となる文字列の範囲を指定している。単語単位ではなく行全体を対象にする場合は`Vsa"`でも構わない。sandwich.vimのユーザには馴染み深いマッピングだと思われる。

これと同一の操作が全角のかぎ括弧などでも行えるようになったと考えると話が早い。つまり、**あああ**を **「あああ」** にしたい時は`saiwj[`と入力すればよい。この場合、`j`が日本語用のbindとして機能するため、`[`が`「`に解釈される。以下に設定の詳細を示す。僕が勝手に付け加えたものもある。

```lua
require('mini.surround').setup({
   mappings = {
    highlight = 'sx',
  },
   custom_surroundings = {
   ['j'] = {
     input = function()
       local ok, val = pcall(vim.fn.getchar)
       if not ok then return end
       local char = vim.fn.nr2char(val)

       local dict = {
         ['('] = { '（().-()）' },
         ['{'] = { '｛().-()｝' },
         ['['] = { '「().-()」' },
         [']'] = { '『().-()』' },
         ['<'] = { '＜().-()＞' },
         ['"'] = { '”().-()”' },
       }

      if char == 'b' then
         local ret = {}
         for _, v in pairs(dict) do table.insert(ret, v) end
         return { ret }
       end

       if dict[char] then return dict[char] end

       error('%s is unsupported surroundings in Japanese')
     end,
     output = function()
       local ok, val = pcall(vim.fn.getchar)
       if not ok then return end
       local char = vim.fn.nr2char(val)

       local dict = {
         ['('] = { left = '（', right = '）' },
         ['{'] = { left = '｛', right = '｝' },
         ['['] = { left = '「', right = '」' },
         [']'] = { left = '『', right = '』' },
         ['<'] = { left = '＜', right = '＞' },
         ['"'] = { left = '”', right = '”' },
       }

       if not dict[char] then error('%s is unsupported surroundings in Japanese') end

       return dict[char]
     end
  }
 },
})
```

mini.aiはtextobjectsの定義プラグインだ。たとえば`vi[`で **[aaa]** のような括弧で囲われたテキストを括弧の外側から全選択できるが、下記の定義拡張を行うと **「あああ」** といった日本語の会話文も同様に`vij[`で外側から全選択できる。

会話文の書き直しが確実視される状況では`/`やfuzzy-motion.vimでの移動よりもこれらのtextobjectsを用いたアプローチが有効に機能する。

```lua
require('mini.ai').setup({
   custom_textobjects = {
   ['j'] = function()
      local ok, val = pcall(vim.fn.getchar)
      if not ok then return end
      local char = vim.fn.nr2char(val)

      local dict = {
        ['('] = { '（().-()）' },
        ['{'] = { '｛().-()｝' },
        ['['] = { '「().-()」' },
        [']'] = { '『().-()』' },
        ['<'] = { '＜().-()＞' },
        ['"'] = { '”().-()”' },
      }

      if char == 'b' then
          local ret = {}
          for _, v in pairs(dict) do table.insert(ret, v) end
          return { ret }
        end

      if dict[char] then return dict[char] end

      error('%s is unsupported textobjects in Japanese')
  end
 }
})
```

それぞれを適用したテキスト処理の様子は以下の通りとなる。Vimのtextobjects/operatorの機能は膨大ゆえここでは一例のみの紹介に留めるが、コーディングのみならず文章創作の分野でも大いに活用できることは分かって頂けたかと思う。

![](/img/183.gif)

## おわりに

上記のgif画像に部分的に映っている小説[「Overwritten」](https://riq0h.jp/2023/02/11/201325/)は本エントリで紹介したプラグイン群を実際に使用して執筆・校正された作品である。本作には百合の良さを実地で書いて学ぶためとか、子供目線のゆるふわディストピア社会を描くとか、単純な叙述トリックに挑戦するといった創作上の試みも複数あるものの、それとは別個の目的として、これらのプラグインを宣伝する意図も含まれている。

本作は中篇小説に近いボリューム（約45000文字）を持つ作品だが、上記のプラグイン群の力を借りてなんとか2週間で完成させることができた。とりわけ長丁場を余儀なくされる校正作業においては、これらのプラグインの助力なくしてはとても効率を維持できなかったと言っても過言ではない。

最後に、Vimの文章創作環境に絶大な改善をもたらしてくれたプラグインの作者たちに感謝を捧げるとともに、皆さんにはあわよくば僕の小説も読んでほしいという偽らざる本音を以て本エントリの結びとする。
