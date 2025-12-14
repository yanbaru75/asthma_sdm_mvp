from datetime import datetime
from statistics import mean

from flask import (
    Flask,
    render_template,
    request,
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLite 設定
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sdm.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------
# モデル定義
# -------------------

class TreatmentOption(db.Model):
    __tablename__ = "treatment_options"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brief_description = db.Column(db.Text, nullable=False)

    details = db.relationship("TreatmentDetail", backref="treatment", lazy=True)
    questions = db.relationship("UnderstandingQuestion", backref="treatment", lazy=True)


class Attribute(db.Model):
    __tablename__ = "attributes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    order_index = db.Column(db.Integer, default=0)

    details = db.relationship("TreatmentDetail", backref="attribute", lazy=True)


class TreatmentDetail(db.Model):
    __tablename__ = "treatment_details"
    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatment_options.id"), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey("attributes.id"), nullable=False)
    pros_text = db.Column(db.Text, nullable=True)
    cons_text = db.Column(db.Text, nullable=True)


class UnderstandingQuestion(db.Model):
    __tablename__ = "understanding_questions"
    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatment_options.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, default=0)

    choices = db.relationship("UnderstandingChoice", backref="question", lazy=True)


class UnderstandingChoice(db.Model):
    __tablename__ = "understanding_choices"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("understanding_questions.id"), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)


# -------------------
# DB 初期化（Flask 3.x 対応）
# -------------------

def init_db():
    """テーブル作成と初期データ投入"""
    db.create_all()

    # すでにデータがあれば何もしない
    if TreatmentOption.query.count() > 0:
        return

    # ---- 治療オプション ----
    t1 = TreatmentOption(
        name="全身ステロイド（屯用）",
        brief_description="発作時など症状が強いときに短期間だけ全身ステロイドを使用する治療です。",
    )
    t2 = TreatmentOption(
        name="全身ステロイド（連用）",
        brief_description="症状を抑えるために、少量の全身ステロイドを継続して服用する治療です。",
    )
    t3 = TreatmentOption(
        name="生物学的製剤",
        brief_description="喘息の原因となる炎症物質をピンポイントで抑える注射薬による治療です。",
    )
    db.session.add_all([t1, t2, t3])
    db.session.flush()

    # ---- 比較項目 ----
    eff = Attribute(name="効果", order_index=1)
    side = Attribute(name="副作用", order_index=2)
    cost = Attribute(name="費用", order_index=3)
    life = Attribute(name="日常生活への影響", order_index=4)
    freq = Attribute(name="通院・投与頻度", order_index=5)
    db.session.add_all([eff, side, cost, life, freq])
    db.session.flush()

    # ---- pros/cons ----
    details = [
        # t1: 屯用
        TreatmentDetail(
            treatment_id=t1.id,
            attribute_id=eff.id,
            pros_text="発作時の症状を速やかに抑えられることが多い。",
            cons_text="効果が一時的で、根本的なコントロールには不十分な場合がある。",
        ),
        TreatmentDetail(
            treatment_id=t1.id,
            attribute_id=side.id,
            pros_text="短期間であれば副作用のリスクは比較的低い。",
            cons_text="繰り返し使用すると、骨粗鬆症や糖尿病などのリスクが高まる。",
        ),
        TreatmentDetail(
            treatment_id=t1.id,
            attribute_id=cost.id,
            pros_text="薬剤費は比較的安価。",
            cons_text="発作が頻回だと、トータルの負担が増える可能性がある。",
        ),
        TreatmentDetail(
            treatment_id=t1.id,
            attribute_id=life.id,
            pros_text="普段は薬を飲まなくてよい場合もある。",
            cons_text="発作の予兆に敏感でいる必要があり、不安につながることがある。",
        ),
        TreatmentDetail(
            treatment_id=t1.id,
            attribute_id=freq.id,
            pros_text="必要時のみの内服で、通院頻度は比較的少ない。",
            cons_text="緊急時に受診や処方が必要になることがある。",
        ),

        # t2: 連用
        TreatmentDetail(
            treatment_id=t2.id,
            attribute_id=eff.id,
            pros_text="症状を安定させ、発作の回数を減らせる可能性がある。",
            cons_text="長期使用が前提となるため、副作用とのバランスが重要。",
        ),
        TreatmentDetail(
            treatment_id=t2.id,
            attribute_id=side.id,
            pros_text="少量であれば副作用をある程度抑えられる場合がある。",
            cons_text="長期連用により、体重増加、血糖上昇、骨粗鬆症などのリスクがある。",
        ),
        TreatmentDetail(
            treatment_id=t2.id,
            attribute_id=cost.id,
            pros_text="生物学的製剤と比べると薬剤費は安価。",
            cons_text="長期間続けるとトータルのコストはかさんでいく。",
        ),
        TreatmentDetail(
            treatment_id=t2.id,
            attribute_id=life.id,
            pros_text="内服習慣が生活に組み込まれれば、安定した日常を送りやすい。",
            cons_text="毎日内服が必要で、飲み忘れへの不安がある。",
        ),
        TreatmentDetail(
            treatment_id=t2.id,
            attribute_id=freq.id,
            pros_text="通院頻度は患者さんの状況に応じて調整可能。",
            cons_text="定期的な検査やフォローが必要になる。",
        ),

        # t3: 生物学的製剤
        TreatmentDetail(
            treatment_id=t3.id,
            attribute_id=eff.id,
            pros_text="重症喘息に対して高い効果が期待できることが多い。",
            cons_text="全ての患者さんに効果があるわけではない。",
        ),
        TreatmentDetail(
            treatment_id=t3.id,
            attribute_id=side.id,
            pros_text="全身ステロイドと比べて、長期的な副作用リスクが少ない場合がある。",
            cons_text="注射部位反応など、特有の副作用が出ることがある。",
        ),
        TreatmentDetail(
            treatment_id=t3.id,
            attribute_id=cost.id,
            pros_text="高い効果により、入院や救急受診の減少が期待できる。",
            cons_text="薬剤費が高額で、自己負担も大きくなりやすい。",
        ),
        TreatmentDetail(
            treatment_id=t3.id,
            attribute_id=life.id,
            pros_text="症状が安定すれば、日常生活や仕事・学校への支障が減る可能性がある。",
            cons_text="定期的な注射のために時間を確保する必要がある。",
        ),
        TreatmentDetail(
            treatment_id=t3.id,
            attribute_id=freq.id,
            pros_text="月1回程度の投与でコントロールを目指す治療が多い。",
            cons_text="通院間隔は長いが、1回あたりの拘束時間は長くなることがある。",
        ),
    ]
    db.session.add_all(details)
    db.session.flush()

    # ---- 理解度チェック質問 & 選択肢 ----
    q_texts = [
        "この治療のメリットについて、どの程度理解できましたか？",
        "この治療の副作用やリスクについて、どの程度理解できましたか？",
        "費用や通院頻度について、どの程度イメージできましたか？",
    ]
    treatments = [t1, t2, t3]

    for t in treatments:
        for i, qt in enumerate(q_texts, start=1):
            q = UnderstandingQuestion(
                treatment_id=t.id,
                text=qt,
                order_index=i,
            )
            db.session.add(q)
            db.session.flush()

            choices = [
                ("全くわからなかった", 1),
                ("あまりわからなかった", 2),
                ("だいたいわかった", 3),
                ("よくわかった", 4),
                ("十分に理解できた", 5),
            ]
            for label, score in choices:
                c = UnderstandingChoice(
                    question_id=q.id,
                    label=label,
                    score=score,
                )
                db.session.add(c)

    db.session.commit()


# -------------------
# ルーティング
# -------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/treatments")
def treatments():
    options = TreatmentOption.query.all()
    return render_template("treatments.html", options=options)


@app.route("/treatments/<int:treatment_id>", methods=["GET", "POST"])
def treatment_detail(treatment_id):
    treatment = TreatmentOption.query.get_or_404(treatment_id)
    attributes = Attribute.query.order_by(Attribute.order_index).all()

    # 属性ごとに details をマッピング
    details_by_attr = {}
    for attr in attributes:
        detail = next(
            (d for d in treatment.details if d.attribute_id == attr.id),
            None,
        )
        details_by_attr[attr.id] = detail

    questions = (
        UnderstandingQuestion.query.filter_by(treatment_id=treatment.id)
        .order_by(UnderstandingQuestion.order_index)
        .all()
    )

    if request.method == "POST":
        # 理解度スコア集計（DBには保存しない）
        scores = []
        for q in questions:
            value = request.form.get(f"question_{q.id}")
            if value:
                scores.append(int(value))

        avg_score = mean(scores) if scores else None
        ask_list = request.form.get("ask_list")

        return render_template(
            "result.html",
            treatment=treatment,
            avg_score=avg_score,
            ask_list=ask_list,
        )

    return render_template(
        "treatment_detail.html",
        treatment=treatment,
        attributes=attributes,
        details_by_attr=details_by_attr,
        questions=questions,
    )


@app.route("/compare")
def compare():
    options = TreatmentOption.query.all()
    attributes = Attribute.query.order_by(Attribute.order_index).all()

    # {(treatment_id, attribute_id): detail}
    detail_map = {}
    for opt in options:
        for d in opt.details:
            detail_map[(opt.id, d.attribute_id)] = d

    return render_template(
        "compare.html",
        options=options,
        attributes=attributes,
        detail_map=detail_map,
    )


# -------------------
# エントリポイント
# -------------------

if __name__ == "__main__":
    # Flask 3.x では here で app_context を作って初期化する
    with app.app_context():
        init_db()

    app.run(debug=True)
