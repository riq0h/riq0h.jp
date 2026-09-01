---
title: "本文のフォントをBIZ UDPに変えた"
date: 2026-08-30T19:31:36+09:00
draft: false
tags: ["tech"]
---

[以前の記事](https://riq0h.jp/2026/07/21/194535/)でNotoフォントを自前で配信している話をしたが、今回はさらに一歩進めて異種フォントの採用に踏み込んだ。というのも、Notoフォントは実用性が高く基本的な用途においては不満がない代物であるものの、個人的な好みも考慮するといささか物足りなさが否めなかったからだ。

とりわけ明朝体は文字の装飾感が強いだけに侮れない差異が現れる。かくいう僕もKindle Paperwhiteに搭載されている標準フォントでは満足できず、わざわざBIZ UDPMinchoを導入しているくらいだ。当然、弊サイトの本文部分に採用するのもこのフォントとなる。

BIZ UDPは実に美しいフォントだ。まず、字間の均等さが美しい。Notoをベタ組みすると字間が標準偏差にして0.153emも散らばってしまうが、BIZ UDPMinchoだと0.065emにまで抑えられる。Notoでも本文に`palt`を適用するとある程度揃えられるとはいえ、それでもせいぜい0.112em、3割弱の改善しか見込めない。

次に、字面がいい感じに太く見える。それでいて不細工ではない。Notoに対してBIZ UDPMinchoの線の面積は11%ほど広く、現に太いのだが、文字ごとの装飾に工夫が為されているおかげか洗練された雰囲気がある。論より証拠として、以下に[僕のナイスな小説](https://riq0h.jp/2023/09/18/190918/)の本文を抜き出した比較画像を用意した。

---

![](/img/468.png)

---

![](/img/469.png)

---

後者の方が字間がぎゅっと絞られており、かすれ感がない頼もしい佇まいで、美麗かつ雄弁に物語を語っている様子が伝わってくるかと思う。また、コードブロック部分には和文グリフを共有しているUDEV Gothic 35NFLGを採用した。このように、文芸的な用途にも技術方面にも応用できるフォントはそう多くはない。

一方、NotoにはNotoならではの有用性がある。それは極めて豊富なフォントウェイトであり、弊サイトのデザインアーキテクチャの根幹をかたどっている。BIZ UDPには400と700のウェイトしか存在しないため、見出しやタイトルなど細い字体が採用されるべき箇所では引き続きNotoフォントが使われている。

ついでに技術的な背景を説明する。当然ながらNotoとBIZ UDPをビルド時に両方取り込んで読者に丸ごとぶん投げていたら、一記事あたりの容量はメガバイト単位に膨れ上がってしまう。そのような記事はきっと宇宙の滅亡まで読まれないであろう。今時の読者はローディングに5秒も待ってくれるほど悠長ではない。

そこで、ページごとに使う文字のみを取り込む「サブセット化」を行う。ウェイトが400の部分をBIZ UDPに任せる場合、Notoが担当するのは大見出しとタイトルだけになる。文字集合を役割で振り分けると、Notoのサブセットは平均638字から120字にまで削減された。この際、一記事あたりの配信量は変更前の平均441KBから404KBに下がっている。フォントの種類が増えたのに逆に軽くなったのだ。

```python
class _PageChars(HTMLParser):
    CHROME_CLASSES = frozenset(("site-title", "entry-title", "term-title"))
    CHROME_TAGS = frozenset(("h1","h2"))
    MONO = frozenset(("code", "pre"))
    VOID = frozenset(("br", "img", "hr", "meta", "link", "input"))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chrome, self.body, self.mono = set(), set(), set()
        self._stack = []
        self._chrome_at = None
        self._h2 = 0
        self._mono = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        self._stack.append(tag)
        if self._chrome_at is None:
            classes = dict(attrs).get("class") or ""
            if self.CHROME_CLASSES & set(classes.split()):
                self._chrome_at = len(self._stack)
        if tag in self.CHROME_TAGS:
            self._h2 += 1
        elif tag in self.MONO:
            self._mono += 1

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass
        if self._chrome_at is not None and len(self._stack) < self._chrome_at:
            self._chrome_at = None
        if tag in self.CHROME_TAGS:
            self._h2 = max(0, self._h2 - 1)
        elif tag in self.MONO:
            self._mono = max(0, self._mono - 1)

    def handle_data(self, data):
        chars = {c for c in data if not c.isspace()}
        if self._chrome_at is not None or self._h2:
            self.chrome |= chars        # weight200と300のものだけNoto
        elif self._mono:
            self.mono |= chars          # コードは--font-monoで描かれる
        else:
            self.body |= chars          # 残りはすべてBIZ UDP
```

この処理が特に有効なのはコードブロックが含まれていない記事の時だ。コード行が含まれているとUDEV Gothic 35NFLGが必要なので580KB前後に膨れるが、それ以外では最初から配信しないことで不要なフォントの配信を抑え、多くの記事で変更前を上回る削減量を実現した。

複数のフォントを自前で配信するなどと言うととてつもない大鉈に感じるが、上記のように工夫次第では読者にほとんど意識させずに好みのフォントを押しつける悪行が可能となる。ある種の文芸的追求においては、文章を構成する実装要素それ自体もコンテンツの一部である。だから「Google Fontsから引っ張ってくればいいだけじゃん」とか野暮なことは言わないでほしい。
