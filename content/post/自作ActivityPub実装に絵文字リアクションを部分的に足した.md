---
title: "自作ActivityPub実装に絵文字リアクションを部分的に足した"
date: 2026-07-12T11:38:12+09:00
draft: false
tags: ["tech"]
---

ActivityPub実装を自作して一年が経った。当時はなるべくミニマルな仕様にしたかったのと、[このような](https://riq0h.jp/2023/06/19/082543/)気持ちもあって躊躇していたが、部分的に足すぶんには共存できると思い直して実装に至った。

僕が抱いている問題意識の根本は、そもそも絵文字リアクションが暗黙的に担っている役割が大きすぎるというものだった。あれほど多彩な種類があるとコミュニケーションの多くをミームで代替できる気がしてしまう。しかしそれは錯覚であって、実際に代替しているのはコミュニケーションではなく、まさしく〈リアクション〉に過ぎないのだ。

ところが利便性が高く、よく目立つ機能はあらゆる余白をスポイルせしめる。通常、テキストで行われるべき返答や、もっと字数を割くべき会話が絵文字リアクションの枠の中に押し込められてしまう。SNSではなくマイクロブログとしての発展を願う立場からすると、これは警戒すべき由々しき懸念であった。

一方、絵文字リアクションそのものは基本的には愉快で楽しい代物である。対応する実装系のFFはおそらくなんらかの絵文字を送信してくれているのに、実装系の仕様を盾に切り捨て続けるのはさすがに狭量ではないかとも感じる。なにしろMastodonを使っていた頃ならまだしも今は自作の実装系を使っているのだから。実装系の仕様は僕自身の態度の写し絵でもある。

そこでまず、弊実装系では自分の投稿に付けられた絵文字リアクションのみ受信する形にした。リモートユーザの投稿に付いた絵文字リアクションは記録しない。また、送信機能は実装しない。さらにクライアント上での表示は行わず、Webフロントエンドの詳細投稿画面でのみ閲覧可能とした。普段はリアクションをあまり意識せず、対応する実装系のユーザから反応があった時に確認しに行く運用を想定している。

これのなにが嬉しいのかというと、見たくなるまでは見ない選択肢を採れること、それでいて受信自体は常に受け入れているので正確な反応を収集できるようになったことだ。従来のMastodon-Likeな設計では、`content`に載っているどのリアクションもLikeに丸められ、Pleroma系の`EmojiReact`に至ってはLikeにすらならず切り捨てられていた。

当時は既存の実装系からなにを選ぶかが前提だったため、絵文字リアクションとべったり付き合うか、もしくはまったく付き合わないかのほぼ二択しかなかったが、自作の実装系を得た上にLLMの力も借りられる今時では付き合い方を柔軟に取捨選択できる。冒頭の記事ほど頑なに絵文字リアクションを拒絶する理由はもはやなくなったと言ってもよい。

具体的な実装は、受信だけならとても簡単だった。まず、favouritesに`:reaction`を足した上で独立したテーブルにはせず、Favouriteの付加属性として扱う。通常のLikeは`reaction = NULL`のままなので、既存のMastodon APIには影響を及ぼさない。次に、Undo側も同様に処理する。`EmojiReact`のActivityレコードは`activity_type: 'Like'` で保存し、取り消し処理を共通化している。

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
    # EmojiReact(Pleroma/Akkoma系)はLikeと同様に処理する
    handle_like_activity
```

また、リアクションのAPペイロードには`tag`にカスタム絵文字の画像URL(Emoji object)が同梱されている。これを投稿本文の絵文字と同じ`process_emoji_tags`で`CustomEmoji`として取り込み、画像は既存の絵文字画像キャッシュ(R2)に相乗りさせる。

リアクション経由で新規に知った絵文字はレコード作成時に先読み取得されるので、初回表示の時点で画像はすでに手元にある。バックフィルは一方通行(nil→絵文字のみ、上書きはしない)なので、Mastodonからのプレーンな再度のLikeが既存のリアクションを消す恐れはない。

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

実装後、折よく投稿した発言がプチバズしたこともあっていい感じに絵文字リアクションが集まった。弊実装系では以下のように見えている。この形式の利点はWebフロントエンドにささやかなソーシャル要素を足せるところだ。僕の友達にはフロントエンドページをじかにブックマークして読んでいる人もいる。彼らにとってLikeやRTの数はなんの意味もないが、面白い絵文字が表示されているのはエンタメ性があるかもしれない。

<div class="letter-embed" data-embed-url="https://letter.mystech.ink/@riq0h/21333328355214435/embed">
  <a href="https://letter.mystech.ink/@riq0h/21333328355214435">@riq0hの投稿を見る</a>
</div>
<script async src="https://letter.mystech.ink/embed.js"></script>

以上、一周年の節目にちょうどよい塩梅の意識変化を得たと思う。かつては絵文字リアクションへの見方がやや極端だったが、実装の自由を手にしていたおかげで適度な距離感を掴めた。三年前の僕へのアンサーとなるが、見たい時にだけ見られるなら問題のほとんどは解決する。重要なのは選択肢であり、選択肢を自分で握ることなのだ。
