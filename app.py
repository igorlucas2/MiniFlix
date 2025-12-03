import os
import json
from datetime import datetime
from functools import lru_cache

from flask import (
    Flask,
    render_template,
    send_from_directory,
    abort,
    url_for,
    jsonify,
    request,
    redirect,
    flash,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from config import MEDIA_ROOT, PROGRESS_FILE, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY, AVATAR_UPLOAD_FOLDER, ALLOWED_AVATAR_EXTENSIONS
from media_indexer import (
    get_series_library,
    get_series_cards,
    find_episode_info,
)
from ia_episodios import gerar_descricao_episodio
from models import db, User

app = Flask(__name__)

# ======================
# Config Flask + DB
# ======================
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"  # rota para redirecionar quando não logado


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_avatar(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_AVATAR_EXTENSIONS


# ======================
# Cache da biblioteca
# ======================

@lru_cache(maxsize=1)
def get_cached_library():
    return get_series_library(MEDIA_ROOT)


@app.route("/reindex")
@login_required
def reindex():
    get_cached_library.cache_clear()
    _ = get_cached_library()
    return "Reindexado com sucesso."

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """
    Página de perfil: mostra e-mail, avatar e permite atualizar o avatar.
    """
    if request.method == "POST":
        file = request.files.get("avatar")
        if file and file.filename:
            if allowed_avatar(file.filename):
                os.makedirs(AVATAR_UPLOAD_FOLDER, exist_ok=True)
                ext = file.filename.rsplit(".", 1)[1].lower()
                filename = f"user_{current_user.id}.{ext}"
                path = os.path.join(AVATAR_UPLOAD_FOLDER, filename)
                file.save(path)

                current_user.avatar_filename = filename
                db.session.commit()
                flash("Avatar atualizado com sucesso!", "success")
            else:
                flash("Formato de imagem não suportado. Use jpg, jpeg, png ou webp.", "warning")
        else:
            flash("Nenhum arquivo selecionado.", "warning")

    return render_template("profile.html", user=current_user)

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if not current_user.check_password(current):
            flash("Senha atual incorreta.", "danger")
        elif not new or len(new) < 6:
            flash("A nova senha deve ter pelo menos 6 caracteres.", "warning")
        elif new != confirm:
            flash("A confirmação da senha não confere.", "warning")
        else:
            current_user.set_password(new)
            db.session.commit()
            flash("Senha alterada com sucesso.", "success")
            return redirect(url_for("profile"))

    return render_template("change_password.html")

# ======================
# Progresso / continuar assistindo (global por enquanto)
# ======================

def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return {}
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_progress(progress: dict):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def build_continue_list(library: dict):
    progress = load_progress()
    items = []

    poster_lookup = {name: data.get("poster") for name, data in library.items()}

    for rel_path, meta in progress.items():
        serie_name = meta.get("serie_name", "")
        episode_name = meta.get("episode_name", os.path.basename(rel_path))
        last_watched = meta.get("last_watched", "")

        items.append(
            {
                "relative_path": rel_path,
                "serie_name": serie_name,
                "episode_name": episode_name,
                "poster": poster_lookup.get(serie_name),
                "last_watched": last_watched,
            }
        )

    items.sort(key=lambda x: x["last_watched"], reverse=True)

    unique = []
    seen_series = set()
    for item in items:
        if item["serie_name"] in seen_series:
            continue
        seen_series.add(item["serie_name"])
        unique.append(item)

    return unique


def get_prev_and_next_episode(library, serie_name: str, relative_path: str):
    serie = library.get(serie_name)
    if not serie:
        return None, None

    seasons = serie.get("seasons", [])
    flat_eps = []

    for season in seasons:
        for ep in season.get("episodes", []):
            flat_eps.append(ep["relative_path"])

    rel_norm = relative_path.replace("\\", "/")

    try:
        idx = flat_eps.index(rel_norm)
    except ValueError:
        return None, None

    prev_ep = flat_eps[idx - 1] if idx > 0 else None
    next_ep = flat_eps[idx + 1] if idx < len(flat_eps) - 1 else None
    return prev_ep, next_ep


# ======================
# Rotas de autenticação
# ======================

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login realizado com sucesso.", "success")
            next_page = request.args.get("next") or url_for("index")
            return redirect(next_page)
        else:
            flash("E-mail ou senha inválidos.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Rota simples para criar usuários.
    Em produção, você pode travar isso ou proteger de outra forma.
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Preencha e-mail e senha.", "warning")
        else:
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash("Esse e-mail já está cadastrado.", "danger")
            else:
                user = User(email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Usuário criado com sucesso. Você já pode fazer login.", "success")
                return redirect(url_for("login"))

    return render_template("register.html")


# ======================
# Rotas principais (protegidas)
# ======================

@app.route("/")
@login_required
def index():
    library = get_cached_library()
    series_cards = get_series_cards(library)
    continue_list = build_continue_list(library)

    return render_template(
        "index.html",
        series_cards=series_cards,
        continue_list=continue_list,
    )


@app.route("/serie/<serie_name>")
@login_required
def serie_detail(serie_name):
    library = get_cached_library()
    serie = library.get(serie_name)
    if not serie:
        abort(404)

    poster = serie.get("poster")
    seasons = serie.get("seasons", [])

    return render_template(
        "serie.html",
        serie_name=serie_name,
        poster=poster,
        seasons=seasons,
    )


@app.route("/watch/<path:relative_path>")
@login_required
def watch(relative_path):
    rel_norm = relative_path.replace("\\", "/")

    library = get_cached_library()
    info = find_episode_info(library, rel_norm)

    if not info:
        abort(404)

    serie_name = info["serie_name"]
    episode_name = info["episode_name"]
    season_name = info.get("season_name", "")
    episode_index = info.get("episode_index")

    progress = load_progress()
    progress[rel_norm] = {
        "serie_name": serie_name,
        "episode_name": episode_name,
        "last_watched": datetime.now().isoformat(),
    }
    save_progress(progress)

    prev_episode, next_episode = get_prev_and_next_episode(
        library, serie_name, rel_norm
    )

    return render_template(
        "watch.html",
        relative_path=rel_norm,
        serie_name=serie_name,
        episode_name=episode_name,
        season_name=season_name,
        episode_index=episode_index,
        prev_episode=prev_episode,
        next_episode=next_episode,
    )


# ======================
# API de episódios por temporada
# ======================

@app.route("/api/serie/<serie_name>/temporada/<int:season_index>")
@login_required
def api_season(serie_name, season_index):
    library = get_cached_library()
    serie = library.get(serie_name)

    if not serie:
        return jsonify({"episodes": []})

    seasons = serie.get("seasons", [])
    if season_index < 0 or season_index >= len(seasons):
        return jsonify({"episodes": []})

    season = seasons[season_index]
    episodes_out = []

    for idx, ep in enumerate(season.get("episodes", []), start=1):
        if ep.get("thumb"):
            thumb_url = url_for("media_file", relative_path=ep["thumb"])
        else:
            thumb_url = url_for("static", filename="no-thumb.jpg")

        description = gerar_descricao_episodio(
            serie_name,
            season.get("name", f"Temporada {season_index+1}"),
            idx,
            ep["filename"],
        )

        episodes_out.append(
            {
                "number": idx,
                "filename": ep["filename"],
                "relative_path": ep["relative_path"],
                "thumb": thumb_url,
                "description": description,
            }
        )

    return jsonify({"episodes": episodes_out})


# ======================
# Arquivos de mídia
# ======================

@app.route("/stream/<path:relative_path>")
@login_required
def stream(relative_path):
    dir_name = os.path.dirname(relative_path)
    file_name = os.path.basename(relative_path)
    video_dir = os.path.join(MEDIA_ROOT, dir_name)

    file_path = os.path.join(video_dir, file_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(video_dir, file_name, as_attachment=False)


@app.route("/media/<path:relative_path>")
@login_required
def media_file(relative_path):
    dir_name = os.path.dirname(relative_path)
    file_name = os.path.basename(relative_path)
    base_dir = os.path.join(MEDIA_ROOT, dir_name)

    file_path = os.path.join(base_dir, file_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(base_dir, file_name, as_attachment=False)


# ======================
# Erros
# ======================

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # cria tabela users se não existir
    app.run(debug=True, host="0.0.0.0")
