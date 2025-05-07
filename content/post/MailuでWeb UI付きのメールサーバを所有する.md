---
title: "MailuでWeb UI付きのメールサーバを所有する"
date: 2023-08-26T21:25:25+09:00
draft: false
tags: ["tech"]
---

![](/img/207.png)

初夏の頃には[こんなこと](https://riq0h.jp/2023/05/05/213838/)を言っていたが、VPSの計算資源が余っているのでやはり自前でメールサーバを建てた。なにしろ幾多の艱難辛苦に晒された10年前と現在では状況がずいぶん違う。今やDockerが普及しており、手の行き届いたOSSが用意されており、培ってきたトラブルシューティングの知識が備わっている。躓いたらコンテナを破棄してやり直せばいい。サーバを建てるたび実行環境の至るところに引っかき傷を残していた過去とはもうおさらばだ。

[Mailu](https://github.com/Mailu/Mailu)というOSSがある。メールサーバの構成要素が統合されていて全部よしなにやってくれる上にWeb UIまで付いてくるすごいやつだ。こんなのがあるんだったらVPSを契約している身でわざわざ他所に金を払っている場合ではない。こうして、僕は意気揚々と構築作業に乗り出したのだった。とはいえ相変わらずメールサーバは手強い。本稿ではDockerを利用したMailuの構築方法について記す。

## ファイルの取得と編集

`docker`および`docker-compose`はすでに導入されているものとする。専用のユーザでホーム直下にディレクトリを作成した後は通常、`docker-compose.yml`の雛形をコピペする形が典型的だが、MailuはWeb上の[セットアップユーティリティ](https://setup.mailu.io/2.0/)でユーザの意図に適った設定ファイルを出力してくれる。これらのファイルは`docker-compose.yml`と`.env`ファイルなのでいつでも編集できる。

ユーティリティの"Choose how you wish to handle security"の欄は現状ではピンと来ないかもしれない。しかし最終的にはおそらく`letsencrypt`か`mail-letsencrypt`を選択することになる。SSL証明書をすでに持っているかどうかは関係ない。理由は後述する。ただし、セットアップの段階では誤った連続試行による取得規制を避けたいので`cert`を選択しておく。

`docker-compose.yml`の重要なポイントとして、ポート設定の`80:80`と`443:443`の左側は必ず別の番号に変更しなければらない。メールサーバ以外のサービスを一切立ち上げていないのならともかく、これらのポートはほぼ確実に専有されている。僕は`7900:80`、`8443:443`にした。メールサーバなのにHTTP/HTTPSポートが必要な理由はタイトル通りWeb UIが備わっているためだ。この修正に際して`mailu.env`に以下の追記が求められる。

```env
REAL_IP_HEADER=X-Real-IP

REAL_IP_FROM=あんたのグローバルIP
```

自動生成の甲斐あって他に修正すべき箇所は大してない。強いて挙げると僕は軽量化優先で`Webmail`と`oletools`を省いている。もし皆さんがCloudflareなどのCDNを間に挟んで**いなければ**ここからの話はとてもスムーズに進む。……だが、今時そんな人いるか？　それこそ10年前とは違う。今はなんでもCDNの上に乗っかっている。ところがメールサーバにはそういう話がてんで通用しない。だから面倒くさいんだ。

## DNSレコードの設定

Cloudflareの設定を例にとる。メールサーバに用いるルートドメインを選択して**DNS → レコード**からサブドメインを新設する。通例であればサーバのIPアドレスをAレコードでサブドメインと紐づけて、MXレコードに当該のドメインを登録しておしまいだが、メールサーバに対しては「プロキシ」を有効にしては**ならない。** 適用後の表示が「DNSのみ」になるように定める。

これはあえてプロキシを有効にしてMXレコードを引いてみると事情がよく判る。CDNを通る過程で情報がおかしくなってしまうのか、サブドメイン部分が不正な値に書き換わって出力されている。この状態ではメールの送受信に障害が生じたり、メールクライアントから接続できないといった不具合に見舞われる。公式のドキュメントにも[やるなと書いてあった。](https://developers.cloudflare.com/support/other-languages/%E6%97%A5%E6%9C%AC%E8%AA%9E/cloudflare%E3%81%AE%E4%BD%BF%E7%94%A8%E6%99%82%E3%81%AB%E3%83%A1%E3%83%BC%E3%83%AB%E3%81%8C%E9%85%8D%E4%BF%A1%E4%B8%8D%E8%83%BD%E3%81%AB%E3%81%AA%E3%82%8B/)以下に実例を示す。

```zsh
$ dig mx mystech.ink
...中略...
;; ANSWER SECTION:
mystech.ink.            300     IN      MX      10 mx.mystech.ink.
#正常なら設定通りのMXレコードが引ける。

$ dig mx mystech.ink
...中略...
;; ANSWER SECTION:
mystech.ink.            300     IN      MX      10 _dc_24782934.mystech.ink.
#プロキシが有効だと不正な値に書き換わる。
```

では「DNSのみ」にすれば万事解決か、というとそうでもない。今度はSSL証明書の問題が残る。プロキシを有効にしているとCloudflareの恩恵で自動的にエッジ証明書が付与されるが、今回はそれがまったく使えないのだ。したがって、メールサーバ用に個別のSSL証明書を用意しなければならない。

すでに持っているSSL証明書がCloudflareやCDNのものではなく、自前で取得したLet's EncryptやZeroSSLなら基本的には使い回せる。しかし、本稿で紹介するのはDockerを利用した構築方法だ。Dockerコンテナの内部で動いているサーバから外部のSSL証明書を直接参照する方法は用意されていない。公式では特定のディレクトリにコピペさせるやり方を採っている。

多くの人が使っている無料のSSL証明書は有効期限が3ヶ月しかない。3ヶ月ごとにいちいち更新した証明書を貼り直したり、ちまちまスクリプトを書いてcronを走らせるのはおよそ洗練されているとは言いがたい。僕たちは最先端の統合スイートOSSでちょっぱやのメールサーバを建てているのではなかったのか？

そこで、前述した`letsencrypt`が顔を覗かせる。これは初回起動時に予め決めたドメインの証明書をcertbotが自動で取得して、更新作業も代行してくれるマジで最高の設定である。こいつに任せておけば証明書周りはDockerコンテナの内部で完結する。このOSSがシンプルなメールサーバだったら話は大団円を迎えていたに違いない。

だが、僕たちはWeb UI付きのメールサーバを建てている。つまり、ブラウザ経由で管理画面なりWebメールクライアントにアクセスする。一方、`letsencrypt`の自動取得機能は80番ポートで通信を行う。ここで問題となるのは、管理画面に用いるサブドメインと、メールサーバのサブドメインが同じだった場合に、脆弱な80番ポートを露出したWebサーバが公開されてしまうことだ。

本来、80番ポートに向かう接続試行はCDNかリバースプロキシでリダイレクト処理を行うが、Cloudflareの恩恵を受けられない身分で証明書周りの設定を済ませるにはそういうわけにもいかない。では、どうすべきか。Web UI自体を使わない手もあるが、それならMailuを選んだ意味がない。面倒な管理をGUIで完結させたいからこそのWeb UI付きメールサーバじゃないか。

幸いにも解決策は見つかった。管理画面用のサブドメインと、メールサーバ用のサブドメインを別々に設ければいい。`hogefuga.com`で例えると、管理画面用に`mail.hogefuga.com`、メールサーバ用に`mx.hogefuga.com`をそれぞれ作る。単なるWebフロントエンドに過ぎない前者はプロキシを有効化して自動でSSL証明書を得られるし、後者は安全に80番ポートを開けて`letsencrypt`の自動取得を受け付けられる。以上を踏まえた記述例を下記に示す。

```dns
hogefuga.com IN A 111.111.111.111 #メールアドレスの後ろ半分になるルートドメイン。プロキシ化する。

mail.hogefuga.com IN A 111.111.111.111 #管理画面用のAレコード。プロキシ化する。

mx.hogefuga.com IN A 111.111.111.111 #メールサーバ用のAレコード。プロキシ化しない。

hogefuga.com IN MX mx.hogefuga.com #メールサーバ用のMXレコード。プロキシ化しない。
```

上記の例では管理画面やWebメールクライアントにアクセスする際は`mail.hogefuga.com`を使って、スタンドアロンのメールクライアントでログインする時には`mx.hogefuga.com`を用いる形となる。`mailu.env`ファイルもこれに沿って修正する。ユーティリティから再度作成し直しても構わない。

```env
# Main mail domain
DOMAIN=あんたのドメイン

# Hostnames for this server, separated with comas
HOSTNAMES=mx.あんたのドメイン

# Choose how secure connections will behave (value: letsencrypt, cert, notls, mail, mail-letsencrypt)
TLS_FLAVOR=letsencrypt

...中略...

# Website name
SITENAME=mail.あんたのドメイン

# Linked Website URL
WEBSITE=https://mail.あんたのドメイン
```

## リバースプロキシの設定

続いて、リバースプロキシの設定を書く。前述の通り管理画面およびWebメールクライアント用と、メールサーバ用の2つのファイルを用意する。

```nginx
#管理画面およびWebメールクライアント用
server {
  server_name mail.あんたのドメイン;

 location / {
    proxy_pass https://localhost:8443;
    proxy_set_header   Host             $host;
    proxy_set_header   Connection       $http_connection;
    proxy_set_header   X-Scheme         $scheme;
    proxy_set_header   X-Real-IP        $remote_addr;
    proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
  }

  listen 443 ssl http2;
  ssl_certificate     /etc/ssl/certs/あんたのドメイン.pem;
  ssl_certificate_key /etc/ssl/private/あんたのドメイン.key;

}
```

CloudflareのSSL/TLS設定で「フル（厳密）」を用いる環境でなければオリジンサーバの証明書は除いても差し支えない。自動で付与されるエッジ証明書でも動作する。MailuはローカルでもHTTPSで通信しているため、`proxy_pass`の記述も合わせる必要がある。

```nginx
#メールサーバ用
server {
  listen 80;
  server_name mx.あんたのドメイン;

 location / {
    proxy_pass http://localhost:7900;
    proxy_set_header   Host             $host;
    proxy_set_header   Connection       $http_connection;
    proxy_set_header   X-Scheme         $scheme;
    proxy_set_header   X-Real-IP        $remote_addr;
    proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
  }
}
```

メールサーバ用のリバースプロキシはSSL証明書の自動取得用に80番ポートが欲しいだけなので簡素な設定で済む。2つのファイルを作成したら`systemctl restart nginx`でnginxを再起動する。

## 初回起動と管理画面の設定

いよいよ初回起動に入る。`docker-compose up`でログを垂れ流して起動する。文字列の中にSSL証明書が取得されたっぽい英文を見つけたら、ひとまず成功と見ていいだろう。Ctrl+cでサーバを停止させた後に`docker-compose up -d`で立ち上げ直して、アドミンユーザの作成を行う。

```zsh
$ docker-compose exec admin flask mailu admin ユーザ名 ドメイン 'パスワード'
```

上記の操作で`ユーザ名@ドメイン`をID、`パスワード`をパスワードとするアドミンアカウントが作成される。ここでようやく管理画面用のURLにアクセスして諸々の設定を行う過程に入る。**メールドメイン → ドメイン名を追加**からメールアドレスの後ろ半分にしたいルートドメインを記入する。

![](/img/208.png)

次に赤枠で囲ったアイコンからユーザを作成する。ここで作成するユーザの名前がメールアドレスの前半分になる。最後に青枠で囲ったアイコンから右上の「鍵を再生成」を押す。すると、SPF/DKIM/DMARCの設定に必要な情報が表示されるので各々をDNSレコードに登録しに行く。デフォルトで迷惑メールフォルダに振り分けられたくなければ絶対に登録した方がよい。

また、Mailuは高機能スパムフィルタのRspamdを搭載している。管理画面の「設定」からスパムメールの閾値（高いほど緩い）が調節可能なほか、「スパムメール対策」ではフィルタリングの詳細な結果を閲覧できる。今のところは完璧に捌いている印象だが、たまにどんなふうに迷惑メールが弾かれているか調べてみると面白い。

![](/img/209.png)

## 送受信の確認

管理画面からWebメールクライアントに移動して実際に送受信を行う。相手のメールがこちらに届いて、その逆にも問題がなければメッセージのソースからSPF/DKIM/DMARCの認証が行えているか検証する。すべてがクリアなら以下の形式で承認されているはずだ。

```conf
Authentication-Results: spf=pass (sender IP is xxx.xxx.xxx.xxx)
smtp.mailfrom=あんたのドメイン; dkim=pass (signature was verified)
header.d=あんたのドメイン;dmarc=pass action=reject header.from=あんたのドメイン;compauth=pass
reason=100
```

さらに同様の作業を普段使っているメールクライアントからも行えるか確認しておく。ログイン情報は管理画面の「クライアント設定」から見られる。いずれの環境でも支障がなければメールサーバの構築作業は無事に終了となる。

## おわりに

さすが全部まとまっているだけあってMailuのセキュリティ設定は十分にこなれているが、それでもメールパスワードの管理は常にユーザの自己責任として生涯ついて回る。特にメールサーバは狙われやすい対象ゆえ、英数字で10桁未満などという寝ぼけたパスワードでは10年前の僕みたいに秒で破られてしまうだろう。

今時、自前でメールサーバを運用する趣味性を持つならばパスワードにも気を配り、暗記頼りや使い回しではないパスワードマネージャによる管理体制を築くべきである。自分で覚えなくていいのならパスワードはどんなにでも長く作り変えられる。ぜひ検討してほしい。どれほどサーバを建てるのが簡単になろうとも安定運用が難しいのはいつまでも変わらない。
