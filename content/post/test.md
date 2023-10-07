---
title: "Nextcloudでもうなんか色々と所有する"
date: 2023-10-07T20:34:07+09:00
draft: true
tags: ['tech']
---

時に単一のサービスでは機能が膨大すぎて使いきれなかったり、逆に賢くまとまりすぎていて連携力に乏しい場合がある。そんな状況ではセルフホスト型でもあえて統合的なプロダクトの利用が検討される。Nextcloudはセルフホスト界の四天王――四天王のうちでどの位置かは人それぞれとして――に相応しい知名度を持つ。

さしずめ、Google Workspaceのオープンソース版と言ったところか。メールクライアントがあり、カレンダーがあり、ストレージがあり、チャットがあり、オフィススイートがある。僕が知らないだけできっと他にも色々ある。それらすべてを使うことも、どれか一つか二つを選んで使うこともできる。サーバの計算資源次第では、Googleのそれよりも圧倒的に優れた統合サービスを手元に置ける。

当初、僕はカレンダーとTodoリストの脱Googleを検討していて[Baïkal](https://sabre.io/baikal/)などの単純なCalDAVサーバを物色していたが、利用頻度は低いもののおそらく使いそうな機能が他にいくつかあることに気がついた。たとえば普段はNASにデータを保存していても、一部を外出ししたい時に検閲されないオンラインストレージがあると望ましい。

他にも単純なメモアプリが欲しかった。導入直前時点では[memos]()をセルフホストしていて、これはこれで良い感じではあったが、Markdown記法とフォルダ分け程度しか求めていない僕にとってはそれでも持て余し気味だった。こんな時には様々な機能をひと揃えにしている総合サービスのスイスアーミーナイフ感がちょうどよくフィットする。本稿ではDockerを利用したNextcloudの構築方法について記す。

## docker-compose.ymlの記述
`docker`および`docker-compose`は導入済みと仮定する。巨大なサービスな割に記述量は意外と少ない。

```docker
version: '3.9'

volumes:
  nextcloud:
  db:

services:
  db:
    image: mariadb
    restart: always
    volumes:
      - db:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=乱数生成
      - MYSQL_PASSWORD=乱数生成
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud

  app:
    image: nextcloud
    restart: always
    ports : 
      - 7999:80
    links:
      - db
    volumes:
      - ./app:/var/www/html
    environment:
      - MYSQL_PASSWORD=乱数生成
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_HOST=db
      - OVERWRITEPROTOCOL=https
```

`MYSQL_PASSWORD`の部分は`openssl rand -hex 16`などで乱数生成する。定義が同じ箇所は同一の内容で揃えなければならない。編集後、`docker-compse pull`でファイルを取得しておく。

## リバースプロキシの設定
僕のブログを定期的に読んでいる人はサーバ構築系の記事がほぼ似通った構成で書かれていることに気づいたかもしれない。事実、Dockerを利用した構築作業は一部の例外を除いて大部分が反復的になりがちだ。つまりやればやるほど作業が楽勝になっていく。「こういうサービスが欲しいな」と思った時に、サブスクではなくまずセルフホスト型のOSSを探すようになる。そうなれば真に自由なインターネット生活は手に入ったも同然だ。

```nginx
server {
  server_name cloud.mystech.ink;

 location / {
    proxy_pass http://localhost:7999;
    proxy_set_header   Host             $host;
    proxy_set_header   Connection       $http_connection;
    proxy_set_header   X-Scheme         $scheme;
    proxy_set_header   X-Real-IP        $remote_addr;
    proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
  }

  listen 443 ssl http2;
  ssl_certificate     /etc/ssl/certs/mystech.ink.pem;
  ssl_certificate_key /etc/ssl/private/mystech.ink.key;
  client_max_body_size 10000M;

}
```

例によって、Cloudflareユーザでオリジンサーバ証明書を取得していない人はぜひ[この記事](https://riq0h.jp/2023/07/22/204725/)を参考に設置を検討してほしい。`nginx -t`でエラーの有無を確認してから`systemctl restart nginx`で再起動を行う。ちなみに`client_max_body_size`はWeb UI上からファイルを送信する際に必要とされる。`10000M`で10GBまでアップロードに対応できる。

## 動作確認


