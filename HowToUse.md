使い方
======

help/ヘルプ
-----------

ここへ誘導する

    @tipkotone help
    @tipkotone ヘルプ

Hello/Hi/こんにちは/はじめまして
--------------------------------

このTipBotを使うには先ずこれをする

    @tipkotone hello
    @tipkotone hi
    @tipkotone address
    @tipkotone こんにちは
    @tipkotone はじめまして
    @tipkotone アドレス

balance 残高
-------------

残高を確認する

    @tipkotone balance
    @tipkotone 残高

deposit/入金
------------

入金用アドレスを確認する

    @tipkotone deposit
    @tipkotone 入金

withdraw/出金
-------------

出金する。  
zアドレスへは出金できません。  
出金額には all が使えます。

    @tipkotone withdraw 10 address
    @tipkotone withdraw all address
    @tipkotone 出金 39 address
    @tipkotone 出金 all address

tip/投げ銭/投銭
---------------

投げ銭する。  
相手がまだ Hello/Hi/こんにちは/はじめまして をしていないと投げ銭できません。  
投銭額には all が使えます。

    @tipkotone tip 4.649 @to_twitter_account
    @tipkotone 投げ銭 all @to_twitter_account 全額投げます！！！

トラブルシューティング
======================

Q, 0.0001KOTO減るのはなんで？  
A, kotodではアカウント機能が無効化されているので、送金を行っています。なので、0.0001のトランザクション手数料がかかります。  
  
Q, tip/投げ銭/投げ銭 や withdraw/出金 すると残高が0になるのはなんで？ あと連続で投げ銭できないのはなんで？  
A, お釣りがどこかに飛んでいかないように、お釣りを自身に送金するという処理をしています。なので、お釣りが承認されるまで残高は0になり、連続での投げ銭ができません。  
  
Q, この額では出金できません・・・と言われたんだけどなんで？  
A, 0.00000054KOTO未満の送金ができないので、残高、額、お釣りのいずれかが0.00000054KOTO未満にならないように調整してください。  

