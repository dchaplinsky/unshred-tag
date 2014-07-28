import os
SECRET_KEY = 'random-secret-key'
SESSION_COOKIE_NAME = 'unshred_session'
DEBUG = False

MONGODB_SETTINGS = {
    'DB': 'unshred',
    'HOST': 'localhost'
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
    # 'social.backends.vk.VKOAuth2',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

JS_ASSETS = ['jquery.js', 'bootstrap.js', 'string_score.js',
             'jquery.hotkeys.js', 'textext.core.js', 'textext.plugin.tags.js',
             'textext.plugin.autocomplete.js', 'textext.plugin.prompt.js',
             'textext.plugin.arrow.js', 'textext.plugin.suggestions.js',
             'jquery.magnific-popup.min.js', 'base.js']
JS_ASSETS_OUTPUT = 'packed.js'
JS_ASSETS_FILTERS = 'yui_js'

CSS_ASSETS = ['bootstrap.css', 'textext.core.css', 'textext.plugin.tags.css',
              'textext.plugin.prompt.css', 'textext.plugin.arrow.css',
              'textext.plugin.autocomplete.css', 'jquery.magnific-popup.css',
              'style.css']
CSS_ASSETS_OUTPUT = 'packed.css'
CSS_ASSETS_FILTERS = 'yui_css'

S3_ENABLED = False
S3_ACCESS_KEY_ID = os.environ.get("aws_access_key_id")
S3_SECRET_ACCESS_KEY = os.environ.get("aws_secret_access_key")
S3_SRC_BUCKET_NAME = 'kurchenko_pink'
S3_DST_BUCKET_NAME = 'kurchenko'

LOCAL_FS_SRC_DIR = '../cv/pink/'
LOCAL_FS_URL = 'http://localhost:5000/'
SPLIT_OUT_DIR = "static/out"
