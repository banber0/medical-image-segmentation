"""
医学影像分割系统 - Flask后端服务
整合Unet模型推理和训练
"""
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import datetime
import uuid
import threading
import json
import io
import base64
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

app = Flask(__name__)

# CORS配置 - 在所有路由之前初始化
# 关键：先拦截 OPTIONS 预检请求，直接返回带完整CORS头的响应
@app.before_request
def handle_preflight():
    """处理OPTIONS预检请求，浏览器CORS预检必须返回正确的CORS头"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

@app.after_request
def after_request(response):
    # 使用 set 而非 add，避免与 before_request 的 header 重复
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

# ================= 数据库配置区 =================
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'mysql+pymysql://root@127.0.0.1:3306/medical_db?charset=utf8mb4'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 连接池配置，避免长时间训练导致连接断开
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {} if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:') else {
    'pool_pre_ping': True,      # 连接前检测连接是否有效
    'pool_recycle': 300,         # 5分钟回收连接
    'pool_size': 10,            # 连接池大小
    'max_overflow': 20,         # 最大溢出连接数
}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MODEL_FOLDER'] = 'models/weights'
app.config['DATASET_FOLDER'] = 'datasets'

# 创建必要目录
for folder in [app.config['UPLOAD_FOLDER'], app.config['MODEL_FOLDER'], app.config['DATASET_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

db = SQLAlchemy(app)

# ================= 数据库模型定义 =================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    organization = db.Column(db.String(100))
    user_type = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Dataset(db.Model):
    __tablename__ = 'datasets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))
    size = db.Column(db.String(20))
    file_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Model(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'))
    config = db.Column(db.Text)
    model_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class TrainingHistory(db.Model):
    __tablename__ = 'training_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'))
    status = db.Column(db.String(20))
    logs = db.Column(db.Text)
    metrics = db.Column(db.Text)
    current_epoch = db.Column(db.Integer, default=0)
    total_epochs = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    image_path = db.Column(db.String(255))
    label_path = db.Column(db.String(255))
    prediction_path = db.Column(db.String(255))
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    iou = db.Column(db.Float)
    dice = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    feedback = db.Column(db.Text)
    score = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class SegmentationHistory(db.Model):
    __tablename__ = 'segmentation_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    image_path = db.Column(db.String(255))
    result_path = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

# 创建数据库表
with app.app_context():
    db.create_all()

# ================= 辅助函数 =================
def save_log(user_id, action, description):
    log = SystemLog(user_id=user_id, action=action, description=description)
    db.session.add(log)
    db.session.commit()

# ================= 用户接口 =================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'success': False, 'message': '用户名已被注册'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, user_type='user')
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': '注册成功！'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        save_log(user.id, '登录', f'用户 {username} 登录系统')
        return jsonify({
            'success': True,
            'message': '登录成功',
            'username': user.username,
            'user_id': user.id,
            'user_type': user.user_type
        })
    else:
        return jsonify({'success': False, 'message': '账号或密码错误'}), 401

@app.route('/api/user/profile', methods=['GET', 'POST'])
def user_profile():
    if request.method == 'GET':
        username = request.args.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone,
                    'organization': user.organization,
                    'userType': user.user_type,
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
                }
            })
        else:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
    elif request.method == 'POST':
        data = request.json
        username = data.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            user.email = data.get('email', user.email)
            user.phone = data.get('phone', user.phone)
            user.organization = data.get('organization', user.organization)
            db.session.commit()
            return jsonify({'success': True, 'message': '个人信息更新成功'})
        else:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

@app.route('/api/user/change-password', methods=['POST'])
def change_password():
    data = request.json
    username = request.args.get('username')
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, old_password):
        user.password = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': '密码修改成功'})
    else:
        return jsonify({'success': False, 'message': '原密码错误'}), 401

# ================= 数据集接口 =================

@app.route('/api/datasets', methods=['GET', 'POST'])
def datasets():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if user_id:
            datasets = Dataset.query.filter_by(user_id=user_id).all()
        else:
            datasets = Dataset.query.all()
        return jsonify({
            'success': True,
            'datasets': [{
                'id': d.id,
                'name': d.name,
                'description': d.description,
                'type': d.type,
                'size': d.size,
                'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S') if d.created_at else ''
            } for d in datasets]
        })
    elif request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择文件'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '请选择文件'}), 400

        # 保存上传的压缩文件
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4()}_{filename}"
        dataset_dir = os.path.join(app.config['DATASET_FOLDER'], unique_name)
        os.makedirs(dataset_dir, exist_ok=True)

        file_path = os.path.join(dataset_dir, filename)
        file.save(file_path)

        # 解压文件
        import zipfile
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(dataset_dir)
            os.remove(file_path)
        except:
            pass  # 如果不是压缩文件，直接使用

        data = request.form
        dataset_size = sum([os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(dataset_dir) for f in fn])

        user_id_str = data.get('user_id', '')
        user_id = 1  # 默认用户ID
        if user_id_str and user_id_str != 'undefined':
            try:
                user_id = int(user_id_str)
            except:
                user_id = 1

        new_dataset = Dataset(
            name=data.get('name'),
            description=data.get('description'),
            type=data.get('type', 'image'),
            size=f"{dataset_size / (1024*1024):.2f}MB",
            file_path=dataset_dir,
            user_id=user_id
        )
        db.session.add(new_dataset)
        db.session.commit()

        save_log(user_id, '上传数据集', f'上传了数据集 {data.get("name")}')

        return jsonify({'success': True, 'message': '数据集上传成功', 'dataset_id': new_dataset.id})

@app.route('/api/datasets/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def dataset_detail(id):
    dataset = db.session.get(Dataset, id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    if request.method == 'GET':
        return jsonify({
            'success': True,
            'dataset': {
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'type': dataset.type,
                'size': dataset.size,
                'created_at': dataset.created_at.strftime('%Y-%m-%d %H:%M:%S') if dataset.created_at else ''
            }
        })
    elif request.method == 'PUT':
        data = request.json
        dataset.name = data.get('name', dataset.name)
        dataset.description = data.get('description', dataset.description)
        dataset.type = data.get('type', dataset.type)
        db.session.commit()
        return jsonify({'success': True, 'message': '数据集更新成功'})
    elif request.method == 'DELETE':
        if os.path.exists(dataset.file_path):
            shutil.rmtree(dataset.file_path)
        db.session.delete(dataset)
        db.session.commit()
        return jsonify({'success': True, 'message': '数据集删除成功'})

@app.route('/api/datasets/<int:id>/files', methods=['GET'])
def dataset_files(id):
    """获取数据集文件列表"""
    dataset = db.session.get(Dataset, id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    files = []
    images_dir = os.path.join(dataset.file_path, 'images')
    masks_dir = os.path.join(dataset.file_path, 'masks')

    if os.path.exists(images_dir):
        for f in os.listdir(images_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif')):
                files.append({'name': f, 'type': 'image'})

    return jsonify({'success': True, 'files': files})

# ================= 模型接口 =================

@app.route('/api/models', methods=['GET', 'POST'])
def models():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if user_id:
            models = Model.query.filter_by(user_id=user_id).all()
        else:
            models = Model.query.all()
        return jsonify({
            'success': True,
            'models': [{
                'id': m.id,
                'name': m.name,
                'type': m.type,
                'status': m.status,
                'model_path': m.model_path,
                'created_at': m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else ''
            } for m in models]
        })
    elif request.method == 'POST':
        data = request.json
        new_model = Model(
            name=data.get('name'),
            type=data.get('type', 'unet'),
            dataset_id=data.get('dataset_id'),
            config=data.get('config', '{}'),
            user_id=data.get('user_id')
        )
        db.session.add(new_model)
        db.session.commit()
        return jsonify({'success': True, 'message': '模型创建成功', 'model_id': new_model.id})

@app.route('/api/models/upload', methods=['POST'])
def upload_model():
    """上传模型文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '请选择文件'}), 400

    # 检查文件类型
    allowed_extensions = {'.pth', '.pt', '.h5', '.onnx', '.pb', '.tflite'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'message': f'不支持的文件类型，仅支持: {", ".join(allowed_extensions)}'}), 400

    name = request.form.get('name', '')
    description = request.form.get('description', '')
    model_type = request.form.get('type', 'unet')
    dataset_id = request.form.get('dataset_id')
    user_id = request.form.get('user_id', '1')

    try:
        user_id = int(user_id) if user_id else 1
    except:
        user_id = 1

    try:
        dataset_id = int(dataset_id) if dataset_id else None
    except:
        dataset_id = None

    # 创建模型目录
    model_dir = os.path.join(app.config['MODEL_FOLDER'], f"upload_{uuid.uuid4()}")
    os.makedirs(model_dir, exist_ok=True)

    # 保存模型文件
    filename = secure_filename(file.filename)
    model_path = os.path.join(model_dir, filename)
    file.save(model_path)

    # 获取文件大小
    file_size = os.path.getsize(model_path)

    # 创建模型记录
    new_model = Model(
        name=name or filename,
        type=model_type,
        dataset_id=dataset_id,
        model_path=model_path,
        status='uploaded',  # 上传的模型状态标记为 uploaded
        user_id=user_id
    )
    db.session.add(new_model)
    db.session.commit()

    save_log(user_id, '上传模型', f'上传了模型 {name or filename}')

    return jsonify({
        'success': True,
        'message': '模型上传成功',
        'model_id': new_model.id,
        'model_path': model_path,
        'size': f"{file_size / (1024*1024):.2f}MB"
    })

@app.route('/api/models/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def model_detail(id):
    model = db.session.get(Model, id)
    if not model:
        return jsonify({'success': False, 'message': '模型不存在'}), 404

    if request.method == 'GET':
        return jsonify({
            'success': True,
            'model': {
                'id': model.id,
                'name': model.name,
                'type': model.type,
                'dataset_id': model.dataset_id,
                'config': model.config,
                'model_path': model.model_path,
                'status': model.status,
                'created_at': model.created_at.strftime('%Y-%m-%d %H:%M:%S') if model.created_at else ''
            }
        })
    elif request.method == 'DELETE':
        print(f"[DELETE] 收到删除模型请求: id={id}, name={model.name}")
        try:
            # 1. 先删除关联的训练历史记录
            deleted_th = TrainingHistory.query.filter_by(model_id=id).delete()
            print(f"[DELETE] 已删除 {deleted_th} 条训练历史记录")
            # 2. 删除关联的分割历史记录
            deleted_sh = SegmentationHistory.query.filter_by(model_id=id).delete()
            print(f"[DELETE] 已删除 {deleted_sh} 条分割历史记录")
            # 3. 删除关联的评估记录
            deleted_ev = Evaluation.query.filter_by(model_id=id).delete()
            print(f"[DELETE] 已删除 {deleted_ev} 条评估记录")
            # 4. 删除关联的反馈记录
            deleted_fb = Feedback.query.filter_by(model_id=id).delete()
            print(f"[DELETE] 已删除 {deleted_fb} 条反馈记录")
            # 5. 删除模型权重文件目录
            if model.model_path and os.path.exists(model.model_path):
                model_dir = os.path.dirname(model.model_path)
                if os.path.exists(model_dir):
                    shutil.rmtree(model_dir)
                    print(f"[DELETE] 已删除模型文件目录: {model_dir}")
            # 6. 最后删除模型数据库记录
            db.session.delete(model)
            db.session.commit()
            print(f"[DELETE] 模型 id={id} 删除完成")
            return jsonify({'success': True, 'message': '模型删除成功'})
        except Exception as e:
            db.session.rollback()
            print(f"[DELETE] 删除失败: {str(e)}")
            return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# ================= 模型训练接口 =================

@app.route('/api/models/train', methods=['POST'])
def train_model():
    data = request.json
    model_id = data.get('model_id')
    dataset_id = data.get('dataset_id')
    user_id = data.get('user_id')
    config = data.get('config', {})

    model = db.session.get(Model, model_id)
    dataset = db.session.get(Dataset, dataset_id)

    if not model or not dataset:
        return jsonify({'success': False, 'message': '模型或数据集不存在'}), 404

    # 立即提取所有需要的值为普通变量，避免后续访问SQLAlchemy对象属性
    dataset_path = dataset.file_path

    # 更新模型状态
    model.status = 'training'
    db.session.commit()

    # 创建训练历史
    training_history_new = TrainingHistory(
        model_id=model_id,
        dataset_id=dataset_id,
        status='running',
        user_id=user_id
    )
    db.session.add(training_history_new)
    db.session.commit()

    # 立即提取ID为普通变量
    new_training_id = training_history_new.id

    # 启动后台训练线程
    def train_in_background():
        # 在后台线程中使用应用上下文
        with app.app_context():
            # 使用普通变量而非SQLAlchemy对象
            _model_id = model_id
            _training_id = new_training_id
            _config = config
            _dataset_path = dataset_path

            try:
                from models.train import train_model

                # 重新查询数据库获取最新数据
                model = db.session.get(Model, _model_id)
                training_history = db.session.get(TrainingHistory, _training_id)

                # 训练配置
                train_config = {
                    'epochs': _config.get('epochs', 10),
                    'batch_size': _config.get('batch_size', 4),
                    'learning_rate': _config.get('learning_rate', 0.001),
                    'val_split': _config.get('val_split', 0.2)
                }

                # 保存总epoch数
                training_history.total_epochs = train_config['epochs']
                db.session.commit()

                # 进度回调函数（外层已有app_context，无需嵌套）
                def update_progress(epoch, total):
                    try:
                        history = db.session.get(TrainingHistory, _training_id)
                        if history:
                            history.current_epoch = epoch
                            db.session.commit()
                    except Exception as e:
                        print(f"进度更新失败: {e}")

                output_dir = os.path.join(app.config['MODEL_FOLDER'], str(_model_id))
                result = train_model(_dataset_path, output_dir, train_config, _training_id, update_progress)

                # 训练完成，更新最终状态
                model = db.session.get(Model, _model_id)
                training_history = db.session.get(TrainingHistory, _training_id)

                if result.get('success'):
                    model.model_path = result.get('best_model')
                    model.status = 'completed'
                    training_history.status = 'completed'
                    training_history.current_epoch = training_history.total_epochs
                    training_history.metrics = json.dumps(result.get('history', {}))
                elif result.get('stopped'):
                    # 用户手动停止训练
                    model.status = 'stopped'
                    training_history.status = 'stopped'
                    training_history.logs = '训练已被用户停止'
                else:
                    model.status = 'failed'
                    training_history.status = 'failed'
                    training_history.logs = result.get('error', 'Unknown error')
                    print(f"训练失败详情: {result}")

                db.session.commit()
                print(f"训练完成，模型 {_model_id} 状态: {model.status}")

            except Exception as e:
                import traceback
                print(f"训练错误: {e}")
                print(f"详细错误: {traceback.format_exc()}")
                model = db.session.get(Model, _model_id)
                training_history = db.session.get(TrainingHistory, _training_id)
                if model:
                    model.status = 'failed'
                if training_history:
                    training_history.status = 'failed'
                    training_history.logs = str(e)
                db.session.commit()

    thread = threading.Thread(target=train_in_background)
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': '模型训练已启动', 'training_id': new_training_id})

@app.route('/api/models/train/status/<int:training_id>', methods=['GET'])
def training_status(training_id):
    """获取训练状态"""
    history = db.session.get(TrainingHistory, training_id)
    if not history:
        return jsonify({'success': False, 'message': '训练记录不存在'}), 404

    model = db.session.get(Model, history.model_id)

    return jsonify({
        'success': True,
        'status': history.status,
        'model_status': model.status if model else 'unknown',
        'metrics': json.loads(history.metrics) if history.metrics else {},
        'logs': history.logs,
        'current_epoch': history.current_epoch or 0,
        'total_epochs': history.total_epochs or 0
    })

@app.route('/api/models/train/stop/<int:training_id>', methods=['POST'])
def stop_training_api(training_id):
    """停止训练"""
    history = db.session.get(TrainingHistory, training_id)
    if not history:
        return jsonify({'success': False, 'message': '训练记录不存在'}), 404

    # 只允许停止正在运行的训练
    if history.status not in ['running', 'pending']:
        return jsonify({'success': False, 'message': '训练已完成或已停止'}), 400

    # 调用训练模块的停止函数
    try:
        from models.train import stop_training
        stop_training(training_id)
        return jsonify({'success': True, 'message': '停止训练请求已发送'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ================= 模型评估接口 =================

@app.route('/api/models/evaluate', methods=['POST'])
def evaluate_model():
    """单样例评估"""
    if 'image' not in request.files or 'label' not in request.files:
        return jsonify({'success': False, 'message': '请上传图片和标签'}), 400

    image = request.files['image']
    label = request.files['label']
    model_id = request.form.get('model_id')
    user_id_str = request.form.get('user_id', '1')

    # 处理 user_id
    user_id = 1
    if user_id_str and user_id_str != 'undefined':
        try:
            user_id = int(user_id_str)
        except:
            user_id = 1

    if image.filename == '' or label.filename == '':
        return jsonify({'success': False, 'message': '请上传图片和标签'}), 400

    # 保存文件
    image_filename = secure_filename(image.filename)
    label_filename = secure_filename(label.filename)

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{image_filename}")
    label_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{label_filename}")

    image.save(image_path)
    label.save(label_path)

    # 加载模型进行预测
    model = db.session.get(Model, model_id)
    if not model or not model.model_path or not os.path.exists(model.model_path):
        return jsonify({'success': False, 'message': '模型不存在或未训练完成'}), 400

    try:
        from models.inference import inference
        from PIL import Image
        import numpy as np

        # 执行推理
        result = inference(image_path, model_path=model.model_path)

        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error')}), 400

        mask = result.get('mask')

        # 保存预测结果
        prediction_filename = f"pred_{uuid.uuid4()}.png"
        prediction_path = os.path.join(app.config['UPLOAD_FOLDER'], prediction_filename)

        pred_img = Image.fromarray(mask)
        pred_img.save(prediction_path)

        # 计算评估指标
        label_img = Image.open(label_path).convert('L')
        label_array = np.array(label_img.resize((256, 256)))
        pred_array = mask

        # 归一化
        label_array = (label_array > 127).astype(np.float32)
        pred_array = (pred_array > 127).astype(np.float32)

        # 计算指标
        intersection = np.sum(label_array * pred_array)
        label_sum = np.sum(label_array)
        pred_sum = np.sum(pred_array)

        dice = (2 * intersection + 1) / (label_sum + pred_sum + 1)
        iou = (intersection + 1) / (label_sum + pred_sum - intersection + 1)
        precision = (intersection + 1) / (pred_sum + 1)
        recall = (intersection + 1) / (label_sum + 1)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)
        accuracy = np.mean(label_array == pred_array)

        # 创建评估记录
        evaluation = Evaluation(
            model_id=int(model_id),
            image_path=image_path,
            label_path=label_path,
            prediction_path=prediction_path,
            accuracy=float(accuracy),
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1),
            iou=float(iou),
            dice=float(dice),
            user_id=user_id
        )
        db.session.add(evaluation)
        db.session.commit()

        # 返回 base64 编码的预测结果图片
        import base64
        with open(prediction_path, 'rb') as f:
            pred_base64 = base64.b64encode(f.read()).decode()

        return jsonify({
            'success': True,
            'message': '模型评估成功',
            'evaluation_id': evaluation.id,
            'result_image': pred_base64,
            'metrics': {
                'accuracy': f'{accuracy*100:.2f}%',
                'precision': f'{precision*100:.2f}%',
                'recall': f'{recall*100:.2f}%',
                'f1_score': f'{f1*100:.2f}%',
                'iou': f'{iou*100:.2f}%',
                'dice': f'{dice*100:.2f}%'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'评估失败: {str(e)}'}), 500

# ================= 影像分割接口 =================

@app.route('/api/segmentation', methods=['POST'])
def segmentation():
    """执行影像分割"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '请上传图片'}), 400

    image = request.files['image']
    model_id = request.form.get('model_id')
    user_id_str = request.form.get('user_id', '1')

    # 处理 user_id
    user_id = 1
    if user_id_str and user_id_str != 'undefined':
        try:
            user_id = int(user_id_str)
        except:
            user_id = 1

    if image.filename == '':
        return jsonify({'success': False, 'message': '请上传图片'}), 400

    # 保存文件
    image_filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{image_filename}")
    image.save(image_path)

    # 加载模型
    model = db.session.get(Model, model_id)
    if not model or not model.model_path or not os.path.exists(model.model_path):
        return jsonify({'success': False, 'message': '模型不存在或未训练完成'}), 400

    try:
        from models.inference import inference

        # 执行推理
        result = inference(image_path, model_path=model.model_path)

        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error')}), 400

        mask = result.get('mask')

        # 保存分割结果
        result_filename = f"seg_{uuid.uuid4()}.png"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)

        from PIL import Image
        result_img = Image.fromarray(mask)
        result_img.save(result_path)

        # 创建分割历史记录
        history = SegmentationHistory(
            model_id=int(model_id),
            image_path=image_path,
            result_path=result_path,
            user_id=user_id
        )
        db.session.add(history)
        db.session.commit()

        # 返回base64编码的结果图片
        import base64
        buffered = io.BytesIO()
        result_img.save(buffered, format='PNG')
        result_base64 = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'message': '影像分割成功',
            'history_id': history.id,
            'result_image': result_base64
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'分割失败: {str(e)}'}), 500

# ================= 历史记录接口 =================

@app.route('/api/history/segmentation', methods=['GET'])
def segmentation_history():
    user_id = request.args.get('user_id')
    if user_id:
        history = SegmentationHistory.query.filter_by(user_id=user_id).all()
    else:
        history = SegmentationHistory.query.all()
    return jsonify({
        'success': True,
        'history': [{
            'id': h.id,
            'modelName': db.session.get(Model, h.model_id).name if h.model_id else '',
            'imageName': os.path.basename(h.image_path) if h.image_path else '',
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M:%S') if h.created_at else ''
        } for h in history]
    })

@app.route('/api/history/segmentation/<int:id>', methods=['GET'])
def segmentation_history_detail(id):
    """获取单条历史记录的详细信息，包含图片"""
    history = db.session.get(SegmentationHistory, id)
    if not history:
        return jsonify({'success': False, 'message': '记录不存在'}), 404

    result = {
        'id': history.id,
        'modelName': db.session.get(Model, history.model_id).name if history.model_id else '',
        'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S') if history.created_at else ''
    }

    # 添加 base64 图片数据
    try:
        if history.image_path and os.path.exists(history.image_path):
            with open(history.image_path, 'rb') as f:
                result['imageData'] = base64.b64encode(f.read()).decode()
        if history.result_path and os.path.exists(history.result_path):
            with open(history.result_path, 'rb') as f:
                result['resultData'] = base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"读取历史图片失败: {e}")

    return jsonify({
        'success': True,
        'detail': result
    })

@app.route('/api/history/training', methods=['GET'])
def training_history():
    user_id = request.args.get('user_id')
    if user_id:
        history = TrainingHistory.query.filter_by(user_id=user_id).all()
    else:
        history = TrainingHistory.query.all()
    return jsonify({
        'success': True,
        'history': [{
            'id': h.id,
            'modelName': db.session.get(Model, h.model_id).name if h.model_id else '',
            'datasetName': db.session.get(Dataset, h.dataset_id).name if h.dataset_id else '',
            'status': h.status,
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M:%S') if h.created_at else ''
        } for h in history]
    })

@app.route('/api/history/evaluation', methods=['GET'])
def evaluation_history():
    user_id = request.args.get('user_id')
    if user_id:
        history = Evaluation.query.filter_by(user_id=user_id).all()
    else:
        history = Evaluation.query.all()
    return jsonify({
        'success': True,
        'history': [{
            'id': h.id,
            'modelName': db.session.get(Model, h.model_id).name if h.model_id else '',
            'imageName': os.path.basename(h.image_path) if h.image_path else '',
            'accuracy': f'{h.accuracy*100:.1f}%' if h.accuracy else '0%',
            'precision': f'{h.precision*100:.1f}%' if h.precision else None,
            'recall': f'{h.recall*100:.1f}%' if h.recall else None,
            'f1_score': f'{h.f1_score*100:.1f}%' if h.f1_score else None,
            'iou': f'{h.iou*100:.1f}%' if h.iou else '0%',
            'dice': f'{h.dice*100:.1f}%' if h.dice else None,
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M:%S') if h.created_at else ''
        } for h in history]
    })

# ================= 反馈接口 =================

@app.route('/api/feedbacks', methods=['GET', 'POST'])
def feedbacks():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if user_id:
            feedbacks = Feedback.query.filter_by(user_id=user_id).all()
        else:
            feedbacks = Feedback.query.all()
        return jsonify({
            'success': True,
            'feedbacks': [{
                'id': f.id,
                'modelName': db.session.get(Model, f.model_id).name if f.model_id else '',
                'feedback': f.feedback,
                'score': f.score,
                'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S') if f.created_at else ''
            } for f in feedbacks]
        })
    elif request.method == 'POST':
        data = request.json
        new_feedback = Feedback(
            model_id=data.get('model_id'),
            feedback=data.get('feedback'),
            score=data.get('score'),
            user_id=data.get('user_id')
        )
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({'success': True, 'message': '反馈提交成功'})

# ================= 管理员接口 =================

def format_datetime(dt):
    """安全格式化时间"""
    if not dt:
        return ''
    if isinstance(dt, str):
        return dt
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

@app.route('/api/admin/users', methods=['GET', 'POST'])
def admin_users():
    if request.method == 'GET':
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [{
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'userType': u.user_type,
                'created_at': format_datetime(u.created_at)
            } for u in users]
        })
    elif request.method == 'POST':
        data = request.json
        hashed_password = generate_password_hash(data.get('password'))
        new_user = User(
            username=data.get('username'),
            password=hashed_password,
            email=data.get('email'),
            user_type=data.get('userType', 'user')
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True, 'message': '用户添加成功'})

@app.route('/api/admin/users/<int:id>', methods=['PUT', 'DELETE'])
def admin_user_detail(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    if request.method == 'PUT':
        data = request.json
        user.email = data.get('email', user.email)
        user.user_type = data.get('userType', user.user_type)
        db.session.commit()
        return jsonify({'success': True, 'message': '用户更新成功'})
    elif request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': '用户删除成功'})

@app.route('/api/admin/logs', methods=['GET'])
def admin_logs():
    logs = SystemLog.query.order_by(SystemLog.created_at.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'logs': [{
            'id': l.id,
            'user': db.session.get(User, l.user_id).username if l.user_id else '系统',
            'action': l.action,
            'description': l.description,
            'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else ''
        } for l in logs]
    })

# ================= 文件服务接口 =================

@app.route('/api/files/<path:filename>', methods=['GET'])
def serve_file(filename):
    """提供文件访问"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({'success': False, 'message': '文件不存在'}), 404

if __name__ == '__main__':
    print("=" * 50)
    print("医学影像分割系统后端服务启动中...")
    print("数据库: MySQL (medical_db)")
    print("模型目录: models/weights")
    print("上传目录: uploads")
    print("=" * 50)
    app.run(
        debug=os.environ.get('FLASK_DEBUG', '0') == '1',
        port=int(os.environ.get('PORT', '5000')),
        host=os.environ.get('HOST', '127.0.0.1'),
    )
