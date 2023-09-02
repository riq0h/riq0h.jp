---
title: "Forgejo+WoodpeckerでCI/CD環境を所有する"
date: 2023-09-03T08:39:29+09:00
draft: true
tags: ['tech']
---

逆になにができないのか判らないほど多機能と化したGitHubなどの大手Gitホスティングサービスだが、その機能性が仇となって限られた用途で利用するにはいささか煩雑な画面操作を要求されることが増えてきたように思う。`gh`コマンドは便利ではあるものの圧の強いUIと格闘するかCLIかの二択は少々極端なきらいが否めない。

そこで自前の計算資源を持っている人間にはリモートリポジトリのセルフホスティングが検討される。世の中には絶対にissueやPRを受け付ける気がない雑多なコード片や、ごく個人的、ないしは見知った少人数のみのプロダクトが存在する。そういったプライベート色の強いリポジトリを管理するには、いっそGitHubよりもミニマルに設計されたOSSの方が快適に用を足せると考えられる。

そもそもgitとは分散型志向のバージョン管理システムであり巨大資本のルールに縛られた一つの場所にコードを置くのは本来の設計理念に反するという考え方もある。もし持て余した計算資源がそこらに転がっているのなら、そこに個人的なリモートリポジトリを生やしてみるとこれまでに得られなかったときめきが感じられるかもしれない。本稿ではForgejoとWoodpeckerを連携させて統合的なCI/CD環境を構築する手法について記す。


## ソフトウェアの紹介

[**■Forgejo**](https://forgejo.org)
ForgejoはGiteaを基にしたGitホスティングソフトウェアのコミュニティ主導フォークで、商業化に傾倒したGiteaから主要な開発者が離反する形で誕生した。昨年末に分派したばかりで見た目以外の目立った変更箇所はさほどないが、その代わりにGitea向けのソフトウェアや連携機能を利用することができる。

[**■Woodpecker**](https://woodpecker-ci.org)
Woodpeckerも同様にDroneを基にしたコミュニティ主導フォークだが、こちらは特に喧嘩別れというわけではないらしい。エンタープライズ向けの有料エディションを持つDroneと違い生涯にわたる完全無料を確約している。

CI/CDとは「継続的インテグレーション/継続的デリバリー」の意で、コードの変更を起点に自動的にテストを行ったり、それを反映した最新バージョンを自動的に展開するための機能群を指す。GitHubのGitHub ActionはCI/CDの一つと言える。企業の提供する無料のCI/CD環境には制約が設けられている一方、セルフホストすれば所有する計算資源の限界まで使い倒せる利点がある。


## ファイルの取得および編集
`docker`および`docker-compose`はすでに導入済みと仮定する。ForgejoとWoodpeckerはそれぞれ別のソフトウェアで、前者がGitホスティング、後者がCI/CDの機能を提供しているが、互いに連携させる前提で構築するため今回は単一の`docker-compose.yml`でそれぞれをまとめる。

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
      - WOODPECKER_GITEA_CLIENT=指定された英数字
      - WOODPECKER_GITEA_SECRET=ランダム生成
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
      - WOODPECKER_AGENT_SECRET=ランダム生成
    networks:
      - forgejo

volumes:
  woodpecker-server-data:
  woodpecker-agent-config:
```

`ports`の箇所はコロンの左側を他の数字に置き換えてもよい。この例では3000番ポートがすでに他のサービスに専有されているので代わりに3333番ポートを指定している。同様に、ForgejoとSSH通信で`git push`などを行うためのポートも標準の22番を避けている。`woodpecker-server`の8000番ポートももし空いていなければ他のに変える。

Woodpecker側の設定もここで指定する。`environment`の記述はブラウザからのアクセスやForgejoとの連携を図る上で必須となる。予めレジストラでそれぞれ任意のサブドメインを割り振っておくと話が早い。たとえばForgejoの方を`git.あんたのドメイン`、Woodpeckerの方を`cicd.あんたのドメイン`などに割り当てる。形式が`WOODPECKER_GITEA_*`なのはForgejoを内部的にGiteaと認識させているためだ。




## リバースプロキシの設定
nginx向けにリバースプロキシを書く。Forgejo用のものとWoodpecker用の二つを用意する。Cloudflareを利用していてオリジンサーバ証明書を取得していなければ[この記事](https://riq0h.jp/2023/07/22/204725/)の冒頭を参考に設置を行う。一度やれば使い回せるのでぜひおすすめしたい。

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

記述を終えたら保存して`nginx -t`で文法をチェックする。問題がなければ`systemctl restart nginx`で再起動を行う。`docker-compose up -d`でコンテナを起動すると、この時点で指定したサブドメインにてForgejoの初期設定画面にアクセスできるはずである。ただし、WoodpeckerはForgejo上の連携作業が完了するまでは閲覧できない。


## Forgejoの設定
ほとんどがすでに埋まっているので自ら記入する項目は少ない。むしろ下手にいじると初期設定に失敗する。強いて挙げるなら管理者アカウントを前もって作成するか、サイトタイトルなどのブランディングに関わる部分を書く程度と思われる。初期設定を進めると数秒でインストール作業が済んで他のページに遷移する。

初期設定を変更または追記したい場合は`forgejo/gitea/conf/app.ini`という大層紛らわしいディレクトリの下に生成されるファイルで編集できる。Woodpeckerとの連携に際して下記の追加が求められる。

```conf
[webhook]
ALLOWED_HOST_LIST = external,loopback
```

また、一人で使用するなら新規登録は予め封じておいた方が無難。ただし、初期設定で管理者アカウントを作らず先に登録を無効化するとWeb上でログインする方法がなくなってしまうのでこの設定は後に行う。

```conf
[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW = false
REGISTER_EMAIL_CONFIRM = false
ALLOW_ONLY_EXTERNAL_REGISTRATION = false
```

一通りの設定が済んだら右上の＋マークから「新しいリポジトリ」を作成して説明通りの`git clone`や`git push`が行えるか確認する。また、SSHキーの紐づけはユーザ設定の「SSH/GPGキー」から行える。`docker-compose.yml`の`ports`で指定したポート番号がSSH通信に用いられるので、それに応じたポートを解放しておかなければならない。

```zsh
ufw allow 4444
ufw reload
```


## Woodpeckerの設定
Forgejoのユーザ設定から「アプリケーション」に進んで「OAuth2アプリケーションの管理」からキーを作成する。アプリケーション名は判別できればなんでも差し支えない。対してリダイレクトURIは`https://cicd.あんたのドメイン/authorize`の形式で明確に認証を指定する。

![](/img/210.png)

ここで生成された`クライアントID`と`クライアントシークレット`の値がそれぞれ`docker-compose.yml`の`WOODPECKER_GITEA_CLIENT`と`WOODPECKER_GITEA_SECRET`に符合する。後者は一度きりしか表示されないので注意されたし。ついでに`WOODPECKER_AGENT_SECRET`の欄を`openssl rand -hex 32`で乱数を出力して埋める。

`docker-compose down`で一旦コンテナを終了させてから`docker-compose up -d`で再起動して、Woodpecker用に割り当てたサブドメインにアクセスする。認証を要求されるのでForgejoで作成したアカウントでログインを行う。ログイン後、右上のアイコンから確認できる「Personal Access Token」の値を以下の要領で`forgejo/gitea/conf/app.ini`に書き込む。

```conf
INTERNAL_TOKEN = XXXXXXXXXXXXXXXXXXXX
```

「＋Add repository」の項目をクリックしてForgejoのリポジトリを追加できたらひとまず成功を考えられる。以降は通常のCI/CDと同じように対象のリポジトリ直下に`.woodpecker/*.yml`の形式でコンテナファイルを作り、目的の用途に適ったパイプラインを記述していくこととなる。したがって、ForgejoとWoodpeckerの構築作業は以上で終了である。


## 実践例
もっとも単純なパイプラインの実行例として静的サイトジェネレータのデプロイを挙げる。実は当ブログも先月よりCloudflare PagesではなくVPS上で稼働しており、ForgejoのリポジトリにPushした変更をWoodpeckerへ渡すことで同様のデプロイ環境を実現している。実際の記述例は以下の通り。

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

上記の例では`hugo `コマンドを実行するコンテナによって吐き出された静的ファイルを`rsync`コマンドでVPSの`/var/www/html`に送信する形でデプロイを行っている。その際に利用されるSSH送信の秘密鍵やポート番号などは公開リポジトリに置くファイルに記述すべき情報ではないため、Woodpeckerの機能を用いて秘匿化する。各リポジトリ画面の右上の歯車から「Secrets」で設定できる。

なお、余談だがWoodpeckerではパイプラインを実行するといい感じのアニメーションが見られる。僕はこれを目の当たりにした瞬間に一発でこのOSSが好きになった。機能的には不必要とはいえこういう遊び心って大切だ。30分くらいは余分に働いてもいい気分になる。

![](/img/211.gif)


## おわりに
かつてGitやCI/CDはオンプレミス環境で実行する代物だったが、いつからかGitHubなどの営利企業が計算資源に幅を利かせてずいぶん使いやすくしてしまった。これらの無料枠は大半のユーザにとってあまりにも寛大すぎたため、あらゆるプロダクトが手軽なバージョン管理とCI/CDの恩恵に与る黄金時代が到来した。

しかし、その一方で営利企業とは当然ながら自己利益優先で動く怪物である。昨日までは大盤振る舞いで使わせてくれたのに今日からはろくに使わせてもらえないなどという事態はいつでも起こりうる。利益率を重視するあまり本来は洗練されていた機能群が混沌の渦中に堕し、積み重なったベンダーロックインの依存性ゆえ抜け出すにも抜け出せない危険性は常に考慮しなければならない。

かといって、なにも完全に移行する必要はない。GitHubにしろ数多あるCI/CD環境にしろ、それはそれで確かに優れたサービスには違いない。ただ、いつでも代替となりうるソフトウェアを使い慣れておけば、用途に応じて賢く使い分けたり、最悪のハルマゲドンの到来に備えられる第二、第三の選択肢が皆さんの手のうちに残り続けるのである。
