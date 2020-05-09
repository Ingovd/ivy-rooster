from typing import Callable, Optional

from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   abort,
                   flash,
                   current_app as app)


from .templates.messages import *


""" Flask blueprint that handles the Rooster CRUD """
rooster_crud = Blueprint('rooster_crud', __name__, template_folder='templates')


# @rooster_crud.route('/', methods=['POST'])
# def handle_create_url(key=None):
#     form_url = request.form.get('long_url', '')
#     if keyurl := commit_url(app.keys.consume, form_url):
#         flash(USR_HTML_URL_ADD_1URL.format(app.short_url(keyurl.key)))
#         return redirect('/')
#     else:
#         return redirect(request.url_rule)


# @rooster_crud.route('/update/<key>', methods=['POST'])
# def handle_update_url(key=None):
#     if not (url := app.urls[key]):
#         abort(404)
#     form_url = request.form.get('long_url', '')
#     if keyurl := commit_url(lambda : key, form_url):
#         flash(USR_UPDATE_1URL_2URL.format(url, keyurl.url))
#         return redirect('/')
#     else:
#         return redirect(request.url_rule)


# @rooster_crud.route('/<key>')
# def handle_read_url(key):
#     """ Redirect route
    
#     TODO: Isolate the caching logic; there exists a caching decorator,
#           but I haven't tested if this caches 404's.
#     """

#     try:
#         if response := app.cache.get(key):
#             return response
#     except Exception as err:
#         app.logger.warning(APP_CACHE_1ERR.format(err))
#     if url := app.urls[key]:
#         response = redirect(url)
#     else:
#         abort(404)
#     try:
#         app.cache.set(key, response)
#     except Exception as err:
#         app.logger.warning(APP_CACHE_1ERR.format(err))
#     return response


# @rooster_crud.route('/delete/<key>')
# def handle_delete_url(key):
#     if url := app.urls[key]:
#         del app.urls[key]
#         flash(USR_URL_DEL_1URL.format(url))
#         return redirect('/')
#     abort(404)


@rooster_crud.route('/', methods=['GET'])
def show_index_view():
    return render_template('index.html')
