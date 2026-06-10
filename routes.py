import csv
import io
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from extensions import db, login_manager
from models import Usuario, Movimentacao

main = Blueprint('main', __name__)

PER_PAGE = 15


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


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

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
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

    total_receitas = db.session.query(func.sum(Movimentacao.valor))\
        .filter_by(usuario_id=current_user.id, tipo='receita').scalar() or Decimal(0)
    total_despesas = db.session.query(func.sum(Movimentacao.valor))\
        .filter_by(usuario_id=current_user.id, tipo='despesa').scalar() or Decimal(0)
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
                           mes_atual=hoje.month,
                           ano_atual=hoje.year)


@main.route('/movimentacoes')
@login_required
def movimentacoes():
    tipo = request.args.get('tipo', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    page = request.args.get('page', 1, type=int)

    query = Movimentacao.query.filter_by(usuario_id=current_user.id)

    if tipo in ('receita', 'despesa'):
        query = query.filter_by(tipo=tipo)

    try:
        if data_inicio:
            query = query.filter(Movimentacao.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        if data_fim:
            query = query.filter(Movimentacao.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    except ValueError:
        flash('Data inválida no filtro.', 'warning')

    pagination = query.order_by(Movimentacao.data.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )

    return render_template('movimentacoes.html',
                           movimentacoes=pagination.items,
                           pagination=pagination,
                           tipo=tipo,
                           data_inicio=data_inicio,
                           data_fim=data_fim)


def _parse_form_movimentacao(form):
    tipo = form.get('tipo')
    categoria = form.get('categoria', '').strip()
    descricao = form.get('descricao', '').strip()
    valor_str = form.get('valor', '')
    data_str = form.get('data', '')

    if not all([tipo, categoria, descricao, valor_str, data_str]):
        return None, 'Preencha todos os campos.'

    try:
        valor = Decimal(valor_str.replace(',', '.'))
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (InvalidOperation, ValueError):
        return None, 'Valor ou data inválidos.'

    return {'tipo': tipo, 'categoria': categoria, 'descricao': descricao, 'valor': valor, 'data': data}, None


@main.route('/movimentacoes/nova', methods=['GET', 'POST'])
@login_required
def nova_movimentacao():
    if request.method == 'POST':
        dados, erro = _parse_form_movimentacao(request.form)
        if erro:
            flash(erro, 'danger')
            return render_template('form_movimentacao.html', acao='Nova')

        db.session.add(Movimentacao(usuario_id=current_user.id, **dados))
        db.session.commit()
        flash('Movimentação cadastrada com sucesso!', 'success')
        return redirect(url_for('main.movimentacoes'))

    return render_template('form_movimentacao.html', acao='Nova', movimentacao=None)


@main.route('/movimentacoes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_movimentacao(id):
    mov = Movimentacao.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    if request.method == 'POST':
        dados, erro = _parse_form_movimentacao(request.form)
        if erro:
            flash(erro, 'danger')
            return render_template('form_movimentacao.html', acao='Editar', movimentacao=mov)

        for campo, val in dados.items():
            setattr(mov, campo, val)
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

    total_receitas = db.session.query(func.sum(Movimentacao.valor))\
        .filter_by(usuario_id=current_user.id, tipo='receita')\
        .filter(db.extract('month', Movimentacao.data) == mes)\
        .filter(db.extract('year', Movimentacao.data) == ano)\
        .scalar() or Decimal(0)

    total_despesas = db.session.query(func.sum(Movimentacao.valor))\
        .filter_by(usuario_id=current_user.id, tipo='despesa')\
        .filter(db.extract('month', Movimentacao.data) == mes)\
        .filter(db.extract('year', Movimentacao.data) == ano)\
        .scalar() or Decimal(0)

    saldo = total_receitas - total_despesas

    return render_template('relatorio.html',
                           movimentacoes=movs,
                           total_receitas=total_receitas,
                           total_despesas=total_despesas,
                           saldo=saldo,
                           mes=mes,
                           ano=ano)


@main.route('/relatorio/exportar-csv')
@login_required
def exportar_csv():
    mes = request.args.get('mes', date.today().month, type=int)
    ano = request.args.get('ano', date.today().year, type=int)

    movs = (Movimentacao.query
            .filter_by(usuario_id=current_user.id)
            .filter(db.extract('month', Movimentacao.data) == mes)
            .filter(db.extract('year', Movimentacao.data) == ano)
            .order_by(Movimentacao.data)
            .all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor'])
    for m in movs:
        writer.writerow([m.data.strftime('%d/%m/%Y'), m.tipo, m.categoria, m.descricao, str(m.valor)])

    filename = f'relatorio_{ano}_{mes:02d}.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


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
            receitas_mes[i] += float(m.valor)
        else:
            despesas_mes[i] += float(m.valor)

    return jsonify({'receitas': receitas_mes, 'despesas': despesas_mes})


@main.route('/api/grafico-categorias')
@login_required
def api_grafico_categorias():
    mes = request.args.get('mes', date.today().month, type=int)
    ano = request.args.get('ano', date.today().year, type=int)
    tipo = request.args.get('tipo', 'despesa')

    rows = (db.session.query(Movimentacao.categoria, func.sum(Movimentacao.valor))
            .filter_by(usuario_id=current_user.id, tipo=tipo)
            .filter(db.extract('month', Movimentacao.data) == mes)
            .filter(db.extract('year', Movimentacao.data) == ano)
            .group_by(Movimentacao.categoria)
            .all())

    return jsonify({
        'labels': [r[0] for r in rows],
        'valores': [float(r[1]) for r in rows]
    })
