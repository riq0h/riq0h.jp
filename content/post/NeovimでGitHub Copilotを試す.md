---
title: "NeovimでGitHub Copilotを試す"
date: 2024-09-30T21:30:09+09:00
draft: false
tags: ['tech']
---

LLMの技術的成果が日に日に突きつけられて喉元まで迫っているのを感じる今日この頃、さすがにろくに使いこなせないのでは困るため、ついにGitHub Copilotを試すことにした。LLMを応用した検索エンジン（[perplexity.ai](https://www.perplexity.ai)）は以前から使っていたが、開発環境と密に統合されるとどんな具合になるのかはやはり気になるところである。

僕の開発環境はNeovimなのでそれに合わせてCopilotを設定していく。GitHub Copilotは最低月額10ドルからのサブスクリプションサービスなのだが、契約完了時に送られてきたクイックガイドにNeovim向けのものがあったのには少々驚かせられた。大抵Vim向けの設定は各々が手弁当で勝手に生やしている印象が強かったからだ。なんならNeovimのプラグインも公式で用意されている。

だが、本稿ではあえてこれを用いず有志がLuaで書き直した[copilot.lua](https://github.com/zbirenbaum/copilot.lua)の方を使う。公式のものと比べて処理の効率化が図られている。プラグインマネージャには[lazy.nvim](https://github.com/folke/lazy.nvim)を用いる。まずは下記の通りにプラグインを導入して起動時に読み込まれるように設定する。

```lua
--lazy
{ "zbirenbaum/copilot.lua", cmd = "Copilot" },

--copilot
require("copilot").setup({
    suggestion = { enabled = false },
    panel = { enabled = false },
})
```

上記の設定で`suggestion`が`false`な理由は、標準とは異なる形でコード支援を受けるためだ。`true`にすると任意のキーでエディタ上にコードの予測が現れる。また、`auto_trigger`を項目に追加して`true`に設定すると自動的に表示されるようになる。しかし、本稿では補完プラグインの[nvim-cmp](https://github.com/hrsh7th/nvim-cmp)と連携を行うのでこれらは無効化しておく必要がある。

次に、一旦Copilotの認証を済ませる。プラグインが読み込まれた後に`:Copilot auth`を実行すると、時限制のトークンコードと共にGitHubの認証ページに案内される。自前で作成したファイルにsecretを格納する形式（誤って公開リポジトリに上げて後で痛い目を見るやつ）かと思っていたので、さすが今時は違うなと素直に感心した次第だ。

続いてnvim-cmpと連携を行う。標準設定ではエディタ上に薄くハイライトされるが、この設定では補完候補の一つとして表示される。個人的には、時として納得のいかないサジェストが前面にぶわっと出るよりは補完候補の一つに収まってくれる方が好ましいと感じる。nvim-cmp本体の詳細な設定は割愛させて頂く。

```lua
--lazy
{ "zbirenbaum/copilot-cmp", config = true, event = "InsertEnter" },

--nvim-cmp
local cmp = require("cmp")

--他の設定は省略

sources = cmp.config.sources({
    { name = "nvim_lsp", max_item_count = 15, keyword_length = 2 },
    { name = "vsnip", max_item_count = 15, keyword_length = 2 },
    { name = "copilot", max_item_count = 15, keyword_length = 2 }, --copilotを補完ソースに追加する
    { name = "nvim_lsp_signature_help" },
    { name = "buffer", max_item_count = 15, keyword_length = 2 },
}),
})

local capabilities = require("cmp_nvim_lsp").default_capabilities()
```

`max_item_count`は補完候補の最大量で`keyword_length`は補完が発動する最小のキーワード数を意味する。デフォルト値で差し支えなければ削っても構わない。上記では他にも補完ソースが記述されているが、当然ながらどれも個別に設定していないと動かない点に留意されたし。

```lua
local lspkind = require("lspkind")

formatting = {
    format = lspkind.cmp_format({
        mode = "symbol",
        maxwidth = 50,
        ellipsis_char = "...",
        symbol_map = { Copilot = "" },
    }),
},
```

[lspkind.nvim](https://github.com/onsails/lspkind.nvim)を利用している場合は補完候補のシンボルに任意の絵文字を配置できる。きれいな絵文字が並んでいるとモチベが上がるのでぜひ設定したい。なお、次候補の選択をTabキーで行っている人は以下の特殊な設定を追記しないとバグるらしい。

```lua
local has_words_before = function()
    if vim.api.nvim_buf_get_option(0, "buftype") == "prompt" then
        return false
    end
    local line, col = unpack(vim.api.nvim_win_get_cursor(0))
    return col ~= 0 and vim.api.nvim_buf_get_text(0, line - 1, 0, line - 1, col, {})[1]:match("^%s*$") == nil
end
cmp.setup({
    mapping = {
        ["<Tab>"] = vim.schedule_wrap(function(fallback)
            if cmp.visible() and has_words_before() then
                cmp.select_next_item({ behavior = cmp.SelectBehavior.Select })
            else
                fallback()
            end
        end),
    },
})
```

以上でGitHub Copilotの提案が補完候補に表示されるようになる。不要な時は次の候補に飛ばせばいいだけなので馴染みやすいと思われる。たとえCopilotの重要性が今後増してくるとしても、既存のLSPによる補完が依然有効なのは変わりない。

![](/img/337.png)

さて、これでCopilotの設定は終わりかと思いきや、実はそうではない。LLM最大の機能と言うべきは対話による改善なので、チャットができないことには魅力半減だ。しかし公式プラグインにも今回紹介した非公式の方にもチャット機能は備わっていない。そこで、[CopiotChat.nvim](https://github.com/CopilotC-Nvim/CopilotChat.nvim)というさらに別のプラグインを導入する。

CopilotChat.nvimは名前通りCopilotとの対話機能を提供するプラグインである。数多くの連携プラグインが用意されており設定内容も多岐に渡るが、本稿では自由記述方式と定型文で質問を行う方法について記す。後者には[telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)との連携機能を用いている。

```lua
--lazy
{ "CopilotC-Nvim/CopilotChat.nvim", build = "make tiktoken" },

--CopilotChat
local select = require("CopilotChat.select")

require("CopilotChat").setup({
    debug = true,

    window = {
        layout = "float",
        relative = "editor",
    },
    prompts = {
        Explain = {
            prompt = "/COPILOT_EXPLAIN 選択されたコードの説明を段落をつけて書いてください。",
        },
        Review = {
            prompt = "/COPILOT_REVIEW 選択されたコードをレビューしてください。",
            callback = function(response, source) end,
        },
        Fix = {
            prompt = "/COPILOT_FIX このコードには問題があります。バグを修正したコードに書き直してください。",
        },
        Optimize = {
            prompt = "/COPILOT_REFACTOR 選択されたコードを最適化してパフォーマンスと可読性を向上させてください。",
        },
        Docs = {
            prompt = "/COPILOT_DOCS 選択されたコードに対してドキュメンテーションコメントを追加してください。",
        },
        Tests = {
            prompt = "/COPILOT_TESTS 選択されたコードの詳細な単体テスト関数を書いてください。",
        },
        FixDiagnostic = {
            prompt = "ファイル内の次のような診断上の問題を解決してください:",
            selection = select.diagnostics,
        },
    },
})

function CopilotChatBuffer()
    local input = vim.fn.input("Quick Chat: ")
    if input ~= "" then
        require("CopilotChat").ask(input, { selection = require("CopilotChat.select").buffer })
    end
end

vim.api.nvim_set_keymap("n", "<leader>9", "<cmd>lua CopilotChatBuffer()<cr>", { noremap = true, silent = true })

function ShowCopilotChatActionPrompt()
    local actions = require("CopilotChat.actions")
    require("CopilotChat.integrations.telescope").pick(actions.prompt_actions())
end

vim.api.nvim_set_keymap(
    "n",
    "<leader>0",
    "<cmd>lua ShowCopilotChatActionPrompt()<cr>",
    { noremap = true, silent = true }
)
```

上記のうち`prompts`に続く日本語文は、デフォルトでは英語で用意されている定型文を書き換えたものとなる。Copilot Chatは質問文と同じ言語で回答が返ってくるため、日本語で回答が欲しければ日本語で質問しなければならない。

![](/img/338.png)

`ShowCopilotChatActionPrompt`ではtelescope.nvimを呼び出す関数が定義されている。この機能のなにが嬉しいのかというとコーディング中に頻繁に用いるであろう定型文をキーマップで即時に呼び出せるところだ。質問文が固定されていると回答も一意に定まりやすい。仮に定型文が100個くらいに増えてもtelescope.nvim由来の絞り込みで容易に対応できる。

他方、自由記述の入力は`CopilotChatBuffer`によって呼び出される。現在のバッファを対象に具体的な質問を行うことで、より高度な提案を引き出す効果が期待できる。ただし、Copilotはあくまでコーディング支援用のツールなので天気や時事問題、文章の校正などについて尋ねても回答は得られない。

![](/img/339.png)

有効な質問を入力すると上記の形式で回答が得られる。期待以上に的を射た内容が多く、これがいつでも使えて月額10ドルなら十分割に合うと感じた。業務上のコードをむやみに読み取らせるのは下手をするとインシデントに発展しかねないが、工夫次第では活用できる見込みが高い。

ホビーユースにおいて成果物自体が目的の場合には、質問とコピペを繰り返しながら制作を進めるアプローチも今時は考えられるだろう。専門技術を積んでいなくとも個々人の需要に適ったものが手に入るのはまさしく望ましい進歩の在り方である。

あるいは勉強目的ですら、極めて短期間のうちに有機的なトライアンドエラーを繰り返せるという意味では、昔の写経プログラミングより効率的な学習効果が得られるかもしれない。いずれにしても、便利な道具の使い方を知っておいて損はない。
