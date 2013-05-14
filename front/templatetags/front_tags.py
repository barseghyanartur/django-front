from django import template
from classytags.core import Tag, Options
from classytags.arguments import Argument, MultiValueArgument
from django.core.cache import cache
from django.core.urlresolvers import reverse
from ..models import Placeholder
import hashlib


register = template.Library()


class FrontEditTag(Tag):
    name = 'front_edit'
    options = Options(
        Argument('name', resolve=False, required=True),
        MultiValueArgument('extra_bits', required=False, resolve=True),
        blocks=[
            ('end_front_edit', 'nodelist'),
        ]
    )

    def render_tag(self, context, name, extra_bits, nodelist=None):
        #print name, extra_bits, nodelist

        hash_val = hashlib.new('sha1', name + ''.join([unicode(token) for token in extra_bits])).hexdigest()
        cache_key = "front-edit-%s" % hash_val

        val = cache.get(cache_key)
        if val is None:
            try:
                val = Placeholder.objects.get(key=hash_val).value
                cache.set(cache_key, val, 3600 * 24)
            except Placeholder.DoesNotExist:
                pass

        if val is None and nodelist:
            val = nodelist.render(context)

        user = context.get('request', None) and context.get('request').user
        if user.is_staff:
            return '<div class="editable" id="%s">%s</div>' % (hash_val, unicode(val).strip())
        return val or ''


class FrontEditJS(Tag):
    name = 'front_edit_scripts'
    options = Options()

    def render_tag(self, context):
        static_url = context.get('STATIC_URL', '/static/')
        user = context.get('request', None) and context.get('request').user
        token = unicode(context.get('csrf_token'))
        if user.is_staff:
            return """
<script>
    document._front_edit = {
        save_url: '%s',
        csrf_token: '%s'
    };
</script>
<script src="%sfront/js/front-edit.js"></script>""".strip() % (
                reverse('front-placeholder-save'),
                token,
                static_url
            )
        else:
            return ''


register.tag(FrontEditTag)
register.tag(FrontEditJS)