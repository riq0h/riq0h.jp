---
title: "MatrixでDiscord/Slackを所有する"
date: 2023-09-30T19:40:58+09:00
draft: true
tags: ['tech']
---

![]()

先日のDiscordの障害は週末夜をオンラインゲームの中で過ごそうと決めていた人々を絶望の淵に叩き込んだ。きょうびオンラインゲームをするとなったらボイスチャットによるコミュニケーションはほぼ必須であり、とりわけDiscordはその分野で支配的な地位を占めている。ちなみに僕は一人で黙々とCounter-Strike2のランクマッチを回していたのであまり関係がなかった。静謐。

しかし他に寄辺のない異常独身男性が集結せしDiscordサーバを運用している立場としては、一つのサービスの死がコミュニケーションの喪失を引き起こす状態は望ましくない。以前から代替ツールを模索してはいたが、企業が提供する似たようなサービスでは面白みに欠けるし、セルフホストはセルフホストで「そのためだけのアカウント」が余計に増えてしまう。なにしろセルフホスト型はどんなに普及してもサーバごとに別のアカウントを作らなければならないのだ。

そこで、ようやく目を付けたのがMatrixプロトコルだった。以前より技術系のコミュニティでよく使われていたり、やたら熱心な信奉者を見かけるこのプロトコルは、セルフホスト型ではあるが分散型ネットワークを形成するため一つのアカウントで他のサーバに接続することができる。

7月に自鯖を持って以来、しばらくはActivityPubにかかりきりだったがそろそろ他の分散型プロトコルに手を出しても良い頃合いだ。もちろん、Discordが圧倒的な市場シェアを誇る現状で移行というわけにはいかないものの、ひとまずは避難所的に運用してMatrixの手触りを学んでおくのも一興だろう。本稿はMatrixのリファレンス実装サーバであるsynapseと、WebクライアントのElementを利用した構築方法について記す。

## ファイルの取得と編集
`docker`および`docker-compose`は導入済みと仮定する。公式のドキュメントや先人の記述をありがたく拝借させて頂いた。任意のディレクトリを作成して一階層ぶん深いところにdocker-compose.ymlファイルを作る。たとえばユーザ名が`matrix`の場合、`/home/matrix/1/2/`のような形式になる。記述例ではこの`1`に該当するディレクトリにファイル群が展開される。

```docker
version: '3'
services:

  redis:
    restart: always
    image: redis:4.0-alpine
    volumes:
      - ../redis:/data
    networks:
      - internal_network

  db:
    restart: always
    image: postgres:13.2-alpine
    volumes:
      - ../db:/var/lib/postgresql/data
    networks:
      - internal_network
    environment:
      - POSTGRES_PASSWORD=乱数生成
      - POSTGRES_USER=synapse
      - POSTGRES_DB=synapse
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --locale=C

  synapse:
    restart: always
    image: matrixdotorg/synapse:latest
    volumes:
      - ../data:/data
    environment:
      - SYNAPSE_SERVER_NAME=あんたのドメイン
      - SYNAPSE_REPORT_STATS=yes
    ports:
      - "7654:8008"
    networks:
      - external_network
      - internal_network

networks:
  external_network:
  internal_network:
    internal: true
```

`POSTGRES_PASSWORD`は`openssl rand -hex 16`などで生成する。`ports`の左側はデフォルトの8008番ポートが埋まっている場合に置き換えて用いる。編集が終わったら`docker-compose run --rm synapse generate`で必要なファイル群を吐き出させる。次に、`/home/matrix/1/data/homeserver.yaml`を書き換える。

```yaml
server_name: "あんたのドメイン"
public_baseurl: https://あんたのドメイン/
allow_public_rooms_without_auth: true
allow_public_rooms_over_federation: true
admin_contact: 'mailto:あんたのメールアドレス'
pid_file: /data/homeserver.pid
listeners:
  - port: 8008
    tls: false
    type: http
    x_forwarded: true
    resources:
      - names: [client, federation]
        compress: false
database:
  name: psycopg2
  args:
    user: synapse
    password: POSTGRES_PASSWORDと同じ
    database: synapse
    host: db
    cp_min: 5
    cp_max: 10
enable_registration: false
enable_registration_without_verification: false
client_base_url: "http://あんたのドメイン/"
enabled: true
host: redis
port: 6379
log_config: "/data/あんたのドメイン.log.config"
media_store_path: /data/media_store
registration_shared_secret: "自動生成"
report_stats: true
macaroon_secret_key: "自動生成"
form_secret: "自動生成"
signing_key_path: "/data/あんたのドメイン.signing.key"
trusted_key_servers:
  - server_name: "matrix.org"
suppress_key_server_warning: true
```

ほとんどの環境ではドメイン部分の修正だけで機能すると思われる。`自動生成`と書かれている箇所は失うと一巻の終わりなのでどこかに保存しておくべし。保存後、`docker-compose down`で一旦終了させてから`docker-compose up -d`で再起動を行う。意味もなくたまに起動がコケるので`docker-compose logs -f`で変なエラーが出ていないか確認する。


## Webクライアントの導入
本稿で紹介するElementはMatrix用クライアントの一つ。他にもいくつか[種類がある](https://matrix.org/ecosystem/clients/)が現状はElementが頭ひとつ抜けている。当初はこれも`docker-compose.yml`に加えてコンテナ化するつもりでいたが、なぜかうまく動かなかったのでビルド済みのバイナリをディレクトリに直接置く形を採った。

`/home/matrix/1/element`などの形式で新規ディレクトリを作成して、そこに`wget https://github.com/vector-im/element-web/releases/download/vv1.11.45/element-v1.11.45.tar.gz`でファイルを置く。バージョンは2023年10月1日時点での最新。`tar xvzf element-v1,11.45.tar.gz`で解凍する。続いて、`element-v1.11.45/config.json`の編集を行う。

```json
{
    "default_server_config": {
        "m.homeserver": {
            "base_url": "https://あんたのドメイン",
            "server_name": "あんたのドメイン"
        },
        "m.identity_server": {
            "base_url": "https://vector.im"
        }
    },
    "disable_custom_urls": false,
    "disable_guests": true,
    "disable_login_language_selector": false,
    "disable_3pid_login": false,
    "brand": "Element",
    "integrations_ui_url": "https://scalar.vector.im/",
    "integrations_rest_url": "https://scalar.vector.im/api",
    "integrations_widgets_urls": [
        "https://scalar.vector.im/_matrix/integrations/v1",
        "https://scalar.vector.im/api",
        "https://scalar-staging.vector.im/_matrix/integrations/v1",
        "https://scalar-staging.vector.im/api",
        "https://scalar-staging.riot.im/scalar/api"
    ],
    "default_country_code": "JP",
    "show_labs_settings": false,
    "features": {},
    "default_federate": true,
    "default_theme": "light",
    "room_directory": {
        "servers": ["matrix.org", "gitter.im", "matrix.fedibird.com"]
    },
    "enable_presence_by_hs_url": {
        "https://matrix.org": false,
        "https://matrix-client.matrix.org": false
    },
    "setting_defaults": {
        "breadcrumbs": true
    },
    "jitsi": {
        "preferred_domain": "meet.element.io"
    },
    "element_call": {
        "url": "https://call.element.io",
        "participant_limit": 8,
        "brand": "Element Call"
    },
    "map_style_url": "自動生成"
}
```

これも特にドメイン部分以外にいじるところはない。`servers`には利用者が多そうなサーバをあらかじめ記述しているが不要なら省いても差し支えはない。


## リバースプロキシの設定
`/etc/nginx/sites-enabled/`に任意の名前でconfファイルを作成する。

```
server {
  listen 443 ssl http2;
  listen 8448 ssl http2;

  server_name あんたのドメイン;

  ssl_certificate     /etc/ssl/certs/あんたのドメイン.pem;
  ssl_certificate_key /etc/ssl/private/あんたのドメイン.key;

  server_tokens off;

  gzip on;
  gzip_types text/css application/javascript image/svg+xml;
  gzip_vary on;

  add_header Strict-Transport-Security "max-age=63072000";

  add_header X-Frame-Options SAMEORIGIN;
  add_header X-Content-Type-Options nosniff;
  add_header X-XSS-Protection "1; mode=block";
  add_header Content-Security-Policy "frame-ancestors 'none'";

  location /.well-known/matrix/client {
    return 200 '{"m.homeserver": {"base_url": "https://あんたのドメイン/"}}';
    default_type application/json;
    add_header Access-Control-Allow-Origin *;
  }

  location ~ ^(/_matrix|/_synapse/client) {
    proxy_pass http://localhost:7654;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $host;
    client_max_body_size 50M;
  }

  location /.well-known/matrix/server {
    add_header 'Content-Type' 'application/json';
    return 200 '{ "m.server": "あんたのドメイン:443" }';
  }

  root /home/matrix/matrix/static/element-v1.11.45;

}
```

Cloudflareを利用していてカスタムオリジンサーバ証明書を取得していない人は[この記事](https://riq0h.jp/2023/07/22/204725/)の冒頭を参考に設定することを強くおすすめしたい。他に注目すべき点としてはHTTPSポートの443番以外に8448番ポートをlistenしているところで、これは他のサーバと通信する際に用いられている。

`nginx -t`で構文エラーの有無を確認して、問題がなければ`systemctl restart nginx`で再起動を行う。ここまでの手順に誤りがなければ設定したドメインからElementの登録画面にアクセスできるはずだ。ただし、`homeserver.yaml`でユーザ登録を無効化しているため、最初のユーザはコマンドラインの操作で登録する。

```cli
docker-compose exec synapse register_new_matrix_user -c /data/homeserver.yaml http://localhost:8008 -u あんたのユーザ名 -p あんたのパスワード -a
```

パスワードに記号類を含めると正常にハッシュ化されずログインできなくなるので、最初は英数字のみで作成してから後でWeb上で変更するか、`homeserver.yaml`の`enable_registration`と`enable_registration_without_verification`を`true`に書き換えて一時的にユーザ登録を有効化して記号類を含んだパスワードを入力する。

無事に登録したユーザでログインできたら構築作業は完了である。

## Federationの確認
最後に、Matrixプロトコルの醍醐味であるところの連合機能を検証しておく。
