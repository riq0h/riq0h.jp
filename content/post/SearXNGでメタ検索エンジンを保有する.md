---
title: "SearXNGでメタ検索エンジンを所有する"
date: 2023-08-20T09:13:55+09:00
draft: false
tags: ["tech"]
---

Mastodonインスタンスを建ててからというもの、VPSの持て余した計算資源を活用すべく様々なOSSを探し回っている。中でもとりわけ印象深かったのがメタ検索エンジンの[SearXNG](https://github.com/searxng/searxng)だ。今や検索エンジンすらセルフホストすることができる。これを使えばGoogleやBingの検索結果をまとめて睥睨しつつ、プライバシー情報は彼らに一切与えない悪魔的所業が可能となる。

![](/img/206.png)

たとえば「肩甲骨」で検索すると僕の設定では上記の検索結果が現れる。それぞれの下部に「bing wikipedia duckduckgo brave」などと記されている通り、設定で有効にした検索エンジンが一覧化される仕組みだ。見たところGoogleはWikipediaがあまりお好みではないらしい。実際、本家Googleで当該の単語を検索してみるとWikipediaは2ページ目に進まないと出てこない。

一方、他の検索エンジンはいずれもWikipediaを先頭に表示している。Wikipediaが自分自身を優先するのは当然としてもこの結果は興味深い。これ一つとってもGoogleが検索結果を操作している形跡がうかがえるからだ。彼らのアルゴリズムが推薦するのは彼らが見せたい情報であって、必ずしも我々が欲しい情報とは限らない。もちろん営利企業の競合他社とて例外ではない。

そうした彼らの真意を見抜きつつ、各々の検索エンジンを並列的に利用することで機能部分だけを美味しく頂いてしまおうというのがメタ検索エンジンの趣旨である。DuckDuckGoやBrave単体では物足りない強欲の壺の生まれ変わりみたいなユーザにはまさにうってつけと言える。

単に利用するぶんには公開インスタンスの[一覧](https://searx.space)から適当なページを選ぶか、もしくは僕の[インスタンス](https://search.mystech.ink)を使ってくれても構わないが、自前で運用すればプライバシー保護をより万全に固められる。そこで、本稿ではDockerを利用した構築方法を記す。

## ファイルの取得および編集

まずは必要なファイルの取得から始める。すでにSearXNGを実行するユーザが作成されていて、`docker`および`docker-compose`が導入されているものとする。なお、一部のコマンドは実行に`sudo`が要求される。

```zsh
$ git clone https://github.com/searxng/searxng-docker.git
$ cd searxng-docker
```

cloneしたフォルダ名が気に入らなければ他の名前に変えてもよい。次に、`docker pull searxng/searxng`でDockerイメージを取得する。この段階でもサーバ自体は起動できるが事前に下準備を行わなければいけない。任意のエディタで`docker-compose.yml`を開いて内容を書き換える。

```docker
version: '3.7'

services:

  # caddy:
  #   container_name: caddy
  #   image: caddy:2-alpine
  #   network_mode: host
  #   volumes:
  #     - ./Caddyfile:/etc/caddy/Caddyfile:ro
  #     - caddy-data:/data:rw
  #     - caddy-config:/config:rw
  #   environment:
  #     - SEARXNG_HOSTNAME=search.mystech.ink
  #   cap_drop:
  #     - ALL
  #   cap_add:
  #     - NET_BIND_SERVICE

  redis:
    container_name: redis
    image: "redis:alpine"
    command: redis-server --save "" --appendonly "no"
    networks:
      - searxng
    tmpfs:
      - /var/lib/redis
    cap_drop:
      - ALL
    cap_add:
      - SETGID
      - SETUID
      - DAC_OVERRIDE

  searxng:
    container_name: searxng
    image: searxng/searxng:latest
    networks:
      - searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=https://あんたのドメイン.com
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    logging:
      driver: "json-file"
      options:
        max-size: "1m"
        max-file: "1"
networks:
  searxng:
    ipam:
      driver: default

# volumes:
#   caddy-data:
#   caddy-config:
```

本稿では同梱されているWebサーバのCaddyを使わず外部のnginxを利用する形をとる。そのためCaddyに関する部分はコメントアウトしている。ついでに`ports`を`"8080:8080"`に変えて、`SEARXNG_BASE_URL`を公開したいURLに変更しておく。続いて、`.env`ファイルを編集する。

```zsh
# By default listen on https://localhost
# To change this:
# * uncomment SEARXNG_HOSTNAME, and replace <host> by the SearXNG hostname
# * uncomment LETSENCRYPT_EMAIL, and replace <email> by your email (require to create a Let's Encrypt certificate)

SEARXNG_HOSTNAME=あんたのドメイン名.com
# LETSENCRYPT_EMAIL=<email>
```

当該箇所のコメントアウトを外してドメイン名を書き込む。最後にシークレットキーを作成して追記する。

```zsh
$ openssl rand -hex 32
```

上記のコマンドを実行するとランダムな英数字が出力されるので、それをコピーした上で`searxng/searxng/settings.ini`を開く。

```yaml
# see https://docs.searxng.org/admin/engines/settings.html#use-default-settings
use_default_settings: true

general:
  debug: false
  instance_name: "好きな名前"
search:
  safe_search: 0
  autocomplete: "google"
server:
  # base_url is defined in the SEARXNG_BASE_URL environment variable, see .env and docker-compose.yml
  secret_key: "ここにコピーした英数字を貼り付ける" # change this!
  limiter: false # can be disabled for a private instance
  image_proxy: true
ui:
  static_use_hash: true
redis:
  url: redis://redis:6379/0
```

`secret_key`に先ほどの英数字を貼り付ける。ここで他の項目を変更しても差し支えはないが一旦使ってからでも遅くはない。とりあえずこれで本体周りのファイル編集は完了となる。

## nginxの設定

nginxはすでに導入されているものとする。まずは`/etc/nginx/site-enabled/`に任意の名前で.confファイルを作る。もしSSL化に必要な鍵ファイルを用意していない場合は、[この記事](https://riq0h.jp/2023/07/22/204725/)の「SSLの対応をCloudflareに丸投げする」の項目を参考にして、鍵ファイルを設置する。一度行えばすべてのWebサービスで併用可能なのでぜひともやってもらいたい。

```nginx
server {
  server_name あんたのドメイン名;

 location / {
    proxy_pass http://localhost:8080;
    proxy_set_header   Host             $host;
    proxy_set_header   Connection       $http_connection;
    proxy_set_header   X-Scheme         $scheme;
    proxy_set_header   X-Real-IP        $remote_addr;
    proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
  }

  listen 443 ssl http2;
  ssl_certificate     /etc/ssl/certs/あんたのドメイン名.pem;
  ssl_certificate_key /etc/ssl/private/あんたのドメイン名.key;

}
```

上記の形でリバースプロキシを記述する。保存後、`nginx -t`を実行して問題がなければ`systemctl restart nginx`で再起動を行う。

## サーバ起動と既知のバグの対処

SearXNGのユーザで`docker-compose up`を実行する。おそらくエラーが出てくると思われる。これはSearXNGのDockerイメージが持つ既知のバグで、初回のみ特定の記述を編集すれば解決できる。`docker-compose.yml`を開き、下記の箇所をコメントアウトする。

```docker
#    cap_drop:
#      - ALL

```

当該箇所はCaddyの部分も含めると全部で3箇所ある。これらをコメントアウトした後に`docker-compose down`で一旦終了させ、`docker-compose up`で起動し直す。正常な動作を確認したらコメントアウトを外して同じ要領で再起動する。最後に、HTTP/HTTPSポートを開放していない場合は開ける。

```zsh
$ ufw allow 80
$ ufw allow 443
$ ufw reload
```

以上の設定が正しく反映されていれば任意のURLでSearXNGのトップページが表示されるはずだ。適当なフレーズで検索したり、各種設定を操作して挙動に障りがなければ構築作業は終了である。

## Tips

**■検索が遅い。**  
正直な話、各検索エンジンの間に自前のサーバを挟んでいる時点で原理的にどうあがいてもミリ秒単位の遅延は免れない。不必要な検索エンジンを設定から除外すると多少は改善される。

**■手持ちの端末ごとに再設定するのがダルい。**  
設定の「クッキー」にある「このURLで違うブラウザに設定を復活」の文字列をアドレス欄にぶち込めば一瞬で再設定できる。

**■設定を変更するとエラーが出る。**  
設定下部の「デフォルト設定に戻す」を押して初期化すると大抵直る。

**■ブラウザの検索窓からも使いたい。**  
ブラウザの設定によってまちまちだが、たとえばVivaldiは設定でURLを`https://あんたのドメイン.com/search?q=%s&category_general=on`とかに設定すると使えるようになる。同期が有効ならモバイルのVivaldiにも自動で適用される。

**■我輩はVimmerだ。**  
設定の「ユーザーインターフェイス」にある「Vim風のホットキー」を有効にすると最強になれる。
