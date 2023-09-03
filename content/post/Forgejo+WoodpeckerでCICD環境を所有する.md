---
title: "Forgejo+WoodpeckerでCI/CD環境を所有する"
date: 2023-09-03T11:13:29+09:00
draft: false
tags: ['tech']
---

逆になにができないのか判らないほど多機能と化したGitHubだが、その機能性が仇となって限られた用途で使用するにはいささか煩雑な画面操作が増えたように思う。`gh`コマンドは確かに有用ではあるものの圧の強いUIと格闘するかCLIかの二択は少々極端なきらいが否めない。

そこで、自前の計算資源を持っている人間にはリモートリポジトリのセルフホスティングが検討される。世の中には絶対にissueやPRを受け付ける気がない雑多なコード片や、ごく個人的、ないしは見知った少人数のみのプロジェクトが存在する。そういった趣旨のリポジトリを管理するには、いっそGitHubよりもミニマルに設計されたサービスの方が快適に用を足せる見込みがある。

そもそもGitとは自由なバージョン管理システムであり、巨大資本のルールに縛られた一つの場所にコードを置くのは十分に機能を活かせていないとも考えられる。もし持て余した計算資源がそこらに転がっているのなら、そこに個人的なリモートリポジトリを生やしてみるとこれまでに得られなかったときめきが感じられるかもしれない。本稿ではForgejoとWoodpeckerを連携させた統合的なCI/CD環境を構築する手法について記す。


## ソフトウェアの紹介
[■Forgejo](https://forgejo.org)  
ForgejoはGiteaを基にしたGitホスティングソフトウェアのコミュニティ主導フォークで、商業化に傾倒したGiteaから主要な開発者が離反する形で誕生した。昨年末に分派したばかりで外観以外の目立った変更箇所はさほど見られないが、代わりにGitea向けのサービスや連携機能を利用できる。

近い将来にはセルフホストされた各リモートリポジトリ同士をActivityPubで相互接続してissueやPRを投げられるようにする計画があるらしい。もし実現すれば従来の大手ホスティングサービスに縛られない分散的なコミュニティを形成する余地が生まれる。

[■Woodpecker](https://woodpecker-ci.org)  
Woodpeckerも同様にDroneを基にしたコミュニティ主導フォークだが、こちらは特に喧嘩別れというわけではない。エンタープライズ向けの有料エディションを持つDroneと違い永久に渡る完全無料を確約している。

CI/CDとは「継続的インテグレーション/継続的デリバリー」の略称で、コードの変更を起点に自動的にテストを行ったり、ビルド結果を反映した最新バージョンを展開したりするための機能群を指す。GitHubの「GitHub Actions」はCI/CDの一つと言える。企業の提供する無料のCI/CD環境には制約が設けられている一方、セルフホストすれば所有する計算資源の限界まで使い倒せる利点がある。


## docker-compose.ymlの編集
`docker`および`docker-compose`は導入済みと仮定する。ForgejoとWoodpeckerは別のソフトウェアだが、互いに連携させる前提で構築するため今回は単一の`docker-compose.yml`で両者をまとめる。

```docker
version: "3"

networks:
  forgejo:
    external: false

services:
  server:
    image: codeberg.org/forgejo/forgejo:1.20
    container_name: forgejo
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - FORGEJO__database__DB_TYPE=postgres
      - FORGEJO__database__HOST=db:5432
      - FORGEJO__database__NAME=forgejo
      - FORGEJO__database__USER=forgejo
      - FORGEJO__database__PASSWD=forgejo
    restart: always
    networks:
      - forgejo
    volumes:
      - ./forgejo:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3333:3000"
      - "4444:22"
    depends_on:
      - db

  db:
    image: postgres:14
    restart: always
    environment:
      - POSTGRES_USER=forgejo
      - POSTGRES_PASSWORD=forgejo
      - POSTGRES_DB=forgejo
    networks:
      - forgejo
    volumes:
      - ./postgres:/var/lib/postgresql/data

  woodpecker-server:
    image: woodpeckerci/woodpecker-server:latest
    ports:
      - "8000:8000"
    volumes:
      - woodpecker-server-data:/var/lib/woodpecker/
    environment:
      - WOODPECKER_OPEN=true
      - WOODPECKER_HOST=あんたのURL
      - WOODPECKER_GRPC_SECURE=true
      - WOODPECKER_GITHUB=false
      - WOODPECKER_GITEA=true
      - WOODPECKER_GITEA_URL=あんたのURL
      - WOODPECKER_GITEA_CLIENT=後述
      - WOODPECKER_GITEA_SECRET=後述
      - WOODPECKER_AGENT_SECRET=後述
    networks:
      - forgejo

  woodpecker-agent:
    image: woodpeckerci/woodpecker-agent:latest
    command: agent
    restart: always
    depends_on:
      - woodpecker-server
    volumes:
      - woodpecker-agent-config:/etc/woodpecker
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WOODPECKER_SERVER=woodpecker-server:9000
      - WOODPECKER_AGENT_SECRET=後述
    networks:
      - forgejo

volumes:
  woodpecker-server-data:
  woodpecker-agent-config:
```

`ports`の箇所はコロンの左側を他の番号に置き換えてもよい。この例では3000番ポートが他のサービスに専有されている都合上、代替として3333番ポートを指定している。セキュリティ保護の観点からForgejoとSSH通信を行うポートも標準の22番を避けている。万が一、`woodpecker-server`の8000番ポートも空いていなければ他の番号に置き換える。

Woodpecker側の設定もここで指定する。`environment`の記述はブラウザ経由のアクセスやForgejoとの連携を図る上で必須となる。予めレジストラでそれぞれ任意のサブドメインを割り振っておくと話が早い。たとえばForgejoの方を`git.あんたのドメイン`、Woodpeckerの方を`cicd.あんたのドメイン`などに割り当てる。定義が`WOODPECKER_GITEA_*`なのはForgejoを内部的にGiteaと認識させているためだ。


## リバースプロキシの設定
nginx向けにリバースプロキシを書く。Forgejo用とWoodpecker用の二つを用意する。Cloudflareを利用していてオリジンサーバ証明書を取得していなければ[この記事](https://riq0h.jp/2023/07/22/204725/)の冒頭を参考にSSL証明書を設置にされたし。一度やれば使い回せるのでぜひおすすめしたい。

```nginx
# Forgejo用
server {
  listen 80;
  listen [::]:80;
  server_name git.あんたのドメイン;
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name git.あんたのドメイン;
  ssl_certificate     /etc/ssl/certs/あんたのドメイン.pem;
  ssl_certificate_key /etc/ssl/private/あんたのドメイン.key;

  location / {
    proxy_pass http://localhost:3333;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

```nginx
# Woodpecker用
server {
  listen 80;
  listen [::]:80;
  server_name cicd.あんたのドメイン;
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name cicd.あんたのドメイン;
  ssl_certificate     /etc/ssl/certs/あんたのドメインpem;
  ssl_certificate_key /etc/ssl/private/あんたのドメイン.key;

  location / {
     proxy_set_header X-Forwarded-For $remote_addr;
     proxy_set_header X-Forwarded-Proto $scheme;
     proxy_set_header Host $http_host;

     proxy_pass http://localhost:8000;
     proxy_redirect off;
     proxy_http_version 1.1;
     proxy_buffering off;

     chunked_transfer_encoding off;
    }
}
```

記述を終えたら保存して`nginx -t`で文法を検証する。問題がなければ`systemctl restart nginx`で再起動を行う。`docker-compose up -d`でコンテナを起動すると、この時点で紐づけたサブドメインからForgejoの初期設定画面にアクセスできるはずである。Woodpeckerの方はForgejoとの連携作業が済むまでは接続できない。


## Forgejoの設定
ほとんどの欄がすでに埋まっているので自ら記入する項目は少ない。むしろ下手にいじると初期設定に失敗する。強いて挙げるなら管理者アカウントを事前に作成するか、サイトタイトルなどのブランディングに関わる部分を記す程度と思われる。初期設定を進めると数秒でインストール作業が完了して他のページに遷移する。

初期設定を編集したい場合は`forgejo/gitea/conf/app.ini`という大層紛らわしいディレクトリの下に生成されるファイルで変更できる。なお、Woodpeckerとの連携に際して以下の追記が求められる。

```ini
[webhook]
ALLOWED_HOST_LIST = external,loopback
```

また、一人で使用するなら新規登録機能は予め封じておいた方が無難だ。ただし、初期設定で管理者アカウントを作らず先に登録を無効化するとブラウザ経由でログインする手段がなくなってしまうのでこの設定は後に行う。

```ini
[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW = false
REGISTER_EMAIL_CONFIRM = false
ALLOW_ONLY_EXTERNAL_REGISTRATION = false
```

一通りの設定が済んだらWebページの右上の＋マークから「新しいリポジトリ」を作成して`git clone`や`git push`の動作を確認する。ちなみに、SSHキーの登録はユーザ設定の「SSH/GPGキー」から行える。`docker-compose.yml`の`ports`で指定したポート番号がSSH通信に用いられるので、それに応じたポートを開ける。

```zsh
ufw allow 4444
ufw reload
```


## Woodpeckerの設定
Forgejoのユーザ設定から「アプリケーション」に進んで「OAuth2アプリケーションの管理」でシークレットキーを作成する。アプリケーション名はなんでも差し支えない。対して、リダイレクトURIは`https://cicd.あんたのドメイン/authorize`の形式で明確に指定しなければならない。

![](/img/210.png)

ここで生成された`クライアントID`と`クライアントシークレット`の値がそれぞれ`docker-compose.yml`の`WOODPECKER_GITEA_CLIENT`と`WOODPECKER_GITEA_SECRET`に符合する。後者は一度しか表示されない。ついでに`WOODPECKER_AGENT_SECRET`の欄を`openssl rand -hex 32`で乱数を出力して埋める。

`docker-compose down`で一旦コンテナを終了させてから`docker-compose up -d`で再起動して、Woodpecker用に割り当てたサブドメインにアクセスする。認証が要求されるのでForgejoで作成したアカウント情報を用いる。「＋Add repository」の項目をクリックしてForgejoのリポジトリを追加できたらひとまず成功と見ていいだろう。

以降は対象のリポジトリ直下に`.woodpecker/*.yml`のディレクトリ構造でコンテナファイルを作り、目的に適った内容のパイプラインを実行させる形となる。したがって、ForgejoとWoodpeckerの構築作業は以上で終了である。


## 実践例
静的サイトジェネレータのデプロイを例にとる。実は当ブログも先月中旬からCloudflare PagesではなくVPS上で稼働しており、Forgejo上のリモートリポジトリにPushした変更をWoodpeckerへ渡すことで同等のデプロイ環境を再現している。実際の記述例は以下の通り。

```yml
clone:
  git:
    image: woodpeckerci/plugin-git
    settings:
      recursive: true

steps:
  build:
    image: klakegg/hugo:ext-alpine
    commands:
      - hugo
  deploy:
    image: drillster/drone-rsync
    secrets: [USER, HOTS, SSH, PORT]
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

上記の例では`hugo`コマンドを実行するコンテナによって吐き出された静的ファイルを、`rsync`コマンドでVPS上の`/var/www/html`に同期する方法にてデプロイを行っている。その際に使用されるSSH通信の秘密鍵やポート番号などはコンテナファイルに直接記述すべきではないので、Woodpeckerの機能を用いて秘匿化してある。これは各リポジトリ画面の右上の歯車から「Secrets」で設定できる。

余談だが、Woodpeckerではパイプラインを実行するととてもかわいいアニメーションが見られる。僕はこれを目の当たりにした瞬間に一発でこのソフトウェアが好きになった。機能的には不必要とはいえこういう遊び心ってすごく大切だ。30分くらいは余分に働いてもいい気分になる。

![](/img/211.gif)


## おわりに
かつてGitやCI/CDはローカルかセルフホスト環境で実行するサービスだったが、いつからかGitHubなどの営利企業が豊富な計算資源に物を言わせてずいぶん手軽に使いやすくしてしまった。これらの無料枠は大半のユーザにとってとてつもなく寛大すぎたため、あらゆるプロジェクトがバージョン管理システムとCI/CDの恩恵に与る未曾有の黄金時代が到来した。

しかし、その一方で営利企業とは当然ながら自己利益優先で動く顔のない怪物だ。昨日までの最良の友が寝て起きたら人を食う魔物に変貌していたなどという事態はいつでも起こりうる。利益率を重視するあまり元々は洗練されていた機能が混沌の渦中に堕し、積み重なったベンダーロックインの依存性ゆえ抜け出すにも抜け出せない危険性は常に考慮しなければならない。

かといって、なにも完全に移行する必要はまったくない。GitHubにしろ数多あるCI/CD環境にしろ、それはそれで確かに優れたソーシャルコーディングサービスには違いない。ただ、平時より怠らず代替となりうるソフトウェアを使い慣れておけば、用途に応じて賢く使い分けたり、最悪のハルマゲドンに備えられる第二、第三の選択肢が皆さんの手のうちに残り続けるのである。
