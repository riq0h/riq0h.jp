---
title: "DockerなしでBlueskyのPDSを建てる方法"
date: 2024-02-25T08:58:04+09:00
draft: false
tags: ['tech']
---

晴れてBlueskyの連合がスタートした。厳密には、我々はBlueskyの構成要素の一つであるPDS（Personal Data Storage）をセルフホスティングできるようになった。これにより各ユーザは自分のデータを自らの管理下に置くことができる。また、他ユーザの登録を許可しているPDSに移動すれば権威的ではない他の個人にデータを預けられる。

一方、MastodonやMisskeyなどと異なるのは、モデレーションやフィードの生成、固有IDの半永続的な管理を担う上位の構成要素が存在しているところだ。これらは膨大な計算資源を要するため、個人でのホスティングは実質不可能とされている。つまり、PDSは文字通り個人データの保管庫であって、あらゆる制約から逃れられるわけではない。公式のルールに違反する投稿は依然として処罰の対象になりうるし、まだ前例はないが他のPDSとの連合から排除される可能性も考えられる。

とはいえ従来の中央集権型SNSと比べるとデータを自主管理する裁量があり、分散型の競合と比べて透過性の高い体験が得られる点はまずまずの落としどころと言える。ほとんどのユーザには特定の相手が分散しているかどうかさえ判別がつかない。現にMastodonやMisskeyには見向きもしなかった各企業やインフルエンサーがこぞって参入してきている現状を踏まえると、僕のような分散主義者的には中途半端でも市井の需要には適っているのかもしれない。

以下に示すサーバ構築の方法は**他の用途でサーバを運用している人**向けの指南書であって、初心者に適した内容ではない。PDSの構築のためにまっさらなサーバを契約した人はSSH接続やファイアウォールなどの最低限の設定を済ませた上で、[GitHubのリポジトリ](https://github.com/bluesky-social/pds)にあるinstall.shを実行すれば簡単に建てられる。

今回の方法はなんらかの理由で**80番/443番ポートが埋まっている**、**構築にサブドメインを用いるつもりでいる**、**有料のSSL証明書を買いたくない**、**その他、Dockerを使いたくない**、などといった条件を満たしてる変人でなければ、ほとんど行う必要のない煩雑な手続きを踏んでいる。このことは予め了承してほしい。

ちなみに、ぶっちゃけると具体的な記述部分は[このページ](https://benharri.org/bluesky-pds-without-docker/)を丸パクリしている。英語に抵抗がない人はこっちを読んだ方が絶対に早い。本稿はあくまで日本語情報の提供を目的にしている。


## nginxのリバースプロキシを書く

```nginx
server {
  listen 80;
  server_name あんたのドメイン.com *.あんたのドメイン.com;
  return 302 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name あんたのドメイン.com *.あんたのドメイン.com;
  ssl_certificate     /etc/ssl/certs/mystech.ink.pem;
  ssl_certificate_key /etc/ssl/private/mystech.ink.key;

  location / {
    include proxy_params;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_pass http://localhost:4567;
  }
}
```

まずは以上の形式でリバースプロキシを書く。もし利用するドメインがTLDで、かつDNSサーバがCloudflareならSSL証明書の部分は不要だ。だが不幸にも`aaa.bbb.com`のようなサブドメインをベースに利用するつもりでいる人はここで工夫がいる。なぜならベースドメインが`aaa.bbb.com`だと各ユーザアカウントごとに作られるドメインが`XXX.aaa.bbb.com`と三階層になってしまう。

Cloudflareは二階層（`aaa.bbb.com`）までしか無料でSSL証明書を配給してくれないため、このままサーバを建てるとユーザアカウント部分が不正なURLと見なされて機能しないのである。これを無料で解決するには二つの方法がある。一つ目は`XXX.aaa.bbb.com`の部分だけ別途無料のSSL証明書を取得することだ。一番手堅く正当な手段と考えられる。

逆に、二つ目は不正上等で建てた上で、カスタムハンドル機能を用いて他の有効なドメインにユーザ名を置き換えるやり方だ。（`ccc.bbb.com`）建てた本人しか使わないPDSならこのテクニックは少々狡猾ながら合理的だろう。一度置き換えてしまえば名前解決に使われるのはカスタムハンドルの方なので実際のところ問題はなにも起こらない。

もちろん本稿では二つ目の方法を紹介する。リバースプロキシを書き終えたら`nginx -t`で文法をチェックした後に`systemctl restart nginx`で再起動を行う。


## データの取得と.envファイルの作成

ここからはユーザ権限で作業を行う。任意のディレクトリ下にて`git clone https://github.com/bluesky-social/pds`を実行してPDSの構築に必要なデータを取得する。`/pds/service`に移動後、下記の要領で`.env`ファイルを作る。

```env
PDS_HOSTNAME="あんたのドメイン"
PDS_JWT_SECRET="乱数生成"
PDS_ADMIN_PASSWORD="乱数生成"
PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX="乱数生成"
PDS_DATA_DIRECTORY=./data
PDS_BLOBSTORE_DISK_LOCATION=./data/blocks
PDS_DID_PLC_URL=https://plc.directory
PDS_BSKY_APP_VIEW_URL=https://api.bsky.app
PDS_BSKY_APP_VIEW_DID=did:web:api.bsky.app
PDS_REPORT_SERVICE_URL=https://mod.bsky.app
PDS_REPORT_SERVICE_DID=did:plc:ar7c4by46qjdydhdevvrndac
PDS_CRAWLERS=https://bsky.network
LOG_ENABLED=true
NODE_ENV=production
PDS_PORT=4567
```

`乱数生成`と書かれているところは文字通り乱数で生成する。`PDS_JWT_SECRET`の部分は`openssl rand --hex 16`で、他の二つは以下のコマンドをそれぞれ打って作る。

```zsh
openssl ecparam --name secp256k1 --genkey --noout --outform DER | tail --bytes=+8 | head --bytes=32 | xxd --plain --cols 32
```

別に桁数を満たしていればなんでもいいじゃないか、と思っていたが、どうやら生成アルゴリズムにSecp256k1（楕円曲線暗号）を用いていないとダメらしい。このアルゴリズムはBitcoinにも使われているんだとか。怒られが発生した場合はおそらく`xxd`が入っていないので`apt install xxd`で適宜導入する。


## PDSの稼働

`/pds/service`にて`pnpm install --production --frozen-lockfile`を実行する。`pnpm`を導入していない場合は`npm install -g pnpm`で入れる。データ格納用のフォルダも`mkdir -p data/blocks`で作成しておく。最後に、systemdのユニット定義ファイルを書く。以降はroot権限での作業となる。

```systemd
[Unit]
Description=Bluesky PDS Service

[Service]
WorkingDirectory=/home/あんたのユーザ名/pds/service
ExecStart=/usr/bin/node --enable-source-maps index.js
Restart=no
EnvironmentFile=/home/bsky/pds/service/.env

[Install]
WantedBy=default.target
```

このファイルは`pds.service`などの名前で`/etc/systemd/system/`直下に保存する。`systemctl daemon-reload`を実行してから`systemctl start pds`でサーバを稼働させる。一連の設定が正しく行われていれば、ブラウザでベースドメインにアクセスした時に下記のメッセージが表示される。

```
This is an AT Protocol Personal Data Server (PDS): https://github.com/bluesky-social/atproto  
Most API routes are under /xrpc/
```

以上でサーバの構築作業は完了である。


## pdsadminの使い方

アカウントの作成などを行える`pdsadmin`コマンドだが、インストールスクリプトを用いずに構築した我々が使うと環境変数を読んでくれないため正しく動かない。そこで`/pds/pdsadmin/`に移動してから`PDS_ENV_FILE=../service/.env bash account.sh list`の形式で`.env`ファイルを直接指定して実行する。ちなみにこれはPDSに登録されているアカウントの一覧を表示してくれる。

```zsh
$ PDS_ENV_FILE=../service/.env bash account.sh list

Handle             Email          DID
riq0h.mystech.ink  mail@riq0h.jp  did:plc:dqlihaiieq7lpjkwv6x62y4a
```

アカウントを登録する際は同じ要領で`PDS_ENV_FILE=../service/.env bash account.sh create`を実行する。当然、この時に作成したアカウントはベースにサブドメインを利用していると不正な状態になっているので、通常と同様に[bsky.app](https://bsky.app)でカスタムハンドルをあてがう必要がある。

なお、カスタムハンドルを設定しなくてもユーザのフォローや投稿は可能だが、他のユーザからは常に「invalid handle」と表示されていて明らかに異常者にしか見えない。趣味でなければ正気に戻しておく方が無難だろう。


## アップデートの方法

標準で用意されている`pdsadmin update`はDocker環境を前提にしているゆえ今回の構築手法では機能しない。代わりにリポジトリを`git pull`で更新して実質的にアップデートを行う。更新後は忘れずに依存ファイルを再取得する。

```zsh
$ cd pds
$ git pull
$ cd service
$ pnpm install --production --frozen-lockfile
$ systemctl restart pds
```


## おわりに

とりあえずこれでBlueskyユーザはデータを自主管理する裁量を得た。まだ真の分散には程遠いが偉大な一歩には違いない。次回以降はPDS間のアカウント移行をテストする予定だ。
