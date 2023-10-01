---
title: "MatrixでDiscord/Slackを所有する"
date: 2023-10-01T20:36:58+09:00
draft: false
tags: ['tech']
---

![](/img/212.png)

先日のDiscordの障害は華金を電脳空間で過ごそうと決めていた人々を絶望の淵に叩き込んだ。きょうびオンラインゲームをやるとなったらボイスチャットはほぼ必須であり、とりわけDiscordは当該の分野で支配的な地位を占めている。ちなみに、僕は独りで黙々とCounter-Strike2のランクマッチを回していたので関係がなかった。静謐。

しかし他に寄辺のない異常独身男性が集結せしDiscordサーバを運用している立場としては、一つのサービスの死がコミュニケーションの喪失を引き起こしかねない現状はまったく好ましくない。彼らは他のSNSをあまり使わない。以前から代替ツールを模索してはいたが、企業運営の類似サービスでは面白みに欠けるし、かといってセルフホスト型だと「そのためだけのアカウント」が余分に増えてしまう。なにしろ従来の形態ではサーバごとに別のアカウントを作らなければならないのだ。

そこで、ようやく手を出したのが[Matrix](https://matrix.org)だった。情報技術系のコミュニティで広く使われていたり、やたら熱心な信奉者を見かけるこのプロトコルは、分散型ネットワークを形成するためセルフホスト型でありながら一つのアカウントで他のサーバに接続することができる。今後、プロトコルの発展次第で作ったアカウントが活かせるのは説得材料になりうる。

7月に自鯖を持って以来、長らくActivityPubにかかりきりだったがそろそろ他の分散型プロトコルを触っても良い頃合いだ。さしあたり避難所的に運用してMatrixと関連エコシステムの手触りを学んでおいて損はない。本稿はMatrixのリファレンス実装サーバであるSynapseと、WebクライアントのElementを利用した構築方法について記す。


## ファイルの取得と編集
`docker`および`docker-compose`は導入済みと仮定する。まず、任意のディレクトリを作成して一階層ぶん深い位置に`docker-compose.yml`ファイルを作る。仮にユーザ名が`matrix`の場合、`/home/matrix/1/2/`のような形式になる。下記の記述例ではこの`1`に該当するディレクトリにファイル群が展開される。

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

`POSTGRES_PASSWORD`は`openssl rand -hex 16`などで乱数生成する。`ports`の左側はデフォルトの8008番ポートが埋まっている際に置き換える。変更が済んだら`docker-compose run --rm synapse generate`でファイル群を吐き出させる。次に、`/home/matrix/1/data/homeserver.yaml`の編集に進む。

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

大抵の環境ではドメイン部分の修正のみで機能すると思われる。`自動生成`と記されている箇所は失うと一巻の終わりなのでバックアップをとっておく。保存後、`docker-compose down`で一旦終了してから`docker-compose up -d`で再起動を行う。なぜかたまに起動がコケるので`docker-compose logs -f`で変なエラーが出ていないか確認する。


## Webクライアントの導入
ElementはMatrix用クライアントの一つである。他にもいくつか[種類があるが](https://matrix.org/ecosystem/clients/)今のところはElementが頭ひとつ抜けている。当初はこれも`docker-compose.yml`に加えてコンテナ化するつもりでいたが、うまく動かなかったのでビルド済みのバイナリをディレクトリに直接置く形を採った。公式のドキュメントでもそのやり方が推奨されているようだ。

まずは`/home/matrix/1/element`などの形式で任意のディレクトリを作成して、そこに`wget https://github.com/vector-im/element-web/releases/download/vv1.11.45/element-v1.11.45.tar.gz`でファイルを置く。バージョンは2023年10月1日時点での最新。ダウンロードが済み次第、`tar xvzf element-v1,11.45.tar.gz`で解凍する。続いて、`element-v1.11.45/config.json`の編集を行う。

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

ここもドメイン部分以外にあえていじる箇所はそう多くない。`servers`の欄には利用者が多そうなサーバをあらかじめ列挙している。


## リバースプロキシの設定
`/etc/nginx/sites-enabled/`に任意の名前でconfファイルを作成する。

```nginx
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

  location /.well-known/matrix/server {
    add_header 'Content-Type' 'application/json';
    return 200 '{ "m.server": "あんたのドメイン:443" }';
  }

  location ~ ^(/_matrix|/_synapse/client) {
    proxy_pass http://localhost:7654;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $host;
    client_max_body_size 50M;
  }
 
  root /home/matrix/matrix/static/element-v1.11.45;

}
```

Cloudflareユーザでオリジンサーバ証明書を設定していない人は[この記事](https://riq0h.jp/2023/07/22/204725/)の冒頭を参考に取得することを強くおすすめしたい。他に特筆すべき点はHTTPSポートの443番以外に8448番ポートをlistenしているところで、これは他のサーバと通信する際に用いられている。

同様に、`.well-known/*`の記述は連合機能を正常に動作させる認証として働く。すべての作業が終わった後に[Matrix Federation Tester](https://federationtester.matrix.org/)にドメインを入力すると前もってサーバの状態を調査できる。必須の作業工程ではないものの、障害発生時のトラブルシューティングにはなにかと役立つ。

`nginx -t`で構文エラーの有無を確認して、`systemctl restart nginx`で再起動を行う。以上の手順に誤りがなければ設定したドメインからElementのスタートページにアクセスできるはずだ。ただし、`homeserver.yaml`で登録を無効化しているため、最初のユーザ登録はCLIで実施する。

```zsh
docker-compose exec synapse register_new_matrix_user -c /data/homeserver.yaml http://localhost:8008 -u あんたのユーザ名 -p あんたのパスワード -a
```

なお、ここでパスワードに記号類を含めると正常にハッシュ化されずログインが不可能になる。これを避けるには英数字のみで作成してからWeb上で変更するか、または`homeserver.yaml`の`enable_registration`と`enable_registration_without_verification`を`true`に書き換えて登録もWeb上で行う。無事にログインに成功したら構築はおおむね成功と見てよい。


## 機能の確認
最後に、Matrixプロトコルの醍醐味である連合機能を検証する。「ルーム」の横の＋ボタンから前述の`servers`に列挙したサーバに属するルームを検索できる。ルームへの初回参加には仕様上かなりの時間がかかるが、参加後はDiscordやSlackとほとんど同じように使える。

![](/img/213.png)
（大規模Mastodonインスタンスで知られるFedibirdの雑談ルームにお邪魔したところ、さっそく鯖缶に捕捉された。）

設計思想の違いとして、上記二つはサーバと各ルームが強力に紐付けられているのに対して、Matrixはルーム単位での参加が可能な点が挙げられる。これによりユーザは単一のサイドパネル上で個別のサーバのルームを一覧化できる。分散型ネットワークで構成されている割にサーバ全体を意識せず横断が行えるのは素直に使い勝手に優れていると感じた。

DiscordやSlackでは特定のサーバの一つのルームが目当てでも、UIの都合上、サーバ単位での参加が前提なので中央集権型にもかかわらず管理が手間と感じることが少なくない。一方、Matrixは分散型の利点を維持しつつも高度な透過性をもたらすエコシステムを実現している。

営利企業にしては良心的な運営方針を持つDiscordやSlackの牙城を崩すのは難しいかもしれないが、何者にも支配されない自由な私的空間として、あるいは単純に緊急時の避難所としてひとまずホームサーバを所有する意義は大いにあると思われる。なんにせよ、無意識に受け入れていた様々な仕様を見直す上でも競合の存在は必要不可欠に違いない。
