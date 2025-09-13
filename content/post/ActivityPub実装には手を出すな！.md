---
title: "ActivityPub実装には手を出すな！"
date: 2025-09-13T9:50:37+09:00
draft: false
tags: ["tech"]
---

ここ一ヶ月弱の間、ろくに文章も書かずになにをしていたのかと言えばActivityPub実装を直していた（泣）ActivityPub実装とは、TwitterがXと化した経緯をきっかけに再び注目を浴びたMastodonやMisskeyなどのサーバソフトウェアを指している。この文言を読んだ覚えがない諸君はまず[この記事](https://riq0h.jp/2025/07/11/163822/)を読まなければならない。

先月に銀河の彼方へと飛び立っていった[僕の実装](https://github.com/riq0h/letter)は今のところ無事に航行を続けている。唯一の乗員にして船長にして技術者である僕が毎日せっせと船中を動き回って穴を塞いでいるからだ。穴はそこかしこに空いている。もともと見落としていた穴もあるし、外部との接触で空いた穴もある。

乗っている船が穴だらけだと気になって眠れない。ここ数週間は平均5時間も寝ていない気がする。コンピュータに触れない電車の中でも、同人誌即売会で売り子をしている最中も、隙あらばスマホを取り出してSSHクライアント越しにサーバログを見ていた。流れゆく大量の文字列の流星群から重要な情報を見つけるために目grepしすぎて目暮警部になった。目がしばしばしすぎて柴犬になった。ドッグフーディングしているだけに。その声は、我が友、李徴子ではないか？

**ActivityPub実装には手を出すな！** このことは最初にはっきりと申し上げておかなくてはならない。生半可なモチベーションでは出奔してまもなく死に至る。走って5秒後に死ぬメロス。一度走り出したからには走り続けなければならない。なぜなら人間関係と投稿データを纏わせた自分自身のアカウントがその上に乗っているからだ。もしや一生終わらないのではないかと感じるほどのコミットを日々余儀なくされる。本記事では特に印象に残った改修箇所を掻い摘んで挙げていく。

## パース職人

青色の文字を押せば任意のページに飛ぶと思っているそこの諸君！ あれをサードパーティクライアントのタイムライン上で実現するのは意外に難しいんだぞ。どうやっているか教えてやる。パース職人の朝は早い。どこの馬の骨とも知れないプレーンテキストがのこのこと歩いてきたら、まずはそいつの身ぐるみを剥いでやらないといけない。既存のHTMLタグを除去して改行をタグに置き換えてやる。

```ruby
def auto_link_urls(text)
    return ''.html_safe if text.blank?

    if text.include?('<') && text.include?('>')
      # HTML混在コンテンツの処理
      linked_text = apply_url_links_to_html(text)
      mention_linked_text = apply_mention_links_to_html(linked_text)
    else
      # プレーンテキストの処理
      escaped_text = escape_and_format_text(text)
      linked_text = apply_url_links(escaped_text)
      mention_linked_text = apply_mention_links(linked_text)
    end
    mention_linked_text.html_safe
  end

  def escape_and_format_text(text)
    plain_text = ActionView::Base.full_sanitizer.sanitize(text).strip
    ERB::Util.html_escape(plain_text).gsub("\n", '<br>')
  end
```

次に正規表現でURLの形式を識別して、まさしくそいつが紛れもないヤツならリンクタグに変換する。しかし表示する際には見てくれがイケていない`https://`の部分を削り取る。どうせリンクと分かっている以上、ごく限られたタイムラインの余白を定型句で埋めるのは野暮だからだ。

```ruby
def apply_url_links(text)
  link_pattern = /(https?:\/\/[^\s]+)/
  text.gsub(link_pattern) do
    url = ::Regexp.last_match(1)
    display_text = mask_protocol(url)
    "<a href=\"#{url}\" target=\"_blank\" rel=\"noopener noreferrer\" " \
      "class=\"text-gray-500 hover:text-gray-700 transition-colors\">#{display_text}</a>"
  end
end
```

一方、相手が送ってきた省略済みのURLを完全な形に直してやらなければならない。こちら側と同じく相手もプロトコル部分を削っていたり手を加えていたりする。丁寧なメイクアップがURLのデビューを華々しく飾り立てる。舞台〈タイムライン〉は詰めかけた観客〈フォロワー〉で爆発寸前だ。

```ruby
def fix_split_url_links(html_text)
  html_text.gsub(/<a\s+([^>]*href=['"]([^'"]+)['"][^>]*)>(.+?)<\/a>/m) do |match|
    attributes = ::Regexp.last_match(1)
    href_url = ::Regexp.last_match(2)
    link_content = ::Regexp.last_match(3)

    if link_content.include?('class="invisible"') || link_content.include?('class="ellipsis"')
      cleaned_content = link_content.gsub(/<span class="invisible">[^<]*<\/span>/, '')
                                    .gsub(/<span class="ellipsis">([^<]*)<\/span>/, '\1')
      display_text = cleaned_content.empty? ? mask_protocol(href_url) : "#{cleaned_content}..."
      "<a #{attributes}>#{display_text}</a>"
    else
      match
    end
  end
end
```

最後に、HTMLが混在した投稿では既存のタグ内に含まれたURLを誤って処理しないように、タグの外部のみリンク化する処理を施す。プロのメイキャッパーはURLが舞台に颯爽と歩いていく最中でも並走しながらチークを塗りたくる。こうして、URLが青色の長いドレスを纏ってタイムラインにさっそうと姿を表す。ただし、こちらのフロントエンド上では灰色に見える。皆さんが脊髄の躍動に任せて指先をハイパーリンクにへばりつかせるまでに、おおよそこんな具合の処理が行われているのだ。

```ruby
def apply_url_links_to_html(html_text)
  # 既存のHTMLタグ位置を記録
  tags = []
  html_text.scan(/<[^>]+>/) { |match| tags << { content: match, start: $LAST_MATCH_INFO.begin(0), end: $LAST_MATCH_INFO.end(0) } }

  url_pattern = /(https?:\/\/[^\s<>"']+)/
  result = html_text.dup
  offset = 0

  html_text.scan(url_pattern) do |url|
    url_start = $LAST_MATCH_INFO.begin(0)
    url_end = $LAST_MATCH_INFO.end(0)

    # URLが既存のHTMLタグ内にないかチェック
    inside_tag = tags.any? do |tag|
      url_start >= tag[:start] && url_end <= tag[:end]
    end

    unless inside_tag
      # リンク化処理
      display_text = mask_protocol(url[0])
      linked_url = "<a href=\"#{url[0]}\" target=\"_blank\" rel=\"noopener noreferrer\" " \
                   "class=\"text-gray-500 hover:text-gray-700 transition-colors\">#{display_text}</a>"

      actual_start = url_start + offset
      actual_end = url_end + offset
      result[actual_start...actual_end] = linked_url
      offset += linked_url.length - url[0].length
    end
  end

  result
end
```

**おい、話はまだ終わっていないぞ！** ここからもっと面倒な話がある。メンションっていうやつがある。ActivityPubでは一般に`@username@domain.com`の形式で個々のアカウントを識別していて、リンク化されたメンションをクリックするとそいつのプロフィールページに飛べる。当然、これは各実装系が田畑から収穫した新鮮なハイパーリンクを丁寧に精米してやっている。米がいくら高くなろうともこの処理は永遠に変わらない。

ちなみにメンション自体はActivityPubの規約に則っていればリンク化とは無関係に機能する。というか本文にユーザ名を含ませる必要すらない。メンションの判定は各投稿のJSONに格納されているフィールド列によって行われるからだ。事実、実装系によっては投稿本文にユーザ名を含まない仕様のものもある。僕の実装には一応ちゃんと精米させることにした。カリフォルニア産が意外にうまい。

```ruby
def apply_mention_links(text)
  mention_pattern = /@([a-zA-Z0-9_.-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/
  text.gsub(mention_pattern) do
    username = ::Regexp.last_match(1)
    domain = ::Regexp.last_match(2)
    mention_url = build_mention_url(username, domain)
    %(<a href="#{mention_url}" class="h-card u-url mention"><span class="p-nickname">@#{username}</span></a>)
  end
end

def build_mention_url(username, domain)
  safe_username = username.gsub(/[^a-zA-Z0-9_.-]/, '')
  safe_domain = domain.gsub(/[^a-zA-Z0-9.-]/, '')

  local_domain = Rails.application.config.activitypub.domain

  if domain == local_domain
    # ローカルユーザの場合
    "#{Rails.application.config.activitypub.base_url}/users/#{ERB::Util.url_encode(safe_username)}"
  else
    # リモートユーザの場合、Actorレコードから正しいURLを取得
    actor = Actor.find_by(username: safe_username, domain: safe_domain)
    if actor&.ap_id.present?
      actor_url = actor.ap_id
      actor_url.start_with?('http') ? actor_url : "https://#{actor_url}"
    else
      "https://#{ERB::Util.url_encode(safe_domain)}/users/#{ERB::Util.url_encode(safe_username)}"
    end
  end
end
```

最終的に上記の仕様に落ち着くまでにはマイナーな実装系を使っているフォロー各位とずいぶん対話を重ねた。MastodonやMisskeyといったメジャーな実装系は様々なパターンに対応しているが、IceshrimpやMitraやGoToSocialといった銀河の辺境を漂う船には辺境ならではの鉄の掟が存在する。一、次の公転周期が来るまでに太陽を破壊すること。二、太陽は1000個くらいある。

![](/img/399.png)

![](/img/400.png)

最終的に相互通信を認められて一緒に太陽狩りをする仲にまでなった時の感動はひとしおだった。吹きつけるプロミネンスの熱波が今も脳裏に輝く……。このようにActivityPubにはあらゆる実装が存在しており、MastodonやMisskeyで表示できるなら大丈夫と思い込んでいるうちは広大な連合宇宙〈フェディバース〉を旅して回るのに事欠くのである。

## WebPushの実装

僕はもっぱらパソカタの人間でスマホはあまり触らない。したがって、誰かが僕に送ってきたいいねやメンションを即座に把握するには、コンピュータのブラウザ上のクライアントで通知を受け取らないといけない。そこで、WebPushを実装した。これはネイティブアプリの通知と違ってまあまあ面倒くさい。

まずはブラウザから登録されたプッシュ通知の購読情報を保護するために以下の属性を用意する。  
・endpoint: ブラウザの通知サービス（FCM、Mozilla等）のエンドポイントURL  
・p256dh_key: ECDH公開鍵（暗号化用）  
・auth_key: 認証用の秘密鍵  
・access_token_id: OAuth認証トークンとの関連付け

```ruby
class WebPushSubscription < ApplicationRecord
  belongs_to :actor
  belongs_to :access_token, class_name: 'Doorkeeper::AccessToken', foreign_key: 'access_token_id', optional: true

  validates :endpoint, presence: true, uniqueness: true
  validates :p256dh_key, presence: true
  validates :auth_key, presence: true
```

続いてクライアントとやり取りする通知設定の項目を作る。人によってはメンションはすぐに受け取りたくてもいいねはそれほどでもないかもしれない。同様に、フォロワー外からのリアクションには関心がない人もいる。なんでもいちいち知らせてくる世の中だからこそ、い
つ知るべきかは自分でコントロールできるべきだ。

```ruby
def default_alerts
  {
    'follow' => true,
    'follow_request' => true,
    'favourite' => true,
    'reblog' => true,
    'mention' => true,
    'poll' => true,
    'status' => false,
    'update' => false,
    'quote' => true,
    'admin.sign_up' => false,
    'admin.report' => false
  }
end

def should_receive_notification_from?(from_actor, target_actor, notification_type)
  return false unless should_send_alert?(notification_type)

  case policy
  when 'none'
    false
  when 'followed'
    Follow.exists?(actor: target_actor, target_actor: from_actor, accepted: true)
  when 'follower'
    Follow.exists?(actor: from_actor, target_actor: target_actor, accepted: true)
  else
    true
  end
end
```

VAPID（Voluntary Application Server Identification）を認証する仕組みも必要だ。WebPushはFCMなどの通知サーバを介して行われているのだが、VAPIDにはそれらのサービスがこちらの実装を識別して不正な利用を防ぐ狙いがある。

ところで、下記のコードを見ると`WebPush.generate_request_details`ではなくOpenSSLとJWTライブラリを直接呼び出している。なぜか前者の方だと鍵の認証がどうしてもうまくいかなかった。まさかそんなわけないと半日費やした犠牲がアンバランスなコードの隙間から垣間見えるかのようだ。

```ruby
def build_vapid_headers(endpoint)
  audience = URI.parse(endpoint).then { |uri| "#{uri.scheme}://#{uri.host}" }

  private_key = OpenSSL::PKey::EC.new(vapid_private_key)
  public_key_uncompressed = private_key.public_key.to_bn.to_s(2)
  public_key_base64 = Base64.urlsafe_encode64(public_key_uncompressed).tr('=', '')

  token = JWT.encode(
    {
      aud: audience,
      exp: 24.hours.from_now.to_i,
      sub: "mailto:#{instance_contact_email}"
    },
    private_key,
    'ES256'
  )

  {
    'Authorization' => "vapid t=#{token},k=#{public_key_base64}",
    'Crypto-Key' => "p256ecdsa=#{public_key_base64}"
  }
end
```

とはいえ、ともかく通知内容はきっちり暗号化されてユーザのブラウザでのみ複合できる形で配信される。初めて自分の実装のデスクトップ通知が画面上に躍り出た時はなにげに感じ入ったものだ。本番稼働してから今まではいちいち通知欄を開いて確認していたが、これからは通知をしっかり把握した上で無視することができる。

```ruby
def perform_webpush_send(subscription, payload)
  encrypted_payload = WebPush::Encryption.encrypt(payload.to_json, subscription.p256dh_key, subscription.auth_key)

  uri = URI.parse(subscription.endpoint)
  http = Net::HTTP.new(uri.host, uri.port)

  request = Net::HTTP::Post.new(uri.request_uri)
  request['Content-Type'] = 'application/octet-stream'
  request['Content-Encoding'] = 'aes128gcm'
  request['TTL'] = '2592000'

  vapid_headers = build_vapid_headers(subscription.endpoint)
  vapid_headers.each { |key, value| request[key] = value }

  request.body = encrypted_payload
  response = http.request(request)
```

## 並行宇宙間特別通信規約

BlueskyはActivityPubとは異なる並行宇宙だが、近年発見されたワームホール〈ブリッジサービス〉を通じて相互通信が可能となった。こちら側からは彼らは`bsky.brid.gy`のドメインを持つユーザとして認識されている。しかし完全にActivityPubに準拠した通信をしてくれるわけではないため一部特別な処理を施している。

たとえば僕の実装には大半の実装系と同じくURLからプレビューリンク（OGP）を自動生成する機能が備わっている。もちろん内部的にはURLであってもメンションリンクなどは対象外とする仕組みにしているが、特殊な形式のURLを持つBlueskyユーザ宛のメンションでは意図せずプレビューリンクが生成されてしまう。そこで下記の要領でドメインごと除外している。

```ruby
def valid_preview_url?(url)
  begin
    uri = URI.parse(url)
    return false unless %w[http https].include?(uri.scheme)
    return false if uri.host.blank?

    # Blueskyドメインは除外
    bluesky_domains = ['bsky.app', 'bsky.social', 'bsky.brid.gy']
    return false if bluesky_domains.any? { |domain| uri.host&.include?(domain) }

    # その他のバリデーション...
    true
  rescue URI::InvalidURIError
    false
  end
end
```

また、こちら側のクライアントからBlueskyユーザの元URLを参照すると、想定に反して生JSONが返ってきてしまう問題もあった。これは例によってブリッジサービスが提供するURLの特殊な形式に起因している。この場合では、受け取ったURLを分解してブラウザ上での表示に適した`https://bsky.app/profile/#{bluesky_handle}/post/#{post_id}`の形に再構成する方針を採った。

```ruby
def public_url
  if object.ap_id.present? && !object.local?
    # bsky.brid.gyの場合はBlueskyの実際のURLに変換
    return convert_bsky_bridge_url(object.ap_id) if object.ap_id.include?('bsky.brid.gy')

    return object.ap_id
  end

  # ローカル投稿の場合の処理...
end

private

def convert_bsky_bridge_url(bridge_url)
  # bsky.brid.gyのブリッジURLを実際のBlueskyURLに変換
  post_id = extract_bluesky_post_id(bridge_url)
  return bridge_url unless post_id

  # ActorからBlueskyハンドルを取得
  bluesky_handle = extract_bluesky_handle_from_actor
  return bridge_url unless bluesky_handle

  # BlueskyのURLを構築
  "https://bsky.app/profile/#{bluesky_handle}/post/#{post_id}"
rescue StandardError => e
  Rails.logger.warn "Failed to convert bsky.brid.gy URL #{bridge_url}: #{e.message}"
  bridge_url
end

def extract_bluesky_post_id(bridge_url)
  # URLの最後の部分（post ID）を抽出
  match = bridge_url.match(/\/app\.bsky\.feed\.post\/([^\/\?#]+)/)
  match&.[](1)
end
```

状況に応じてユーザ名も実は変換している。ActivityPubでは`@username@domain.com`の形式が一般的だが、BlueskyではDID（分散識別子）と呼ばれる`did:plc:xxxxxx`の形式でユーザを識別しており、これをActivityPub側でそのまま受け取ると共通の処理をする上で困難が生じる。そのため、なんらかの理由で分散識別子型のユーザ名が流れ込んできた際にも対応できる処理を施している。

```ruby
def extract_bluesky_handle_from_actor
  actor = object.actor
  return nil unless actor

  # まずusernameを試す
  username = actor.username
  if username&.exclude?('did:plc:')
    return username
  end

  # preferredUsernameがあれば使用
  return actor.preferred_username if actor.respond_to?(:preferred_username) && actor.preferred_username.present?

  nil
end
```

並行宇宙の先はActitvityPub実装にとって未知の世界だ。ワームホールを超えての航行は残念ながら叶わない。だが、通信越しに体験を共有する楽しみは得られる。当初はフォローどころか検索にも引っ掛けられず苦労したが、今ではMastodonインスタンスを運用していた頃と変わらずBlueskyユーザたちと交流を深めている。

## N+1問題の対処

N+1問題はプログラマがプログラマとして生まれてから死ぬまでに対処し続けなければならない習慣病の一つだ。なぜ人はデータベースを余計に呼び出してしまうのか。なぜ分かっていても無駄なクエリの発行を止められないのか。きっとアマゾンの奥地でもN+1問題は発生しているに違いない。開発中にも気をつけていたはずなのにいつの間にか復活していたりもする。

基本的な対処方法としては、まず事前読み込み（Eager Loading）を行う。`.includes()`を使用して関連データを一括で取得しておくと後続のアクセスでクエリを発生させずに済む。次に`.joins()`を用いて必要なデータのみを選択的に結合する。同時に`WHERE`条件を加えて不要なデータを取得しない。逆に、大量のデータが見込まれる場合には`.find_batches()`でバッチ処理を行うと負荷の軽減に役立つ。どれも典型的なアプローチだが、コーディングが進行していくにつれてなぜか忘れてしまう。

一連の施策を実装していくと以下の形になる。下手をすると100クエリくらい発生していたものが3クエリとかで整う。これまでタイムラインや通知欄の更新に5秒くらい待たされていたのが数十ミリ秒で終わる。基礎的で地味だが効果は絶大だ。宇宙空間で燃費が悪いのは命取りである。最寄りの反物質給油所までは100光年くらい航行しないと辿り着けない。

```ruby
def base_timeline_query
  query = ActivityPubObject.joins(:actor)
                           .includes(:actor, :media_attachments, :poll)
                           .where(object_type: %w[Note Question])
                           .where(is_pinned_only: false)
                           .order('objects.id DESC')
  query
end

def fetch_reblogs(followed_ids)
  reblogs = Reblog.joins(:actor, :object)
                  .where(actor_id: followed_ids)
                  .where(objects: { visibility: %w[public unlisted] })
                  .includes(object: %i[actor media_attachments poll], actor: {})
                  .order('reblogs.created_at DESC')
  apply_reblog_pagination_filters(reblogs).limit(limit * 10)
end

def load_user_post_objects
  ActivityPubObject
    .joins(:actor)
    .where(actor: @actor)
    .where(visibility: %w[public unlisted])
    .where(object_type: 'Note')
    .where(local: true)
    .includes(:actor)
end

def load_user_reblog_objects
  Reblog.joins(:actor, :object)
        .where(actor: @actor)
        .where(objects: { visibility: %w[public unlisted] })
        .includes(:actor, object: %i[actor media_attachments])
end

def load_pinned_posts
  @actor.pinned_statuses
        .includes(object: %i[actor media_attachments mentions tags])
        .ordered
end
```

## おわりに

人様の実装系を使っていた頃はなにもかもが当然にあるものと思っていた。メンションリンクも、プレビューリンクも、動画の一コマ目を切り抜いてサムネイルにする仕組みも、自分で実装しなければ本当は手に入らない。URLのリンク化さえ勝手にはやってくれない。これまで全部クライアント側がよしなにやってくれているのだろうと思い込んでいた処理の数々は、実際にはどれも実装系の仕事だったのだ。ごん、お前だったのか。いつもURLを青色に塗ってくれたのは……。

幸いにも苦労の甲斐あり、僕の実装は上も下も分からない宇宙空間のなかで心なしかまっすぐ飛びはじめているように見える。一日中修理に追われ続け、ふと一息をついて窓の外を眺めた時、銀河に横たわる暗闇ときらめく星々の景色に自由を見出す。その間にも船はひっきりなしに通信を傍受して人々のつぶやきを垂れ流している。自ら飛び続けているかぎりはすべてが美しい。
