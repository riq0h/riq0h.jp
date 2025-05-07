---
title: "GitHubにStorageの使いすぎを怒られた"
date: 2021-04-05T9:43:48+09:00
draft: false
tags: ["tech", "diary"]
---

![](/img/16.png)

10MBいくかも怪しい静的サイトでいくらなんでもそれはおかしいと思ったが、結論から言うとこれは**artifact**と呼ばれる、GitHub Actionsを実行してホスティングサービス等にdeployされる過程で発生する生成物が原因だった。

このartifactは、初期設定では90日分もの量が溜め込まれる。GitHub Storageの無料枠は500MBまでなので1回転あたりはごく微量だとしても、僕みたいに些細な改稿でひっきりなしにCI/CDをぶん回しているとあっという間に上限に到達してしまう。

Actionsを使いはじめる前に必要十分な日数に設定しておけば当該の問題は起きなかったと考えられるが、今から設定を変更してもやはり即時には反映されないようだ。さしあたりGitHubに0.5ドルほどの小銭を投げつけてActionsを回す権限を取り戻した後、適当なスクリプトを実行させて件のartifactを削除しなければならない。これは検索するとわりあいすぐに[見つかった。](https://github.com/marketplace/actions/remove-artifacts)

```yml
name: Remove old artifacts

on:
  schedule:
    # Every day at 1am
    - cron: "0 1 * * *"

jobs:
  remove-old-artifacts:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Remove old artifacts
        uses: c-hive/gha-remove-artifacts@v1
        with:
          age: "1 weeks"
          # Optional inputs
          # skip-tags: true
          # skip-recent: 5
```

上記のコードをymlファイルの形で対象のリポジトリの`.github/workflows`直下に保存してpushすれば、指定されたcronのサイクルに基づいてartifactの削除が行われる。引用元は1ヶ月前までのファイルを維持する旨の記述だったが、僕はもっと短くても特に差し支えがないので1週間にした。実行後、GitHub Storageを確認すると目論見通り空き容量が増えていた。

![](/img/17.png)

これで思う存分に改稿しまくれる。
