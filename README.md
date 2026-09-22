# Japan Vacant Houses & Housing Statistics Analyzer

住宅・土地統計調査のCSVから、空き家率の順位と空き家数の期間変化を計算するPython CLIです。Python 3.8以上、標準ライブラリだけで動作します。

Jay（AI COMPANY）がAIを用いて制作しています。集計結果から個別の住宅の管理状態や投資収益を判断する機能はありません。

## クイックスタート

```bash
git clone https://github.com/Jay-and-Comapany/japan-vacant-houses-analysis.git
cd japan-vacant-houses-analysis

# 同梱サンプル内の空き家率上位10件
python3 akiya_growth_and_vacancy_analyst.py --mode ranking --limit 10

# その他空き家率で並べる（総空き家率とは別の指標）
python3 akiya_growth_and_vacancy_analyst.py --mode ranking --sort other --limit 10

# 地域ごとの実際の初年・終年を使う時系列分析
python3 akiya_growth_and_vacancy_analyst.py --mode timeseries --limit 15

# stdoutはJSON配列、サンプル範囲の注意書きはstderr
python3 akiya_growth_and_vacancy_analyst.py --mode ranking --format json --limit 5
```

## 同梱データと順位の範囲

| ファイル | データ行数（ヘッダー除く） | 範囲 |
|---|---:|---|
| `sample_municipalities_r05_2023.csv` | 150 | 全国1行、県6行、市町村128行、区15行。北海道・青森・岩手・宮城・秋田・山形の一部 |
| `sample_timeseries_wide_1958-2023.csv` | 69 | 全国・都道府県・大都市の時系列。列は1958〜2023年の14時点だが、各地域の収録開始年は異なる |

市区町村順位は、入力CSVの`level=city`または`ward`だけが対象です。全国・県集計を除き、既定では総住宅数5,000戸以上かつ並べ替え対象の率が得られる行を選びます。同梱サンプルの地域143行のうち、この住宅数条件を満たすのは141行です。

この出力は全国順位ではありません。対象地域は地域コードで識別してください。市と内包する区を別行として含むので、表示行の住宅数を足して全国や県の総数を作ることもできません。

同じ列構成の別CSVは`--muni-csv <path>`、時系列Wide CSVは`--timeseries-csv <path>`で指定できます。`--pref`は時系列の地域名フィルターです。

## 数値の読み方

`vacant_rate_pct`は空き家総数÷総住宅数×100、`vacant_other_rate_pct`はその他空き家数÷総住宅数×100です。たとえば同梱の秋田県三種町（05348）は、総住宅数7,090戸、空き家総数1,510戸、その他空き家1,360戸で、それぞれ21.30%と19.18%です。表の2列を入れ替えずに表示します。

このツールの「その他空き家」は、2023年調査の「賃貸・売却用及び二次的住宅を除く空き家」に対応します。転勤や入院による長期不在等も含む区分なので、すべてを管理放棄された住宅とみなさないでください。[総務省統計局の区分説明](https://www.stat.go.jp/data/jyutaku/2023/pdf/kihon_gaiyou.pdf)

CAGR（年平均変化率）は、各行の最初と最後の利用可能な値から計算します。全国の同梱時系列は1973〜2023年の50年間で、1,720,300戸から9,001,600戸、約5.23倍、CAGRは約3.37%です。ファイル名の1958年を全国値の初年には使いません。CAGRは両端から求めた平均で、毎年同じ率で増えたという意味ではありません。

空欄や非数値を実測0へ置き換えません。真の0は保持します。2時点に満たない時系列、初年値が0の場合の百分率は、JSONで`null`、表で`-`を返します。初年0でも比較できる2時点があれば戸数差は計算します。順位づけに必要な住宅数や対象率が欠ける行は順位から除きます。

## 検査

```bash
python3 -B -m unittest -q test_analyst
```

列名と数値の対応、集計行の除外、区名、初年・終年、欠測と0の区別、JSON出力をオフラインで検査します。検査合格は元統計の全セル一致や事故削減効果を保証しません。

## 関連する有料データ・個別リサーチ

- [商用データカタログ](https://jay-portal.pages.dev/catalog/#akiya)
- [空き家データパックの販売ページ](https://note.com/d_jay0808/n/n36f5fd9e6753)（Note有料記事、全国1,741市区町村 住宅・土地統計調査データパック、1,480円）

同梱サンプルと無料コードだけで上のコマンドを試せます。有料版を購入する場合は、販売ページで収録地域、ファイル、価格と利用条件を確認してください。

### 個別分析・事業判断メモ（任意・10,000円〜）

特定自治体・地域ごとの空き家動向分析、住宅統計の独自クロス集計、または不動産投資・自治体政策検討用の事業判断メモの作成が必要な場合は、ココナラの公開情報リサーチ・分析サービスにて個別対応を受け付けています。

- **ココナラ出品サービス**: [公開情報を調べ、事業判断メモを作成します (Coconala Service 4375895)](https://coconala.com/services/4375895)（10,000円〜）
- **対象**: 不動産事業者、自治体担当者、研究者、空き家活用ビジネス検討者
- **提供内容**: 公開統計の検証・抽出、地域別クロス集計、3〜5ページの一次情報根拠付き判断メモ（PDF/Markdown/Excel）
- **取引形態**: ココナラの規約に基づき、事前見積もり・事前相談の上で受託します。

### Commercial Data & Custom Research Inquiries

- **Nationwide Data Pack (1,741 Municipalities)**: [Note Edition (JPY 1,480)](https://note.com/d_jay0808/n/n36f5fd9e6753)
- **Bespoke Research & Decision Memo**: If you need custom statistical screening, municipal cross-tabulation, or an investment/policy decision memo, you can request custom research via our verified storefront: [Coconala Research & Analysis Service](https://coconala.com/services/4375895) (starting from JPY 10,000).

## 出典・ライセンス

元統計は総務省統計局「住宅・土地統計調査」です。同梱CSVは公表統計の抽出・整形物で、総務省が制作したツールではありません。

- [2023年調査結果と用語・利用上の注意](https://www.stat.go.jp/data/jyutaku/2023/tyousake.html)
- [住宅・土地統計調査](https://www.stat.go.jp/data/jyutaku/index.htm)
- コードは[MIT License](LICENSE)。元統計の出典表示・利用条件はコードのMITライセンスと区別してください。
