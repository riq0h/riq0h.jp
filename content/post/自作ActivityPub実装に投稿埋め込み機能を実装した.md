---
title: "自作ActivityPub実装に投稿埋め込み機能を実装した"
date: 2025-12-05T15:52:55+09:00
draft: true
tags: ["tech"]
---

本稿は[Fediverse Advent Calendar 2025](https://adventar.org/calendars/12280)の7日目の記事である。僕は[自作のActivityPub実装](https://riq0h.jp/2025/07/11/163822/)を運用している。詳細は左記のリンク先に譲るとして、簡単に説明するとRails8とHotwireで構築された一人専用の実装系だ。内蔵クライアントを持たず、フロントエンド部分は閲覧にのみ対応している。

このような最小限の構成に手馴染みの良さを感じている一方、リッチな既存の実装系と比べるとやはり機能の不足は否めない。僕にとってその最たるものが投稿埋め込み機能であった。ブロガーにとってこれはとりわけ重要なキーアイテムと言っても過言ではない。

投稿埋め込み機能があれば追加の説明なしにコンテキストを挿入できるし、一度投稿した画像も使い回せる。フレームによって境界が区切られているからアイキャッチ的にも使える。アカウントの存在を周知することでフォロワーの増加にも繋がる。まさに良いことづくめの実にすばらしい機能なのだ。

そこで、自作ActivityPub実装に本機能を実装した。自分ひとりだけが利用する実装系であり、基本的に自分以外の投稿が埋め込まれる可能性を考慮しなくても良かったので、通常のiframe利用と比べて警戒すべき点はそう多くなかったように思われる。

## 設計方針

MastodonはReactとReduxで埋め込み部分をレンダリングしていたが、僕の実装系はHotwireベースなのでより簡潔にまとめられると考えた。具体的にはReactを排除してERBテンプレートを直接レンダリングし、バニラJSでシンプルにiframeを制御する。

```javascript
(function () {
  "use strict";

  const embeds = new Map();

  function generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  function init() {
    // 埋め込み要素を探す
    document.querySelectorAll("div.letter-embed").forEach(function (container) {
      const embedUrl = container.getAttribute("data-embed-url");
      if (!embedUrl) return;

      const id = generateId();
      const iframe = document.createElement("iframe");

      iframe.src = embedUrl;
      iframe.width = "100%";
      iframe.height = "400"; // 初期高さ
      iframe.style.border = "none";
      iframe.style.overflow = "hidden";
      iframe.style.display = "block";
      iframe.sandbox =
        "allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox";
      iframe.setAttribute("loading", "lazy");
      iframe.setAttribute("scrolling", "no");

      embeds.set(id, iframe);

      iframe.onload = function () {
        iframe.contentWindow.postMessage(
          {
            type: "setHeight",
            id: id,
          },
          "*",
        );
      };

      // コンテナの中身をクリアしてiframeだけを残す
      container.innerHTML = "";
      container.appendChild(iframe);

      // コンテナのスタイルをリセット
      container.style.margin = "0";
      container.style.padding = "0";
      container.style.border = "none";
      container.style.background = "none";
      container.style.overflow = "hidden";
    });
  }

  // 高さ調整メッセージを受信
  window.addEventListener("message", function (e) {
    if (e.data && e.data.type === "setHeight" && e.data.height) {
      embeds.forEach(function (iframe) {
        if (iframe.contentWindow === e.source) {
          iframe.height = e.data.height;
        }
      });
    }
  });

  // DOMContentLoaded後に実行
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
```

また、画面デザインも特殊な装飾は一切行わずにフロントエンド部のビューをほぼ再利用する。Mastodonをはじめ多くのActivityPub実装は、利用者を増やそうとするモチベーションが存在しているために華美なロゴやスタイリング、キャッチコピーなどが表示されていることが多い。

対して、僕の実装系はごく個人的なプロジェクトで目的意識がないゆえ質素なデザインで済む。ページ上でSNSとそれ以外を隔てる境界として機能しつつ、それでいてブログの世界観を壊さない。そのような形が望ましい。

## 実装内容

巷に蔓延る埋め込みページには固定サイズを超えるコンテンツ（画像や長文など）に対応せず、そのまま見切れたりスクロールバーを露出させる代物が少なくない。破綻した境界は世界観を壊す。埋め込み機能が美しくあるには自分の世界を内側に押し留める努力をしなければならない。

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="robots" content="noindex" />
    <%= stylesheet_link_tag "application", "data-turbo-track": "reload" %> <%=
    stylesheet_link_tag "tailwind", "data-turbo-track": "reload" %>

    <style>
      html,
      body {
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: "Noto Sans JP", sans-serif;
        font-weight: 400;
        font-size: 16px;
        overflow: hidden;
      }
    </style>
  </head>
  <body class="embed">
    <%= yield %>

    <script>
      (function () {
        let lastHeight = 0;

        function notifyHeight() {
          const height = Math.max(
            document.documentElement.scrollHeight,
            document.body.scrollHeight,
          );

          if (height !== lastHeight) {
            lastHeight = height;
            window.parent.postMessage(
              {
                type: "setHeight",
                height: height,
              },
              "*",
            );
          }
        }

        window.addEventListener("load", notifyHeight);

        const observer = new MutationObserver(notifyHeight);
        observer.observe(document.body, {
          childList: true,
          subtree: true,
        });

        if ("ResizeObserver" in window) {
          const resizeObserver = new ResizeObserver(notifyHeight);
          resizeObserver.observe(document.body);
        }
      })();
    </script>
  </body>
</html>
```

本機能の実装では、上記の通り`postMessage`で親ウインドウに高さを通知し、`MutationObserver`と`ResizeObserver`で動的なリサイズに対応した。画像の読み込みも監視して全体のサイズが確定してから描写を開始する仕組みだ。

フロントエンド側では埋め込みボタンを設置する。[letter.mystech.ink](https://letter.mystech.ink)の任意の投稿の詳細画面に遷移して、右下のクリップボードアイコンをクリックすると埋め込みコードを取得できる。あえてハンバーガーメニューなどにしなかったのは、こうしてボタンを横に並べていけばそのうちオールドマッキントッシュのドックみたいになるのではないかと期待しているからだ。

今のところ、皆さんは僕のSNSの投稿を任意のWebページ上に埋め込むことができる。自作ActivityPub実装の投稿が、さらに自作の機能によってどこかに埋め込まれているのを見るのはなかなかの誉れである。じゃんじゃん埋め込んでもらって構わない。

## トラブルシューティング

Cloudflare絡みでいくつか引っかかった点があったので共有したい。まず、投稿埋め込み機能を実装する都合上、Rails側でX-Frame-Optionsを許可しなければならないが、Cloudflare側でも同様のルールを作成しておかないと弾かれてしまう。Cloudflareのトップページからドメイン → ルール → 概要に進んで「レスポンスヘッダー変換ルール」から以下の要領で作成する。

![](/img/435.png)

次に、投稿埋め込み機能のJavaScriptがキャッシングされると更新しても古いスクリプトが動き続けてしまうので、同じく「キャッシュルール」から以下の要領で`/embed.js`をキャッシュの例外に設定する。以上で問題は解決される。

![](/img/436.png)

## まとめ

<div class="letter-embed" data-embed-url="https://letter.mystech.ink/@riq0h/20092815569287592/embed">
  <a href="https://letter.mystech.ink/@riq0h/20092815569287592">@riq0hの投稿を見る</a>
</div>
<script async src="https://letter.mystech.ink/embed.js"></script>

実装ハードルが高いと聞いていた投稿埋め込み機能であったが、主に自分しか使わないActivityPub実装であったこと、自分の求める機能やデザインが最小限であったこと、Claude Sonnet 4.5が頑張ってくれたことなどによって比較的簡単に実装できた。
