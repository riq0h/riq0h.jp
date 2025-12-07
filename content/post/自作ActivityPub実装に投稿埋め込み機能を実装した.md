---
title: "自作ActivityPub実装に投稿埋め込み機能を実装した"
date: 2025-12-07T18:08:55+09:00
draft: false
tags: ["tech"]
---

本稿は[Fediverse Advent Calendar 2025](https://adventar.org/calendars/12280)の7日目の記事である。僕は[自作のActivityPub実装](https://riq0h.jp/2025/07/11/163822/)を運用している。詳細は左記のリンク先に譲るとして、簡単に説明するとRails 8とHotwireで構築された一人専用の実装系だ。内蔵クライアントを持たず、フロントエンドは閲覧にのみ対応している。

[フロントエンド部分](https://letter.mystech.ink)はリアルなマイクロブログとして機能させるためにLikeやRTに相当するアクティビティは可視化せず、代わりにRSSを通じて投稿を取得できる。外からは昔の質素な一言ブログのように見えるが、内部では共通の通信規格で交信を行っている分散型SNSソフトウェアと捉えてもらうと話が早い。

このようなミニマルな構成に手馴染みの良さを感じている一方、リッチな既存の実装系と比べるとやはり機能の不足は否めない。同種のソフトウェアであるMastodonやMisskeyには非常に多くの外部向け機能が備わっており、僕にとってその最たるものが投稿埋め込み機能であった。ブロガーにとってこれは、とりわけ重要なアイテムと言っても過言ではない。（以下はMastodonの例）

<blockquote class="mastodon-embed" data-embed-url="https://mastodon.social/@Gargron/115605334176250687/embed" style="background: #FCF8FF; border-radius: 8px; border: 1px solid #C9C4DA; margin: 0; max-width: auto; min-width: auto; overflow: hidden; padding: 0;"> <a href="https://mastodon.social/@Gargron/115605334176250687" target="_blank" style="align-items: center; color: #1C1A25; display: flex; flex-direction: column; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', Roboto, sans-serif; font-size: 14px; justify-content: center; letter-spacing: 0.25px; line-height: 20px; padding: 24px; text-decoration: none;"> <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="32" height="32" viewBox="0 0 79 75"><path d="M63 45.3v-20c0-4.1-1-7.3-3.2-9.7-2.1-2.4-5-3.7-8.5-3.7-4.1 0-7.2 1.6-9.3 4.7l-2 3.3-2-3.3c-2-3.1-5.1-4.7-9.2-4.7-3.5 0-6.4 1.3-8.6 3.7-2.1 2.4-3.1 5.6-3.1 9.7v20h8V25.9c0-4.1 1.7-6.2 5.2-6.2 3.8 0 5.8 2.5 5.8 7.4V37.7H44V27.1c0-4.9 1.9-7.4 5.8-7.4 3.5 0 5.2 2.1 5.2 6.2V45.3h8ZM74.7 16.6c.6 6 .1 15.7.1 17.3 0 .5-.1 4.8-.1 5.3-.7 11.5-8 16-15.6 17.5-.1 0-.2 0-.3 0-4.9 1-10 1.2-14.9 1.4-1.2 0-2.4 0-3.6 0-4.8 0-9.7-.6-14.4-1.7-.1 0-.1 0-.1 0s-.1 0-.1 0 0 .1 0 .1 0 0 0 0c.1 1.6.4 3.1 1 4.5.6 1.7 2.9 5.7 11.4 5.7 5 0 9.9-.6 14.8-1.7 0 0 0 0 0 0 .1 0 .1 0 .1 0 0 .1 0 .1 0 .1.1 0 .1 0 .1.1v5.6s0 .1-.1.1c0 0 0 0 0 .1-1.6 1.1-3.7 1.7-5.6 2.3-.8.3-1.6.5-2.4.7-7.5 1.7-15.4 1.3-22.7-1.2-6.8-2.4-13.8-8.2-15.5-15.2-.9-3.8-1.6-7.6-1.9-11.5-.6-5.8-.6-11.7-.8-17.5C3.9 24.5 4 20 4.9 16 6.7 7.9 14.1 2.2 22.3 1c1.4-.2 4.1-1 16.5-1h.1C51.4 0 56.7.8 58.1 1c8.4 1.2 15.5 7.5 16.6 15.6Z" fill="currentColor"/></svg> <div style="color: #787588; margin-top: 16px;">Post by @Gargron@mastodon.social</div> <div style="font-weight: 500;">View on Mastodon</div> </a> </blockquote> <script data-allowed-prefixes="https://mastodon.social/" async src="https://mastodon.social/embed.js"></script>
<br>

投稿埋め込み機能があれば追加の説明なしにコンテキストを挿入できるし、一度投稿した画像も使い回せる。フレームによって境界が区切られているのでアイキャッチ的にも使える。アカウントの存在が周知されてフォロワーの増加にも繋がる。まさに良いことづくめの実にすばらしい機能なのだ。

そこで、自作ActivityPub実装に本機能を実装した。自分ひとりだけが利用する実装系であり、基本的に自分以外の投稿が埋め込まれる可能性を考慮しなくても良かったので、通常のiframe利用と比べて警戒すべき点はそう多くなかったように思われる。以下、解説を行う。

## 設計方針

MastodonはJSON APIを介してReactで埋め込み部分をレンダリングしていたが、僕の実装系はHotwireベースなのでより簡潔にまとめられると考えた。具体的にはサーバ側でERBテンプレートをレンダリングし、バニラJSでシンプルにiframeを制御する。

```javascript
// embed.js
(function() {
  'use strict';

  const embeds = new Map();

  function generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  function init() {
    document.querySelectorAll('div.letter-embed').forEach(function(container) {
      const embedUrl = container.getAttribute('data-embed-url');
      if (!embedUrl) return;

      const id = generateId();
      const iframe = document.createElement('iframe');

      iframe.src = embedUrl;
      iframe.width = '100%';
      iframe.height = '400';
      iframe.style.border = 'none';
      iframe.style.overflow = 'hidden';
      iframe.style.display = 'block';
      iframe.sandbox =
        'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox';
      iframe.setAttribute('loading', 'lazy');
      iframe.setAttribute('scrolling', 'no');

      embeds.set(id, iframe);

      iframe.onload = function() {
        iframe.contentWindow.postMessage(
          {
            type: 'setHeight',
            id: id
          },
          '*'
        );
      };

      container.innerHTML = '';
      container.appendChild(iframe);

      container.style.margin = '0';
      container.style.padding = '0';
      container.style.border = 'none';
      container.style.background = 'none';
      container.style.overflow = 'hidden';
    });
  }

  window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'setHeight' && e.data.height) {
      embeds.forEach(function(iframe) {
        if (iframe.contentWindow === e.source) {
          iframe.height = e.data.height;
        }
      });
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
```

また、画面デザインも特殊な装飾は一切行わずにフロントエンドのビューをほぼ再利用する。Mastodonをはじめ多くのActivityPub実装は、利用者を増やそうとするモチベーションが存在しているために華美なロゴやスタイリング、キャッチコピーなどが表示されていることが多い。

対して、僕の実装系はごく個人的なプロジェクトで目的意識がないゆえ簡素なデザインで済む。元のフロントエンド部分と同じくLikeやRTに相当する表示領域もいらない。ページ上で本文を隔てる境界として機能しつつ、それでいて挿入される場所の世界観を壊さない。そのような形が望ましい。

## 実装内容

巷に蔓延る埋め込み機能には特定のサイズを超えるコンテンツ（画像や長文など）に対応しきれず、そのまま見切れたり、逆にはみ出したり、スクロールバーを露出させる代物が少なくない。破綻した境界は世界観を壊す。埋め込み機能が美しくあるには自己の領分を押し留める努力をしなければならない。

```javascript
// embedded.html.erb
    (function () {
      let lastHeight = 0;

      function notifyHeight() {
        const article = document.querySelector('article');
        const height = article ? article.offsetHeight + 1 : Math.max(
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

      const mediaElements = document.querySelectorAll('img, video, iframe');
      mediaElements.forEach(function(el) {
        el.addEventListener('load', notifyHeight);
        el.addEventListener('error', notifyHeight);
      });

      let checkCount = 0;
      const intervalId = setInterval(function() {
        notifyHeight();
        checkCount++;
        if (checkCount >= 10) {
          clearInterval(intervalId);
        }
      }, 500);
    })();
```

本機能の実装では、上記の通り`postMessage`で親ウインドウに高さを通知し、`MutationObserver`と`ResizeObserver`で動的なリサイズに対応した。画像の読み込みも監視して、全体のサイズが確定してから描写を開始する仕組みだ。特定の解像度での見切れを防止するために1pxの余白も追加している。大抵の環境ではうまく働いてくれると思う。

フロントエンド側には埋め込みコードのコピーボタンを設置してある。任意の投稿の時刻表示から詳細画面に遷移して、右下のクリップボードアイコンをクリックすると埋め込みコードを取得できる。こうした便利アイコンをあえてまとめずに横に並べていくと、そのうち昔のマッキントッシュのようなレトロ感を出せると期待している。

今のところ、皆さんは僕のSNSの投稿を任意のWebページ上に埋め込むことができる。自作ActivityPub実装の投稿が、さらに自作の機能によってどこかに埋め込まれているのを見るのはなかなかの誉れである。自分の言葉を伝播せしめている実感がある。じゃんじゃん埋め込んでもらって構わない。特定の条件下で機能しないなどのフィードバックも随時募集している。

## トラブルシューティング

Cloudflare絡みでいくつか引っかかった点があったので共有したい。まず、投稿埋め込み機能を実装する都合上、Rails側でX-Frame-Optionsを許可しなければならないが、Cloudflare側でも同様のルールを作成しておかないと弾かれてしまう。Cloudflareのトップページからドメイン → ルール → 概要に進んで「レスポンスヘッダー変換ルール」から以下の要領で作成する。

![](/img/435.png)

次に、投稿埋め込み機能のJavaScriptがキャッシングされると更新しても古いスクリプトが動き続けてしまうので、同じく「キャッシュルール」から以下の要領で`/embed.js`をキャッシュの例外に設定する。以上で問題が解決される。

![](/img/436.png)

## まとめ

<div class="letter-embed" data-embed-url="https://letter.mystech.ink/@riq0h/20092815569287592/embed">
  <a href="https://letter.mystech.ink/@riq0h/20092815569287592">@riq0hの投稿を見る</a>
</div>
<script async src="https://letter.mystech.ink/embed.js"></script>

実装のハードルが高いと聞いていた投稿埋め込み機能であったが、主に自分しか使わないActivityPub実装であったこと、求める機能性やデザインが最小限であったこと、あとClaude Sonnet 4.5が頑張ってくれたことなどによって比較的簡単に実装できた。
