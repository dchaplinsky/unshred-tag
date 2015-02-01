import os
SECRET_KEY = 'random-secret-key'
SESSION_COOKIE_NAME = 'unshred_session'
DEBUG = True

MONGODB_SETTINGS = {
    'DB': os.environ.get("mongodb_db", "unshred"),
    'HOST': os.environ.get("mongodb_host", "localhost"),
    'USERNAME': os.environ.get("mongodb_username", None),
    'PASSWORD': os.environ.get("mongodb_password", None),
    'PORT': (int(os.environ.get("mongodb_port"))
             if os.environ.get("mongodb_port") else None)
}

DEBUG_TB_INTERCEPT_REDIRECTS = False
SESSION_PROTECTION = 'strong'

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

SOCIAL_AUTH_LOGIN_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'

SOCIAL_AUTH_USER_MODEL = 'models.user.User'
SOCIAL_AUTH_AUTHENTICATION_BACKENDS = (
    'social.backends.google.GoogleOAuth2',
    'social.backends.twitter.TwitterOAuth',
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.vk.VKOAuth2',
)

# Keypairs for social auth backends
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_VK_OAUTH2_KEY = ''
SOCIAL_AUTH_VK_APP_SECRET = ''

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

JS_ASSETS = ['vendor/jquery/jquery.js',
             'vendor/jquery.cookie/jquery.cookie.js',
             'vendor/bootstrap/bootstrap.js',
             'vendor/string_score/string_score.js',
             'vendor/jquery.hotkeys/jquery.hotkeys.js',
             'vendor/textext/js/textext.core.js',
             'vendor/textext/js/textext.plugin.tags.js',
             'vendor/textext/js/textext.plugin.autocomplete.js',
             'vendor/textext/js/textext.plugin.prompt.js',
             'vendor/textext/js/textext.plugin.arrow.js',
             'vendor/textext/js/textext.plugin.suggestions.js',
             # patch to add quicksilver search to textext suggestions
             'scripts/textext.plugin.suggestions.monkeypatch.js',
             'vendor/jquery.magnific-popup/jquery.magnific-popup.js',
             'vendor/jquery.rotate/jquery.rotate.js',
             # includes bugfix for this issue:
             # https://github.com/pklauzinski/jscroll/issues/39
             'vendor/jquery.jscroll/jquery.jscroll.js',
             'vendor/sceditor/jquery.sceditor.bbcode.js',

             'vendor/jquery.freetrans/jquery.freetrans.js',
             'vendor/jquery.freetrans/Matrix.js',

             'scripts/zoomer.js',  # includes customisation
             'scripts/base.js',
             'scripts/review.js',

             'scripts/unshred_api_client.js',

             # TODO: compile JSX offline and/or bundle with assets.
             #'vendor/react-0.13.1/react.min.js',
             #'vendor/react-0.13.1/JSXTransformer.js',
             ]
JS_ASSETS_OUTPUT = 'scripts/packed.js'

JS_ASSETS_FILTERS = 'yui_js'

CSS_ASSETS = ['vendor/bootstrap/bootstrap.css',
              'vendor/textext/css/textext.core.css',
              'vendor/textext/css/textext.plugin.tags.css',
              'vendor/textext/css/textext.plugin.prompt.css',
              'vendor/textext/css/textext.plugin.arrow.css',
              'vendor/textext/css/textext.plugin.autocomplete.css',
              'vendor/jquery.magnific-popup/jquery.magnific-popup.css',
              'vendor/sceditor/themes/square.css',
              'vendor/jquery.freetrans/jquery.freetrans.css',
              'styles/textext.overwrite.css',
              'styles/stitch.css',
              'styles/style.css']
CSS_ASSETS_OUTPUT = 'styles/packed.css'
CSS_ASSETS_FILTERS = 'yui_css'

S3_ENABLED = bool(os.environ.get("s3_enabled"))
S3_ACCESS_KEY_ID = os.environ.get("aws_access_key_id")
S3_SECRET_ACCESS_KEY = os.environ.get("aws_secret_access_key")
S3_SRC_BUCKET_NAME = 'kurchenko_pink'
S3_DST_BUCKET_NAME = 'kurchenko'

LOCAL_FS_SRC_DIR = '../cv/pink/'
LOCAL_FS_URL = 'http://localhost:5000/'
SPLIT_OUT_DIR = "static/out"

# Redundancy level for shreds processing
USERS_PER_SHRED = 2

# Restrict an access to site to admins only
SITE_IS_CLOSED = False

# Include fixtures.py blueprint that will provide set of endpoints to reset
# db and create test users/shreds/tags. Required mostly for UI testing.
# Enable with great care
ENABLE_FIXTURES_ENDPOINTS = False
