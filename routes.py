from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from models import Usuario, Movimentacao

main = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@main.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar = request.form.get('confirmar_senha', '')

        if not nome or not email or not senha:
            flash('Preencha todos os campos.', 'danger')
            return render_template('cadastro.html')

        if senha != confirmar:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro.html')

        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('cadastro.html')

        usuario = Usuario(nome=nome, email=email)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()

        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('cadastro.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.check_senha(senha):
            flash('E-mail ou senha incorretos.', 'danger')
            return render_template('login.html')

        login_user(usuario)
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    movimentacoes = Movimentacao.query.filter_by(usuario_id=current_user.id).all()

    total_receitas = sum(m.valor for m in movimentacoes if m.tipo == 'receita')
    total_despesas = sum(m.valor for m in movimentacoes if m.tipo == 'despesa')
    saldo = total_receitas - total_despesas

    recentes = (Movimentacao.query
                .filter_by(usuario_id=current_user.id)
                .order_by(Movimentacao.data.desc())
                .limit(5)
                .all())

    return render_template('dashboard.html',
                           total_receitas=total_receitas,
                           total_despesas=total_despesas,
                           saldo=saldo,
                           recentes=recentes,
                           mes_atual=mes_atual,
                           ano_atual=ano_atual)


@main.route('/movimentacoes')
@login_required
def movimentacoes():
    tipo = request.args.get('tipo', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')

    query = Movimentacao.query.filter_by(usuario_id=current_user.id)

    if tipo in ('receita', 'despesa'):
        query = query.filter_by(tipo=tipo)

    if data_inicio:
        query = query.filter(Movimentacao.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())

    if data_fim:
        query = query.filter(Movimentacao.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())

    lista = query.order_by(Movimentacao.data.desc()).all()

    return render_template('movimentacoes.html', movimentacoes=lista,
                           tipo=tipo, data_inicio=data_inicio, data_fim=data_fim)


@main.route('/movimentacoes/nova', methods=['GET', 'POST'])
@login_required
def nova_movimentacao():
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor = request.form.get('valor')
        data_str = request.form.get('data')

        if not all([tipo, categoria, descricao, valor, data_str]):
            flash('Preencha todos os campos.', 'danger')
            return render_template('form_movimentacao.html', acao='Nova')

        try:
            valor = float(valor.replace(',', '.'))
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Valor ou data inválidos.', 'danger')
            return render_template('form_movimentacao.html', acao='Nova')

        mov = Movimentacao(
            usuario_id=current_user.id,
            tipo=tipo,
            categoria=categoria,
            descricao=descricao,
            valor=valor,
            data=data
        )
        db.session.add(mov)
        db.session.commit()

        flash('Movimentação cadastrada com sucesso!', 'success')
        return redirect(url_for('main.movimentacoes'))

    return render_template('form_movimentacao.html', acao='Nova', movimentacao=None)


@main.route('/movimentacoes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_movimentacao(id):
    mov = Movimentacao.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria', '').strip()
        descricao = request.form.get('descricao', '').strip()
        valor = request.form.get('valor')
        data_str = request.form.get('data')

        if not all([tipo, categoria, descricao, valor, data_str]):
            flash('Preencha todos os campos.', 'danger')
            return render_template('form_movimentacao.html', acao='Editar', movimentacao=mov)

        try:
            mov.valor = float(valor.replace(',', '.'))
            mov.data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Valor ou data inválidos.', 'danger')
            return render_template('form_movimentacao.html', acao='Editar', movimentacao=mov)

        mov.tipo = tipo
        mov.categoria = categoria
        mov.descricao = descricao
        db.session.commit()

        flash('Movimentação atualizada!', 'success')
        return redirect(url_for('main.movimentacoes'))

    return render_template('form_movimentacao.html', acao='Editar', movimentacao=mov)


@main.route('/movimentacoes/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_movimentacao(id):
    mov = Movimentacao.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    db.session.delete(mov)
    db.session.commit()
    flash('Movimentação excluída.', 'info')
    return redirect(url_for('main.movimentacoes'))


@main.route('/relatorio')
@login_required
def relatorio():
    mes = request.args.get('mes', date.today().month, type=int)
    ano = request.args.get('ano', date.today().year, type=int)

    movs = (Movimentacao.query
            .filter_by(usuario_id=current_user.id)
            .filter(db.extract('month', Movimentacao.data) == mes)
            .filter(db.extract('year', Movimentacao.data) == ano)
            .order_by(Movimentacao.data)
            .all())

    total_receitas = sum(m.valor for m in movs if m.tipo == 'receita')
    total_despesas = sum(m.valor for m in movs if m.tipo == 'despesa')
    saldo = total_receitas - total_despesas

    return render_template('relatorio.html',
                           movimentacoes=movs,
                           total_receitas=total_receitas,
                           total_despesas=total_despesas,
                           saldo=saldo,
                           mes=mes,
                           ano=ano)


@main.route('/api/grafico')
@login_required
def api_grafico():
    ano = request.args.get('ano', date.today().year, type=int)

    receitas_mes = [0.0] * 12
    despesas_mes = [0.0] * 12

    movs = (Movimentacao.query
            .filter_by(usuario_id=current_user.id)
            .filter(db.extract('year', Movimentacao.data) == ano)
            .all())

    for m in movs:
        i = m.data.month - 1
        if m.tipo == 'receita':
            receitas_mes[i] += m.valor
        else:
            despesas_mes[i] += m.valor

    return jsonify({
        'receitas': receitas_mes,
        'despesas': despesas_mes
    })
