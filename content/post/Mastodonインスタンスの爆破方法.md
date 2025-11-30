---
title: "Mastodonインスタンスの爆破方法"
date: 2025-11-30T23:28:05+09:00
draft: false
tags: ["tech", "diary"]
---

[自作のActivityPub実装](http://localhost:44123/2025/07/11/163822/)を運用しはじめてから4ヶ月ほどが経過した。様々な艱難辛苦を経て弊機は無事、安定軌道に乗っている。いよいよ数光年後方に置いてきた船を処理する時がきた。たとえ心細くても、むやみに電波を発する構造物をいつまでもFediverseの海に放っておくわけにはいかないのだ。交信を試みる幾千の船にいらぬ負担をかけてしまう。僕はそっと古巣の起爆装置に手をかけた。

このような備忘録的記事はいずれどれもLLMに読み込まれて一個の情報単位に均され、僕が書いた生の文章が人々に読まれる機会は次第に減っていくだろう。単純にMastodonのインスタンスを閉鎖したい人にとって、僕個人のナラティブや事情は可聴域外の音声データとなにも変わらない。同様の情報は他にいくらでもある。それでも書くのは、結局そうせずにはいられないからだ。

## Bridgy Fedサービスを停止する

まずはブリッジサービスを停止する。おそらくこの語で表される仕組みは一つや二つではないと思われるが、ここではBlueskyとの交信を可能にするサービスを指す。当該SNSのユーザ人口を考えると利用している人はかなり多いはずだ。サービスの停止は`@bsky.brid.gy@bsky.brid.gy`をブロックするだけで完了する。

とはいえ、もしかするとこの手順は不要かもしれない。インスタンスとの通信が一定期間途絶した段階で、自動的にブリッジアカウントの削除を行う仕様になっている可能性もある。しかし万が一、そのような処理が走らなかった場合には、Blueskyの方に魂を失った幽霊船が取り残されることになる。後で運営者に頼んでもそのブリッジアカウントの本当の持ち主だと証明しうる手立てはない。

そう考えると、ブリッジサービスの利用者は必要の際にはなるべく明示的に利用停止の手続きをとる方が公益に資するだろう。今後も同様の仕組みでなんらかの交信を試みるサービスは登場するであろうから、インスタンスの運営者に限らずオプトアウトの作法には慣れておいた方がよいと思う。ブロック後、数時間経つと確かにBluesky側からアカウントが消滅していた。

## 埋め込みURLを置き換える

ブログをやっている人にとってSNSの埋め込み機能は便利なものだ。追加の文言なしで状況を説明しやすいし、画像を再度添付する手間も省ける。ところがこの機能は実装のハードルが相当高いらしく、どの実装系にも備わっているとは限らない。もちろん、僕のActivityPub実装にも今のところは搭載していない。

<blockquote lang="ja" cite="https://letter.mystech.ink/users/riq0h/posts/20081357962222423" data-source="fediverse">
  <p>たまには絹の麻婆豆腐もいいね！</p>
  <figure><img src="https://media.mystech.ink/img/65db84d3c084d812d333769105cf35b5" width="400" height="225" alt="麻婆豆腐" loading="lazy" /></figure>
  <footer>
     — Rikuoh Tsujitani (@riq0h) <a href="https://letter.mystech.ink/users/riq0h/posts/20081357962222423"><time datetime="2025-11-30T11:53:25.000Z">2025/11/30 20:53:25</time></a>
  </footer>
</blockquote>

そこで代わりに、上記の形にblockquoteで体裁を繕った。これはPhanpyというサードパーティクライアントの機能だが、動的な要素をなにも含まないただのHTMLなので良くも悪くも依存はない。さしあたりしばらくはこの方法でやり過ごして、後でじっくりと埋め込み機能の実装を検討するつもりだ。

## Mastodonの自己破壊コマンドを入力する

準備が整ったら作業ディレクトリに入り、`tootctl self-destruct`コマンドを入力する。これはMastodonが提供している自己破壊機能で、既知のすべてのサーバに対して交信を永久に終了するアクティビティを送信する。他のサーバ群がそれを正常に処理すると、対象のインスタンスは以降どこからも認識されなくなる。まさにFediverseのスペースデブリを化す。

```bash
mastodon@f7b2ce1d610b:~$ tootctl self-destruct
Type in the domain of the server to confirm: mystech.ink
This operation WILL NOT be reversible.
While the data won't be erased locally, the server will be in a BROKEN STATE afterwards.
The deletion process itself may take a long time, and will be handled by Sidekiq, so do not shut it down until it has finished (you will be able to re-run this command to see the state of the self-destruct process).
Are you sure you want to proceed? yes
To switch Mastodon to self-destruct mode, add the following variable to your evironment (e.g. by adding a line to your `.env.production`) and restart all Mastodon processes:
  SELF_DESTRUCT=Im15c3RlY2guaW5rIg==--2688f77d7224f21ae4b3937b86a0de976de90c94
You can re-run this command to see the state of the self-destruct process.
mastodon@f7b2ce1d610b:~$
```

指示に従って自己破壊用の環境変数を`.env.production`に加えて再起動すると、インスタンスのトップページが閉鎖告知用のものに切り替わる。この時点でもアカウント設定からデータのバックアップを要求できるが、インスタンス運営者の場合はサーバを直接操作してデータベースを保存するはずなので、権限を持たないユーザ用の機能と思われる。

![](/img/434.png)

自己破壊処理は非常に時間を要するので、1、2日ほど待ってからコンテナまたはプロセスを終了する。一応、自己破壊コマンドを再度入力すると進捗を教えてもらえる。処理完了後、Docker環境なら`docker volume rm mastodon_redis mastodon_postgres`などで関連のボリュームをまとめて削除してもよい。非Docker環境は単純に作業ディレクトリを削除するだけで済む。

## リバースプロキシの設定を変更し、410 Goneを送信する

最後に、全リクエストに対してサーバを閉鎖させた意思を示す`410 Gone`ステータスコードを送信する。この措置により、前述のアクティビティを受信しなかったか、または処理していないサーバに対しても交信の即時終了を促すことができる。自己破壊コマンドが船のデブリ化だとしたら、こちらは爆破作業に近い。Fediverseという連合宇宙の環境保護のためにも、立つ鳥は跡を濁してはならない。

```nginx
server {
    listen 80;
    server_name your-domain.com;

    return 410;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    return 410;
}
```

上記の要領でNginxの設定ファイルを書き換えてから再起動すると、当該のドメインは次に処理を変更するまで延々と410 Goneを返し続ける。ドメインを再利用する予定が特にないのなら当面は継続する方が望ましい。電波を受けるのも発するのもただではない。連合宇宙のコミュニティは各員の協調で成り立っているのである。

## おわりに

こうして、一つの宇宙船がFediverseの片隅でひっそりと役目を終えた。数光年後方で控えめに一瞬、ぴかりと光ってすぼまったその姿は、ただの一人の男が根城にしていた場所に相応しい素朴さが感じられた。
