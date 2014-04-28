from flask import Flask, render_template, request, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from ConfigParser import ConfigParser
from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, ForeignKey, Table, UnicodeText, Text, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from flask_limiter import Limiter

app = Flask(__name__)
limiter = Limiter(app, global_limits=["30 per minute"])

config = ConfigParser()
config.readfp(open('config.ini'))

engine = create_engine(config.get('database', 'connection-string'))
db = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db.query_property()

result_question_table = Table('result_question', Base.metadata,
    Column('result_id', Integer, ForeignKey('result.id')),
    Column('question_id', Integer, ForeignKey('question.id'))
)

class Result(Base):
    __tablename__ = "result"
    id = Column(Integer, primary_key = True)
    userAgent = Column(Unicode(512))
    notes = Column(Unicode(4096))
    questions = relationship("Question", secondary=result_question_table, backref="results")
    answers = relationship("Answer")

class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key = True)
    name = Column(String(256))
    answers = relationship("Answer")

class Answer(Base):
    __tablename__ = "answer"
    id = Column(Integer, primary_key = True)
    result_id = Column(Integer, ForeignKey("result.id"))
    question_id = Column(Integer, ForeignKey("question.id"))
    user_agent = Column(String(512))
    value = Column(Boolean)

Base.metadata.create_all(bind=engine)

@app.route("/")
def index():
    return render_template('survey.html', ua = request.user_agent.string)

@app.route('/post', methods=['POST'])
def post():
    result = Result()
    result.userAgent = request.user_agent.string
    result.notes = request.form["notes"]
    db.add(result)
    db.commit()
    for key, value in request.form.items():
        if key.startswith('q-'):
            q = db.query(Question).filter(Question.name == key).first()
            if q == None:
                q = Question()
                q.name = key
                db.add(q)
            result.questions.append(q)
            a = Answer()
            a.user_agent = request.user_agent.string
            a.result_id = result.id
            a.question_id = q.id
            a.value = value.lower() in ['true', 'yes', 'on']
            db.add(a)
            q.answers.append(a)
            result.questions.append(q)
            result.answers.append(a)
    db.commit()
    return redirect("/thanks/" + str(result.id))

@app.route('/thanks/<int:result>')
def thanks(result):
    return render_template("thanks.html", result = result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
