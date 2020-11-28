from functools import wraps
from flask import request, redirect, url_for, render_template, flash, \
    abort, jsonify,session, g
from baboo import app, db
from baboo.models import User, Post_Data, Follow

#ログイン認証
def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if g.user is None:
            flash('ログインしてね')
            return redirect(url_for('login'), next=request.path)
        return f(*args, **kwargs)
    return decorated_view

@app.before_request
def load_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user_id = None
    else:
        g.user = User.query.get(session['user_id'])


#トップ（ログイン時はタイムラインにリダイレクト）
@app.route('/')
def top():
    if not ('user_id' in session):
        return render_template('top.html')

    user_id = session['user_id']
    user = User.query.get(user_id)
    return redirect(url_for('timeline'))

#ログインフォームを表示かつログイン処理
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user, authenticated = User.authenticate(db.session.query,
                                                request.form['email'],
                                                request.form['password']
                                                )
        if authenticated:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            flash('ログインしたよ')
            return redirect(url_for('timeline'))
        else:
            flash('ログインに失敗したよ')
    return render_template('login.html')

#ログアウト処理
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash('ログアウトしたよ')
    return redirect(url_for('top'))

#会員登録処理と登録フォームを表示
@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()

        user = User.query.filter_by(name=request.form['name']).first()
        follow = Follow(
            follower_id=user.id,
            follow_id=user.id
        )
        db.session.add(follow)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('edit.html')

#ユーザーの書き込みを表示
@app.route('/user/<string:user_name>')
def user_baboo(user_name):
    other = User.query.filter_by(name=user_name).first()
    other_baboo = Post_Data.query.filter_by(name=user_name).all()

    follow_list = []
    if 'user_id' in session:
        follow_relationships = Follow.query.filter_by(follower_id=session['user_id']).all()
        for follow in follow_relationships:
            follow_list.append(follow.follow_id)

    return render_template(
        'user_baboo.html',
        other_baboo=other_baboo,
        other=other,
        follow_list=follow_list
    )

#ユーザー情報の詳細を表示
@app.route('/user/detail')
@login_required
def user_detail():
    user = User.query.get(session['user_id'])
    return render_template('detail.html', user=user)

#ユーザー情報を編集
@app.route('/user/edit/', methods=['GET' ,'POST'])
@login_required
def user_edit():
    if not ('user_id' in session):
        abort(404)

    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        flash('名前とEmailアドレスを変更したよ')
        ps = request.form['password'].strip()
        if ps:
            user.password = ps
            flash('パスワードを変更したよ')
        else:
            flash('パスワードは変更してないよ')

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('user_detail', user_name=user.name))

    return render_template('edit.html', user=user)

''' jsを使って消去できなかった　
@app.route('/users/delete/', methods=['DELETE'])
def user_delete():
    user = User.query.get(session['user_id'])
    if user is None:
        response = jsonify({'status': 'Not Found'})
        response.status_code = 404
        return response
    db.session.delete(user)
    db.session.commit()
    session.pop('user_id', None)
    return jsonify({'status': 'OK'})
'''

#アカウント消去
#Flaskのチュートリアルでは上の書き方をしていたので、下の書き方ではなにかまずいのかもしれない
@app.route('/user/delete/')
@login_required
def user_delete():
    user = User.query.get(session['user_id'])
    if user is None:
        flash('ユーザーが見つかりません')
        return redirect(url_for('top'))

    follower = Follow.query.filter_by(follower_id=user.id).delete()
    follow = Follow.query.filter_by(follow_id=user.id).delete()
    data = Post_Data.query.filter_by(user_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash('アカウントを消去しました')
    return redirect(url_for('top'))

# フォローの一覧を表示
@app.route('/follow')
@login_required
def follows():
    follow = Follow.query.filter_by(follower_id=session['user_id'])
    others = []
    for other in follow:
        if other.id == session['user_id']:
            continue
        user = User.query.filter_by(id=other.follow_id).first()
        others.append(user)
    return render_template('follows.html', others=others)

# フォロワーの一覧を表示
@app.route('/follower')
@login_required
def followers():
    follower = Follow.query.filter_by(follow_id=session['user_id'])
    others = []
    for other in follower:
        if other.id == session['user_id']:
            continue
        user = User.query.filter_by(id=other.follower_id).first()
        others.append(user)
    return render_template('followers.html', others=others)

#フォローする
@app.route('/follow/<string:user_name>/add')
@login_required
def follow_add(user_name):
    follow = Follow(
        follower_id=session['user_id'],
        follow_id=User.query.filter_by(name=user_name).first().id
    )
    db.session.add(follow)
    db.session.commit()
    flash('フォローしました')
    return redirect(url_for('user_baboo', user_name=user_name))

#フォローを取り消す
@app.route('/follow/<string:user_name>/remove')
@login_required
def follow_remove(user_name):
    other = User.query.filter_by(name=user_name).first()
    follow = Follow.query.filter(db.and_(Follow.follower_id==session['user_id'], Follow.follow_id==other.id)).first()
    if follow is None:
        flash('フォローしていないよ')
    db.session.delete(follow)
    db.session.commit()
    flash('フォロー解除したよ')
    return redirect(url_for('user_baboo', user_name=user_name))

#書き込む
@app.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        data = Post_Data(
            user_id=user.id,
            name=user.name,
            text=request.form['text']
        )
        db.session.add(data)
        db.session.commit()
        flash('バブった！！')
        return redirect(url_for('timeline'))
    return render_template('write.html', user=user)

#書き込みを取り消す
@app.route('/write/<int:data_id>/remove/')
@login_required
def write_remove(data_id):
    data = Post_Data.query.get(data_id)
    if data is None:
        flash('そのbabooは存在しません')
        return redirect(url_for('top'))

    user = User.query.get(session['user_id'])
    if not user.name == data.name:
        flash('本人じゃないよ')
        return redirect(url_for('top'))
    db.session.delete(data)
    db.session.commit()
    flash('消去しました')
    return redirect(url_for('top'))

#タイムラインを表示（フォローをした人の書き込みを表示）
@app.route('/timeline/')
@login_required
def timeline():
    user = User.query.get(session['user_id'])

    follow = Follow.query.filter_by(follower_id=user.id).all()
    follows_list = []
    for rel in follow:
        follows_list.append(rel.follow_id)

    data = Post_Data.query.filter(Post_Data.user_id.in_(follows_list)).all()

    return render_template(
        'timeline.html',
        user=user,
        data=data
    )

#ユーザーリストを表示
@app.route('/userlist/')
def userlist():
    others = User.query.all()
    return render_template('userlist.html', others=others)