---
title: "自作ActivityPub実装に絵文字リアクションを部分的に追加した"
date: 2026-07-11T11:11:12+09:00
draft: true
tags: ["tech"]
---

自作ActivityPub実装を開発して一年が経った。当時はなるべくミニマルな仕様にしたいのと、[このような](https://riq0h.jp/2023/06/19/082543/)気持ちもあって躊躇していたが、目に見える範囲を抑えれば共存できると思い直して実装に踏み込んだ。

僕が抱いている問題意識は、そもそも絵文字リアクションがタイムライン上で占めている専有面積が多すぎるというものだった。SNSではなくマイクロブログとしての発展を期待している立場からすると、投稿本文よりもリアクション部分に注目が集まりやすい設計はソーシャル要素が勝ちすぎているように感じられたのだ。頻繁に見えるから飽きが早くなるし、安直に送受信できるからコミュニケーションが作業的になる。

そこでまず、弊実装系では他ユーザの絵文字リアクションを取得しない設計にした。受信するのは自分の投稿に付けられたリアクションのみとなる。また、送信は実装しない。さらにクライアント上での表示は狙わず、Webフロントエンドの詳細投稿画面でのみ閲覧可能とした。普段はリアクションをあまり意識せず、対応する実装系のユーザから反応があった時に確認しに行く運用を想定している。

これのなにが嬉しいのかというと、見たくなるまでは見ない選択肢を採れること、それでいて受信自体は常に受け入れているので正確な反応を把握できるようになったことだ。従来のMastodon-Likeな設計では、`content`に載っているどのリアクションもLikeに丸められ、Pleroma系の`EmojiReact`に至ってはLikeにすらならず切り捨てられていた問題があった。

当時は既存の実装系からなにを選ぶかが前提だったため、絵文字リアクションとべったり付き合うか、もしくはまったく付き合わないかのほぼ二択しかなかったが、実装系を自作した今では付き合い方を柔軟に取捨選択できる。前述の記事ほど絵文字リアクションを拒絶する理由はもはやなくなったと言ってもよい。

具体的な実装は、受信だけなら割と簡単だった。まず、favouritesに`:reaction`を足した上で独立したテーブルにはせず、Favouriteの付加属性として扱う。通常のLikeはreaction = NULL のままなので、既存のMastodon APIには影響を及ぼさない。次に、Undo側も同様に処理する。`EmojiReact`のActivityレコードは`activity_type: 'Like'` で保存し、取り消し処理を共通化している。

```ruby
  # db/migrate/20260709000001_add_reaction_to_favourites.rb
  class AddReactionToFavourites < ActiveRecord::Migration[8.0]
    def change
      add_column :favourites, :reaction, :string
    end
  end
```

```ruby
  # app/controllers/inbox_controller.rb (shared inboxも同様)
  when 'Like', 'EmojiReact'
    # EmojiReact(Pleroma/Akkoma系)はLikeと同様に処理する(reaction付きふぁぼ)
    handle_like_activity
```

また、リアクションのAPペイロードにはtagにカスタム絵文字の画像URL(Emoji object)が同梱されている。これを投稿本文の絵文字と同じprocess_emoji_tagsでCustomEmojiとして取り込み、画像は既存の絵文字画像キャッシュ(R2)に相乗りさせる。

リアクション経由で新規に知った絵文字はレコード作成時に先読み取得されるので、初回表示の時点で画像はすでに手元にある。バックフィルは一方通行(nil→絵文字のみ、上書きはしない)なので、Mastodonからのプレーンな再Likeが既存リアクションを消すことはない。

```ruby
  # app/controllers/concerns/activity_pub_like_handlers.rb
  def create_or_update_like(target_object)
    return unless target_object.actor.local?

    reaction = extract_reaction_content

    # リアクションのカスタム絵文字(tag内Emoji)を取り込む。表示用の画像は
    # after_create_commitの先読みでR2にキャッシュされる
    process_emoji_tags(@activity['tag'], domain: @sender.domain) if reaction

    if like_already_exists?(target_object)
      backfill_reaction(target_object, reaction)
      return
    end

    create_new_like(target_object, reaction)
  end

  # 既存のfavがプレーン(reaction無し)で、後からリアクションが届いた場合は絵文字だけ補完する
  def backfill_reaction(target_object, reaction)
    return if reaction.blank?

    favourite = find_existing_favourite(target_object)
    return unless favourite && favourite.reaction.blank?

    favourite.update!(reaction: reaction)
  end
```

実装後、折よくポストした投稿がプチバズしたこともあっていい感じに絵文字リアクションが集まった。弊実装系では以下のように見えている。この形式のなにが嬉しいのかというと、Webフロントエンドにささやかなソーシャル用途を足せるところだ。僕の友達にはフロントエンドページをじかにブックマークして読んでいる人もいる。彼らにとってLikeやRTの数はなんの意味もないが、面白い絵文字が表示されているのはエンタメ性があるかもしれない。

<div class="letter-embed" data-embed-url="https://letter.mystech.ink/@riq0h/21333328355214435/embed">
  <a href="https://letter.mystech.ink/@riq0h/21333328355214435">@riq0hの投稿を見る</a>
</div>
<script async src="https://letter.mystech.ink/embed.js"></script>

以上、一周年の節目にちょうどよい塩梅の意識変化を得たと思う。かつては絵文字リアクションへの見方がやや極端だったが、実装の自由を手にしたおかげでちょうど良い距離感を掴んだ。二年前の僕へのアンサーとなるが、見たい時にだけ見られるなら問題のほとんどは解決する。重要なのは選択肢であり、選択肢を自分で握ることなのだ。
