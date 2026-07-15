# 記事ごとの動的OGP画像生成 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ページ種ごとに実際のマストヘッド・日付・タグ・タイトルを反映したOGP画像(`og.png`)をビルド時に自動生成し、全ページ共通の静的画像を置き換える。

**Architecture:** Hugoのカスタム出力フォーマット(`ogcard`)で各ページに専用の最小HTML(`ogcard.html`)を書き出す → Woodpecker CIの新ステップ`ogimages`で`public/`をローカルHTTPサーバーとして配信し、ヘッドレスChromiumで各`ogcard.html`を1200×630pxでスクリーンショットして`og.png`として保存、`ogcard.html`自体は削除 → `head.html`が`{{ .Permalink }}og.png`を指す`og:image`/`twitter:image`タグを出力する。

**Tech Stack:** Hugo v0.163.3 (出力フォーマット機能)、`hugomods/hugo:base`(Alpine)上のChromium(ヘッドレス)、Python3標準ライブラリの`http.server`、POSIX sh、Woodpecker CI。

## Global Constraints

- **AI関与を示すコメント・コミットトレーラーは一切使わない**(`Co-Authored-By: Claude`等を含め、by Anthropic/by Claudeのような文言は不可)。このプロジェクトの全コミットに適用される標準ルール。
- 色・太さ・フォントは新規の値を作らず、`themes/tangentline/assets/css/main.css`の`:root`で定義済みの`--c-*`/`--w-*`/`--font-*`カスタムプロパティをそのまま参照する。
- 404ページ(`.Kind == "404"`)はOGPカード生成・`og:image`/`twitter:image`タグの両方から完全に除外する。
- ページ送り(`/page/2/`等)は1ページ目とだけ同じ`og.png`を共有する。2ページ目以降の`ogcard.html`は生成されても削除するだけで、スクリーンショットは撮らない。
- Chromiumインストール自体の失敗はビルド全体を失敗させる。個別ページのスクリーンショット失敗は静的フォールバック画像で継続するが、スクリプトは最後に非ゼロ終了してビルド全体を失敗扱いにする(サイレントに握りつぶさない)。
- **このシェル環境ではBashのヒアドキュメント(`cat > file << 'EOF'`)で新規ファイルを書くとANSIエスケープコードが実際のファイル内容に混入することが確認されている。新規ファイル作成には必ずWriteツールを使うこと。**

---

## 検証済みの前提事実(実装前に確認済み)

以下はこの計画を書く前に実際に検証済みの事実。実装時に再確認する必要はない。

1. `.Permalink`/`.RelPermalink`はページ送り(`/page/2/`等)のコンテキスト内でも**常にページ1の正規URLを指す**(実測: `public/page/2/index.html`の`<link rel="canonical">`は`https://riq0h.jp/`)。したがって`head.html`の`og:image`タグに`{{ .Permalink }}og.png`を使えば、ページ送りに対する特別な分岐は一切不要。
2. `[outputs]`テーブルはHugoの種別(kind)ごとに独立しており、キーに挙げていない種別(404など)は既存のデフォルト出力を保ったままになる。404を`[outputs]`に一切書かないことで、404ページのOGP除外は自然に達成される。
3. カスタム出力フォーマット(`mediaType = "text/html"`, `baseName = "ogcard"`)を`home`/`section`/`taxonomy`/`term`/`page`の`[outputs]`に追加すると、`layouts/_default/list.ogcard.html`(list系: home/section/taxonomy/term)と`layouts/_default/single.ogcard.html`(page)がそれぞれ正しく解決される(実機で確認済み)。
4. ページ送りの複製問題について: `.Paginator`を直接参照するテンプレート(検証用の簡易テンプレートで確認)ではページ送り由来の`/page/N/ogcard.html`も生成されてしまうが、**`ogcard-content.html`パーシャル(および`.Paginator`を一切参照しない`list.ogcard.html`/`single.ogcard.html`)ではHugoはそもそもページ送り分の`ogcard.html`を生成しない**(Task 1実装後に実機で再確認済み: `find public -name 'ogcard.html' -path '*/page/*'`は0件)。つまりテンプレートが`.Paginator`に一切触れない限り、Hugoの出力フォーマット生成はページ送りの複製を作らない。`scripts/generate-og-images.sh`側の`*/page/*`除外ロジックは、将来テンプレートが`.Paginator`を参照するようになった場合に備えた保険として残すが、現状は発火しない安全策。
5. `hugomods/hugo:base`(Alpine 3.24.1)には`apk add --no-cache chromium`で`chromium`/`chromium-browser`の両バイナリが入り、`--headless=new --disable-gpu --no-sandbox --window-size=1200,630 --screenshot=...`で正しく1200×630のPNGが撮れることを実機で確認済み。`wget`/`timeout`/`dirname`/`find`はAlpineに標準搭載、`python3`は別途`apk add`が必要。
6. **Chromiumの`--screenshot`モードは、ページが存在しない・接続できない場合でも常に終了コード0を返し、エラーページをそのままスクリーンショットとして書き出す。**したがって終了コードだけでは失敗を検知できない。`timeout`コマンドでラップして異常終了/ハングを検知しつつ、出力ファイルが`-s`(存在してサイズ0超)であることも合わせて確認する設計にする。
7. Woodpecker CIの各ステップは同一ワークスペースを共有するため(既存の`deploy`ステップが`build`の`public/`をそのまま参照していることからも既知)、新しい`ogimages`ステップは`build`が生成した`public/`にそのままアクセスできる。

---

### Task 1: Hugo側 — OGPカード出力フォーマット・CSS・テンプレート

**Files:**
- Modify: `hugo.toml`
- Create: `themes/tangentline/assets/css/ogcard.css`
- Create: `themes/tangentline/layouts/partials/ogcard-content.html`
- Create: `themes/tangentline/layouts/_default/single.ogcard.html`
- Create: `themes/tangentline/layouts/_default/list.ogcard.html`

**Interfaces:**
- Produces: 各ページ種のURL配下に`ogcard.html`が生成される(例: `public/ogcard.html`, `public/post/ogcard.html`, `public/tags/ogcard.html`, `public/tags/tech/ogcard.html`, `public/2022/02/09/183050/ogcard.html`)。Task 4のスクリプトはこの`ogcard.html`というファイル名を`find`で検索する。

- [ ] **Step 1: hugo.tomlに`ogcard`出力フォーマットと`[outputs]`を追加し、`params.images`を削除する**

現在の`hugo.toml`の該当箇所:

```toml
[services.rss]
limit = 8

[markup]
```

これを次のように変更する(`[services.rss]`と`[markup]`の間に挿入):

```toml
[services.rss]
limit = 8

[outputFormats.ogcard]
mediaType = "text/html"
baseName = "ogcard"
isPlainText = false
notAlternative = true

[outputs]
home = ["html", "rss", "ogcard"]
section = ["html", "ogcard"]
taxonomy = ["html", "ogcard"]
term = ["html", "ogcard"]
page = ["html", "ogcard"]

[markup]
```

さらに、次の`[params]`ブロック:

```toml
[params]
images = ["siteicon.png"]

[params.footer]
```

を次のように変更する(`[params]`ヘッダーと`images`行を削除し、`[params.footer]`だけを残す):

```toml
[params.footer]
```

- [ ] **Step 2: `themes/tangentline/assets/css/ogcard.css`を作成する**

Writeツールで新規作成:

```css
/* ==========================================================================
   OGPカード(ビルド時にヘッドレスChromiumで撮影する専用ページ用。
   実サイトのHTMLとしては配信されない)
   ========================================================================== */
html { overflow-y: hidden; scrollbar-gutter: auto; }

.ogcard {
  width: 1200px;
  height: 630px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg);
}

.ogcard-inner { width: 1020px; }

.ogcard .site-title { font-size: 40px; }

.ogcard .entry-meta {
  font-size: 22px;
  margin-bottom: 28px;
}

.ogcard .entry-title {
  font-size: 56px;
  line-height: 1.35;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.ogcard .list-title {
  font-size: 44px;
  font-weight: var(--w-title);
  color: var(--c-heading);
  text-align: center;
  font-feature-settings: "palt";
}
```

- [ ] **Step 3: 共有パーシャル`themes/tangentline/layouts/partials/ogcard-content.html`を作成する**

Writeツールで新規作成:

```html
{{- $css := resources.Get "css/main.css" | minify | fingerprint -}}
{{- $ogcss := resources.Get "css/ogcard.css" | minify | fingerprint -}}
<!doctype html>
<html lang="{{ site.Language.Locale }}">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.bunny.net">
<link href="https://fonts.bunny.net/css?family=noto-serif-jp:300,400,500,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{ $css.RelPermalink }}">
<link rel="stylesheet" href="{{ $ogcss.RelPermalink }}">
</head>
<body>
<div class="ogcard">
  <div class="ogcard-inner">
    <header class="masthead">
      <p class="site-title">{{ partial "hang-title.html" site.Title }}</p>
    </header>
    {{- if eq .Kind "page" }}
    <div class="entry-meta">
      <time>{{ .Date.Format "2006年1月2日" }}</time>
      {{- with .Params.tags }}
      <span class="entry-tags">{{- range . }}<a>#{{ . }}</a>{{ end -}}</span>
      {{- end }}
    </div>
    <h1 class="entry-title">{{ .Title }}</h1>
    {{- else if not .IsHome }}
    <p class="list-title">{{ .Title }}</p>
    {{- end }}
  </div>
</div>
</body>
</html>
```

- [ ] **Step 4: 出力フォーマット用テンプレート2つを作成する**

Writeツールで`themes/tangentline/layouts/_default/single.ogcard.html`を新規作成:

```html
{{ partial "ogcard-content.html" . }}
```

Writeツールで`themes/tangentline/layouts/_default/list.ogcard.html`を新規作成:

```html
{{ partial "ogcard-content.html" . }}
```

- [ ] **Step 5: ビルドして各ページ種の`ogcard.html`を確認する**

Run: `cd /home/riq0h/riq0h.jp && rm -rf public && hugo --noBuildLock -e production`

Expected: `WARN`/`ERROR`が出ずに `Total in ...ms` で終わる。

続けて内容を確認する:

Run: `grep -o '<p class="site-title">[^<]*<span class="hang">[^<]*</span></p>' public/ogcard.html`
Expected: `<p class="site-title">点と接線<span class="hang">。</span></p>`

Run: `grep -c 'entry-meta\|entry-title' public/ogcard.html`
Expected: `0` (トップページはマストヘッドのみ)

Run: `grep -o '<p class="list-title">[^<]*</p>' public/post/ogcard.html`
Expected: `<p class="list-title">post</p>`

Run: `grep -o '<p class="list-title">[^<]*</p>' public/tags/ogcard.html`
Expected: `<p class="list-title">tags</p>`

Run: `grep -o '<p class="list-title">[^<]*</p>' public/tags/tech/ogcard.html`
Expected: `<p class="list-title">tech</p>`

Run: `grep -o '<time>[^<]*</time>\|#diary\|<h1 class="entry-title">[^<]*</h1>' public/2022/02/09/183050/ogcard.html`
Expected:
```
<time>2022年2月9日</time>
#diary
<h1 class="entry-title">ビーカーをコーヒーで満たしたい</h1>
```

Run: `find public -name 'ogcard.html' -path '*/page/*' | head -3`
Expected: 出力なし(0件)。`ogcard-content.html`は`.Paginator`を参照しないため、Hugoはページ送り分の`ogcard.html`をそもそも生成しない(検証済みの前提事実 4を参照)

タグが複数ある記事でも正しく表示されることを確認する(`content/post/Google AnalyticsをやめてGoatCounterに乗り換えた.md`, date=2021-03-26T11:28:15+09:00, tags=["tech","diary"]):

Run: `grep -o '<time>[^<]*</time>\|#tech\|#diary\|<h1 class="entry-title">[^<]*</h1>' public/2021/03/26/112815/ogcard.html`
Expected:
```
<time>2021年3月26日</time>
#tech
#diary
<h1 class="entry-title">Google AnalyticsをやめてGoatCounterに乗り換えた</h1>
```

- [ ] **Step 6: コミット**

```bash
git add hugo.toml themes/tangentline/assets/css/ogcard.css themes/tangentline/layouts/partials/ogcard-content.html themes/tangentline/layouts/_default/single.ogcard.html themes/tangentline/layouts/_default/list.ogcard.html
git commit -m "記事ごとのOGPカードを出力フォーマットとして生成する"
```

---

### Task 2: head.html — 404除外とog:image/twitter:imageタグ

**Files:**
- Modify: `themes/tangentline/layouts/partials/head.html`

**Interfaces:**
- Consumes: Task 1で追加された`ogcard`出力フォーマット(このタスクでは`{{ .Permalink }}og.png`という文字列を直接組み立てるだけで、Hugoの出力フォーマットAPIには依存しない)
- Produces: 404以外の全ページで`<meta property="og:image" content="...">`/`<meta name="twitter:image" content="...">`が出力される

- [ ] **Step 1: head.htmlの該当箇所を変更する**

`themes/tangentline/layouts/partials/head.html`の現在の内容(該当部分):

```html
<link rel="canonical" href="{{ .Permalink }}">
{{ template "_internal/opengraph.html" . }}
{{ template "_internal/twitter_cards.html" . }}
{{ with .OutputFormats.Get "rss" -}}
<link rel="alternate" type="application/rss+xml" title="{{ site.Title }}" href="{{ .Permalink }}">
{{- end }}
```

これを次のように変更する:

```html
<link rel="canonical" href="{{ .Permalink }}">
{{ if ne .Kind "404" }}
{{ template "_internal/opengraph.html" . }}
{{ template "_internal/twitter_cards.html" . }}
<meta property="og:image" content="{{ .Permalink }}og.png">
<meta name="twitter:image" content="{{ .Permalink }}og.png">
{{ end }}
{{ with .OutputFormats.Get "rss" -}}
<link rel="alternate" type="application/rss+xml" title="{{ site.Title }}" href="{{ .Permalink }}">
{{- end }}
```

Editツールで`old_string`に前者、`new_string`に後者を指定する。

- [ ] **Step 2: ビルドして404ページと通常ページの出力を確認する**

Run: `cd /home/riq0h/riq0h.jp && rm -rf public && hugo --noBuildLock -e production`
Expected: `WARN`/`ERROR`なしでビルド成功

Run: `grep -c 'og:image\|twitter:image\|opengraph' public/404.html`
Expected: `0`

Run: `grep -o '<meta property="og:image" content="[^"]*">' public/2022/02/09/183050/index.html`
Expected: `<meta property="og:image" content="https://riq0h.jp/2022/02/09/183050/og.png">`

Run: `grep -o '<meta name="twitter:image" content="[^"]*">' public/2022/02/09/183050/index.html`
Expected: `<meta name="twitter:image" content="https://riq0h.jp/2022/02/09/183050/og.png">`

Run: `grep -o '<meta property="og:image" content="[^"]*">' public/page/2/index.html`
Expected: `<meta property="og:image" content="https://riq0h.jp/og.png">` (ページ送りでもページ1のog.pngを指すこと)

- [ ] **Step 3: コミット**

```bash
git add themes/tangentline/layouts/partials/head.html
git commit -m "OGP画像タグをページごとのog.pngに差し替え、404ページでは出力しないようにする"
```

---

### Task 3: 静的フォールバック画像の生成

**Files:**
- Create: `themes/tangentline/images/ogp-fallback.png` (バイナリ、1200×630)

**Interfaces:**
- Produces: Task 4のスクリプトが`FALLBACK_PNG`として参照する固定パス

- [ ] **Step 1: フォールバック用の一時HTMLをWriteツールで作成する**

パス: `/tmp/claude-1000/-home-riq0h-riq0h-jp/0322260f-4002-437b-b080-22a6474821eb/scratchpad/ogp-fallback-source.html`(スクラッチディレクトリ。実行環境によって異なる場合はそのセッションのスクラッチディレクトリを使う)

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1200px; height: 630px; background: #fff; display: flex; align-items: center; justify-content: center; }
  svg { width: 460px; height: 460px; display: block; }
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 900">
  <rect width="900" height="900" fill="#fff"/>
  <path d="M 14.7,1190.6 L 20.9,1136.8 L 27.1,1084.8 L 33.3,1034.7 L 39.5,986.5 L 45.7,940.0 L 52.0,895.2 L 58.2,852.2 L 64.4,810.9 L 70.6,771.3 L 76.8,733.3 L 83.1,697.0 L 89.3,662.2 L 95.5,629.0 L 101.7,597.3 L 107.9,567.2 L 114.2,538.5 L 120.4,511.4 L 126.6,485.6 L 132.8,461.2 L 139.0,438.3 L 145.3,416.6 L 151.5,396.3 L 157.7,377.3 L 163.9,359.6 L 170.1,343.1 L 176.4,327.9 L 182.6,313.8 L 188.8,300.9 L 195.0,289.1 L 201.2,278.4 L 207.4,268.8 L 213.7,260.3 L 219.9,252.8 L 226.1,246.2 L 232.3,240.7 L 238.5,236.1 L 244.8,232.4 L 251.0,229.7 L 257.2,227.8 L 263.4,226.7 L 269.6,226.4 L 275.9,226.9 L 282.1,228.2 L 288.3,230.2 L 294.5,232.9 L 300.7,236.3 L 307.0,240.3 L 313.2,245.0 L 319.4,250.2 L 325.6,256.1 L 331.8,262.4 L 338.1,269.3 L 344.3,276.6 L 350.5,284.5 L 356.7,292.7 L 362.9,301.4 L 369.1,310.4 L 375.4,319.8 L 381.6,329.5 L 387.8,339.5 L 394.0,349.8 L 400.2,360.3 L 406.5,371.0 L 412.7,382.0 L 418.9,393.1 L 425.1,404.3 L 431.3,415.6 L 437.6,427.0 L 443.8,438.5 L 450.0,450.0 L 456.2,461.5 L 462.4,473.0 L 468.7,484.4 L 474.9,495.7 L 481.1,506.9 L 487.3,518.0 L 493.5,529.0 L 499.8,539.7 L 506.0,550.2 L 512.2,560.5 L 518.4,570.5 L 524.6,580.2 L 530.9,589.6 L 537.1,598.6 L 543.3,607.3 L 549.5,615.5 L 555.7,623.4 L 561.9,630.7 L 568.2,637.6 L 574.4,643.9 L 580.6,649.8 L 586.8,655.0 L 593.0,659.7 L 599.3,663.7 L 605.5,667.1 L 611.7,669.8 L 617.9,671.8 L 624.1,673.1 L 630.4,673.6 L 636.6,673.3 L 642.8,672.2 L 649.0,670.3 L 655.2,667.6 L 661.5,663.9 L 667.7,659.3 L 673.9,653.8 L 680.1,647.2 L 686.3,639.7 L 692.6,631.2 L 698.8,621.6 L 705.0,610.9 L 711.2,599.1 L 717.4,586.2 L 723.6,572.1 L 729.9,556.9 L 736.1,540.4 L 742.3,522.7 L 748.5,503.7 L 754.7,483.4 L 761.0,461.7 L 767.2,438.8 L 773.4,414.4 L 779.6,388.6 L 785.8,361.5 L 792.1,332.8 L 798.3,302.7 L 804.5,271.0 L 810.7,237.8 L 816.9,203.0 L 823.2,166.7 L 829.4,128.7 L 835.6,89.1 L 841.8,47.8 L 848.0,4.8 L 854.3,-40.0 L 860.5,-86.5 L 866.7,-134.7 L 872.9,-184.8 L 879.1,-236.8 L 885.3,-290.6" fill="none" stroke="#080808" stroke-width="4" stroke-linecap="butt"/>
  <circle cx="450" cy="450" r="62" fill="none" stroke="#080808" stroke-width="4"/>
</svg>
</body>
</html>
```

- [ ] **Step 2: ローカルのGoogle Chromeでスクリーンショットを撮る**

Run: `google-chrome-stable --headless=new --disable-gpu --no-sandbox --window-size=1200,630 --screenshot=/home/riq0h/riq0h.jp/themes/tangentline/images/ogp-fallback.png "file:///tmp/claude-1000/-home-riq0h-riq0h-jp/0322260f-4002-437b-b080-22a6474821eb/scratchpad/ogp-fallback-source.html"`

Expected: `... bytes written to file .../ogp-fallback.png`

- [ ] **Step 3: 生成物を確認する**

Run: `file themes/tangentline/images/ogp-fallback.png`
Expected: `themes/tangentline/images/ogp-fallback.png: PNG image data, 1200 x 630, ...`

- [ ] **Step 4: 一時HTMLを削除し、コミット**

```bash
rm -f /tmp/claude-1000/-home-riq0h-riq0h-jp/0322260f-4002-437b-b080-22a6474821eb/scratchpad/ogp-fallback-source.html
git add themes/tangentline/images/ogp-fallback.png
git commit -m "OGPスクリーンショット失敗時の静的フォールバック画像を追加"
```

---

### Task 4: scripts/generate-og-images.sh

**Files:**
- Create: `scripts/generate-og-images.sh`

**Interfaces:**
- Consumes: Task 1が生成する`public/**/ogcard.html`、Task 3の`themes/tangentline/images/ogp-fallback.png`
- Produces: `public/**/og.png`(ページ送り由来の複製を除く)。実行後`ogcard.html`は1つも残らない。1件でもスクリーンショットに失敗した場合は非ゼロ終了。

- [ ] **Step 1: スクリプトをWriteツールで作成する**

`scripts/generate-og-images.sh`:

```sh
#!/bin/sh
set -eu

PUBLIC_DIR="public"
PORT=8080
FALLBACK_PNG="themes/tangentline/images/ogp-fallback.png"

python3 -m http.server "$PORT" --directory "$PUBLIC_DIR" >/tmp/og-http-server.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

for i in $(seq 1 30); do
  if wget -q -O /dev/null "http://localhost:$PORT/" 2>/dev/null; then
    break
  fi
  sleep 0.2
done

find "$PUBLIC_DIR" -name 'ogcard.html' > /tmp/og-ogcard-list.txt

FAILED=0

while IFS= read -r f; do
  dir=$(dirname "$f")
  rel=${f#"$PUBLIC_DIR"}
  case "$rel" in
    */page/*)
      rm -f "$f"
      continue
      ;;
  esac
  url="http://localhost:$PORT${rel}"
  if timeout 20 chromium --headless=new --disable-gpu --no-sandbox \
      --window-size=1200,630 --virtual-time-budget=1500 \
      --screenshot="$dir/og.png" "$url" >/tmp/og-chromium.log 2>&1 \
     && [ -s "$dir/og.png" ]; then
    :
  else
    echo "WARN: OGP screenshot failed for $url" >&2
    cat /tmp/og-chromium.log >&2
    cp "$FALLBACK_PNG" "$dir/og.png"
    FAILED=1
  fi
  rm -f "$f"
done < /tmp/og-ogcard-list.txt

if [ "$FAILED" -eq 1 ]; then
  echo "One or more OGP screenshots failed; static fallback image was used." >&2
  exit 1
fi
exit 0
```

- [ ] **Step 2: 実行権限を付与する**

Run: `chmod +x scripts/generate-og-images.sh`

- [ ] **Step 3: ローカルでスクリプトを検証する(chromium互換のbinaryがなければ`google-chrome-stable`で代用して一時的に検証)**

まず、このマシンには`chromium`ではなく`google-chrome-stable`が入っているため、検証専用に一時コピーを作りコマンド名だけ差し替えて実行する。

Run: `cd /home/riq0h/riq0h.jp && rm -rf public && hugo --noBuildLock -e production`

Run: `sed 's/chromium --headless/google-chrome-stable --headless/' scripts/generate-og-images.sh > /tmp/generate-og-images-local-test.sh && sh /tmp/generate-og-images-local-test.sh; echo "exit=$?"`

Expected: `exit=0`

Run: `find public -name 'ogcard.html' | wc -l`
Expected: `0`

Run: `file public/og.png public/2022/02/09/183050/og.png public/tags/tech/og.png public/2021/03/26/112815/og.png`
Expected: 4行とも `PNG image data, 1200 x 630, ...`

Readツールで`public/2021/03/26/112815/og.png`(タグ2つ・比較的長いタイトル)を目視確認する。マストヘッド・日付・2つのタグ・タイトルが3行以内に収まってバランスよく表示されていることを確認する。もし3行に収まらずレイアウトが崩れる場合は、`ogcard.css`の`.ogcard .entry-title`のフォントサイズを調整する。

Run: `rm -f /tmp/generate-og-images-local-test.sh`

- [ ] **Step 4: わざと1件だけ失敗させてフォールバックを確認する**

Run: `cd /home/riq0h/riq0h.jp && rm -rf public && hugo --noBuildLock -e production`

Run: `mv public/tags/tech/ogcard.html /tmp/tech-ogcard-backup.html && printf '<html><body><script>fetch("http://10.255.255.1/").then(()=>{}) ;</script></body></html>' > public/tags/tech/ogcard.html`

(この壊れたページは`--virtual-time-budget`のタイムアウト内で応答が返らないネットワーク先を参照するため、正常なレンダリングにならないことを期待する。もし依然として`exit=0`かつ正しいog.pngが生成される場合は、フォールバック検知の条件を`-s`のファイルサイズ閾値など、より厳密な形に見直すこと。)

Run: `sed 's/chromium --headless/google-chrome-stable --headless/' scripts/generate-og-images.sh > /tmp/generate-og-images-local-test.sh && sh /tmp/generate-og-images-local-test.sh; echo "exit=$?"`

Expected: `exit=1`、標準エラーに`WARN: OGP screenshot failed`が出力される

Run: `cmp public/tags/tech/og.png themes/tangentline/images/ogp-fallback.png && echo "fallback used correctly"`
Expected: `fallback used correctly`

Run: `rm -f /tmp/generate-og-images-local-test.sh /tmp/tech-ogcard-backup.html`

- [ ] **Step 5: コミット**

```bash
git add scripts/generate-og-images.sh
git commit -m "OGPカードHTMLをスクリーンショットしてog.pngに変換するスクリプトを追加"
```

---

### Task 5: Woodpecker CIへの組み込み

**Files:**
- Modify: `.woodpecker/.woodpecker.yml`

**Interfaces:**
- Consumes: Task 4の`scripts/generate-og-images.sh`

- [ ] **Step 1: `.woodpecker/.woodpecker.yml`を変更する**

現在の内容:

```yaml
clone:
  git:
    image: woodpeckerci/plugin-git
    settings:
      recursive: true
      partial: false
      depth: 1

steps:
  build:
    image: hugomods/hugo:base
    commands:
      - hugo --noBuildLock

  deploy:
    image: drillster/drone-rsync
    settings:
      hosts:
        from_secret: HOST
      user:
        from_secret: USER
      key:
        from_secret: SSH
      port:
        from_secret: PORT
      source: public
      target: /var/www/html
```

これを次のように変更する(`build`と`deploy`の間に`ogimages`を挿入):

```yaml
clone:
  git:
    image: woodpeckerci/plugin-git
    settings:
      recursive: true
      partial: false
      depth: 1

steps:
  build:
    image: hugomods/hugo:base
    commands:
      - hugo --noBuildLock

  ogimages:
    image: hugomods/hugo:base
    commands:
      - apk add --no-cache chromium python3
      - sh ./scripts/generate-og-images.sh

  deploy:
    image: drillster/drone-rsync
    settings:
      hosts:
        from_secret: HOST
      user:
        from_secret: USER
      key:
        from_secret: SSH
      port:
        from_secret: PORT
      source: public
      target: /var/www/html
```

- [ ] **Step 2: YAML構文を確認する**

Run: `python3 -c "import yaml, sys; yaml.safe_load(open('.woodpecker/.woodpecker.yml'))" && echo "valid yaml"`
Expected: `valid yaml`

- [ ] **Step 3: コミット**

```bash
git add .woodpecker/.woodpecker.yml
git commit -m "WoodpeckerにOGP画像生成ステップを追加する"
```

- [ ] **Step 4: 作業ブランチでCIを実際に走らせて確認する(ユーザー確認が必要)**

このステップはローカルでは完結しない。ユーザーに作業ブランチをpushしてもらい、Woodpecker CI上で`ogimages`ステップがChromiumインストールからスクリーンショットまで成功することを確認してもらう。あわせて、デプロイ後にTwitter Card ValidatorやFacebookのシェアデバッガー等で実際に`og:image`が取得・表示されるかも確認する(設計書 検証方法 6・7に対応)。

---

## 実装後の最終確認チェックリスト

- [ ] `hugo --noBuildLock -e production`でエラーなくビルドできる
- [ ] `public/`以下に`ogcard.html`が1つも残っていない(スクリプト実行後)
- [ ] トップ・記事1件・タグページ・タグ索引・投稿一覧それぞれで`og.png`が1200×630で生成されている
- [ ] 404ページに`og:image`/`twitter:image`/`opengraph`関連タグが一切出力されていない
- [ ] ページ送り(`/page/2/`等)の`og:image`がページ1と同じURLを指している
- [ ] 256記事ぶんの処理でビルド時間がどの程度伸びるかを実測する(設計書 検証方法 5)
- [ ] 作業ブランチでWoodpecker CIを実際に走らせ、Chromiumインストールからスクリーンショットまで成功することを確認する
- [ ] デプロイ後、Twitter Card Validator・Facebookシェアデバッガー等で実画像が取得・表示されることを確認する
