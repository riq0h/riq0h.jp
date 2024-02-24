---
title: "DockerなしでBlueskyのPDSを建てる方法"
date: 2024-02-24T20:19:04+09:00
draft: true
tags: ['tech']
---

Blueskyの連合がスタートした。厳密には、我々はBlueskyの構成要素の一つ「PDS」（Personal Data Storage）をセルフホスティングできるようになった。これにより各ユーザは自分のデータを自らの管理下に置ける。また、他ユーザの登録を許可しているPDSに移動すれば権威的ではない他の存在にデータを委任する選択肢を持てる。

一方、MastodonやMisskeyなどと異なるのは、モデレーションやフィードの生成、固有IDの半永続的な記録を担う上位の構成要素が存在しているところだ。これらは莫大な計算資源を要するため、個人でのホスティングは実質不可能とされている。つまり、PDSはあくまで個人データの保管庫であって一切の制約から逃れられるわけではない。公式のルールに違反する投稿は依然として処罰の対象になりうるし、まだ前例はないが他のPDSとの連合から排除される可能性も考えられる。

とはいえ完全な中央集権型のSNSと比べるとデータを自己管理できる自由があり、完全な分散型の競合と比べて透過性の高い体験が得られる点はまずまずの落としどころと言えなくもない。現にMastodonやMisskeyには見向きもしなかった各企業やインフルエンサーがこぞって押し寄せてきている現状を踏まえると、分散主義者的には中途半端でも市井の需要には適っているのかもしれない。

さて肝心のサーバ構築だが、以下に示す方法は**すでにサーバを運用している人**向けの指南書であって、初心者に適した内容ではない。PDSの構築のためにまっさらなサーバを契約した人は最低限の設定（SSH接続など）を済ませた上で、GitHubのリポジトリにあるinstall.shを実行すれば簡単に建てられる。

今回の方法はなんらかの理由で**他の用途で80番/443番ポートが埋まっている**、**構築にサブドメインを用いるつもりでいる**、**有料の証明書を買いたくない**、というけったいな条件を満たしてる変人でなければ、ほとんど行う必要のない煩雑な手続きを踏んでいる。このことは予め了承してほしい。

ちなみに、ぶっちゃけるとこの指南書は[このページ](https://benharri.org/bluesky-pds-without-docker/)を丸パクリしている。英語の読解に難がない人はこっちを読んだ方が絶対に早い。本エントリはあくまで日本語情報の提供を目的にしている。


## nginxのリバースプロキシを書く

```
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

まずは以上の形式でリバースプロキシを書く。もし利用するドメインがTLDで、かつDNSサーバがCloudflareならSSL証明書の部分は不要だ。だが不幸にも`aaa.bbb.com`のようなサブドメインを利用するつもりでいる人はここで工夫がいる。なぜならベースドメインが`aaa.bbb.com`だと各ユーザアカウントごとに作られるドメインが`XXX.aaa.bbb.com`と三階層になってしまう。

Cloudflareは二階層（`aaa.bbb.com`）までしか無料でSSL証明書を配給してくれないため、このままサーバを建てるとユーザアカウント部分が不正なURLと見なされて機能しないのである。これを無料で解決するには二つの方法がある。一つは`XXX.aaa.bbb.com`の部分だけ別の無料のSSL証明書を取得する。一番手堅い正当な手段と言える。

二つ目は不正を上等で建てた上で、カスタムハンドル機能を用いてSSL通信可能な他のドメインにユーザ名を置き換えることだ。建てた本人しか使わないPDSならこの運用方法は少々狡猾ながら合理的と言える。一度置き換えてしまえばブラウザ上で以降の解決に使われるのはそっちの方だけなので実際のところ問題はなにも起こらない。

もちろん本エントリでは二つ目の方法を紹介する。リバースプロキシを書き終えたら`nginx -t`で文法をチェックした後に`systemctl restart nginx`で再起動を行う。


## データの取得と.envファイルの作成

ここからはroot以外のユーザで作業を行う。任意のディレクトリ下にて`git clone https://github.com/bluesky-social/pds`を実行してPDSの構築に必要なデータを取得する。`/pds/service`に移動後、下記の要領で`.env`ファイルを作る。

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

`乱数生成`と書かれているところは文字通り乱数で生成する。`PDS_JWT_SECRET`の部分は`openssl rand --hex 16`で、他の二つは重複しない形で以下のコマンドを打つ。

```zsh
openssl ecparam --name secp256k1 --genkey --noout --outform DER | tail --bytes=+8 | head --bytes=32 | xxd --plain --cols 32
```

別に桁数を満たしていればなんでもいいじゃないか、と思っていたが、どうやら生成アルゴリズムにSecp256k1（楕円曲線暗号）を用いていないとダメらしい。ちなみにこのアルゴリズムはBitcoinにも使われているんだとか。怒られが発生した場合はおそらく`xxd`が入っていないと思われるので`apt install xxd`などで適宜導入する。


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

このファイルは`pds.service`などの名前で`/etc/systemd/system/`直下に保存する。`systemctl reload-daemon`を実行してから`systemctl start pds`でサーバを稼働させる。一連の設定が正しく行われていれば、ブラウザでベースドメインにアクセスした時に下記のメッセージが表示される。

>This is an AT Protocol Personal Data Server (PDS): https://github.com/bluesky-social/atproto  
>Most API routes are under /xrpc/


## pdsadminの使い方

アカウントの作成などをコマンド経由で行える`pdsadmin`コマンドだが、インストールスクリプトを用いないで構築した我々が使うと環境変数を読んでくれないので正しく動かない。そこで`/pds/pdsadmin`に移動してから`sudo PDS_ENV_FILE=../service/.env bash account.sh list`の形で`.env`ファイルを指定して実行する。ちなみにこのコマンドはPDSに登録されているアカウントの一覧を表示してくれる。

```zsh
$ sudo PDS_ENV_FILE=../service/.env bash account.sh list

Handle             Email          DID
riq0h.mystech.ink  mail@riq0h.jp  did:plc:dqlihaiieq7lpjkwv6x62y4a
```

アカウントを登録する際は同じ要領で`sudo PDS_ENV_FILE=../service/.env bash account.sh create`を実行する。対話形式でユーザアカウントのフルパスとメールアドレスを入力すると作成できる。当然、この時に作成したアカウントはサブドメインを利用していると不正な状態なので、通常と同様に[bsky.app](https://bsky.app)からログインしてカスタムハンドルをあてがう必要がある。

カスタムハンドルを設定する前でもユーザのフォローや投稿は可能だが、他のユーザからは「invalid handle」と表示されていて明らかに異常者にしか見えない。趣味でなければあらかじめ設定しておく方が無難だ。


## おわりに

とりあえずこれでBlueskyユーザはひとまずデータを自主管理する自由を得た。まだ真の分散には程遠いが偉大な一歩には違いない。
