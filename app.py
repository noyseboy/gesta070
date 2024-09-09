from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from flask_migrate import Migrate
from datetime import datetime, timedelta
from config import Config
from models import db, Aluno, User,AgendamentoProvaTeorica,AgendamentoTreinoPratico,Aviso,Feedback,Mensagem,Pagamento
import os


app = Flask(__name__)
# Inicialização do banco de dados e migrações
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

def find_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        return {'username': user.username, 'user_type': user.user_type}
    aluno = Aluno.query.filter_by(username=username).first()
    if aluno and aluno.password == password:
        return {'username': aluno.username, 'user_type': 'aluno'}
    return None

def generate_calendar(year, month):
    # Primeiro dia do mês
    first_day = datetime(year, month, 1)
    # Último dia do mês
    last_day = (first_day + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    # Dias da semana para o cabeçalho
    days_of_week = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    # Gerar lista de dias
    days = []
    day = first_day
    while day <= last_day:
        days.append({
            'day': day.day,
            'date': day.strftime('%Y-%m-%d'),
            'occupied': False  # Você pode definir como True se o dia estiver ocupado
        })
        day += timedelta(days=1)
    # Ajustar para que o calendário comece na semana correta
    first_weekday = first_day.weekday()
    for _ in range(first_weekday):
        days.insert(0, {'day': '', 'date': '', 'occupied': False})
    return days

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        user = find_user(username, password)
        if user and user['user_type'] == user_type:
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            if user_type == 'adm':
                return redirect(url_for('cadastro_aluno'))
            else:
                return redirect(url_for('painel_aluno'))
        else:
            flash('Login ou senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_type', None)
    return redirect(url_for('login'))

@app.route('/painel_aluno')
def painel_aluno():
    if 'username' in session and session['user_type'] == 'aluno':
        aluno = Aluno.query.filter_by(username=session['username']).first()
        if aluno:
            nome = aluno.nome
            categoria = aluno.categoria
            
            # Verificar se a data_processo é uma string e converter para datetime se necessário
            if isinstance(aluno.data_processo, str):
                data_processo = datetime.strptime(aluno.data_processo, '%Y-%m-%d')
            else:
                data_processo = aluno.data_processo
            
            data_fim = data_processo + timedelta(days=365)
            agora = datetime.now()
            dias_restantes = (data_fim - agora).days
            
            return render_template('painel_aluno.html', nome=nome, categoria=categoria, dias_restantes=dias_restantes)
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    
@app.route('/area_estudo')
def area_estudo():
    if 'username' in session and session['user_type'] == 'aluno':
        return render_template('area_estudo.html')
    else:
        return redirect(url_for('login'))

@app.route('/agendar_prova_teorica', methods=['GET', 'POST'])
def agendar_prova_teorica():
    if 'username' in session and session['user_type'] == 'aluno':
        now = datetime.now()
        calendar_days = generate_calendar(now.year, now.month)
        
        if request.method == 'POST':
            selected_date = request.form.get('selected_date')
            selected_time = request.form.get('selected_time')
            if selected_date and selected_time:
                new_schedule = AgendamentoProvaTeorica(username=session['username'], data_hora=f"{selected_date} {selected_time}")
                db.session.add(new_schedule)
                db.session.commit()
                flash('Prova teórica agendada com sucesso!', 'success')
            else:
                flash('Nenhuma data ou horário selecionado.', 'danger')
        
        agendamentos = AgendamentoProvaTeorica.query.filter_by(username=session['username']).all()
        return render_template('agendar_prova_teorica.html', calendar_days=calendar_days, agendamentos=agendamentos)
    else:
        return redirect(url_for('login'))

@app.route('/agendar_treino_pratico', methods=['GET', 'POST'])
def agendar_treino_pratico():
    if 'username' in session and session['user_type'] == 'aluno':
        instrutores = ['Instrutor A', 'Instrutor B', 'Instrutor C', 'Instrutor D', 'Instrutor E']
        
        if request.method == 'POST':
            tipo_aula = request.form.get('tipo_aula')  # Use get() para evitar KeyError se o campo estiver faltando
            data_hora = request.form.get('data_hora')
            instrutor = request.form.get('instrutor')
            dias_semana = request.form.getlist('dias_semana')
            
            # Converter lista de dias para uma string separada por vírgulas
            dias_semana_str = ', '.join(dias_semana)
            
            if tipo_aula and data_hora and instrutor:
                if 'tipo_aula' in locals():  # Verifica se o tipo_aula existe na instância
                    new_agendamento = AgendamentoTreinoPratico(
                        username=session['username'],
                        tipo_aula=tipo_aula,
                        data_hora=data_hora,
                        instrutor=instrutor,
                        dias_semana=dias_semana_str
                    )
                else:
                    new_agendamento = AgendamentoTreinoPratico(
                        username=session['username'],
                        data_hora=data_hora,
                        instrutor=instrutor,
                        dias_semana=dias_semana_str
                    )
                db.session.add(new_agendamento)
                db.session.commit()
                flash('Treino prático agendado com sucesso!', 'success')
            else:
                flash('Por favor, preencha todos os campos.', 'danger')
        
        # Recuperar agendamentos do banco de dados
        treinos = AgendamentoTreinoPratico.query.filter_by(username=session['username']).all()
        return render_template('agendar_treino_pratico.html', treinos=treinos, instrutores=instrutores)
    else:
        return redirect(url_for('login'))


@app.route('/status_processo')
def status_processo():
    if 'username' in session and session['user_type'] == 'aluno':
        # Consultar o banco de dados para obter os agendamentos do usuário logado
        agendamentos_provas = AgendamentoProvaTeorica.query.filter_by(username=session['username']).all()
        agendamentos_treinos = AgendamentoTreinoPratico.query.filter_by(username=session['username']).all()

        return render_template('status_processo.html', agendamentos_provas=agendamentos_provas, agendamentos_treinos=agendamentos_treinos)
    else:
        return redirect(url_for('login.html'))

@app.route('/central_avisos')
def central_avisos():
    avisos = Aviso.query.all()
    return render_template('central_avisos.html', avisos=avisos)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'username' in session and session['user_type'] == 'aluno':
        if request.method == 'POST':
            feedback_text = request.form.get('feedback')
            aluno_username = session['username']  # Assumindo que o username do aluno está armazenado na sessão
            aluno = Aluno.query.filter_by(username=aluno_username).first()
            if feedback_text and aluno:
                # Criar instância do modelo Feedback e adicionar ao banco
                novo_feedback = Feedback(aluno_id=aluno.id, texto=feedback_text)
                db.session.add(novo_feedback)
                db.session.commit()
                flash('Feedback enviado com sucesso!', 'success')
                return redirect(url_for('feedback'))
            else:
                flash('Por favor, insira seu feedback.', 'error')
        return render_template('feedback.html')
    else:
        return redirect(url_for('login'))

@app.route('/enviar_feedback', methods=['POST'])
def enviar_feedback():
    if 'username' in session and session['user_type'] == 'aluno':
        feedback_text = request.form.get('feedback')
        if feedback_text:
            flash('Feedback enviado com sucesso!', 'success')
            return redirect(url_for('feedback'))
        else:
            flash('Por favor, insira seu feedback.', 'error')
            return redirect(url_for('feedback'))
    else:
        return redirect(url_for('login'))

@app.route('/cadastro_aluno', methods=['GET', 'POST'])
def cadastro_aluno():
    if request.method == 'POST':
        nome = request.form['nome']
        data_nascimento = request.form['data_nascimento']
        cpf = request.form['cpf']
        numero_contato = request.form['numero_contato']  # Novo campo
        sexo = request.form['sexo']
        categoria = request.form['categoria']
        data_processo = request.form['data_processo']
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Nome de usuário e senha são obrigatórios.', 'error')
            return redirect(url_for('cadastro_aluno'))

        # Verificar se o CPF já está em uso
        if Aluno.query.filter_by(cpf=cpf).first():
            flash('O CPF informado já está cadastrado.', 'error')
            return redirect(url_for('cadastro_aluno'))

        try:
            novo_aluno = Aluno(
                nome=nome,
                data_nascimento=datetime.strptime(data_nascimento, '%Y-%m-%d'),
                cpf=cpf,
                numero_contato=numero_contato,  # Incluído o número de contato
                sexo=sexo,
                categoria=categoria,
                data_processo=datetime.strptime(data_processo, '%Y-%m-%d'),
                username=username,
                password=password
            )
            db.session.add(novo_aluno)
            db.session.commit()
            flash('Aluno cadastrado com sucesso.', 'success')
            return render_template('cadastro_aluno.html', aluno=novo_aluno)
        except IntegrityError as e:
            db.session.rollback()
            flash('Erro de integridade: Dados já existem ou são inválidos.', 'error')
            return redirect(url_for('cadastro_aluno'))
        except ValueError as e:
            flash(f'Erro de valor: {str(e)}', 'error')
            return redirect(url_for('cadastro_aluno'))
        except Exception as e:
            flash(f'Erro ao processar o cadastro do aluno: {str(e)}', 'error')
            return redirect(url_for('cadastro_aluno'))

    return render_template('cadastro_aluno.html')

# Perguntas e respostas corretas
perguntas_respostas = {
    'q1': 'E',
    'q2': 'B',
    'q3': 'D',
    # Adicione mais perguntas e respostas conforme necessário
}

respostas_texto = {
    'q1': 'E - agindo com sentimento de solidariedade, cortesia e respeito.',
    'q2': 'B - parar o veículo e facilitar a travessia.',
    'q3': 'D - cuidadoso e atento.',
    # Adicione mais perguntas e respostas conforme necessário
}

@app.route('/simulado', methods=['GET'])
def simulado():
    return render_template('simulado.html')

@app.route('/submit', methods=['POST'])
def submit():
    respostas = request.form
    pontuacao = 0
    respostas_erradas = {}
    total_perguntas = len(perguntas_respostas)  # Número total de perguntas

    for pergunta_id, resposta in respostas.items():
        resposta_correta = perguntas_respostas.get(pergunta_id)
        if resposta == resposta_correta:
            pontuacao += 1
        else:
            respostas_erradas[pergunta_id] = respostas_texto.get(pergunta_id)

    resultado = {
        'pontuacao': pontuacao,
        'total_perguntas': total_perguntas,
        'respostas_erradas': respostas_erradas
    }
    
    return render_template('resultado.html', resultado=resultado)


# gerenciar alunos
@app.route('/gerenciar_alunos')
def gerenciar_alunos():
    if 'user_type' in session and session['user_type'] == 'adm':
        alunos = Aluno.query.all()
        
        for aluno in alunos:
            # Converta strings para objetos datetime se necessário
            if isinstance(aluno.data_processo, str):
                aluno.data_processo = datetime.strptime(aluno.data_processo, '%Y-%m-%d')
            if isinstance(aluno.data_nascimento, str):
                aluno.data_nascimento = datetime.strptime(aluno.data_nascimento, '%Y-%m-%d')
            
            # Adiciona dados do pagamento ao aluno, se disponível
            aluno.pagamento = Pagamento.query.filter_by(aluno_id=aluno.id).first()
            
            # Converte datas das parcelas para uma lista legível se o pagamento estiver parcelado
            if aluno.pagamento and aluno.pagamento.forma_pagamento == 'parcelado':
                datas_parcelas = aluno.pagamento.data_parcelas.split(',')
                aluno.pagamento.datas_parcelas_formatadas = '<br>'.join(datas_parcelas)
        
        return render_template('gerenciar_alunos.html', alunos=alunos)
    else:
        return redirect(url_for('login'))
    
#apagar aluno
@app.route('/deletar_aluno/<int:aluno_id>', methods=['POST'])
def deletar_aluno(aluno_id):
    if 'user_type' in session and session['user_type'] == 'adm':
        aluno = Aluno.query.get(aluno_id)
        if aluno:
            try:
                if aluno.pagamento:
                    db.session.delete(aluno.pagamento)
                db.session.delete(aluno)
                db.session.commit()
                flash('Aluno removido com sucesso!', 'success')
            except IntegrityError as e:
                db.session.rollback()
                flash(f'Erro ao remover o aluno. Detalhes do erro: {e}', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Ocorreu um erro inesperado: {e}', 'danger')
        else:
            flash('Aluno não encontrado.', 'danger')
        return redirect(url_for('gerenciar_alunos'))
    else:
        return redirect(url_for('login'))


@app.route('/adicionar_aviso', methods=['GET', 'POST'])
def adicionar_aviso():
    if request.method == 'POST':
        texto_aviso = request.form.get('texto_aviso')
        if texto_aviso:
            novo_aviso = Aviso(texto=texto_aviso)
            db.session.add(novo_aviso)
            db.session.commit()
            flash('Aviso adicionado com sucesso!', 'success')
        else:
            flash('Erro ao adicionar aviso. Tente novamente.', 'error')
    
    # Consulta para obter todos os avisos
    avisos = Aviso.query.all()
    return render_template('adicionar_aviso.html', avisos=avisos)

# Rota para deletar avisos
@app.route('/deletar_avisos', methods=['POST'])
def deletar_avisos():
    if 'user_type' in session and session['user_type'] == 'adm':
        aviso_id = request.form.get('aviso_id')
        if aviso_id:
            Aviso.query.filter_by(id=aviso_id).delete()
            db.session.commit()
            flash('Aviso apagado com sucesso!', 'success')
        else:
            flash('Aviso não encontrado.', 'error')
        return redirect(url_for('adicionar_aviso'))
    else:
        return redirect(url_for('login'))
    

@app.route('/visualizar_feedbacks')
def visualizar_feedbacks():
    if 'user_type' in session and session['user_type'] == 'adm':
        feedbacks = Feedback.query.all()
        return render_template('visualizar_feedbacks.html', feedbacks=feedbacks)
    else:
        return redirect(url_for('login'))
    
@app.route('/enviar_mensagem', methods=['GET', 'POST'])
def enviar_mensagem():
    if 'user_type' in session and session['user_type'] == 'adm':
        alunos = Aluno.query.all()
        if request.method == 'POST':
            aluno_id = request.form['aluno_id']
            texto = request.form['texto']
            nova_mensagem = Mensagem(aluno_id=aluno_id, texto=texto)
            db.session.add(nova_mensagem)
            db.session.commit()
            # Redireciona para a página de confirmação
            return redirect(url_for('mensagem_enviada'))
        return render_template('enviar_mensagem.html', alunos=alunos)
    else:
        return redirect(url_for('login'))

@app.route('/mensagem_enviada')
def mensagem_enviada():
    return render_template('mensagem_enviada.html')
    
@app.route('/visualizar_mensagens')
def visualizar_mensagens():
    if 'user_type' in session and session['user_type'] in ['adm', 'aluno']:
        mensagens = Mensagem.query.all()
        return render_template('visualizar_mensagens.html', mensagens=mensagens)
    else:
        return redirect(url_for('login'))

@app.route('/cadastrar_pagamento/<int:aluno_id>', methods=['GET', 'POST'])
def cadastrar_pagamento(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)  # Certifique-se de que o aluno existe

    if request.method == 'POST':
        try:
            forma_pagamento = request.form['forma_pagamento']
            valor_total = float(request.form['valor_total'])
            valor_entrada = float(request.form.get('valor_entrada', 0.0))  # Valor de entrada padrão é 0.0
            
            num_parcelas = None
            valor_parcela = None
            data_parcelas = None
            status_parcelas = None
            
            if forma_pagamento == 'parcelado':
                num_parcelas = int(request.form.get('num_parcelas', 0))
                valor_parcela = (valor_total - valor_entrada) / num_parcelas if num_parcelas > 0 else 0
                data_primeira_parcela = datetime.strptime(request.form['data_primeira_parcela'], '%Y-%m-%d')

                # Calcular datas das parcelas
                datas_parcelas = []
                for i in range(num_parcelas):
                    data_parcela = data_primeira_parcela + timedelta(days=i * 30)  # Ajuste o intervalo conforme necessário
                    datas_parcelas.append(data_parcela.strftime('%d/%m/%Y'))

                data_parcelas = ','.join(datas_parcelas)
                status_parcelas = ','.join(['0'] * num_parcelas)  # Inicialmente, todas as parcelas estão não pagas
            else:
                num_parcelas = None
                valor_parcela = None
                data_parcelas = None
                status_parcelas = None

            # Criar ou atualizar o pagamento e associá-lo ao aluno
            pagamento_existente = Pagamento.query.filter_by(aluno_id=aluno.id).first()

            if pagamento_existente:
                # Atualizar o pagamento existente
                pagamento_existente.forma_pagamento = forma_pagamento
                pagamento_existente.valor_total = valor_total
                pagamento_existente.valor_entrada = valor_entrada
                pagamento_existente.num_parcelas = num_parcelas
                pagamento_existente.valor_parcela = valor_parcela
                pagamento_existente.data_parcelas = data_parcelas
                pagamento_existente.status_parcelas = status_parcelas
            else:
                # Criar um novo pagamento
                pagamento_existente = Pagamento(
                    forma_pagamento=forma_pagamento,
                    valor_total=valor_total,
                    valor_entrada=valor_entrada,
                    num_parcelas=num_parcelas,
                    valor_parcela=valor_parcela,
                    data_parcelas=data_parcelas,
                    status_parcelas=status_parcelas,
                    aluno_id=aluno.id
                )
                db.session.add(pagamento_existente)

            db.session.commit()
            print("Pagamento cadastrado com sucesso!")  # Diagnóstico: Confirmação de sucesso
            return redirect(url_for('gerenciar_alunos'))

        except ValueError as e:
            # Captura de ValueError e exibição de uma mensagem de erro
            print(f"Erro de valor: {e}")  # Diagnóstico: Exibir erro no console
            return render_template('cadastrar_pagamento.html', aluno=aluno, erro="Erro de valor: Verifique os valores inseridos.")
        except Exception as e:
            # Captura de qualquer outra exceção
            print(f"Erro inesperado: {e}")  # Diagnóstico: Exibir erro no console
            return render_template('cadastrar_pagamento.html', aluno=aluno, erro=f"Erro inesperado: {str(e)}")

    return render_template('cadastrar_pagamento.html', aluno=aluno)

@app.route('/atualizar_parcela/<int:aluno_id>/<int:parcela_index>', methods=['POST'])
def atualizar_parcela(aluno_id, parcela_index):
    aluno = Aluno.query.get(aluno_id)
    if aluno and aluno.pagamento:
        pagamento = aluno.pagamento
        if pagamento.forma_pagamento == 'parcelado':
            status_atual = pagamento.status_parcelas.split(',')
            if parcela_index < len(status_atual):
                # Marca a parcela como paga
                status_atual[parcela_index] = '1'
                pagamento.status_parcelas = ','.join(status_atual)
                db.session.commit()
                flash('Parcela atualizada com sucesso!', 'success')
            else:
                flash('Índice de parcela inválido.', 'danger')
        else:
            flash('Pagamento não é parcelado, não é possível dar baixa.', 'warning')
    else:
        flash('Aluno ou pagamento não encontrado.', 'danger')
    return redirect(url_for('gerenciar_alunos'))

@app.route('/agendamentos')
def agendamentos():
    agendamentos_teoricos = AgendamentoProvaTeorica.query.all()
    agendamentos_praticos = AgendamentoTreinoPratico.query.all()
    return render_template('agendamentos.html', agendamentos_teoricos=agendamentos_teoricos, agendamentos_praticos=agendamentos_praticos)


@app.route('/buscar_alunos', methods=['GET'])
def buscar_alunos():
    query = request.args.get('query', '')

    if query:
        alunos = Aluno.query.filter(
            (Aluno.nome.ilike(f'%{query}%')) |
            (Aluno.cpf.ilike(f'%{query}%'))
        ).all()
    else:
        alunos = []

    return render_template('buscar_alunos.html', alunos=alunos, query=query)

@app.route('/parcelas', methods=['GET'])
def parcelas():
    hoje = datetime.now().date()

    # Função auxiliar para obter datas e status das parcelas
    def obter_parcelas(pagamento):
        datas = pagamento.data_parcelas.split(',') if pagamento.data_parcelas else []
        status = pagamento.status_parcelas.split(',') if pagamento.status_parcelas else []
        return [(datetime.strptime(d, '%d/%m/%Y').date(), s) for d, s in zip(datas, status)]

    # Parcelas em atraso
    parcelas_atraso = []
    parcelas_vencer = []

    pagamentos = Pagamento.query.all()
    for pagamento in pagamentos:
        parcelas = obter_parcelas(pagamento)
        print(f'Parcelas obtidas: {parcelas}')  # Verificar as parcelas obtidas
        for data, status in parcelas:
            if status == '0':  # Apenas parcelas pendentes
                if data < hoje:
                    parcelas_atraso.append((pagamento, pagamento.aluno, data))
                elif hoje <= data <= hoje + timedelta(days=30):
                    parcelas_vencer.append((pagamento, pagamento.aluno, data))

    # Verificar se as listas foram preenchidas corretamente
    print(f'Parcelas em atraso: {parcelas_atraso}')
    print(f'Parcelas a vencer: {parcelas_vencer}')
    
    return render_template('parcelas.html', parcelas_atraso=parcelas_atraso, parcelas_vencer=parcelas_vencer)

@app.route('/estatisticas_inscricoes', methods=['GET'])
def estatisticas_inscricoes():
    # Total de inscrições
    total_inscricoes = db.session.query(Aluno).count()

    # Total de inscrições por categoria
    inscricoes_A = db.session.query(Aluno).filter(Aluno.categoria == 'A').count()
    inscricoes_B = db.session.query(Aluno).filter(Aluno.categoria == 'B').count()
    inscricoes_AB = db.session.query(Aluno).filter(Aluno.categoria == 'AB').count()

    # Total de inscrições por sexo
    inscricoes_masculino = db.session.query(Aluno).filter(Aluno.sexo == 'M').count()
    inscricoes_feminino = db.session.query(Aluno).filter(Aluno.sexo == 'F').count()

    return render_template(
        'estatisticas.html',
        total_inscricoes=total_inscricoes,
        inscricoes_A=inscricoes_A,
        inscricoes_B=inscricoes_B,
        inscricoes_AB=inscricoes_AB,
        inscricoes_masculino=inscricoes_masculino,
        inscricoes_feminino=inscricoes_feminino
    )

@app.route('/pesquisa_inscricoes', methods=['GET', 'POST'])
def pesquisa_inscricoes():
    if request.method == 'POST':
        categoria = request.form.get('categoria')
        sexo = request.form.get('sexo')
        mes = request.form.get('mes')  # Captura o mês selecionado no formulário
        
        # Inicialize variáveis de resultado
        total_inscricoes = 0
        total_categoria_a = 0
        total_categoria_b = 0
        total_categoria_ab = 0
        total_masculino = 0
        total_feminino = 0

        # Filtrar Alunos
        query = Aluno.query
        
        # Filtra por categoria se selecionado
        if categoria != 'todas':
            query = query.filter_by(categoria=categoria)
        
        # Filtra por sexo se selecionado
        if sexo != 'todos':
            query = query.filter_by(sexo=sexo)

        # Filtra por mês e ano se selecionado
        if mes:
            try:
                mes_data = datetime.strptime(mes, '%m/%Y')
                ano = mes_data.year
                mes_num = mes_data.month

                query = query.filter(
                    db.extract('year', Aluno.data_processo) == ano,
                    db.extract('month', Aluno.data_processo) == mes_num
                )
            except ValueError:
                return render_template('pesquisa_inscricoes.html', erro="Formato de mês inválido.")
        
        # Ordenar pela data do processo (do mais antigo ao mais recente)
        query = query.order_by(Aluno.data_processo.asc())

        # Executa a consulta
        alunos = query.all()
        total_inscricoes = len(alunos)
        
        for aluno in alunos:
            if aluno.categoria == 'A':
                total_categoria_a += 1
            elif aluno.categoria == 'B':
                total_categoria_b += 1
            elif aluno.categoria == 'AB':
                total_categoria_ab += 1
            if aluno.sexo == 'M':
                total_masculino += 1
            elif aluno.sexo == 'F':
                total_feminino += 1

        resultado = {
            'alunos': alunos,  # Adiciona a lista de alunos nos resultados
            'total_inscricoes': total_inscricoes,
            'total_categoria_a': total_categoria_a,
            'total_categoria_b': total_categoria_b,
            'total_categoria_ab': total_categoria_ab,
            'total_masculino': total_masculino,
            'total_feminino': total_feminino
        }
        
        return render_template('pesquisa_inscricoes.html', resultado=resultado)
    
    return render_template('pesquisa_inscricoes.html')



@app.route('/calcular_lucro_mensal', methods=['GET', 'POST'])
def calcular_lucro_mensal():
    if request.method == 'POST':
        mes = request.form.get('mes')
        
        try:
            mes_data = datetime.strptime(mes, '%m/%Y')
            ano = mes_data.year
            mes_num = mes_data.month
            
            # Inicialize variáveis
            valor_avista_total = 0.0
            valor_entrada_total = 0.0
            valor_parcelas_pagas = 0.0
            valor_parcelas_vencidas = 0.0
            valor_parcelas_a_vencer = 0.0

            # Filtrar pagamentos à vista
            pagamentos_avista = Pagamento.query.filter(
                Pagamento.forma_pagamento == 'avista'
            ).all()

            for pagamento in pagamentos_avista:
                valor_avista_total += pagamento.valor_total

            # Filtrar pagamentos parcelados
            pagamentos_parcelado = Pagamento.query.filter(
                Pagamento.forma_pagamento == 'parcelado'
            ).all()

            for pagamento in pagamentos_parcelado:
                if pagamento.valor_entrada:
                    valor_entrada_total += pagamento.valor_entrada
                
                if pagamento.data_parcelas:
                    datas_parcelas = pagamento.data_parcelas.split(',')
                    status_parcelas = pagamento.status_parcelas.split(',') if pagamento.status_parcelas else []

                    for i, data_parcela_str in enumerate(datas_parcelas):
                        data_parcela = datetime.strptime(data_parcela_str, '%d/%m/%Y').date()
                        status = status_parcelas[i] if i < len(status_parcelas) else '0'
                        
                        if data_parcela.month == mes_num and data_parcela.year == ano:
                            if status == '1':  # Parcela paga
                                valor_parcelas_pagas += pagamento.valor_parcela or 0.0
                            elif status == '0':  # Parcela não paga
                                valor_parcelas_vencidas += pagamento.valor_parcela or 0.0
                        
                        # Verifica se a parcela está a vencer
                        if (data_parcela.month == mes_num + 1 or 
                            (data_parcela.month == 1 and mes_num == 12)) and \
                            data_parcela.year == ano:
                            valor_parcelas_a_vencer += pagamento.valor_parcela or 0.0

            lucro_mensal = valor_avista_total + valor_entrada_total + valor_parcelas_pagas

            resultado = {
                'valor_avista_total': valor_avista_total,
                'valor_entrada_total': valor_entrada_total,
                'valor_parcelas_pagas': valor_parcelas_pagas,
                'valor_parcelas_vencidas': valor_parcelas_vencidas,
                'valor_parcelas_a_vencer': valor_parcelas_a_vencer,
                'lucro_mensal': lucro_mensal
            }

            return render_template('calcular_lucro_mensal.html', resultado=resultado)

        except ValueError:
            return render_template('calcular_lucro_mensal.html', erro="Formato de mês inválido.")
    
    return render_template('calcular_lucro_mensal.html')


if __name__ == '__main__':
    app.run(debug=True)