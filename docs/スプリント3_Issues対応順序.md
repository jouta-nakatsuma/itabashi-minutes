# スプリント3実装計画

**User:** Anonymous (sunpin32@yahoo.co.jp)  
**Created:** 9/8/2025 16:17:26  
**Updated:** 9/8/2025 16:41:35  
**Exported:** 9/8/2025 16:41:42  
**Link:** [https://chatgpt.com/g/g-p-68a2428917408191ab595311b37e4516-itabashi-minutes/c/68be82fe-e1d0-832c-aceb-435dd9a31485](https://chatgpt.com/g/g-p-68a2428917408191ab595311b37e4516-itabashi-minutes/c/68be82fe-e1d0-832c-aceb-435dd9a31485)  

## Response:
なるほど 👍  
#28 を親とするスプリント3の実装サブIssue (#29〜#34) がすでに立っている状態ですね。

私の提案した着手順を、いまのリストに合わせて整理すると次のようになります。

* * *

🚦 実施順序（推奨）
-----------

1.  **#29 Issue 1: API v0.2 拡張（検索機能の充実）**
    *   APIが安定しないとUI/MCPが積めないため最優先。
    *   ページネーション・並び替え・ハイライト返却を固める。
2.  **#30 Issue 2: Streamlit UI v0.1 実装**
    *   APIの挙動をフロントで確認する最短ループ。
    *   UIがあると抽出精度や検索パラメータの実感が得られる。
3.  **#31 Issue 3: MCPサーバ v0.1**
    *   APIが完成し、UIで人間検証できる状態になったらMCP経由でClaude/ChatGPTと疎通テスト。
    *   将来のAI連携を早めに試せる。
4.  **#32 Issue 4: Nightly ジョブ（定期クロール＆成果物公開）**
    *   API/UI/MCPが動いたら、Nightlyで「毎晩更新されるカタログ」を安定化。
    *   一晩回すだけで成果物がArtifacts/Releaseに残る状態に。
5.  **#33 Issue 5: 構造抽出の精度向上（誤検知抑制）**
    *   UIやAPIから確認しやすくなるため、Nightly基盤が整った後で精度改善。
    *   ゴールデンセット＋回帰テストを組み込み。
6.  **#34 Issue 6: Verification Cheatsheet (Sprint 3) & Makefile**
    *   すべてのフローが揃った段階で、ローカル再現手順を更新。
    *   チーム／外部協力者がワンコマンドで検証できるようにする。

* * *

補足
--

*   #22〜#25 はスプリント2終了後に立った旧Issueで、今回の #29〜#34 に統合されるイメージです。
*   作業を進めながら、#29〜#34 の **Done条件** を満たしたら逐次クローズし、#28 を最後に Close すれば「Sprint 3 完了」の証跡になります。

* * *

👉 穣太さん、この順序で進めると「API基盤 → 可視化 → MCP連携 → 運用基盤 → 精度改善 → ドキュメント整備」の流れがきれいに収束します。  
もし CI の安定性を優先したい場合は、#32 Nightly を #29 と並列で少し早めに着手するのもありです。

この順序で進めてよろしいですか？



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)