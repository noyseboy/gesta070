from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_processo = db.Column(db.DateTime, nullable=False) 
    categoria = db.Column(db.String(2), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    sexo = db.Column(db.String(1), nullable=False) 
    data_nascimento = db.Column(db.Date, nullable=False)  
    cpf = db.Column(db.String(11), unique=True, nullable=False)  
    numero_contato = db.Column(db.String(15), nullable=False)  
    mensagens = db.relationship('Mensagem', backref='aluno_relacionado', cascade="all, delete-orphan")
    feedbacks = db.relationship('Feedback', backref='aluno_relacionado', cascade="all, delete-orphan")
    pagamento = db.relationship('Pagamento', backref='aluno_pagamento', uselist=False) 
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)

class AgendamentoProvaTeorica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    data_hora = db.Column(db.String(50), nullable=False)

class AgendamentoTreinoPratico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    data_hora = db.Column(db.String(20), nullable=False)
    instrutor = db.Column(db.String(100), nullable=False)
    dias_semana = db.Column(db.String(100), nullable=False)  # Aumente o comprimento conforme necessário
    tipo_aula = db.Column(db.String(50), nullable=False)

class Aviso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    aluno = db.relationship('Aluno', backref=db.backref('feedbacks_relacionados', lazy=True))

class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    aluno = db.relationship('Aluno', backref=db.backref('mensagens_relacionadas', lazy=True))

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forma_pagamento = db.Column(db.String(20), nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    valor_entrada = db.Column(db.Float, nullable=True)  # Valor de entrada
    num_parcelas = db.Column(db.Integer, nullable=True)
    valor_parcela = db.Column(db.Float, nullable=True)
    data_parcelas = db.Column(db.Text, nullable=True)  # Guardar datas como texto, separadas por vírgula
    status_parcelas = db.Column(db.Text, nullable=True)  # Guardar o status de cada parcela como texto, separado por vírgula
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'), nullable=False)
    aluno = db.relationship('Aluno', backref='pagamento_relacionado')
