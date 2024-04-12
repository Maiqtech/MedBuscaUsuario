from medbusca import app, db
from medbusca import models
from flask import Flask, render_template, url_for, request, flash, redirect
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from medbusca.forms import DisponibilidadeMedicoForm
from flask import request
from medbusca.models import Disponibilidade_medico_view, Especialidade_m, Gestor, ReceberInfo # Importando o modelo correto
import csv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
from io import TextIOWrapper, StringIO
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc



# Rota para exibir o formulário de busca
@app.route('/')
def hero():
    return render_template('index.html')

@app.route('/busca', methods=['POST','GET'])
def busca():
    formresultado = DisponibilidadeMedicoForm()
    
    # Busca todas as especialidades, cidades e estados disponíveis no banco de dados
    especialidades = Disponibilidade_medico_view.query.with_entities(Disponibilidade_medico_view.descricao_esp).distinct().all()
    cidades = Disponibilidade_medico_view.query.with_entities(Disponibilidade_medico_view.cidade_unidade).distinct().all()
    estados = Disponibilidade_medico_view.query.with_entities(Disponibilidade_medico_view.estado_unidade).distinct().all()
    
    # Transforma as listas de tuplas em listas simples
    lista_especialidades = [esp[0] for esp in especialidades]
    lista_cidades = [cidade[0] for cidade in cidades]
    lista_estados = [estado[0] for estado in estados]
    
    return render_template('busca.html', formresultado=formresultado, especialidades=lista_especialidades, cidades=lista_cidades, estados=lista_estados)





@app.route('/sobre', methods=['POST', 'GET'])
def sobre():
    return render_template('sobre.html')

# Rota para processar a busca
@app.route('/resultados', methods=['POST', 'GET'])
def resultados():
    formresultado = DisponibilidadeMedicoForm(request.form)
    if request.method == 'POST' and formresultado.validate():
        estado = request.form['estado_unidade']  # Captura usando os nomes dos campos no HTML
        cidade = request.form['cidade_unidade']  # Captura usando os nomes dos campos no HTML
        especialidade = request.form['especialidade']  # Captura usando os nomes dos campos no HTML

        # Modificando a consulta para buscar pela descrição da especialidade
        resultados = Disponibilidade_medico_view.query.filter(
            Disponibilidade_medico_view.estado_unidade == estado,
            Disponibilidade_medico_view.cidade_unidade == cidade,
            Disponibilidade_medico_view.descricao_esp == especialidade
        ).all()

        print(resultados)  # Verifique se há dados retornados após a consulta

        return render_template('resultados.html', resultados=resultados)

    return render_template('busca.html', formresultado=formresultado)




  

#  # imports do SELENIUM

def buscar_localizacao_google_maps(endereco):
    # Configura as opções do Chrome
    options = Options()
    # Execução sem abrir a interface gráfica
    # Assim, podemos gerar o endereço sem abrir janelas, ou seja, de forma 'silenciosa'
    options.add_argument("--headless")

    # Inicializa o serviço do ChromeDriver
    service = Service(ChromeDriverManager().install())

    # Inicializa o driver do Chrome
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://www.google.com.br/maps/")
        # Espera até encontrar o campo de pesquisa
        search_box = driver.find_element(By.XPATH, "//input[@autofocus='autofocus']")
        search_box.clear()
        search_box.send_keys(endereco)
        search_box.send_keys(Keys.RETURN)

        # Aguarda um tempo para carregar a página
        time.sleep(5)

        # Obtém a URL da página atual
        url = driver.current_url

    except NoSuchElementException as e:
        print("Elemento não encontrado:", e)
        url = None

    driver.quit()
    return url


@app.route('/atualiza_endurl', methods=['POST', 'GET'])
def atualizaurl():
    unidades = ReceberInfo.query.all()
    for unidade in unidades:
        endereco = (
            unidade.rua_unidade + " " + unidade.nome_unidade + " " +
            unidade.bairro_unidade + " " + unidade.cidade_unidade + " " +
            unidade.cep_unidade + " " + unidade.estado_unidade
        )
        # Obtém o link da localização usando a função buscar_localizacao_google_maps
        endereco_url = buscar_localizacao_google_maps(endereco)
        # Atualiza o campo url_unidade na tabela Disponibilidade_medico_view com o link obtido
        unidade.url_unidade = endereco_url

    # Confirma as alterações no banco de dados fora do loop
    db.session.commit()

    return render_template('atualizar.html', unidades=unidades)
#Exibe relação de upas
#exibeupas

@app.route('/especialidades', methods=['POST','GET'])
def especialidades():
    especialidades = Especialidade_m.query.all()
    return render_template('especialidades.html', especialidades=especialidades)



#Exibe relação de upas
#exibeupas
@app.route('/exibeupas/<int:id_especialidade_m>', methods=['POST', 'GET'])
def exibeupas(id_especialidade_m):
    if id_especialidade_m != 0:
        unidades = models.Unidades_por_especialidade_view.query.filter_by(id_especialidade_m=id_especialidade_m)
    else:
        unidades = models.Unidades_por_especialidade_view.query.all()
    return render_template('exibeupas.html', unidades=unidades)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form['cpf']
        senha = request.form['senha']

        user = Gestor.query.filter_by(cpf=cpf, senha=senha).first()

        if user:
            if user.adm == 1:
                # Redireciona para a página onde se encontra o cadastro de gestores (adm_sistema)
                return redirect(url_for('adm_sistema'))
            else:
                # Se não for administrador, redireciona para outra página
                return redirect(url_for('gestor_upa'))  # Altere para a página correta, se necessário

        else:
            return render_template('login.html', error='Credenciais inválidas')

    return render_template('login.html')

@app.route('/adm_sistema', methods=['GET', 'POST'])
def adm_sistema():
    # Renderiza a página adm_sistema
    return render_template('adm_sistema.html')


@app.route('/gestor_upa', methods=['GET', 'POST'])
def gestor_upa():
    message = None  # Inicializa a mensagem como nula
    
    if 'csv_file' in request.files:
        csv_file = request.files['csv_file']
        
        if csv_file:
            try:
                csv_text = TextIOWrapper(csv_file, encoding='utf-8')
                csv_data = csv.DictReader(csv_text)

                # Receber o ID da unidade do CSV
                id_unidade_list = [row.get('id_unidade') for row in csv_data]

                # Excluir os registros com base no ID da unidade do CSV
                ReceberInfo.query.filter(ReceberInfo.id_unidade.in_(id_unidade_list)).delete(synchronize_session=False)

                csv_text.seek(0)  # Retornar ao início do arquivo
                csv_data = csv.DictReader(csv_text)  # Recarregar os dados

                for row in csv_data:
                    try:
                        id_especialidade_m = int(row.get('id_especialidade_m')) if row.get('id_especialidade_m') else None
                    except (TypeError, ValueError):
                        id_especialidade_m = None

                    new_entry = ReceberInfo(
                        id_unidade=row.get('id_unidade'),
                        crm_medico=row.get('crm_medico'),
                        dataHoraInicio=row.get('dataHoraInicio'),
                        dataHoraFim=row.get('dataHoraFim') if row.get('dataHoraFim') not in ('', 'null') else None,
                        id_especialidade_m=id_especialidade_m,
                        descricao_esp=row.get('descricao_esp'),
                        rua_unidade=row.get('rua_unidade'),
                        cep_unidade=row.get('cep_unidade'),
                        numero_unidade=row.get('numero_unidade'),
                        bairro_unidade=row.get('bairro_unidade'),
                        cidade_unidade=row.get('cidade_unidade'),
                        estado_unidade=row.get('estado_unidade'),
                        nome_unidade=row.get('nome_unidade'),
                        url_unidade=row.get('url_unidade')
                        # Adicione outras colunas conforme necessário
                    )
                    db.session.add(new_entry)
                
                db.session.commit()

                message = "Arquivo CSV recebido e dados salvos no servidor com sucesso!"

            except exc.SQLAlchemyError as e:
                db.session.rollback()
                error_msg = f"Erro ao processar o arquivo CSV: {str(e)}"
                print(error_msg)
                message = error_msg

    return render_template('gestor_upa.html', message=message)

@app.route('/cadastrar_gestor', methods=['GET', 'POST'])
def cadastrar_gestor():
    message = None  # Inicializa a mensagem como nula
    
    if request.method == 'POST':
        cpf = request.form['cpf']
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        senha = request.form['senha']
        adm = True if 'adm' in request.form else False  # Define como True se 'adm' estiver presente no form

        try:
            # Criar um novo gestor com os dados recebidos
            novo_gestor = Gestor(
                cpf=cpf,
                nome=nome,
                telefone=telefone,
                email=email,
                senha=senha,
                adm=adm
            )

            # Adicionar o novo gestor ao banco de dados
            db.session.add(novo_gestor)
            db.session.commit()

            # Define a mensagem de confirmação
            message = "Gestor cadastrado com sucesso!"

        except Exception as e:
            # Se ocorrer um erro ao cadastrar o gestor, faça um rollback
            db.session.rollback()
            message = f"Erro ao cadastrar o gestor: {str(e)}"

    return render_template('adm_sistema.html', message=message)

