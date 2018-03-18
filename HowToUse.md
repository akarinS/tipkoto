使い方
======

鍵アカウントで使いたい場合は、一度鍵を外して follow me/フォローミー でBotにフォローしてもらってから鍵をつけ直してください。

help/ヘルプ
-----------

ここへ誘導する。

    @tipkotone help
    @tipkotone ヘルプ

hello/hi/address/こんにちは/はじめまして/アドレス
--------------------------------

このTipBotを使うには先ずこれをする。

    @tipkotone hello
    @tipkotone hi
    @tipkotone address
    @tipkotone こんにちは
    @tipkotone はじめまして
    @tipkotone アドレス
    
follow me/フォローミー
----------------------

フォローしてもらう。

    @tipkotone follow me
    @tipkotone フォローミー

balance/残高
-------------

残高を確認する。

    @tipkotone balance
    @tipkotone 残高
    @tipkotone 残高を教えて

deposit/address/入金/アドレス
-----------------------------

入金用アドレスを確認する。

    @tipkotone deposit
    @tipkotone 入金
    @tipkotone address
    @tipkotone アドレス
    @tipkotone アドレスなんやったっけ

withdraw/出金
-------------

出金する。  
zアドレスへは出金できません。  
出金額には "all","全額" が使えます。  
金額とアドレスの順序はどちらでも大丈夫です。

    @tipkotone withdraw 10 address
    @tipkotone withdraw all address
    @tipkotone 出金 39 address
    @tipkotone 出金 全額 address

    @tipkotone withdraw address 10
    @tipkotone withdraw address all

tip/投げ銭/投銭
---------------

投げ銭する。  
相手がまだ hello/hi/address/こんにちは/はじめまして/アドレス をしていないと投げ銭できません。  
投げ銭額には "all","全額" が使えます。  
金額と宛先の順序はどちらでも大丈夫です。

    @tipkotone tip 4.649 @to_twitter_account
    @tipkotone 投げ銭 全額 @to_twitter_account 全額投げます！！！

    @tipkotone tip @to_twitter_account 1.14114
    @tipkotone 投銭 @to_twitter_account 39

トラブルシューティング
======================

Q, 0.0001KOTO減るのはなんで？  
A, kotodではアカウント機能が無効化されているので、送金を行っています。なので、0.0001のトランザクション手数料がかかります。  
  
Q, tip/投げ銭/投げ銭 や withdraw/出金 すると残高が0になるのはなんで？ あと連続で投げ銭できないのはなんで？  
A, お釣りがどこかに飛んでいかないように、お釣りを自身に送金するという処理をしています。なので、お釣りが承認されるまで残高は0になり、連続での投げ銭ができません。  
  
Q, この額では出金できません・・・と言われたんだけどなんで？  
A, 0.00000054KOTO未満の送金ができないので、残高、額、お釣りのいずれかが0.00000054KOTO未満にならないように調整してください。  

