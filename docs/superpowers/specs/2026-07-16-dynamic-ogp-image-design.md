# 記事ごとの動的OGP画像生成 設計書

日付: 2026-07-16
対象: riq0h.jp (Hugo製ブログ「点と接線。」、tangentlineテーマ)
状態: 承認済み

## 目的

現状は全ページ共通の静的OGP画像(サイトアイコン)を使っているが、記事ごとに実際のマストヘッド・日付・タグ・記事タイトルを反映した専用のOGP画像を、ビルド時に自動生成できるようにする。デザインの二重管理を避けるため、実サイトのCSS変数・パーシャルをできる限り再利用する。

## 制約・前提

- Woodpecker CI(ユーザー自身のサーバーで稼働、計算資源上の制約なし)を使う。ビルドイメージは`hugomods/hugo:base`(Alpine系)
- Facebook/Twitter等のOGPクローラーは`og:image`にSVGを受け付けずラスター画像(PNG/JPEG)が必須のため、「動的生成」は実質「ビルド時に記事ごとに個別のPNGを1枚ずつ書き出す」形になる(実行時の真の動的生成ではない)
- フォント(Noto Serif JP)はビルド時にbunny.netへ実際にアクセスして読み込む(自前同梱はしない)
- 静的フォールバック画像には三次関数版の意匠を採用し、`themes/tangentline/images/ogp-fallback.png`(1200×630、実装時に生成)として配置する

## 1. アーキテクチャ

処理は3段階のパイプラインとして実装する。

```
① Hugoビルド
   通常のindex.html群に加え、対象ページ種それぞれについて
   OGPカード専用の最小HTML(ogcard.html)を同じディレクトリに書き出す
   (Hugoのカスタム出力フォーマット機能を使用)

② スクリーンショット変換(ビルド後、Woodpecker内)
   public/**/ogcard.html を全て見つけ、ヘッドレスChromiumで
   1200x630pxのビューポートのまま撮影しog.pngとして同じ場所に保存。
   処理後、中間HTML(ogcard.html)は削除する

③ 配信
   head.htmlのog:image / twitter:imageを
   「そのページの{{ .RelPermalink }}og.png」を指す独自タグに差し替える
```

## 2. OGPカードの視覚設計

**キャンバス**: 1200×630px、背景`--c-bg`(白)。コンテンツ全体を縦横中央に配置し、記事タイトルの行数が変わっても常にバランスが取れるようにする。

**共通パーツ(対象ページ種すべて)**:
- マストヘッド: 「点と接線。」を実サイトと同じ末尾ぶら下げ処理(hang-title.htmlパーシャルを再利用)付きで中央揃え(40px・weight `var(--w-title)`・字間.12em・色`var(--c-heading)`)
- その下に一重線(`var(--c-rule)`、実サイトの罫線と同一)

**ページ種ごとの下部コンテンツ**:

| ページ種 | 表示内容 |
|---|---|
| 記事ページ(kind=page) | 日付(左)+タグ(右)の行(22px・weight `var(--w-meta)`・色`var(--c-meta)`) → 記事タイトル(56px・weight `var(--w-title)`・色`var(--c-heading)`、左揃え、最大3行) |
| トップページ(IsHome) | マストヘッド+罫線のみ |
| 投稿一覧・タグページ・タグ索引 | `.Title`をそのまま(44px・weight `var(--w-title)`) |
| 404 | 対象外(後述) |

色・太さは新規の値を作らず、実サイトの`main.css`で定義済みの`--c-heading`/`--w-title`等のCSSカスタムプロパティをそのまま参照する(main.cssを実際にlinkして使う)。これにより将来サイトの配色・ウェイトを調整した際、OGPカードも自動的に追従する。

**ページ送り(`/page/2/`等)の扱い**: OGPカードは各一覧(トップ・投稿一覧・タグページ)の1ページ目についてのみ生成する。2ページ目以降は1ページ目と同じ`og.png`を指す(ページ送りごとに個別のOGカードは作らない)。

## 3. 404ページの扱い

Hugoは404ページに`.Kind == "404"`という特別な種別を割り当てる。`head.html`で`{{ if ne .Kind "404" }}`により、OGP関連のメタタグ(`_internal/opengraph.html`・`_internal/twitter_cards.html`の呼び出しと、後述の独自og:image/twitter:imageタグ)を丸ごとスキップする。404ページはOGカード自体を生成しない(出力フォーマットの対象からも除外)。

## 4. og:image / twitter:imageの差し込み方

Hugo内蔵のOGPテンプレートは`site.Params.images`をフォールバック画像として使うが、今回は「対象ページには必ずページごとの`og.png`が存在する」設計にするため、内蔵テンプレートの自動画像解決には頼らない。

- `_internal/opengraph.html`・`_internal/twitter_cards.html`は引き続き呼び出す(タイトル・URL・サイト名・ロケール等はこれに任せる)
- **画像タグだけは自分たちで明示的に1本追加**する: `<meta property="og:image" content="{{ .Permalink }}og.png">` / `<meta name="twitter:image" content="{{ .Permalink }}og.png">`
- `hugo.toml`の`params.images = ["siteicon.png"]`は不要になるため削除する(内蔵テンプレートがこれを見て別のog:imageタグを重複出力してしまうのを防ぐため)

## 5. ビルドパイプラインの変更

`.woodpecker/.woodpecker.yml`の`build`ステップの後に、新しいステップ`ogimages`を追加する。

```yaml
ogimages:
  image: hugomods/hugo:base
  commands:
    - apk add --no-cache chromium
    - ./scripts/generate-og-images.sh
```

`scripts/generate-og-images.sh`の役割:
1. `public/`以下の全`ogcard.html`を`find`で列挙
2. それぞれをヘッドレスChromium(`--headless=new --disable-gpu --no-sandbox --window-size=1200,630 --screenshot=<同じディレクトリ>/og.png`)で撮影
3. 撮影後、`ogcard.html`自体を削除する(本番サイトに中間HTMLが実在URLとして漏れ出さないようにするため必須)

## 6. 失敗時の挙動

- **Chromiumのインストール自体が失敗した場合**: ビルド全体を失敗させ、デプロイを止める
- **特定ページ1件だけスクリーンショットに失敗した場合**: そのページの`og.png`として静的フォールバック画像(`themes/tangentline/images/ogp-fallback.png`)をコピーし、処理は最後まで継続する。ただし最終的にスクリプトは非ゼロ終了し、ビルド全体を失敗扱いにして気づけるようにする(サイレントに握りつぶさない)

## 7. 検証方法

1. ローカルで`hugo`実行後、トップ・記事1件・タグページ・タグ索引・投稿一覧それぞれで`ogcard.html`が正しい場所に生成されているか確認
2. `scripts/generate-og-images.sh`をローカルで単体実行し、各ページ種で`og.png`が1200×630で正しい見た目になっているか目視確認(記事タイトルが長い場合・タグが複数ある場合も含む)
3. 処理後に`ogcard.html`が1つも残っていないことを確認
4. 各ページの`head.html`出力が正しく`{{ .Permalink }}og.png`を指しているか確認。404ページにはOGP系メタタグが一切出力されていないことも確認
5. 256記事ぶんの処理でビルド時間がどの程度伸びるか実測
6. 作業ブランチで実際にWoodpecker CI上のビルドを走らせ、Chromiumインストールからスクリーンショットまで一連の流れが成功するか確認
7. デプロイ後、Twitter Card ValidatorやFacebookのシェアデバッガー等で実際に画像が取得・表示されるか確認
8. わざと1ページだけ撮影に失敗させ、静的画像へのフォールバックとビルド全体の失敗扱いが設計通りに動くか確認

## 8. スコープ外

- 404以外の将来的な新ページ種(現状存在しないため未対応)
- Chromiumインストールのビルド間キャッシュ最適化(現時点では計算資源上の制約がないため見送り)
- favicon(別途対応済み・本設計の対象外)
